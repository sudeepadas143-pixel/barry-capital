"""KW (reports/KW_CONFIG.md, FROZEN): weekly-only variants vs the current weekly engine.
EXPLORATORY (all data examined before; tuning < 2018, 2018+ reported separately but not unseen).

    python scripts/kw_eval.py run
    python scripts/kw_eval.py render
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research import kenny_sim as KSIM, kenny_weekly as KWK, v5_data as DG, v5_gate as GT  # noqa: E402
from research import v5_ledger as LG, v5_manifest as MF  # noqa: E402

_s = importlib.util.spec_from_file_location("cycle2_research", ROOT / "scripts" / "cycle2_research.py")
C = importlib.util.module_from_spec(_s)
sys.modules["cycle2_research"] = C
_s.loader.exec_module(C)

CONFIG = GT.KW_CONFIG
OUT = ROOT / "reports" / "kw_results.json"
MD = ROOT / "reports" / "KW_RESULTS.md"
SPEC = ROOT / "reports" / "cycle2_model_spec.json"
SPLIT = pd.Timestamp("2018-01-01", tz="UTC")
GRID = [(h, th) for h in (4, 8) for th in (1.0, 1.5, 2.0, 2.5)]
VARIANTS = ("W1", "W2")
REPS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "SPY", "QQQ", "AAPL", "GLD")
SIDE = {"bot": 1, "top": -1}
CODE_FILES = list(GT.KW_CODE)


def sig_metrics(o, h, l, c, idx_t, idx, side):
    """Per-signal forward returns, 26-week MFE/MAE (%), distance and timing to the +-26w extreme."""
    rows = []
    n = len(c)
    for s in idx:
        if s + 1 >= n:
            continue
        px = o[s + 1]
        r = {"i": int(s), "t": idx_t[s]}
        for H in (13, 26, 52):
            r[f"f{H}"] = side * (c[s + H] / px - 1) if s + H < n else np.nan
        hi = min(n, s + 27)
        r["mfe"] = (h[s + 1:hi].max() / px - 1) if side > 0 else (1 - l[s + 1:hi].min() / px)
        r["mae"] = (1 - l[s + 1:hi].min() / px) if side > 0 else (h[s + 1:hi].max() / px - 1)
        a, b = max(0, s - 26), min(n, s + 27)
        if b - s < 27:
            r["dist"] = r["timing"] = np.nan
        elif side > 0:
            k = a + int(np.argmin(l[a:b]))
            r["dist"], r["timing"] = c[s] / l[k] - 1, s - k
        else:
            k = a + int(np.argmax(h[a:b]))
            r["dist"], r["timing"] = 1 - c[s] / h[k], s - k
        rows.append(r)
    return pd.DataFrame(rows)


def one(sym):
    r = C.build((sym, "1W"))
    if r is None:
        return None
    spec = json.loads(SPEC.read_text())
    o, h, l, c = r["ohlc"]
    df = DG.load(sym, "1W")
    assert df.index.equals(r["idx"])
    b0, s0, st = KSIM.shipped_signals(df, "1W", spec)
    sig = {"W0": {"bot": b0, "top": s0}}
    for v in VARIANTS:
        ev = KWK.evidence(df, st, v)
        for hl, th in GRID:
            b, s, _ = KWK.run(ev, hl, {"bot": th, "top": th})
            sig[f"{v}|{hl}|{th}"] = {"bot": b, "top": s}
    mets = {k: {d: sig_metrics(o, h, l, c, r["idx"], v[d], SIDE[d]).assign(sym=sym) for d in v} for k, v in sig.items()}
    yrs_pre = max(0.0, (min(SPLIT, r["idx"][-1]) - max(r["idx"][0], pd.Timestamp("2008-01-01", tz="UTC"))).total_seconds() / 3.15576e7)
    yrs_post = max(0.0, (r["idx"][-1] - max(SPLIT, r["idx"][0])).total_seconds() / 3.15576e7)
    r["sig"], r["mets"], r["yrs"] = sig, mets, (yrs_pre, yrs_post)
    return r


def agg(rows, key, d, period):
    T = pd.concat([r["mets"][key][d] for r in rows], ignore_index=True)
    T = T[T["t"] >= pd.Timestamp("2008-01-01", tz="UTC")]
    T = T[(T["t"] < SPLIT)] if period == "pre" else T[(T["t"] >= SPLIT)]
    yrs = sum(r["yrs"][0 if period == "pre" else 1] for r in rows)
    out = {"n": int(len(T)), "rate": len(T) / yrs if yrs else 0.0}
    if len(T):
        ep = 0
        for s, g in T.groupby("sym"):
            ii = np.sort(g["i"].to_numpy())
            ep += 1 + int(np.sum(np.diff(ii) > 6))
        out.update({"episodes_rate": ep / yrs, **{f"{k}_med": float(np.nanmedian(T[k])) for k in ("f13", "f26", "f52", "mfe", "mae", "dist", "timing")},
                    **{f"{k}_mean": float(np.nanmean(T[k])) for k in ("f13", "f26", "f52")}})
    return out


def label_quality(rows, key, d, period):
    al = {}
    for r in rows:
        a = r["sig"][key][d]
        t = r["idx"][a]
        al[r["sym"]] = a[(t >= SPLIT) if period == "post" else (t < SPLIT)]
    e = C.evaluate(rows, "1W", d, al, "warning", reps=199)
    det, tr = e.get("det") or {}, e.get("trade") or {}
    p = det.get("precision")
    return {"hit": (p[0] if isinstance(p, (list, tuple)) else p), "win": tr.get("win_rate"), "net13": tr.get("net_mean")}


def _commit_ledger(tid):
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"KW ledger: record trial {tid} (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    LG.verify_against_git(LG.LEDGER)


def run():
    mode = GT.require_kw_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    LG.record("kw-1W", "KW-1", ["exploration"], {"config": CONFIG, "mode": mode}, CODE_FILES,
              ["rate", "forward_return", "mfe", "mae", "distance", "timing", "hit_rate", "win_rate"], True, CONFIG, data_files,
              notes=f"exploration; review mode {mode}")
    _commit_ledger("kw-1W")
    with ProcessPoolExecutor(4) as ex:
        rows = [r for r in ex.map(one, DG.EVAL_SYMBOLS) if r is not None]
    R = {"instruments": len(rows), "tuning": {}, "chosen": {}, "results": {}, "reps": {}}
    for v in VARIANTS:
        for d in ("bot", "top"):
            best, bval = None, -np.inf
            for hl, th in GRID:
                a = agg(rows, f"{v}|{hl}|{th}", d, "pre")
                R["tuning"][f"{v}|{d}|{hl}|{th}"] = a
                if a["n"] < 25 or a["rate"] < 0.05:
                    continue
                if a["f26_med"] > bval:
                    best, bval = (hl, th), a["f26_med"]
            R["chosen"][f"{v}|{d}"] = best
    for d in ("bot", "top"):
        keys = {"W0": "W0"}
        for v in VARIANTS:
            if R["chosen"][f"{v}|{d}"]:
                hl, th = R["chosen"][f"{v}|{d}"]
                keys[v] = f"{v}|{hl}|{th}"
        for name, key in keys.items():
            R["results"][f"{name}|{d}"] = {p: {**agg(rows, key, d, p), **label_quality(rows, key, d, p)} for p in ("pre", "post")}
    # adoption (KW_CONFIG.md)
    R["adopt"] = {}
    for d in ("bot", "top"):
        base = R["results"][f"W0|{d}"]["post"]
        ok = []
        for v in VARIANTS:
            x = R["results"].get(f"{v}|{d}", {}).get("post")
            if x and x["n"] and x["f26_med"] > base.get("f26_med", -np.inf) and (x["hit"] or 0) >= (base["hit"] or 0) - 0.05 and x["rate"] >= 0.05:
                ok.append(v)
        R["adopt"][d] = max(ok, key=lambda v: R["results"][f"{v}|{d}"]["pre"]["f26_med"]) if ok else "W0"
    for r in rows:
        if r["sym"] in REPS:
            R["reps"][r["sym"]] = {}
            for d in ("bot", "top"):
                for name in ("W0", R["adopt"][d]) if R["adopt"][d] != "W0" else ("W0", *[v for v in VARIANTS if R["chosen"][f"{v}|{d}"]]):
                    key = name if name == "W0" else f"{name}|{R['chosen'][f'{name}|{d}'][0]}|{R['chosen'][f'{name}|{d}'][1]}"
                    T = r["mets"][key][d]
                    R["reps"][r["sym"]][f"{name}|{d}"] = [{"date": str(x["t"].date()), "f26": x["f26"], "dist": x["dist"], "timing": x["timing"]}
                                                          for _, x in T.iterrows()]
    R["meta"] = {"mode": mode, "config": CONFIG, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(R, indent=1, default=str))
    print("done", flush=True)


def _p(x, pct=True, s=True):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    return (f"{x * 100:+.1f}%" if s else f"{x * 100:.1f}%") if pct else f"{x:.2f}"


def render():
    R = json.loads(OUT.read_text())
    L = ["# KW: weekly engine variants (EXPLORATORY)", "",
         f"Config `reports/KW_CONFIG.md`; {R['instruments']} instruments, weekly candles from 2008. Tuning < 2018; 2018+ shown separately "
         "(examined in earlier research, so not unseen). Forward returns are in the signal direction (SELL: positive = price fell).", "",
         "Chosen (h weeks, θ) on pre-2018: " + ", ".join(f"{k} {v}" for k, v in R["chosen"].items()) + ".", "",
         "| side · variant · period | signals/asset-yr | episodes/asset-yr | n | fwd 13w | fwd 26w (median / mean) | fwd 52w | MFE/MAE 26w | dist. from extreme | timing (weeks vs extreme) | major-turn hit | barrier win |",
         "|---|---:|---:|---:|---:|---|---:|---|---:|---:|---:|---:|"]
    for d in ("bot", "top"):
        for name in ("W0", *VARIANTS):
            x = R["results"].get(f"{name}|{d}")
            if not x:
                continue
            for p in ("pre", "post"):
                v = x[p]
                if not v["n"]:
                    L.append(f"| {'BUY' if d == 'bot' else 'SELL'} · {name} · {p} | 0 | | 0 | | | | | | | | |")
                    continue
                L.append(f"| {'BUY' if d == 'bot' else 'SELL'} · {name} · {'<2018' if p == 'pre' else '2018+'} | {v['rate']:.2f} | {v['episodes_rate']:.2f} | {v['n']} | "
                         f"{_p(v['f13_med'])} | {_p(v['f26_med'])} / {_p(v['f26_mean'])} | {_p(v['f52_med'])} | {_p(v['mfe_med'], s=False)}/{_p(v['mae_med'], s=False)} | "
                         f"{_p(v['dist_med'], s=False)} | {v['timing_med']:+.0f} | {_p(v['hit'], pct=False)} | {_p(v['win'], pct=False)} |")
    L += ["", f"**Adopted:** BUY {R['adopt']['bot']}, SELL {R['adopt']['top']}.", "", "## Representative instruments (chart review; not used for tuning)", ""]
    for sym, D in R["reps"].items():
        L.append(f"**{sym}**")
        for k, lst in D.items():
            name, d = k.split("|")
            txt = "; ".join(f"{e['date']} ({_p(e['f26'])} 26w, {e['timing']:+.0f}w)" if e["timing"] == e["timing"] else f"{e['date']} (open)" for e in lst) or "none"
            L.append(f"* {'BUY' if d == 'bot' else 'SELL'} {name}: {txt}")
        L.append("")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run()
    elif len(sys.argv) > 1 and sys.argv[1] == "render":
        render()
    else:
        print(__doc__)
