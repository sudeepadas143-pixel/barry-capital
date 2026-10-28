"""KW-3: weekly SELL recovery. Stage 1 `diag` (reports/KW3_DIAG_CONFIG.md, pre-2018 only) and stage 2
`eval` (reports/KW3_CONFIG.md). EXPLORATORY (all data examined before; 2018+ is a robustness check).

    python scripts/kw3_eval.py diag | eval | render
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

from hcmtf.universe import COST_BPS  # noqa: E402
from research import kenny_sim as KSIM, kenny_weekly_sell as WS, v5_data as DG, v5_gate as GT  # noqa: E402
from research import v5_ledger as LG, v5_manifest as MF  # noqa: E402

_s = importlib.util.spec_from_file_location("cycle2_research", ROOT / "scripts" / "cycle2_research.py")
C = importlib.util.module_from_spec(_s)
sys.modules["cycle2_research"] = C
_s.loader.exec_module(C)

SPEC = ROOT / "reports" / "cycle2_model_spec.json"
SPLIT = pd.Timestamp("2018-01-01", tz="UTC")
START = pd.Timestamp("2008-01-01", tz="UTC")
DIAG_OUT, DIAG_MD = ROOT / "reports" / "kw3_diag.json", ROOT / "reports" / "KW3_DIAG.md"
OUT, MD = ROOT / "reports" / "kw3_results.json", ROOT / "reports" / "KW3_RESULTS.md"
CHARS = ("ext26", "ext40", "dd52", "rally52", "tsm", "roc13", "roc13_acc", "rsi", "rsi_max8", "div8", "vratio", "wick_up",
         "rev4", "failed4", "slope40")
CLASS_OF = {"equity": "equities", "equity_index": "equities", "crypto": "crypto"}


def _roll_any(x, n):
    x = np.asarray(x, float)
    return np.convolve(np.nan_to_num(x), np.ones(n), "full")[:len(x)] > 0


def chars_at(f, i):
    return {k: float(f[k][i]) if k in f else np.nan for k in CHARS}


def prep(sym):
    r = C.build((sym, "1W"))
    if r is None:
        return None
    df = DG.load(sym, "1W")
    assert df.index.equals(r["idx"])
    spec = json.loads(SPEC.read_text())
    _, s0, st = KSIM.shipped_signals(df, "1W", spec)
    f = WS.features(df)
    f["div8"] = _roll_any(f["div"], 8).astype(float)
    f["rev4"] = _roll_any((f["star"] | f["engulf"]).astype(float), 4).astype(float)
    f["failed4"] = _roll_any(f["failed_high"].astype(float), 4).astype(float)
    o, h, l, c = r["ohlc"]
    prior_dd = (WS.highest(h, 26) - c) / f["atr"]
    return r, df, st, s0, f, (o, h, l, c), prior_dd


# ----------------------------------------------------------------------------- stage 1

def diag_one(sym):
    p = prep(sym)
    if p is None:
        return None
    r, df, st, s0, f, (o, h, l, c), prior_dd = p
    idx = r["idx"]
    cut = int(idx.searchsorted(SPLIT))
    rows = []
    for s in s0:
        if s + WS.H >= cut:                                   # outcome must lie entirely before 2018
            continue
        rows.append({"sym": sym, "cls": r["cls"], "t": str(idx[s].date()), "class": WS.classify(h, l, c, f["atr"], s, prior_dd[s]), **chars_at(f, s)})
    miss = []
    sig = np.asarray(s0, int)
    for e in r["labs"]["top"].events:
        if e + 4 >= cut:
            continue
        if not ((sig >= e - 13) & (sig <= e + 4)).any():
            miss.append({"sym": sym, "cls": r["cls"], "t": str(idx[e].date()), "class": "missed_top", **chars_at(f, e)})
    return rows + miss


def diag():
    mode = GT.require_kw3d_ready()
    data_files = _data_files()
    LG.record("kw3-diag", "KW-3D", ["exploration"], {"config": GT.KW3D_CONFIG, "mode": mode}, list(GT.KW3D_CODE),
              ["class_counts", "characteristics"], True, GT.KW3D_CONFIG, data_files, notes="pre-2018 diagnosis only")
    _commit_ledger("kw3-diag")
    with ProcessPoolExecutor(4) as ex:
        rows = [x for rs in ex.map(diag_one, DG.EVAL_SYMBOLS) if rs for x in rs]
    T = pd.DataFrame(rows)
    out = {"n": len(T), "counts": T["class"].value_counts().to_dict(),
           "by_asset": T.groupby([T["cls"].map(CLASS_OF).fillna("other"), "class"]).size().unstack(fill_value=0).to_dict(orient="index"),
           "medians": T.groupby("class")[list(CHARS)].median().to_dict(orient="index")}
    DIAG_OUT.write_text(json.dumps(out, indent=1, default=str))
    L = ["# KW-3 stage 1: why the weekly SELL fails (pre-2018 development data)", "",
         f"{len(T)} W0 SELL signals (outcome window before 2018) plus missed labelled major tops. Classes per `reports/KW3_DIAG_CONFIG.md`.", "",
         "| class | n | " + " | ".join(CHARS) + " |", "|---|---:|" + "---:|" * len(CHARS)]
    for k, v in out["medians"].items():
        L.append(f"| {k} | {out['counts'][k]} | " + " | ".join(f"{v[c]:.2f}" for c in CHARS) + " |")
    L += ["", "By asset group (counts):", "", "| group | " + " | ".join(sorted(out["counts"])) + " |", "|---|" + "---:|" * len(out["counts"])]
    for g, d in out["by_asset"].items():
        L.append(f"| {g} | " + " | ".join(str(d.get(k, 0)) for k in sorted(out["counts"])) + " |")
    DIAG_MD.write_text("\n".join(L) + "\n")
    print("wrote", DIAG_MD)


# ----------------------------------------------------------------------------- stage 2

def signals(f, st, low, cand, prm):
    if cand == "A":
        return WS.cand_A(f, prm)
    if cand == "B":
        return WS.cand_B(f, prm)
    if cand == "C":
        return WS.cand_C_signals(f, st["top"]["K_S"], prm, low)
    raise ValueError(cand)


def metrics_one(sym, grid):
    p = prep(sym)
    if p is None:
        return None
    r, df, st, s0, f, (o, h, l, c), prior_dd = p
    idx = r["idx"]
    sets = {"W0": np.asarray(s0, int), "SMA40x": WS.base_sma40_cross(f), "RSI70": WS.base_rsi70(f)}
    for cand, prms in grid.items():
        for prm in prms:
            sets[f"{cand}|{prm}"] = signals(f, st, l, cand, prm)
    cost = COST_BPS[r["cls"]] / 1e4
    rows = []
    for name, sig in sets.items():
        for s in sig:
            if idx[s] < START or s + 1 >= len(c):
                continue
            px = o[s + 1]
            row = {"name": name, "sym": sym, "grp": CLASS_OF.get(r["cls"], "other"), "t": idx[s], "class": WS.classify(h, l, c, f["atr"], s, prior_dd[s]),
                   "strong_up": bool(np.nan_to_num(f["tsm"][s]) >= 1.0)}
            for Hh in (4, 13, 26):
                row[f"dec{Hh}"] = WS.decline_within(h, l, c, f["atr"], s, Hh)
                row[f"f{Hh}"] = -(c[s + Hh] / px - 1) if s + Hh < len(c) else np.nan
            end = min(len(c), s + 27)
            row["mfe"] = 1 - l[s + 1:end].min() / px
            row["mae"] = h[s + 1:end].max() / px - 1
            row["net13"] = row["f13"] - cost if row["f13"] == row["f13"] else np.nan
            a, b = max(0, s - 26), min(len(c), s + 27)
            row["lag"] = float(s - (a + int(np.argmax(h[a:b])))) if b - s >= 27 else np.nan
            rows.append(row)
    tops = []
    for e in r["labs"]["top"].events:
        if idx[e] < START or e + 4 >= len(c):
            continue
        tops.append({"sym": sym, "grp": CLASS_OF.get(r["cls"], "other"), "t": idx[e],
                     **{name: bool(((np.asarray(sig) >= e - 13) & (np.asarray(sig) <= e + 2)).any()) for name, sig in sets.items()}})
    yrs = {"pre": max(0.0, (min(SPLIT, idx[-1]) - max(idx[0], START)).total_seconds() / 3.15576e7),
           "post": max(0.0, (idx[-1] - max(SPLIT, idx[0])).total_seconds() / 3.15576e7)}
    return {"sym": sym, "grp": CLASS_OF.get(r["cls"], "other"), "rows": rows, "tops": tops, "yrs": yrs}


def summary(R, name, period, grp=None):
    T = R["T"]
    T = T[(T["name"] == name) & ((T["t"] < SPLIT) if period == "pre" else (T["t"] >= SPLIT))]
    tops = R["tops"]
    tops = tops[(tops["t"] < SPLIT) if period == "pre" else (tops["t"] >= SPLIT)]
    yrs = sum(x["yrs"][period] for x in R["res"] if grp is None or x["grp"] == grp)
    if grp:
        T, tops = T[T["grp"] == grp], tops[tops["grp"] == grp]
    out = {"n": int(len(T)), "rate": len(T) / yrs if yrs else 0.0, "top_catch": float(tops[name].mean()) if len(tops) and name in tops else np.nan,
           "n_tops": int(len(tops))}
    if len(T):
        cls = T["class"].value_counts(normalize=True)
        out.update({"useful": float(cls.get("useful", 0)), "premature": float(cls.get("premature", 0)), "late": float(cls.get("late", 0)),
                    "false_reversal": float(cls.get("false_reversal", 0)),
                    **{f"dec{h}": float(np.nanmean(T[f"dec{h}"])) for h in (4, 13, 26)},
                    **{f"f{h}_med": float(np.nanmedian(T[f"f{h}"])) for h in (4, 13, 26)},
                    "mfe_med": float(np.nanmedian(T["mfe"])), "mae_med": float(np.nanmedian(T["mae"])), "lag_med": float(np.nanmedian(T["lag"])),
                    "net13_mean": float(np.nanmean(T["net13"])),
                    "strong_up_share": float(T["strong_up"].mean()),
                    "strong_up_premature": float((T[T["strong_up"]]["class"] == "premature").mean()) if T["strong_up"].any() else np.nan,
                    "inst_useful_median": float(T.groupby("sym")["class"].apply(lambda x: (x == "useful").mean()).median())})
    return out


def evaluate():
    cfg = json.loads((ROOT / "reports" / "kw3_grid.json").read_text())
    mode = GT.require_kw3_ready()
    LG.record("kw3-eval", "KW-3", ["exploration"], {"config": GT.KW3_CONFIG, "mode": mode}, list(GT.KW3_CODE),
              ["useful_rate", "decline_rate", "forward_return", "mfe", "mae", "top_catch", "lag", "false_alerts", "net_return"], True,
              GT.KW3_CONFIG, _data_files(), notes=f"exploration; review mode {mode}")
    _commit_ledger("kw3-eval")
    grid = {k: v for k, v in cfg["grid"].items()}
    with ProcessPoolExecutor(4) as ex:
        res = [x for x in ex.map(metrics_one, DG.EVAL_SYMBOLS, [grid] * len(DG.EVAL_SYMBOLS)) if x]
    T = pd.DataFrame([row for x in res for row in x["rows"]])
    tops = pd.DataFrame([t for x in res for t in x["tops"]])
    R = {"T": T, "tops": tops, "res": res}
    # walk-forward parameter choice per candidate: for each test year >= 2012 use the best pre-year useful rate
    chosen, wf_rows = {}, []
    for cand, prms in grid.items():
        pre = {prm: summary(R, f"{cand}|{prm}", "pre") for prm in prms}
        ok = {prm: v for prm, v in pre.items() if v["n"] >= 25}
        chosen[cand] = max(ok, key=lambda p: (ok[p]["useful"], ok[p]["f26_med"])) if ok else prms[0]
        for y in range(2012, 2027):
            hist = T[(T["t"] < pd.Timestamp(f"{y}-01-01", tz="UTC") - pd.Timedelta(weeks=27))]   # outcome windows closed before y
            best, bu = prms[0], -1
            for prm in prms:
                g = hist[hist["name"] == f"{cand}|{prm}"]
                if len(g) >= 25 and (u := (g["class"] == "useful").mean()) > bu:
                    best, bu = prm, u
            yr = T[(T["name"] == f"{cand}|{best}") & (T["t"] >= pd.Timestamp(f"{y}-01-01", tz="UTC")) & (T["t"] < pd.Timestamp(f"{y + 1}-01-01", tz="UTC"))]
            wf_rows.append(yr.assign(name=f"{cand}|WF"))
    T = pd.concat([T, *wf_rows], ignore_index=True)
    for cand in grid:                                                  # top catch for WF uses the frozen pre-2018 choice
        tops[f"{cand}|WF"] = tops[f"{cand}|{chosen[cand]}"]
    R["T"], R["tops"] = T, tops
    names = ["W0", "SMA40x", "RSI70", *[f"{c}|{chosen[c]}" for c in grid], *[f"{c}|WF" for c in grid]]
    out = {"chosen": chosen, "results": {}}
    for nm in names:
        out["results"][nm] = {p: {"all": summary(R, nm, p), **{g: summary(R, nm, p, g) for g in ("equities", "crypto", "other")}} for p in ("pre", "post")}
    out["adopt"] = adopt(out, grid)
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print("done", flush=True)


def adopt(out, grid):
    """KW3_CONFIG.md adoption rule."""
    base = out["results"]["W0"]
    verdict = {}
    for cand in grid:
        nm = f"{cand}|WF"
        x, b = out["results"][nm], base
        why = []
        for p in ("pre", "post"):
            xa, ba = x[p]["all"], b[p]["all"]
            if not xa["n"]:
                why.append(f"{p}: no signals")
                continue
            if xa["useful"] < ba["useful"] + 0.05:
                why.append(f"{p}: useful {xa['useful']:.2f} < W0 {ba['useful']:.2f} + 0.05")
            if xa["f26_med"] < ba["f26_med"] + 0.01:
                why.append(f"{p}: 26w median {xa['f26_med']:+.3f} < W0 {ba['f26_med']:+.3f} + 0.01")
        xp, bp = x["post"]["all"], b["post"]["all"]
        if xp["n"]:
            if xp["top_catch"] < bp["top_catch"] - 0.05:
                why.append(f"post: top catch {xp['top_catch']:.2f} < W0 {bp['top_catch']:.2f} - 0.05")
            if xp["rate"] > 2 * bp["rate"]:
                why.append(f"post: rate {xp['rate']:.2f} > 2x W0 {bp['rate']:.2f}")
            if xp["lag_med"] > bp["lag_med"] + 2:
                why.append(f"post: median lag {xp['lag_med']:+.0f} > W0 {bp['lag_med']:+.0f} + 2")
            for g in ("equities", "crypto"):
                xg, bg = x["post"][g], b["post"][g]
                if xg["n"] >= 20 and bg["n"] >= 20 and xg["useful"] <= bg["useful"]:
                    why.append(f"post {g}: useful {xg['useful']:.2f} <= W0 {bg['useful']:.2f}")
        verdict[cand] = {"pass": not why, "why": why}
    ok = [c for c, v in verdict.items() if v["pass"]]
    best = max(ok, key=lambda c: out["results"][f"{c}|WF"]["pre"]["all"]["useful"]) if ok else None
    return {"verdict": verdict, "adopted": best}


def render():
    out = json.loads(OUT.read_text())
    L = ["# KW-3: weekly SELL recovery (EXPLORATORY)", "",
         "Config `reports/KW3_CONFIG.md`. Weekly EVAL instruments from 2008. <2018 = development; 2018+ = robustness check on data examined "
         "in earlier research (not unseen). `|WF` = parameter chosen walk-forward per year on earlier signals. Forward returns are in the SELL "
         "direction (positive = price fell). Decline = price falls 3 weekly ATR below the signal close within the horizon.", "",
         f"Pre-2018 parameter choice: {out['chosen']}.", ""]
    hdr = ("| signal · period · group | n | /inst-yr | useful | premature | late | false rev. | decline 4/13/26w | fwd 4/13/26w (median) | MFE/MAE 26w | "
           "major tops caught | lag vs peak (w) | strong-uptrend share / premature there | net 13w short after costs |")
    L += [hdr, "|---|---:|---:|---:|---:|---:|---:|---|---|---|---:|---:|---|---:|"]
    for nm, x in out["results"].items():
        for p in ("pre", "post"):
            for g in ("all", "equities", "crypto"):
                v = x[p][g]
                if not v["n"]:
                    continue
                L.append(f"| {nm} · {'<2018' if p == 'pre' else '2018+'} · {g} | {v['n']} | {v['rate']:.2f} | {v['useful']:.2f} | {v['premature']:.2f} | "
                         f"{v['late']:.2f} | {v['false_reversal']:.2f} | {v['dec4']:.2f}/{v['dec13']:.2f}/{v['dec26']:.2f} | "
                         f"{v['f4_med'] * 100:+.1f}/{v['f13_med'] * 100:+.1f}/{v['f26_med'] * 100:+.1f}% | {v['mfe_med'] * 100:.1f}/{v['mae_med'] * 100:.1f}% | "
                         f"{v['top_catch']:.2f} of {v['n_tops']} | {v['lag_med']:+.0f} | {v['strong_up_share']:.2f} / {v['strong_up_premature']:.2f} | "
                         f"{v['net13_mean'] * 100:+.2f}% |")
    L += ["", "## Adoption (KW3_CONFIG.md)", ""]
    for c, v in out["adopt"]["verdict"].items():
        L.append(f"* {c}: {'PASS' if v['pass'] else 'fail'}" + ("" if v["pass"] else " — " + "; ".join(v["why"])))
    L.append(f"\n**Adopted: {out['adopt']['adopted'] or 'none (W0 kept)'}.**")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


def _data_files():
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    LG.verify_against_git(LG.LEDGER)
    return sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})


def _commit_ledger(tid):
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"KW3 ledger: record trial {tid} (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    LG.verify_against_git(LG.LEDGER)


if __name__ == "__main__":
    {"diag": diag, "eval": evaluate, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
