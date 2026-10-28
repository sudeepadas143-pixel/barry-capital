"""V4 phase 1 diagnostics, as planned in reports/V4_ANALYSIS_PLAN.md (read that first).

    python scripts/v4_root_cause.py            # all timeframes → reports/v4_root_cause.json
    python scripts/v4_root_cause.py 4H 1D      # some timeframes (merged into the json)

Measures only. Nothing in hcmtf/ or pine/ is changed or imported for writing. For every warm
structure break (and the shipped MAJOR / CONFIRMED signals, and the EMA-cross / Supertrend
baselines) it attaches the v3 outcome and four per-event controls on the same symbol and
direction: R0 unconditional, R1 local time (±2H candles), R2 same HTF state and year, R3 same
volatility tercile and year. Then it summarises cells (TF × group × side × set) with
month-cluster bootstrap intervals, heavy-tail checks, detection/lag against ex-post swings,
and the research-audit measurements listed in the plan.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf import engine as G, evaluate as E, study as St  # noqa: E402
from hcmtf.report2 import active_params  # noqa: E402
from hcmtf.universe import FRESH, UNIVERSE  # noqa: E402
from hcmtf.v3 import group_of, regime  # noqa: E402

OUT = ROOT / "reports" / "v4_root_cause.json"
TFS = ["1H", "4H", "1D", "1W"]
SHORT = {tf: max(E.HORIZON[tf] // 4, 3) for tf in TFS}
LONG = {tf: 2 * E.HORIZON[tf] for tf in TFS}
SEED = 20261027
REPS = 1000


# ------------------------------------------------------------------ per series (worker)

def _local_mean(x: np.ndarray, k: int) -> np.ndarray:
    """Mean of the non-NaN values of x within ±k positions (R1)."""
    v = np.nan_to_num(x)
    m = (~np.isnan(x)).astype(float)
    cs, cm = np.r_[0.0, np.cumsum(v)], np.r_[0.0, np.cumsum(m)]
    idx = np.arange(len(x))
    lo, hi = np.maximum(idx - k, 0), np.minimum(idx + k + 1, len(x))
    with np.errstate(invalid="ignore", divide="ignore"):
        return (cs[hi] - cs[lo]) / (cm[hi] - cm[lo])


def _side_mean(x: np.ndarray, k: int, after: bool) -> np.ndarray:
    """Mean of the non-NaN values of x over the k positions strictly after (or before) each one."""
    v = np.nan_to_num(x)
    m = (~np.isnan(x)).astype(float)
    cs, cm = np.r_[0.0, np.cumsum(v)], np.r_[0.0, np.cumsum(m)]
    idx = np.arange(len(x))
    lo, hi = (idx + 1, np.minimum(idx + k + 1, len(x))) if after else (np.maximum(idx - k, 0), idx)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (cs[hi] - cs[lo]) / (cm[hi] - cm[lo])


def _group_mean(x: np.ndarray, keys: list[np.ndarray], use: np.ndarray) -> np.ndarray:
    """Per candle: mean of x over in-window candles sharing all keys (R2, R3)."""
    df = pd.DataFrame({f"k{j}": k for j, k in enumerate(keys)})
    df["x"] = np.where(use, x, np.nan)
    return df.groupby([f"k{j}" for j in range(len(keys))], dropna=False)["x"].transform("mean").to_numpy()


def _htf_rel(f, d: int) -> np.ndarray:
    a1, a2 = np.nan_to_num(f.t1 * d), np.nan_to_num(f.t2 * d)
    against = (a1 < 0) | (a2 < 0)
    with_ = (a1 + a2 >= 1) & ~against
    return np.where(against, "against", np.where(with_, "with", "neutral"))


def _runs(x: np.ndarray) -> np.ndarray:
    """Lengths of runs of equal values (NaN breaks runs)."""
    if len(x) == 0:
        return np.array([])
    chg = np.r_[True, x[1:] != x[:-1]]
    starts = np.flatnonzero(chg)
    return np.diff(np.r_[starts, len(x)])


def one(args):
    asset, tf = args
    s = St.prepare_one((asset, tf))
    if s is None:
        return None
    f, H = s.f, E.HORIZON[tf]
    start = pd.Timestamp(St.WINDOWS[tf][0][0], tz="UTC")
    n = len(f.c)
    inwin = np.asarray(s.index >= start)
    year = s.index.year.to_numpy()
    vr = f.vol_rank
    vterc = np.where(np.isnan(vr), "na", np.where(vr < 100 / 3, "low", np.where(vr < 200 / 3, "mid", "high")))
    reg = regime(f)
    tabs = {"h": s.table, "s": E.bar_outcomes(f, SHORT[tf], s.cost), "l": E.bar_outcomes(f, LONG[tf], s.cost)}
    ctl = {}
    for d in (1, -1):
        r = tabs["h"][d]["r_h"]
        use = inwin & ~np.isnan(r)
        rel = _htf_rel(f, d)
        mfe2 = np.where(np.isnan(tabs["h"][d]["mfe"]), np.nan, (tabs["h"][d]["mfe"] >= 2).astype(float))
        ctl[d] = {
            "R0": np.full(n, np.nanmean(np.where(use, r, np.nan))),
            "R1": _local_mean(r, 2 * H),
            # post hoc (see V4_ROOT_CAUSE_AUDIT): R1 includes candles BEFORE the break, whose
            # forward windows contain the very move that defines the break; split it
            "R1a": _side_mean(r, 2 * H, after=True),
            "R1b": _side_mean(r, 2 * H, after=False),
            "R2": _group_mean(r, [year, rel], use),
            "R3": _group_mean(r, [year, vterc], use),
            "R1_s": _local_mean(tabs["s"][d]["r_h"], 2 * H),
            "R1_l": _local_mean(tabs["l"][d]["r_h"], 2 * H),
            "R1_mfe2": _local_mean(mfe2, 2 * H),
            "rel": rel,
        }

    def attach(ev: pd.DataFrame, name: str) -> pd.DataFrame:
        ev = ev[["i", "dir"] + [c for c in ("cls", "choch", "htf_with", "htf_against") if c in ev]].copy()
        ev = ev[inwin[ev["i"].to_numpy(int)]]
        if len(ev) == 0:
            return ev
        i, d = ev["i"].to_numpy(int), ev["dir"].to_numpy(int)
        pick = lambda tab, k: np.where(d > 0, tab[1][k][i], tab[-1][k][i])
        for k in ("r_h", "ret_h", "mfe", "mae", "barrier"):
            ev[k] = pick(tabs["h"], k)
        ev["r_s"] = pick(tabs["s"], "r_h")
        ev["r_l"] = pick(tabs["l"], "r_h")
        for k in ("R0", "R1", "R1a", "R1b", "R2", "R3", "R1_s", "R1_l", "R1_mfe2", "rel"):
            ev[k] = np.where(d > 0, ctl[1][k][i], ctl[-1][k][i])
        ev["set"] = name
        ev["regime"] = reg[i]
        ev["vterc"] = vterc[i]
        return ev.dropna(subset=["r_h"])

    trig = s.trig[s.trig["warm"]].copy()
    # how late: move already made from the extreme since the previous break, in ATR, and bars since it
    prev = np.r_[0, trig["i"].to_numpy(int)[:-1]]
    late, since = [], []
    for j, (i, d) in enumerate(zip(trig["i"].to_numpy(int), trig["dir"].to_numpy(int))):
        a = prev[j] if j else max(i - 50, 0)
        seg = f.l[a:i + 1] if d > 0 else f.h[a:i + 1]
        k = int(np.argmin(seg)) if d > 0 else int(np.argmax(seg))
        late.append(d * (f.c[i] - seg[k]) / f.atr[i])
        since.append(i - (a + k))
    trig["late_atr"], trig["late_bars"] = late, since
    neutral = trig["cls"].isin(["continuation", "realignment"]) & ~trig["htf_with"]
    trig["cls5"] = np.where(neutral, "neutral", trig["cls"])

    p = active_params(tf)
    sig = St.signals_for(s, p)
    parts = []
    b = attach(trig.assign(cls=trig["cls5"]), "breaks")
    if len(b):
        b = b.join(trig[["late_atr", "late_bars"]])
        parts.append(b)
    for name, ev in (("MAJOR", sig[sig["tier"] == "major"]), ("CONFIRMED", sig[sig["tier"] == "confirmed"]),
                     ("B1 EMA20/50 cross", s.base["ema_cross"]), ("B2 Supertrend flip", s.base["supertrend"])):
        a = attach(ev, name)
        if len(a):
            lt = trig.set_index("i")
            a["late_atr"] = lt["late_atr"].reindex(a["i"]).to_numpy()
            a["late_bars"] = lt["late_bars"].reindex(a["i"]).to_numpy()
            parts.append(a)
    ev = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    if len(ev):
        ev["symbol"], ev["group"], ev["tf"] = s.symbol, group_of(s.cls), tf
        ev["time"] = s.index[ev["i"].to_numpy(int)]
        ev["overlap_next"] = False
        # outcome windows overlapping the next same-set event on this symbol (dependence)
        for name, g in ev.groupby("set"):
            gi = np.sort(g["i"].to_numpy(int))
            nxt = np.r_[gi[1:], 10**12]
            ev.loc[g.sort_values("i").index, "overlap_next"] = (nxt - gi) <= H

    # detection and lag against ex-post swings (future data: scoring only)
    piv = E.zigzag(f.c, f.atr, 4.0)
    legs = []
    for name, evs in (("breaks", trig), ("MAJOR", sig[sig["tier"] == "major"]),
                      ("with-HTF (MAJOR+CONFIRMED)", sig[sig["tier"].isin(["major", "confirmed"])])):
        tl = E.timeliness(evs[["i", "dir"]], f, 4.0)
        tl = tl[inwin[tl["turn_i"].to_numpy(int)]]
        tl["set"] = name
        legs.append(tl)
    legs = pd.concat(legs, ignore_index=True)
    legs["symbol"], legs["group"], legs["tf"] = s.symbol, group_of(s.cls), tf

    # HTF state structure: run lengths and how often a with-HTF signal of each side is possible
    rel_b, rel_s = ctl[1]["rel"][inwin], ctl[-1]["rel"][inwin]
    t2 = f.t2[inwin]
    htf = {"symbol": s.symbol, "group": group_of(s.cls), "tf": tf, "bars": int(inwin.sum()),
           "with_bull": float((rel_b == "with").mean()), "with_bear": float((rel_s == "with").mean()),
           "t2_runs": _runs(np.nan_to_num(t2, nan=9)).tolist(), "t1_runs": _runs(np.nan_to_num(f.t1[inwin], nan=9)).tolist()}

    # Pine strategy twin: same-direction MAJOR signals that arrive while a trade is open
    # (Pine resets the stop and the time-exit clock on them; evaluate.simulate ignores them)
    maj = sig[sig["tier"] == "major"]
    tr = E.simulate(maj, f, s.cost, St.MAX_HOLD[tf])
    hit = 0
    for e, x, d in zip(tr["entry_i"], tr["exit_i"], tr["dir"]):
        same = maj[(maj["i"] >= e) & (maj["i"] < x) & (maj["dir"] == d)]
        hit += int(len(same) > 0)
    twin = {"symbol": s.symbol, "tf": tf, "trades": int(len(tr)), "trades_with_same_dir_signal_inside": hit}
    return ev, legs, htf, twin


# ------------------------------------------------------------------ statistics

def cboot(x: np.ndarray, cl: np.ndarray, reps: int = REPS, seed: int = SEED):
    """Mean with a 95% cluster-bootstrap interval (ratio estimator, clusters resampled)."""
    ok = ~np.isnan(x)
    x, cl = x[ok], cl[ok]
    if len(x) == 0:
        return np.nan, np.nan, np.nan
    u, inv = np.unique(cl, return_inverse=True)
    s = np.bincount(inv, weights=x, minlength=len(u))
    c = np.bincount(inv, minlength=len(u)).astype(float)
    pick = np.random.default_rng(seed).integers(0, len(u), (reps, len(u)))
    with np.errstate(invalid="ignore", divide="ignore"):
        b = s[pick].sum(1) / c[pick].sum(1)
    lo, hi = np.nanpercentile(b, [2.5, 97.5])
    return float(x.mean()), float(lo), float(hi)


def cell(e: pd.DataFrame, tf: str) -> dict:
    n = len(e)
    if n == 0:
        return {"n": 0}
    month = e["time"].dt.tz_localize(None).dt.to_period("M").astype(str).to_numpy()
    quarter = e["time"].dt.tz_localize(None).dt.to_period("Q").astype(str).to_numpy()
    r = e["r_h"].to_numpy(float)
    out = {"n": int(n), "symbols": int(e["symbol"].nunique()), "months": int(len(np.unique(month))),
           "overlap_share": float(e["overlap_next"].mean())}
    m, lo, hi = cboot(r, month)
    out.update(mean=m, lo=lo, hi=hi, median=float(np.median(r)),
               trim5=float(pd.Series(r).clip(*np.percentile(r, [5, 95])).mean()),
               share_pos=float((r > 0).mean()))
    srt = np.sort(r)
    k1, k5 = max(int(round(0.01 * n)), 1), max(int(round(0.05 * n)), 1)
    out["mean_ex_top1"] = float(srt[:-k1].mean()) if n > k1 else np.nan
    pos = r[r > 0].sum()
    out["top5_share_of_gains"] = float(srt[-k5:].sum() / pos) if pos > 0 else np.nan
    out["mfe_med"], out["mae_med"] = float(e["mfe"].median()), float(e["mae"].median())
    out["hit_2v1"] = float((e["barrier"] == 1).mean())
    out["stop_1"] = float((e["barrier"] == -1).mean())
    out["ret_pct"] = 100 * float(e["ret_h"].mean())
    for k in ("R0", "R1", "R1a", "R1b", "R2", "R3"):
        x = r - e[k].to_numpy(float)
        mm, ll, hh = cboot(x, month)
        out[f"x{k}"] = [mm, ll, hh, float(np.nanmedian(x))]
        out[f"{k}_mean"] = float(np.nanmean(e[k]))
    xr1 = r - e["R1"].to_numpy(float)
    srt1 = np.sort(xr1[~np.isnan(xr1)])
    out["xR1_ex_top1"] = float(srt1[:-k1].mean()) if len(srt1) > k1 else np.nan
    if tf == "1W":
        out["xR1_q"] = list(cboot(xr1, quarter))
    out["xR1_s"] = list(cboot(e["r_s"].to_numpy(float) - e["R1_s"].to_numpy(float), month))
    out["xR1_l"] = list(cboot(e["r_l"].to_numpy(float) - e["R1_l"].to_numpy(float), month))
    # visually convincing: reached +2 ATR within H
    out["mfe2"] = float((e["mfe"] >= 2).mean())
    out["mfe2_local_random"] = float(np.nanmean(e["R1_mfe2"]))
    out["mfe2_but_lost"] = float(((e["mfe"] >= 2) & (e["r_h"] <= 0)).mean())
    if "late_atr" in e and e["late_atr"].notna().any():
        out["late_atr_med"] = float(e["late_atr"].median())
        out["late_bars_med"] = float(e["late_bars"].median())
        out["late_gt_mfe"] = float((e["late_atr"] > e["mfe"]).mean())
    # iid p-value vs R0, as the v3 random baseline effectively computes it (normal approximation)
    sd = float(np.nanstd(r))
    out["p_iid_vs_R0"] = float(_norm_sf((m - out["R0_mean"]) / (sd / np.sqrt(n)))) if sd > 0 else np.nan
    # effects this cell could detect: 80% power, two-sided 5%
    out["mde"] = 1.43 * (hi - lo) / 2
    a = out
    a["adequate"] = bool(n >= 100 and out["months"] >= 24)
    a["information"] = bool(out["xR1"][1] > 0 and out["xR2"][1] > 0 and out["xR1"][3] > 0 and out["xR1_ex_top1"] > 0)
    # post-hoc sensitivity: the same rule with the after-only local control
    xa = np.sort((r - e["R1a"].to_numpy(float))[~np.isnan(e["R1a"].to_numpy(float))])
    a["information_R1a"] = bool(out["xR1a"][1] > 0 and out["xR2"][1] > 0 and out["xR1a"][3] > 0
                                and len(xa) > k1 and xa[:-k1].mean() > 0)
    a["xR0_lo_gt0"] = bool(out["xR0"][1] > 0)
    return out


def _norm_sf(z):
    from scipy.stats import norm
    return norm.sf(z)


SETS = {
    "all breaks": lambda e: (e["set"] == "breaks"),
    "MTF reversal (any CHoCH)": lambda e: (e["set"] == "breaks") & e["choch"].astype(bool),
    "MTF continuation (no CHoCH)": lambda e: (e["set"] == "breaks") & ~e["choch"].astype(bool),
    "continuation with HTF": lambda e: (e["set"] == "breaks") & (e["cls"] == "continuation"),
    "realignment with HTF": lambda e: (e["set"] == "breaks") & (e["cls"] == "realignment"),
    "counter_reversal": lambda e: (e["set"] == "breaks") & (e["cls"] == "counter_reversal"),
    "counter_continuation": lambda e: (e["set"] == "breaks") & (e["cls"] == "counter_continuation"),
    "neutral HTF": lambda e: (e["set"] == "breaks") & (e["cls"] == "neutral"),
    "MAJOR (shipped)": lambda e: e["set"] == "MAJOR",
    "CONFIRMED (shipped)": lambda e: e["set"] == "CONFIRMED",
    "B1 EMA20/50 cross": lambda e: e["set"] == "B1 EMA20/50 cross",
    "B2 Supertrend flip": lambda e: e["set"] == "B2 Supertrend flip",
}
GROUPS = ["crypto", "equities", "commodities", "rates_fx", "all"]


def run_tf(tf: str, workers: int = 8) -> dict:
    with ProcessPoolExecutor(workers) as ex:
        res = [r for r in ex.map(one, [(a, tf) for a in UNIVERSE + FRESH]) if r is not None]
    ev = pd.concat([r[0] for r in res if len(r[0])], ignore_index=True)
    legs = pd.concat([r[1] for r in res], ignore_index=True)
    out = {"tf": tf, "symbols": len(res), "cells": {}, "regimes": {}, "detection": {}, "htf": {}, "twin": {}}
    for grp in GROUPS:
        g = ev if grp == "all" else ev[ev["group"] == grp]
        for side, d in (("bullish", 1), ("bearish", -1)):
            gs = g[g["dir"] == d]
            for name, m in SETS.items():
                c = cell(gs[m(gs)], tf)
                if c["n"]:
                    out["cells"][f"{grp}|{side}|{name}"] = c
    # regimes (trend and volatility) for breaks and MAJOR, excess vs R1
    for name in ("all breaks", "MAJOR (shipped)"):
        for side, d in (("bullish", 1), ("bearish", -1)):
            e = ev[SETS[name](ev) & (ev["dir"] == d)]
            month = e["time"].dt.tz_localize(None).dt.to_period("M").astype(str).to_numpy()
            for col in ("regime", "vterc"):
                for k, idx in e.groupby(col).groups.items():
                    sub = e.loc[idx]
                    x = (sub["r_h"] - sub["R1"]).to_numpy(float)
                    m_, lo, hi = cboot(x, month[e.index.get_indexer(idx)])
                    out["regimes"][f"{name}|{side}|{col}={k}"] = {"n": int(len(sub)), "mean_r": float(sub["r_h"].mean()),
                                                                  "xR1": [m_, lo, hi]}
    # detection / lag
    for grp in GROUPS:
        lg = legs if grp == "all" else legs[legs["group"] == grp]
        for name, g in lg.groupby("set"):
            for side, d in (("bullish", 1), ("bearish", -1)):
                x = g[g["dir"] == d]
                det = x[x["detected"]]
                out["detection"][f"{grp}|{side}|{name}"] = {
                    "legs": int(len(x)), "detected": float(x["detected"].mean()) if len(x) else np.nan,
                    "lag_med": float(det["lag_bars"].median()) if len(det) else np.nan,
                    "captured_med": float(det["captured"].median()) if len(det) else np.nan,
                    "after_leg_end": float((det["captured"] <= 0).mean()) if len(det) else np.nan}
    # HTF state structure
    hs = pd.DataFrame([r[2] for r in res])
    for grp in GROUPS:
        h = hs if grp == "all" else hs[hs["group"] == grp]
        if len(h) == 0:
            continue
        w = h["bars"] / h["bars"].sum()
        r2 = np.concatenate([np.array(x) for x in h["t2_runs"]]) if len(h) else np.array([])
        r1 = np.concatenate([np.array(x) for x in h["t1_runs"]]) if len(h) else np.array([])
        out["htf"][grp] = {"with_bull": float((h["with_bull"] * w).sum()), "with_bear": float((h["with_bear"] * w).sum()),
                           "t1_run_med": float(np.median(r1)) if len(r1) else np.nan,
                           "t2_run_med": float(np.median(r2)) if len(r2) else np.nan,
                           "t2_run_mean": float(np.mean(r2)) if len(r2) else np.nan}
    tw = pd.DataFrame([r[3] for r in res])
    out["twin"] = {"trades": int(tw["trades"].sum()), "affected": int(tw["trades_with_same_dir_signal_inside"].sum())}
    # V3 p-values for the same cells, for the dependence check
    return out


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def main(tfs):
    R = json.loads(OUT.read_text()) if OUT.exists() else {}
    for tf in tfs:
        print(f"[{tf}] running", flush=True)
        R[tf] = _clean(run_tf(tf))
        OUT.write_text(json.dumps(R, indent=1))
        print(f"[{tf}] done", flush=True)


if __name__ == "__main__":
    main([a for a in sys.argv[1:]] or TFS)
