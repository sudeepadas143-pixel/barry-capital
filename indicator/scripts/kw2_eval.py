"""KW-2 (reports/KW2_CONFIG.md, FROZEN): targeted fixes for the two weekly defects found in KW-1
(SELL firing after crashes; BUY absent on high-volatility charts). EXPLORATORY; tuning < 2018.

    python scripts/kw2_eval.py run
    python scripts/kw2_eval.py render
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research import kenny_sim as KSIM, kenny_weekly as KWK, v5_data as DG, v5_gate as GT  # noqa: E402
from research import v5_ledger as LG, v5_manifest as MF  # noqa: E402

_s = importlib.util.spec_from_file_location("kw_eval", ROOT / "scripts" / "kw_eval.py")
KE = importlib.util.module_from_spec(_s)
sys.modules["kw_eval"] = KE
_s.loader.exec_module(KE)
C = KE.C

CONFIG = GT.KW2_CONFIG
OUT = ROOT / "reports" / "kw2_results.json"
MD = ROOT / "reports" / "KW2_RESULTS.md"
GRID = {"top": {"X1": (2.0, 4.0, 6.0), "X2": (2.0, 4.0, 6.0)}, "bot": {"Y1": (0.02, 0.05), "Y2": (0.02, 0.05)}}
CODE_FILES = list(GT.KW2_CODE)


def one(sym):
    r = C.build((sym, "1W"))
    if r is None:
        return None
    spec = json.loads(KE.SPEC.read_text())
    o, h, l, c = r["ohlc"]
    df = DG.load(sym, "1W")
    assert df.index.equals(r["idx"])
    b0, s0, st = KSIM.shipped_signals(df, "1W", spec)
    sig = {"W0": {"bot": b0, "top": s0}}
    for v, ps in GRID["top"].items():
        for g in ps:
            sig[f"{v}|{g}"] = {"top": KWK.kw2_sell(df, st, v, g), "bot": np.array([], int)}
    for v, ps in GRID["bot"].items():
        for q in ps:
            sig[f"{v}|{q}"] = {"bot": KWK.kw2_buy(df, st, v, q), "top": np.array([], int)}
    r["sig"] = sig
    r["mets"] = {k: {d: KE.sig_metrics(o, h, l, c, r["idx"], v[d], KE.SIDE[d]).assign(sym=sym) for d in v} for k, v in sig.items()}
    pre = max(0.0, (min(KE.SPLIT, r["idx"][-1]) - max(r["idx"][0], KE.pd.Timestamp("2008-01-01", tz="UTC"))).total_seconds() / 3.15576e7)
    post = max(0.0, (r["idx"][-1] - max(KE.SPLIT, r["idx"][0])).total_seconds() / 3.15576e7)
    r["yrs"] = (pre, post)
    return r


def _commit_ledger(tid):
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"KW ledger: record trial {tid} (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    LG.verify_against_git(LG.LEDGER)


def run():
    mode = GT.require_kw2_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    LG.record("kw2-1W", "KW-2", ["exploration"], {"config": CONFIG, "mode": mode}, CODE_FILES,
              ["rate", "forward_return", "mfe", "mae", "distance", "timing", "hit_rate", "win_rate"], True, CONFIG, data_files,
              notes=f"exploration; review mode {mode}")
    _commit_ledger("kw2-1W")
    with ProcessPoolExecutor(4) as ex:
        rows = [r for r in ex.map(one, DG.EVAL_SYMBOLS) if r is not None]
    R = {"instruments": len(rows), "tuning": {}, "chosen": {}, "results": {}, "reps": {}}
    for d, vs in GRID.items():
        for v, ps in vs.items():
            best, bval = None, -np.inf
            for prm in ps:
                a = KE.agg(rows, f"{v}|{prm}", d, "pre")
                R["tuning"][f"{v}|{d}|{prm}"] = a
                if a["n"] >= 25 and a["rate"] >= 0.05 and a["f26_med"] > bval:
                    best, bval = prm, a["f26_med"]
            R["chosen"][f"{v}|{d}"] = best
    for d, vs in GRID.items():
        keys = {"W0": "W0", **{v: f"{v}|{R['chosen'][f'{v}|{d}']}" for v in vs if R["chosen"][f"{v}|{d}"] is not None}}
        for name, key in keys.items():
            R["results"][f"{name}|{d}"] = {p: {**KE.agg(rows, key, d, p), **KE.label_quality(rows, key, d, p)} for p in ("pre", "post")}
    R["adopt"] = {}
    for d, vs in GRID.items():
        base = R["results"][f"W0|{d}"]["post"]
        ok = [v for v in vs if (x := R["results"].get(f"{v}|{d}", {}).get("post")) and x["n"] and x["f26_med"] > base.get("f26_med", -np.inf)
              and (x["hit"] or 0) >= (base["hit"] or 0) - 0.05 and x["rate"] >= 0.05]
        R["adopt"][d] = max(ok, key=lambda v: R["results"][f"{v}|{d}"]["pre"]["f26_med"]) if ok else "W0"
    for r in rows:
        if r["sym"] in KE.REPS:
            R["reps"][r["sym"]] = {}
            for d, vs in GRID.items():
                for name in ("W0", *[v for v in vs if R["chosen"][f"{v}|{d}"] is not None]):
                    key = name if name == "W0" else f"{name}|{R['chosen'][f'{name}|{d}']}"
                    R["reps"][r["sym"]][f"{name}|{d}"] = [{"date": str(x["t"].date()), "f26": x["f26"], "timing": x["timing"]}
                                                          for _, x in r["mets"][key][d].iterrows()]
    R["meta"] = {"mode": mode, "config": CONFIG, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(R, indent=1, default=str))
    print("done", flush=True)


def render():
    R = json.loads(OUT.read_text())
    p_ = KE._p
    L = ["# KW-2: targeted weekly fixes (EXPLORATORY)", "",
         f"Config `reports/KW2_CONFIG.md`; {R['instruments']} instruments, weekly candles from 2008. Tuning < 2018; 2018+ examined before (not unseen). "
         "Forward returns in the signal direction (SELL: positive = price fell).", "",
         "Chosen on pre-2018: " + ", ".join(f"{k} {v}" for k, v in R["chosen"].items()) + ".", "",
         "| side · variant · period | signals/asset-yr | n | fwd 13w | fwd 26w (median / mean) | fwd 52w | MFE/MAE 26w | dist. from extreme | timing (weeks) | major-turn hit | barrier win |",
         "|---|---:|---:|---:|---|---:|---|---:|---:|---:|---:|"]
    for k, x in R["results"].items():
        name, d = k.split("|")
        for p in ("pre", "post"):
            v = x[p]
            if not v["n"]:
                continue
            L.append(f"| {'BUY' if d == 'bot' else 'SELL'} · {name} · {'<2018' if p == 'pre' else '2018+'} | {v['rate']:.2f} | {v['n']} | {p_(v['f13_med'])} | "
                     f"{p_(v['f26_med'])} / {p_(v['f26_mean'])} | {p_(v['f52_med'])} | {p_(v['mfe_med'], s=False)}/{p_(v['mae_med'], s=False)} | "
                     f"{p_(v['dist_med'], s=False)} | {v['timing_med']:+.0f} | {p_(v['hit'], pct=False)} | {p_(v['win'], pct=False)} |")
    L += ["", f"**Adopted:** BUY {R['adopt']['bot']}, SELL {R['adopt']['top']}.", "", "## Representative instruments (chart review; not used for tuning)", ""]
    for sym, D in R["reps"].items():
        L.append(f"**{sym}**")
        for k, lst in D.items():
            name, d = k.split("|")
            txt = "; ".join(f"{e['date']} ({p_(e['f26'])} 26w)" if e["f26"] == e["f26"] else f"{e['date']} (open)" for e in lst) or "none"
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
