"""v3 validation, as pre-registered in reports/PREREG_V3.md (read that first).

    python -m hcmtf.v3            # all timeframes → reports/V3_RESULTS.md, v3_results.json
    python -m hcmtf.v3 --render   # markdown only

Nothing here changes the engine. It measures configurations C0–C6 and baselines B1/B2 on all 70
symbols, bullish and bearish separately, with
  * random-entry p-values (same symbols, dates, count and side),
  * combinatorial purged CV (purgedcv) for the "pick the best configuration" question,
  * probability of backtest overfitting (finlab, CSCV) across C0–C6,
  * deflated Sharpe ratios (finlab) with n_trials = 60,
and applies the pre-registered verdict rule.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import engine as G, evaluate as E, study as St
from .metrics import boot_diff, cluster_ci, holm, random_baseline
from .report2 import active_params
from .universe import FRESH, UNIVERSE

OUT = Path(__file__).resolve().parent.parent / "reports"
TFS = ["1H", "4H", "1D", "1W"]
CONFIGS = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "B1", "B2"]
CANDIDATES = ["C0", "C1", "C2", "C3", "C4", "C5", "C6"]
NAMES = {"C0": "every structure break", "C1": "with-HTF breaks (MAJOR+CONFIRMED)", "C2": "MAJOR (shipped)",
         "C3": "CONFIRMED", "C4": "MAJOR + acceptance", "C5": "with-HTF + acceptance",
         "C6": "counter-HTF reversals (suppressed)", "B1": "EMA 20/50 cross", "B2": "Supertrend flip"}
GROUPS = {"crypto": ("crypto",), "equities": ("equity", "equity_index"), "commodities": ("commodity",),
          "rates_fx": ("bond", "fx")}
N_TRIALS = 60
BUCKET = {"1H": "W", "4H": "W", "1D": "M", "1W": "M"}
BAR = {"1H": pd.Timedelta(hours=1), "4H": pd.Timedelta(hours=4), "1D": pd.Timedelta(days=1), "1W": pd.Timedelta(weeks=1)}


def group_of(cls: str) -> str:
    return next(g for g, members in GROUPS.items() if cls in members)


def regime(f) -> np.ndarray:
    """Regime Detector logic: volatile / range / up / down, per candle, causal."""
    from . import ta
    e = ta.ema(f.c, 100)
    slope = e - ta.shift(e, 20)
    out = np.where(f.vol_rank >= 80, "volatile",
                   np.where(f.adx < 20, "range", np.where((f.c > e) & (slope > 0), "trend_up",
                                                          np.where((f.c < e) & (slope < 0), "trend_down", "transition"))))
    return out


def events_for(s: St.Series, tf: str, start) -> pd.DataFrame:
    p = active_params(tf)
    pa = G.with_(p, accept=True)
    trig = s.trig[s.trig["warm"]]
    sig = St.signals_for(s, p)
    sga = St.signals_for(s, pa)
    trade = lambda x: x[x["tier"].isin(["major", "confirmed"])]
    sets = {
        "C0": trig[["i", "dir", "level"]],
        "C1": trade(sig), "C2": sig[sig["tier"] == "major"], "C3": sig[sig["tier"] == "confirmed"],
        "C4": sga[sga["tier"] == "major"], "C5": trade(sga),
        "C6": trig[trig["cls"] == "counter_reversal"],
        "B1": s.base["ema_cross"], "B2": s.base["supertrend"],
    }
    reg = regime(s.f)
    rows = []
    for k, ev in sets.items():
        ev = ev[["i", "dir"] + (["level"] if "level" in ev else [])].copy()
        ev = ev[s.index[ev["i"].to_numpy(int)] >= start]
        if len(ev) == 0:
            continue
        ev = St.tag(s, ev)
        ev["config"] = k
        ev["group"] = group_of(s.cls)
        ev["regime"] = reg[ev["i"].to_numpy(int)]
        rows.append(ev)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def collect(tf: str):
    series = St.prepare(tf, UNIVERSE + FRESH)
    start = pd.Timestamp(St.WINDOWS[tf][0][0], tz="UTC")
    ev = pd.concat([events_for(s, tf, start) for s in series], ignore_index=True)
    return series, ev, start


# ------------------------------------------------------------------ statistics


def bucket_matrix(ev: pd.DataFrame, tf: str, configs: list[str], agg: str = "mean") -> pd.DataFrame:
    """Rows = time buckets (all of them), columns = configs, value = mean r_h (0 if none).

    agg="mean" is the pre-registered statistic (every bucket weighs the same). agg="sum"
    (post-hoc sensitivity, see V3_RESULTS) is the bucket's total r_h divided by the number of
    symbols, i.e. event-weighted, like trading every signal.
    """
    b = ev["time"].dt.tz_localize(None).dt.to_period(BUCKET[tf]).dt.start_time
    m = ev.assign(b=b).pivot_table(index="b", columns="config", values="r_h", aggfunc=agg)
    if agg == "sum":
        m = m / max(ev["symbol"].nunique(), 1)
    full = pd.period_range(m.index.min(), m.index.max(), freq=BUCKET[tf]).start_time
    return m.reindex(full).reindex(columns=configs).fillna(0.0)


def cpcv_selection(mat: pd.DataFrame, tf: str) -> dict:
    """In each purged CPCV split pick the config with the best train mean; record its test mean."""
    from purgedcv import CombinatorialPurgedCV
    horizon = E.HORIZON[tf] * BAR[tf] * (1.6 if tf in ("1D", "1W") else 1.0)
    span = pd.Timedelta(days=7) if BUCKET[tf] == "W" else pd.Timedelta(days=31)
    t1 = pd.Series(mat.index + span + horizon, index=mat.index)
    cv = CombinatorialPurgedCV(n_groups=6, n_test_groups=2, embargo_pct=0.01)
    picks, test_means, ranks = [], [], []
    pred = np.zeros((len(mat), cv.get_n_splits()))
    for j, (tr, te) in enumerate(cv.split(mat, t1=t1)):
        trm = mat.iloc[tr].mean()
        best = trm.idxmax()
        picks.append(best)
        tem = mat.iloc[te].mean()
        test_means.append(float(tem[best]))
        ranks.append(float((tem.rank(ascending=False)[best] - 1) / (len(tem) - 1)))
        pred[te, j] = mat.iloc[te][best].to_numpy()
    paths = cv.build_paths(mat, t1=t1)
    pm = paths.combine(pred)            # (n_samples, n_paths)
    path_means = [float(x) for x in np.asarray(pm).mean(axis=0)]
    return {"picks": picks, "pick_counts": pd.Series(picks).value_counts().to_dict(),
            "test_mean_of_pick": float(np.mean(test_means)), "test_rank_of_pick": float(np.mean(ranks)),
            "path_means": path_means}


def pbo(mat: pd.DataFrame) -> dict:
    from finlab.pbo import probability_of_backtest_overfitting
    S = 16
    T = len(mat) - len(mat) % S
    x = mat.iloc[-T:].to_numpy()
    res = probability_of_backtest_overfitting(x, n_partitions=S)
    return {"pbo": float(res.pbo), "n_splits": int(getattr(res, "n_splits", 0) or 0), "rows": int(T)}


def dsr(series: pd.Series, var_sr: float) -> dict:
    from finlab.stats import deflated_sharpe
    from scipy.stats import kurtosis, skew
    x = series.to_numpy(float)
    if len(x) < 10 or x.std() == 0:
        return {"sr": None, "dsr": None, "n": int(len(x))}
    sr = float(x.mean() / x.std(ddof=1))
    r = deflated_sharpe(sr, N_TRIALS, max(var_sr, 1e-12), len(x), float(skew(x)), float(kurtosis(x, fisher=False)))
    return {"sr": sr, "dsr": float(r.dsr if hasattr(r, "dsr") else r[0]), "sr_star": float(getattr(r, "sr_star", np.nan)),
            "n": int(len(x))}


def summarize(ev: pd.DataFrame, series_by_sym: dict, window) -> dict:
    if len(ev) == 0:
        return {"n": 0}
    m, lo, hi = cluster_ci(ev, "r_h")
    rb = random_baseline(ev, series_by_sym, [window], reps=200)
    syms = ev["symbol"].nunique()
    return {"n": int(len(ev)), "mean_r": m, "lo": lo, "hi": hi, "median_r": float(ev["r_h"].median()),
            "precision": float((ev["barrier"] == 1).mean()), "false_pos": float((ev["barrier"] == -1).mean()),
            "ret_pct": 100 * float(ev["ret_h"].mean()), "mfe": float(ev["mfe"].median()),
            "mae": float(ev["mae"].median()), "rand_r": rb.get("rand_mean_r"), "p": rb.get("p_value"),
            "symbols": int(syms)}


def run_tf(tf: str) -> dict:
    series, ev, start = collect(tf)
    by_sym = {s.symbol: s for s in series}
    end = max(s.index[-1] for s in series) + pd.Timedelta(days=1)
    win = (start, end)
    out = {"tf": tf, "n_symbols": len(series), "start": str(start.date()), "end": str(end.date()), "cells": {},
           "regimes": {}, "bearish": {}}
    groups6 = None
    # per config × side × group
    for side, d in (("bullish", 1), ("bearish", -1)):
        for grp in list(GROUPS) + ["all"]:
            sub = ev[(ev["dir"] == d) & ((ev["group"] == grp) if grp != "all" else True)]
            if len(sub) == 0:
                continue
            mat = bucket_matrix(sub, tf, CONFIGS)
            sr = {}
            for k in CONFIGS:
                x = mat[k][mat[k] != 0]
                sr[k] = float(x.mean() / x.std(ddof=1)) if len(x) > 10 and x.std() > 0 else np.nan
            var_sr = float(np.nanvar([sr[k] for k in CANDIDATES]))
            cell = {}
            for k in CONFIGS:
                e = sub[sub["config"] == k]
                row = summarize(e, by_sym, win)
                if row["n"]:
                    x = mat[k][mat[k] != 0]
                    row.update({"dsr": dsr(x, var_sr)})
                    # chronological 6-group check (amendment 1): mean r_h per sixth of the buckets
                    eb = e["time"].dt.tz_localize(None).dt.to_period(BUCKET[tf]).dt.start_time
                    gm = []
                    for g in np.array_split(np.arange(len(mat)), 6):
                        ee = e[(eb >= mat.index[g[0]]) & (eb <= mat.index[g[-1]])]
                        gm.append(float(ee["r_h"].mean()) if len(ee) else None)
                    row["groups6"] = gm
                cell[k] = row
            # incremental value (paired by design: same data, different rule)
            inc = {}
            for a, b, name in (("C1", "C0", "HTF gate"), ("C2", "C1", "realignment only"),
                               ("C4", "C2", "acceptance on MAJOR"), ("C5", "C1", "acceptance on with-HTF"),
                               ("C6", "C2", "suppressed reversals vs MAJOR")):
                ea, eb = sub[sub["config"] == a], sub[sub["config"] == b]
                inc[name] = list(boot_diff(ea, eb)) if len(ea) >= 20 and len(eb) >= 20 else None
            cand = mat[CANDIDATES]
            sel = cpcv_selection(cand, tf) if len(cand) >= 30 else None
            pb = pbo(cand) if len(cand) >= 64 else None
            cand_s = bucket_matrix(sub, tf, CONFIGS, agg="sum")[CANDIDATES]
            sel_s = cpcv_selection(cand_s, tf) if len(cand_s) >= 30 else None
            pb_s = pbo(cand_s) if len(cand_s) >= 64 else None
            out["cells"][f"{side}|{grp}"] = {"configs": cell, "increments": inc, "cpcv": sel, "pbo": pb,
                                             "cpcv_sum": sel_s, "pbo_sum": pb_s}
    # regimes for C2 and C0, all groups
    for side, d in (("bullish", 1), ("bearish", -1)):
        for k in ("C2", "C0"):
            e = ev[(ev["config"] == k) & (ev["dir"] == d)]
            out["regimes"][f"{k}|{side}"] = {r: {"n": int(len(g)), "mean_r": float(g["r_h"].mean())}
                                             for r, g in e.groupby("regime")}
    # bearish representation
    for grp in list(GROUPS) + ["all"]:
        sub = ev if grp == "all" else ev[ev["group"] == grp]
        c0 = sub[sub["config"] == "C0"]
        c2 = sub[sub["config"] == "C2"]
        c6 = sub[sub["config"] == "C6"]
        out["bearish"][grp] = {
            "breaks_bull": int((c0["dir"] > 0).sum()), "breaks_bear": int((c0["dir"] < 0).sum()),
            "major_bull": int((c2["dir"] > 0).sum()), "major_bear": int((c2["dir"] < 0).sum()),
            "suppressed_bull": int((c6["dir"] > 0).sum()), "suppressed_bear": int((c6["dir"] < 0).sum()),
        }
    return out


def verdicts(R: dict) -> dict:
    tests = {}
    for tf, r in R.items():
        for key, cell in r["cells"].items():
            side, grp = key.split("|")
            if grp == "all":
                continue
            c2 = cell["configs"].get("C2", {})
            if c2.get("n", 0) >= 30 and c2.get("p") is not None:
                tests[f"{tf}|{key}"] = c2["p"]
    adj = holm(tests)
    V = {}
    for tf, r in R.items():
        for key, cell in r["cells"].items():
            side, grp = key.split("|")
            if grp == "all":
                continue
            c2, c0 = cell["configs"].get("C2", {}), cell["configs"].get("C0", {})
            k = f"{tf}|{key}"
            if c2.get("n", 0) < 30:
                V[k] = ("UNPROVEN", f"n={c2.get('n', 0)} MAJOR signals (< 30)")
                continue
            g6 = [x for x in (c2.get("groups6") or []) if x is not None]
            pos6 = sum(1 for x in g6 if x > 0)
            d = (c2.get("dsr") or {}).get("dsr")
            strict = (c2["mean_r"] > 0 and adj.get(k, 1) < 0.05 and d is not None and d > 0.95 and pos6 >= 4
                      and c2["mean_r"] > c0.get("mean_r", np.inf))
            loose = c2["mean_r"] > 0 and (c2.get("p") or 1) < 0.10
            why = (f"n={c2['n']}, r {c2['mean_r']:+.2f} [{c2['lo']:+.2f}, {c2['hi']:+.2f}] vs random {c2['rand_r']:+.2f}, "
                   f"p {c2['p']:.3f} (Holm {adj.get(k, 1):.3f}), DSR {('%.2f' % d) if d is not None else '–'}, "
                   f"positive in {pos6}/{len(g6)} periods, C0 {c0.get('mean_r', float('nan')):+.2f}")
            V[k] = ("DEMONSTRATED" if strict else "PROMISING" if loose else "UNPROVEN", why)
    return V


# ------------------------------------------------------------------- markdown

def _f(x, nd=2, sign=True):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def markdown(R: dict, V: dict) -> str:
    L = ["# v3 validation", "",
         "Pre-registered in [`PREREG_V3.md`](PREREG_V3.md). All 70 symbols, signals measured from the next",
         "candle's open over H candles (1H 24, 4H 30, 1D 20, 1W 13), r_h in ATR after costs, 95% month-",
         "cluster CIs, random = same symbols/dates/count/side, DSR with 60 trials. Bullish and bearish",
         "are evaluated separately.", "", "## Verdicts for the shipped MAJOR signal (C2)", "",
         "| TF / side / group | verdict | evidence |", "|---|---|---|"]
    for k, (v, why) in V.items():
        L.append(f"| {k.replace('|', ' / ')} | **{v}** | {why} |")
    for tf in [t for t in TFS if t in R]:
        r = R[tf]
        L += ["", f"## {tf}  ({r['n_symbols']} symbols, {r['start']} → {r['end']})", ""]
        L += ["### Bearish representation", "", "| group | breaks bull / bear | MAJOR bull / bear | suppressed counter-HTF reversals bull / bear |",
              "|---|---:|---:|---:|"]
        for g, b in r["bearish"].items():
            L.append(f"| {g} | {b['breaks_bull']} / {b['breaks_bear']} | {b['major_bull']} / {b['major_bear']} | "
                     f"{b['suppressed_bull']} / {b['suppressed_bear']} |")
        for key, cell in r["cells"].items():
            side, grp = key.split("|")
            L += ["", f"### {side} · {grp}", "",
                  "| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
            for k, c in cell["configs"].items():
                if not c.get("n"):
                    continue
                d = (c.get("dsr") or {}).get("dsr")
                L.append(f"| {k} {NAMES[k]} | {c['n']} | {100 * c['precision']:.0f}% | {100 * c['false_pos']:.0f}% | "
                         f"{_f(c['mean_r'])} [{_f(c['lo'])}, {_f(c['hi'])}] | {_f(c.get('median_r'))} | {_f(c['ret_pct'])} | "
                         f"{_f(c['mfe'], sign=False)} / {_f(c['mae'], sign=False)} | {_f(c['rand_r'])} | "
                         f"{_f(c['p'], 3, False)} | {_f(d, 2, False)} |")
            inc = cell["increments"]
            L += ["", "Incremental value (difference in mean r_h, 90% month-cluster CI): " + "; ".join(
                f"{n} {_f(v[0])} [{_f(v[1])}, {_f(v[2])}]" for n, v in inc.items() if v)]
            if cell.get("pbo"):
                L.append(f"PBO across C0–C6: **{cell['pbo']['pbo']:.2f}** ({cell['pbo']['rows']} buckets).")
            if cell.get("pbo_sum"):
                L.append(f"PBO, event-weighted buckets (post-hoc sensitivity): {cell['pbo_sum']['pbo']:.2f}.")
            if cell.get("cpcv_sum"):
                c = cell["cpcv_sum"]
                L.append(f"Purged CPCV, event-weighted (post-hoc): picks {c['pick_counts']}; mean OOS rank of the pick {c['test_rank_of_pick']:.2f}.")
            if cell.get("cpcv"):
                c = cell["cpcv"]
                L.append(f"Purged CPCV, best-in-train config chosen per split: picks {c['pick_counts']}; mean OOS r_h of the pick "
                         f"{_f(c['test_mean_of_pick'])}; mean OOS rank of the pick {c['test_rank_of_pick']:.2f} (0 = best, 1 = worst); "
                         f"path means {[round(x, 2) for x in c['path_means']]}.")
        L += ["", "### Regime at entry (all groups)", "", "| set | " + " | ".join(["volatile", "range", "trend_up", "trend_down", "transition"]) + " |",
              "|---|---:|---:|---:|---:|---:|"]
        for k, d in r["regimes"].items():
            L.append(f"| {k} | " + " | ".join(f"{d[x]['mean_r']:+.2f} (n={d[x]['n']})" if x in d else "–"
                                              for x in ["volatile", "range", "trend_up", "trend_down", "transition"]) + " |")
    return "\n".join(L) + "\n"


def main(tfs, render_only=False):
    from .report import _clean
    path = OUT / "v3_results.json"
    R = json.loads(path.read_text()) if path.exists() else {}
    for tf in ([] if render_only else tfs):
        print(f"[{tf}] running", flush=True)
        R[tf] = _clean(run_tf(tf))
        path.write_text(json.dumps(R, indent=1))
    R = {k: R[k] for k in TFS if k in R}
    V = verdicts(R)
    (OUT / "V3_RESULTS.md").write_text(markdown(R, V))
    (OUT / "v3_verdicts.json").write_text(json.dumps(V, indent=1))
    for k, (v, why) in V.items():
        print(f"{k}: {v} — {why}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args or TFS, render_only="--render" in sys.argv)
