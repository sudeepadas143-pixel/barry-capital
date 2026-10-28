"""HC-MTF 6.0 stage 1 (continuation models A–D) EXPLORATION on cached crypto 1H/4H, exactly as
frozen in reports/V6_CONT_CONFIG.md (section numbers refer to it).

    python scripts/v6_cont_explore.py run      # gate, manifest, ledger trials, compute, results json
    python scripts/v6_cont_explore.py render   # reports/V6_CONT_RESULTS.md (+ per-pair appendix)

Exploratory only: every candle read was examined before. Nothing here changes a definition,
parameter, threshold or decision rule of the frozen configuration.
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf import engine as G, ta  # noqa: E402
from hcmtf.evaluate import bar_outcomes  # noqa: E402
from hcmtf.metrics import holm  # noqa: E402
from research import v5_baselines as B, v5_context as X, v5_data as DG, v5_eval as EV  # noqa: E402
from research import v5_gate as GT, v5_inference as INF, v5_ledger as LG, v5_manifest as MF, v5_state as ST  # noqa: E402
from research import v6_signals as S6  # noqa: E402
from research.v41 import cluster_id  # noqa: E402
from research.v5_costs import CRYPTO_SHORT_FALLBACK_ANNUAL, FUNDING_EDGE, FUNDING_STALE, YEAR_SECONDS  # noqa: E402

CONFIG = "reports/V6_CONT_CONFIG.md"
OUT = ROOT / "reports" / "v6_cont_results.json"
MD = ROOT / "reports" / "V6_CONT_RESULTS.md"
MD_PAIRS = ROOT / "reports" / "V6_CONT_PER_PAIR.md"
START = pd.Timestamp("2020-01-01", tz="UTC")                                     # §1
TFS = {"1H": {"H": 24, "hold": 48}, "4H": {"H": 30, "hold": 60}}                # §5
FEE, SLIP_TOP, SLIP_REST = 0.0020, 0.0010, 0.0020                                # §6
EVAL_GAP = 1.25                                                                  # §5
SEED = 20261027
REPS_RAND, REPS_REMOVAL, REPS_WILD = 200, 200, 9999
UNIVERSE = (*X.TARGETS, X.BTC)
CFG_IDS = tuple(S6.CONFIGS)
CONTRASTS = {"C0": ("A", None), "C1": ("B", "A"), "C2": ("C", "B"), "C3": ("D", "A")}    # (kept model, parent)
FAMILY = {"C0": "V6-A", "C1": "V6-B", "C2": "V6-C", "C3": "V6-D"}
COMPARATORS = ("ema_cross", "supertrend_flip", "htf_flip")
CODE_FILES = ["research/v6_signals.py", "research/v5_context.py", "research/v5_eval.py", "research/v5_baselines.py",
              "research/v5_state.py", "research/v5_data.py", "research/v5_inference.py", "research/v5_costs.py",
              "research/v5_gate.py", "scripts/v6_cont_explore.py"]


def cells() -> list[tuple[str, str, int, str]]:
    """Every decision cell: (contrast, config, side, TF). 112 in total (§8)."""
    out = []
    for c, (model, _) in CONTRASTS.items():
        for cfg in CFG_IDS:
            if model in S6.AFFECTS[cfg]:
                out += [(c, cfg, s, tf) for s in (1, -1) for tf in TFS]
    return out


def cell_key(c, cfg, side, tf) -> str:
    return f"{c}|{cfg}|{side:+d}|{tf}"


# ----------------------------------------------------------------------------- costs (as v5_costs, vectorised)

def close_times(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Vectorised v5_eval._close_time (tested equal)."""
    t = index.as_unit("ns").asi8
    med = pd.Series(np.diff(t).astype(float)).rolling(50, min_periods=1).median().to_numpy()
    cap = t + np.r_[0.0, med].astype(np.int64)
    nxt = np.r_[t[1:], np.iinfo(np.int64).max]
    return pd.DatetimeIndex(np.minimum(nxt, cap).astype("datetime64[ns]")).tz_localize("UTC")


def short_cost_vector(index: pd.DatetimeIndex, hold: int, funding):
    """v5_costs.short_holding_cost for a short entered at open i+1 and exited at the close time
    of i+hold, for every candle i (tested equal). NaN past the data."""
    n = len(index)
    cost = np.full(n, np.nan)
    src = np.full(n, "", dtype=object)
    m = n - hold
    if m <= 0:
        return cost, src
    ct = close_times(index)
    entry, exit_ = index[1:m + 1], ct[hold:hold + m]
    est = CRYPTO_SHORT_FALLBACK_ANNUAL * (exit_ - entry).total_seconds().to_numpy() / YEAR_SECONDS
    cost[:m], src[:m] = est, "estimated_crypto_10pct"
    if funding is None or len(funding) == 0:
        return cost, src
    ft = funding.index.as_unit("ns").asi8
    cs = np.r_[0.0, np.cumsum(funding["rate"].to_numpy(float))]
    e, x = entry.as_unit("ns").asi8, exit_.as_unit("ns").asi8
    edge, stale = FUNDING_EDGE.value, FUNDING_STALE.value
    lo, hi = np.searchsorted(ft, e - edge, "right"), np.searchsorted(ft, x, "right")
    has = hi > lo
    cov = (ft[0] <= e) & (ft[-1] >= x - edge)
    first_gap = np.where(has, ft[np.minimum(lo, len(ft) - 1)] - np.maximum(e - edge, ft[0]), 0)
    gc = np.r_[0, np.cumsum(np.r_[0, np.diff(ft)] > stale)]
    bad = gc[hi] - gc[np.minimum(lo + 1, hi)]
    ok = cov & np.where(has, (first_gap <= stale) & (bad == 0), (x - e) < edge)
    paid = cs[hi] - cs[np.minimum(np.searchsorted(ft, e, "right"), hi)]
    cost[:m] = np.where(ok, -paid, est)
    src[:m] = np.where(ok, "observed_funding", "estimated_crypto_10pct")
    return cost, src


def window_gap(index: pd.DatetimeIndex, tf: str, length: int) -> np.ndarray:
    """True where the rows i+1 .. i+length span more than 1.25 x length nominal durations."""
    n = len(index)
    out = np.zeros(n, bool)
    if n > length:
        step = S6.NOMINAL[tf]
        span = (index[length:] + step) - index[1:n - length + 1]
        out[:n - length] = span.to_numpy() > (EVAL_GAP * length * step).to_timedelta64()
    return out


class _F:
    pass


# ----------------------------------------------------------------------------- per-pair worker

def _rng(*keys):
    return np.random.default_rng(np.random.SeedSequence(SEED, spawn_key=tuple(int(k) for k in keys)))


def worker(args):
    sym, tf, liq, first = args
    _, h1n, h2n = G.LADDER[tf]
    df, htf1, htf2 = DG.load(sym, tf), DG.load(sym, h1n), DG.load(sym, h2n)
    st = ST.classify(df, htf1, htf2)
    idx = df.index
    n = len(idx)
    H, hold = TFS[tf]["H"], TFS[tf]["hold"]
    is_btc = sym == X.BTC
    el = X.eligibility(sym, idx, first, liq, st["warm"].to_numpy(bool), None if is_btc else np.ones(n, bool))
    window = np.arange(n) >= int(idx.searchsorted(START))
    elig = el["eligible"].to_numpy(bool) & window
    rank = el["rank"].to_numpy(float)
    slip = np.where(np.nan_to_num(rank, nan=99) <= 10, SLIP_TOP, SLIP_REST)
    gap = S6.gaps(idx, tf)
    entry_gap = np.r_[gap[1:], True]
    no_exit = np.arange(n) + H >= n
    wgap, tgap = window_gap(idx, tf, H), window_gap(idx, tf, hold)
    funding = DG.load_funding(sym)
    pstart = X.perp_start(sym)
    cl = cluster_id(idx, tf)
    vol = st["vol_regime"].to_numpy(object)
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    f = _F(); f.o, f.h, f.l, f.c = o, h, l, c; f.atr = ta.atr(h, l, c, 14)
    bo = bar_outcomes(f, H, 0.0)
    hc, _ = short_cost_vector(idx, H, funding)
    px = np.r_[o[1:], np.nan]
    rh, mfe, mae, bar = {}, {}, {}, {}
    for side in (1, -1):
        cost = FEE + slip + (np.where(np.isnan(hc), np.nan, hc) if side < 0 else 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            rh[side] = bo[side]["r_h"] - cost * px / f.atr
        mfe[side], mae[side], bar[side] = bo[side]["mfe"], bo[side]["mae"], bo[side]["barrier"]
    full = ~no_exit & ~wgap & ~entry_gap                                    # full rh window
    rhx, trend = {}, {}
    for ema in sorted({S6.CONFIGS[k].ema for k in CFG_IDS}):
        tr = S6.trend_state(S6.indicators(df, ema))
        trend[ema] = tr
        for side in (1, -1):
            r = np.where(st["warm"].to_numpy(bool) & (tr != S6.UNKNOWN) & full, rh[side], np.nan)
            ct = EV.candle_table(sym, idx, tf, H, {"trend": tr}, {"r_h": r})
            rhx[(ema, side)] = rh[side] - EV.causal_benchmark(ct, "r_h", ["trend"], H, 200)
    rows, trades, rand = [], {}, {}
    for ci, cfg_id in enumerate(CFG_IDS):
        cfg = S6.CONFIGS[cfg_id]
        for side in (1, -1):
            sg, ind, tr = S6.signals(df, tf, cfg, side)
            for r in sg.itertuples(index=False):
                i, j = int(r.i), int(r.j)
                x = rhx[(cfg.ema, side)][i]
                rows.append({"sym": sym, "cfg": cfg_id, "side": side, "i": i, "j": j, "t": idx[i], "cl": int(cl[i]),
                             "B": bool(r.B), "C": bool(r.C), "D": bool(r.D), "window": bool(window[i]),
                             "eligible": bool(elig[i]), "first_fail": el["first_fail"].iat[i], "rank": rank[i],
                             "slip": float(slip[i]), "no_exit": bool(no_exit[i]), "gap": bool(wgap[i]),
                             "entry_gap": bool(entry_gap[i]), "rh": rh[side][i], "rh_x": x, "mfe": mfe[side][i],
                             "mae": mae[side][i], "barrier": bar[side][i], "vol": vol[i], "year": int(idx[i].year),
                             "perp_ok": bool(sym in X.PERP_PAIRS and pstart is not None and idx[i] >= pstart)})
                key = (i, j, side)
                if key not in trades and elig[i] and full[i] and not np.isnan(x):
                    stop = float(np.min(l[j:i + 1]) - 0.5 * f.atr[i]) if side > 0 else float(np.max(h[j:i + 1]) + 0.5 * f.atr[i])
                    t = None if (tgap[i] or i + hold >= n) else EV.trade(o, h, l, c, idx, i, side, hold, stop, "crypto", funding)
                    if t is not None:
                        e_, x_ = t["entry_i"], t["exit_i"]
                        t["mae"] = float((o[e_] - np.min(l[e_:x_ + 1])) / o[e_]) if side > 0 else float((np.max(h[e_:x_ + 1]) - o[e_]) / o[e_])
                        t["slip"] = float(slip[i])
                    trades[key] = t if t is not None else ("trade_gap" if tgap[i] else "no_exit_in_data")
            # matched random entry (C0) for configs that define A
            if "A" in S6.AFFECTS[cfg_id]:
                ok = elig & full & ~np.isnan(rhx[(cfg.ema, side)])
                a_i = np.array([int(v) for v in sg["i"] if ok[int(v)]], int)
                pool = ok & (tr == (S6.UP if side > 0 else S6.DOWN))
                cnt = pd.Series(cl[a_i]).value_counts() if len(a_i) else pd.Series(dtype=int)
                rng = _rng(UNIVERSE.index(sym), ci, side + 1, list(TFS).index(tf))
                sums, counts, short = np.zeros(REPS_RAND), np.zeros(REPS_RAND), 0
                for b, k in cnt.items():
                    cand = np.flatnonzero(pool & (cl == b))
                    m = min(int(k), len(cand))
                    short += int(m < k)
                    if m == 0:
                        continue
                    v = rh[side][cand]
                    for rr in range(REPS_RAND):
                        sums[rr] += v[rng.choice(len(cand), m, replace=False)].sum()
                    counts += m
                rand[(cfg_id, side)] = {"sums": sums, "counts": counts, "shortfall_blocks": short}
    U = pd.DataFrame(rows)
    if len(U):
        U["in_S"] = U["eligible"] & ~U["no_exit"] & ~U["gap"] & ~U["entry_gap"] & U["rh_x"].notna()
        tt = [trades.get((int(a), int(b), int(s))) for a, b, s in zip(U["i"], U["j"], U["side"])]
        U["trade_status"] = [x if isinstance(x, str) else ("ok" if isinstance(x, dict) else "") for x in tt]
        for k_ in ("net", "gross", "mae_trade"):
            U[k_] = np.nan
        U["cost_src"] = ""
        okm = U["trade_status"].eq("ok").to_numpy()
        U.loc[okm, "net"] = [t["net"] - t["slip"] for t, m in zip(tt, okm) if m]
        U.loc[okm, "gross"] = [t["gross"] for t, m in zip(tt, okm) if m]
        U.loc[okm, "mae_trade"] = [t["mae"] for t, m in zip(tt, okm) if m]
        U.loc[okm, "cost_src"] = [t["holding_cost_source"] for t, m in zip(tt, okm) if m]
    books = {}
    for cfg_id in CFG_IDS:
        for side in (1, -1):
            for model in "ABCD":
                if not len(U):
                    continue
                m = (U["cfg"] == cfg_id) & (U["side"] == side) & U["in_S"] & (U["trade_status"] == "ok")
                if model != "A":
                    m &= U[model]
                ts = []
                for a, b in zip(U.loc[m, "i"], U.loc[m, "j"]):
                    t = dict(trades[(int(a), int(b), side)])
                    t["round_trip"] = t["round_trip"] + t["slip"]
                    t["net"] = t["net"] - t["slip"]
                    ts.append(t)
                if ts:
                    s = EV.sequential_daily(o, c, idx, ts).cumsum()
                    books[(cfg_id, side, model)] = {"trades": len(ts), "total_log_return": float(s.iloc[-1]),
                                                    "max_drawdown": float((s - s.cummax()).min())}
    comps = []
    trP = trend[S6.P.ema]
    for side in (1, -1):
        gen = {"ema_cross": B.ema_cross(df, side), "supertrend_flip": B.supertrend_flip(df, side), "htf_flip": B.htf_flip(st, side)}
        for name, ii in gen.items():
            for i in ii:
                i = int(i)
                x = rhx[(S6.P.ema, side)][i]
                if elig[i] and full[i] and not np.isnan(x):
                    comps.append({"sym": sym, "comp": name, "side": side, "i": i, "cl": int(cl[i]), "rh": rh[side][i], "rh_x": x,
                                  "trend": trP[i]})
    return {"sym": sym, "tf": tf, "units": U, "rand": rand, "books": books, "comps": pd.DataFrame(comps),
            "first_fail_counts": el["first_fail"][window].value_counts().to_dict(), "eligible_candles": int(elig.sum()),
            "candles_in_window": int(window.sum())}


# ----------------------------------------------------------------------------- statistics and decisions

def _num(x):
    return None if x is None or not np.isfinite(x) else float(x)


def _pos(v):
    return v is not None and v > 0


def c0_stats(S: pd.DataFrame, rand_sums: np.ndarray, rand_counts: np.ndarray, reps_wild: int = REPS_WILD) -> dict:
    x = S["rh_x"].to_numpy(float)
    out = {"n": int(len(S)), "pairs": int(S["sym"].nunique())}
    if len(S) < 2:
        out["evaluable"] = False
        return out
    t = INF.cluster_mean_test(x, S["cl"].to_numpy(), reps=reps_wild, seed=SEED)
    pp = S.groupby("sym")["rh_x"].agg(["count", "mean"])
    q = pp[pp["count"] >= 20]
    thr = np.percentile(np.abs(S["rh"].to_numpy(float)), 95)
    keep = np.abs(S["rh"].to_numpy(float)) <= thr
    best = pp["mean"].idxmax()
    with np.errstate(invalid="ignore", divide="ignore"):
        rm = rand_sums / rand_counts
    alt = S[~S["sym"].isin(X.MAJORS)]["rh_x"]
    out.update({"mean": float(x.mean()), "median": float(np.median(x)), "rh_mean": float(S["rh"].mean()),
                "test": {k: t.get(k) for k in ("mean", "ci95", "p_wild", "clusters", "valid")}, "G": t["clusters"],
                "eq_pair_mean": float(pp["mean"].mean()), "qualifying_pairs": int(len(q)),
                "median_pair": _num(q["mean"].median()) if len(q) else None,
                "positive_share": float((q["mean"] > 0).sum() / len(q)) if len(q) else None,
                "altcoin_mean": _num(alt.mean()) if len(alt) else None,
                "trim5": _num(x[keep].mean()) if keep.any() else None, "best_pair": best,
                "drop_best": _num(S[S["sym"] != best]["rh_x"].mean()) if (S["sym"] != best).any() else None,
                "random_entry": {"p2.5": _num(np.nanpercentile(rm, 2.5)), "p50": _num(np.nanpercentile(rm, 50)),
                                 "p97.5": _num(np.nanpercentile(rm, 97.5))} if np.isfinite(rm).any() else None,
                "per_pair": pp.reset_index().to_dict("records")})
    out["evaluable"] = bool(len(S) >= 100 and out["pairs"] >= 10 and t["clusters"] >= 10 and t.get("valid"))
    out["p"] = t.get("p_wild") if out["evaluable"] else None
    return out


def diff_stats(S: pd.DataFrame, kept: np.ndarray, reps_wild: int = REPS_WILD, reps_removal: int = REPS_REMOVAL) -> dict:
    x = S["rh_x"].to_numpy(float)
    k = np.asarray(kept, bool)
    n_k, n_r = int(k.sum()), int((~k).sum())
    out = {"n_parent": int(len(S)), "n_kept": n_k, "n_removed": n_r, "pairs": int(S["sym"].nunique())}
    if n_k == 0 or n_r == 0:
        out["evaluable"] = False
        return out
    t = INF.cluster_diff_test(x, k, S["cl"].to_numpy(), reps=reps_wild, seed=SEED)
    d = S.assign(_k=k)
    g = d.groupby("sym")
    pp = pd.DataFrame({"n_k": g["_k"].sum().astype(int), "n_r": g["_k"].apply(lambda s: int((~s).sum())),
                       "mean_k": d[d["_k"]].groupby("sym")["rh_x"].mean(), "mean_r": d[~d["_k"]].groupby("sym")["rh_x"].mean()})
    pp["delta"] = pp["mean_k"] - pp["mean_r"]
    q = pp[(pp["n_k"] >= 20) & (pp["n_r"] >= 20)]
    defined = pp["delta"].notna()

    def dlt(mask):
        a, b = x[mask & k], x[mask & ~k]
        return float(a.mean() - b.mean()) if len(a) and len(b) else None

    thr = np.percentile(np.abs(S["rh"].to_numpy(float)), 95)
    keep = np.abs(S["rh"].to_numpy(float)) <= thr
    best = pp.loc[defined, "delta"].idxmax() if defined.any() else None
    rem = X.matched_removal_means(x, S["sym"].to_numpy(object), k, reps_removal, SEED)
    alt = ~S["sym"].isin(X.MAJORS).to_numpy()
    out.update({"delta": t.get("delta"), "mean_kept": _num(x[k].mean()), "mean_removed": _num(x[~k].mean()),
                "mean_parent": float(x.mean()), "test": {kk: t.get(kk) for kk in ("delta", "ci95", "p_wild", "clusters", "valid")},
                "G": t["clusters"], "eq_pair_delta": _num(pp.loc[defined, "delta"].mean()) if defined.any() else None,
                "qualifying_pairs": int(len(q)), "median_pair_delta": _num(q["delta"].median()) if len(q) else None,
                "positive_share": float((q["delta"] > 0).sum() / len(q)) if len(q) else None,
                "altcoin_delta": dlt(alt), "trim5": dlt(keep), "best_pair": best,
                "drop_best": dlt(S["sym"].to_numpy(object) != best) if best is not None else None,
                "removal": {"p2.5": _num(np.nanpercentile(rem, 2.5)), "p50": _num(np.nanpercentile(rem, 50)),
                            "p97.5": _num(np.nanpercentile(rem, 97.5))},
                "pairs_both": int(((pp["n_k"] > 0) & (pp["n_r"] > 0)).sum()),
                "per_pair": pp.reset_index().rename(columns={"index": "sym"}).to_dict("records")})
    out["evaluable"] = bool(n_k >= 100 and n_r >= 100 and out["pairs_both"] >= 10 and t["clusters"] >= 10 and t.get("valid"))
    out["p"] = t.get("p_wild") if out["evaluable"] else None
    return out


def decide(contrast: str, c: dict, p_holm: float) -> str:
    """§9 per cell."""
    if not c.get("evaluable"):
        return "INCONCLUSIVE (underpowered)"
    if contrast == "C0":
        ok = (_pos(c["mean"]) and p_holm < 0.05 and c["random_entry"] is not None and c["rh_mean"] > c["random_entry"]["p97.5"]
              and _pos(c["eq_pair_mean"]) and c["qualifying_pairs"] >= 8 and _pos(c["median_pair"])
              and (c["positive_share"] or 0) >= 0.60 and _pos(c["altcoin_mean"]) and _pos(c["trim5"]) and _pos(c["drop_best"]))
        if ok:
            return "BEATS BASELINE"
        no = c["test"]["ci95"][1] <= 0 or (c["mean"] <= 0 and c["eq_pair_mean"] <= 0)
    else:
        ok = (_pos(c["delta"]) and p_holm < 0.05 and c["mean_kept"] is not None and c["mean_kept"] > c["removal"]["p97.5"]
              and _pos(c["eq_pair_delta"]) and c["qualifying_pairs"] >= 8 and _pos(c["median_pair_delta"])
              and (c["positive_share"] or 0) >= 0.60 and _pos(c["altcoin_delta"]) and _pos(c["trim5"]) and _pos(c["drop_best"]))
        if ok:
            return "ADDS VALUE"
        no = c["test"]["ci95"][1] <= 0 or ((c["delta"] or 0) <= 0 and (c["eq_pair_delta"] is not None and c["eq_pair_delta"] <= 0))
    return "NO VALUE" if no else "INCONCLUSIVE"


PASS = ("BEATS BASELINE", "ADDS VALUE")


def qualifies(verdicts: dict, contrast: str, side: int) -> dict:
    """§9: config P only. Passing at one TF and not NO VALUE at the other."""
    v = {tf: verdicts.get(cell_key(contrast, "P", side, tf)) for tf in TFS}
    tfs = [tf for tf in TFS if v[tf] in PASS and v[[o for o in TFS if o != tf][0]] != "NO VALUE"]
    return {"qualifies": bool(tfs), "tfs": tfs}


def apply_decisions(cellres: dict, trading_medians: dict) -> dict:
    ps = {k: (c["p"] if c.get("evaluable") and c.get("p") is not None else 1.0) for k, c in cellres.items()}
    within = {}
    for fam in CONTRASTS:
        within.update(holm({k: p for k, p in ps.items() if k.startswith(fam + "|")}))
    glob = holm(ps)
    out = {"cells": {}, "disagreements": []}
    for k, c in cellres.items():
        con = k.split("|")[0]
        v1, v2 = decide(con, c, within[k]), decide(con, c, glob[k])
        out["cells"][k] = {"p_holm_family": within[k], "p_holm_all": glob[k], "verdict": v1, "verdict_all_cell_holm": v2}
        if v1 != v2:
            out["disagreements"].append({"cell": k, "primary": v1, "all_cell_holm": v2})
    for scope, key in (("primary", "verdict"), ("all_cell_holm", "verdict_all_cell_holm")):
        V = {k: v[key] for k, v in out["cells"].items()}
        sides = {}
        for side in (1, -1):
            q = {c: qualifies(V, c, side) for c in CONTRASTS}
            q["C2"]["qualifies"] = q["C2"]["qualifies"] and q["C1"]["qualifies"]     # MACD only on top of a qualifying RSI step
            succ = []
            if q["C0"]["qualifies"]:
                for con, model in (("C1", "B"), ("C2", "C"), ("C3", "D")):
                    if q[con]["qualifies"]:
                        for tf in q[con]["tfs"]:
                            med = trading_medians.get((model, side, tf))
                            if med is not None and med >= 0:
                                succ.append({"feature": con, "model": model, "tf": tf, "pair_median_net": med})
            sides[f"{side:+d}"] = {"qualifies": q, "success_routes": succ}
        p_cells = {k: v for k, v in V.items() if k.split("|")[1] == "P"}
        c0_all_no = all(v == "NO VALUE" for k, v in p_cells.items() if k.startswith("C0|"))
        inc_all_no = all(v == "NO VALUE" for k, v in p_cells.items() if not k.startswith("C0|"))
        if any(s["success_routes"] for s in sides.values()):
            stage = "SUCCESS (exploratory)"
        elif c0_all_no or inc_all_no:
            stage = "REJECTED"
        else:
            stage = "INCONCLUSIVE"
        out[scope] = {"sides": sides, "stage": stage}
    if out["primary"]["stage"] != out["all_cell_holm"]["stage"]:
        out["disagreements"].append({"stage": True, "primary": out["primary"]["stage"], "all_cell_holm": out["all_cell_holm"]["stage"]})
    return out


def trading_summary(d: pd.DataFrame) -> dict:
    ok = d[d["trade_status"] == "ok"]
    out = {"units": int(len(d)), "trades": int(len(ok)), "status": d["trade_status"].value_counts().to_dict(),
           "cost_sources": ok["cost_src"].value_counts().to_dict()}
    if len(ok):
        net = ok["net"].to_numpy(float)
        slip = ok["slip"].to_numpy(float)
        pm = ok.groupby("sym")["net"].mean()
        srt = np.sort(net)[::-1]
        top = max(1, int(np.ceil(0.01 * len(net))))
        pair_tot = ok.groupby("sym")["net"].sum().sort_values(ascending=False)
        tot = net.sum()
        out.update({"net_mean": float(net.mean()), "net_median": float(np.median(net)),
                    "net_pct": [float(v) for v in np.percentile(net, [5, 25, 50, 75, 95])],
                    "net_mean_slip0": float((net + slip).mean()), "net_mean_slip2": float((net - slip).mean()),
                    "pair_median_of_mean_net": float(pm.median()), "pairs": int(len(pm)), "pairs_positive": int((pm > 0).sum()),
                    "worst_trade": float(net.min()), "mae_pct": [float(v) for v in np.percentile(ok["mae_trade"], [5, 50, 95])],
                    "top1pct_trades_share_of_total": _num(srt[:top].sum() / tot) if tot != 0 else None,
                    "top5_pairs_share_of_total": _num(pair_tot.iloc[:5].sum() / tot) if tot != 0 else None,
                    "total_net": float(tot)})
    return out


def _books(results, key) -> dict:
    b = [r["books"][key] for r in results if key in r["books"]]
    if not b:
        return {"pairs": 0}
    return {"pairs": len(b), "median_total_log_return": float(np.median([x["total_log_return"] for x in b])),
            "median_max_drawdown": float(np.median([x["max_drawdown"] for x in b])),
            "pairs_positive": int(sum(x["total_log_return"] > 0 for x in b))}


def evaluate(results: list[dict], reps_wild: int = REPS_WILD, reps_removal: int = REPS_REMOVAL) -> dict:
    out = {"cells": {}, "trading": {}, "comparators": {}, "regimes": {}, "btc": {}, "exclusions": {}, "contrast_C_vs_A": {}}
    tmed = {}
    for tf in TFS:
        rs = [r for r in results if r["tf"] == tf]
        U = pd.concat([r["units"] for r in rs if len(r["units"])], ignore_index=True)
        T, Bt = U[U["sym"] != X.BTC], U[U["sym"] == X.BTC]
        tg = [r for r in rs if r["sym"] != X.BTC]
        out["exclusions"][tf] = {
            "candles": {r["sym"]: {"in_window": r["candles_in_window"], "eligible": r["eligible_candles"],
                                   "first_fail": r["first_fail_counts"]} for r in rs},
            "signals": {f"{cfg}|{s:+d}": {
                "in_window": int(((T["cfg"] == cfg) & (T["side"] == s) & T["window"]).sum()),
                "first_fail": T[(T["cfg"] == cfg) & (T["side"] == s) & T["window"]]["first_fail"].replace("", "pass").value_counts().to_dict(),
                "no_exit": int(((T["cfg"] == cfg) & (T["side"] == s) & T["eligible"] & T["no_exit"]).sum()),
                "gap": int(((T["cfg"] == cfg) & (T["side"] == s) & T["eligible"] & T["gap"]).sum()),
                "entry_gap": int(((T["cfg"] == cfg) & (T["side"] == s) & T["eligible"] & T["entry_gap"]).sum()),
                "no_benchmark": int(((T["cfg"] == cfg) & (T["side"] == s) & T["eligible"] & ~T["no_exit"] & ~T["gap"] & ~T["entry_gap"] & T["rh_x"].isna()).sum()),
                "in_S_A": int(((T["cfg"] == cfg) & (T["side"] == s) & T["in_S"]).sum())} for cfg in CFG_IDS for s in (1, -1)}}
        for con, cfg, side, tf_ in cells():
            if tf_ != tf:
                continue
            model, parent = CONTRASTS[con]
            base = T[(T["cfg"] == cfg) & (T["side"] == side) & T["in_S"]].reset_index(drop=True)
            k = cell_key(con, cfg, side, tf)
            if con == "C0":
                rr = [r["rand"][(cfg, side)] for r in tg if (cfg, side) in r["rand"]]
                sums = np.sum([x["sums"] for x in rr], axis=0) if rr else np.zeros(REPS_RAND)
                cnts = np.sum([x["counts"] for x in rr], axis=0) if rr else np.zeros(REPS_RAND)
                c = c0_stats(base, sums, cnts, reps_wild)
                c["random_entry_shortfall_blocks"] = int(sum(x["shortfall_blocks"] for x in rr))
            else:
                S = base if parent == "A" else base[base[parent]].reset_index(drop=True)
                c = diff_stats(S, S[model].to_numpy(bool), reps_wild, reps_removal) if len(S) else {"evaluable": False, "n_parent": 0}
            out["cells"][k] = c
        for side in (1, -1):
            base = T[(T["cfg"] == "P") & (T["side"] == side) & T["in_S"]]
            out["contrast_C_vs_A"][f"{side:+d}|{tf}"] = diff_stats(base.reset_index(drop=True), base["C"].to_numpy(bool), 999, 50) \
                if len(base) and base["C"].any() and (~base["C"]).any() else None
            for model in "ABCD":
                m = base if model == "A" else base[base[model]]
                tr = {"targets": trading_summary(m), "books": _books(tg, ("P", side, model))}
                if side < 0:
                    tr["short_primary_perp_pairs"] = trading_summary(m[m["perp_ok"]])
                    tr["short_perp_unverified"] = trading_summary(m[~m["perp_ok"]])
                out["trading"][f"P|{model}|{side:+d}|{tf}"] = tr
                tmed[(model, side, tf)] = tr["targets"].get("pair_median_of_mean_net")
                out["regimes"][f"{model}|{side:+d}|{tf}"] = {
                    "by_year": m.groupby("year")["rh_x"].agg(["count", "mean"]).reset_index().to_dict("records"),
                    "by_vol_tercile": m.groupby("vol")["rh_x"].agg(["count", "mean"]).reset_index().to_dict("records")}
                b = Bt[(Bt["cfg"] == "P") & (Bt["side"] == side) & Bt["in_S"]]
                b = b if model == "A" else b[b[model]]
                out["btc"][f"{model}|{side:+d}|{tf}"] = {"n": int(len(b)), "mean_rh_x": _num(b["rh_x"].mean()) if len(b) else None,
                                                         "trading": trading_summary(b)}
            Cm = pd.concat([r["comps"] for r in tg if len(r["comps"])], ignore_index=True) if any(len(r["comps"]) for r in tg) else pd.DataFrame()
            for name in COMPARATORS:
                cc = Cm[(Cm["comp"] == name) & (Cm["side"] == side)] if len(Cm) else Cm
                if not len(cc):
                    continue
                t = INF.cluster_mean_test(cc["rh_x"].to_numpy(float), cc["cl"].to_numpy(), reps=reps_wild, seed=SEED)
                both = pd.concat([base[["rh_x", "cl"]].assign(k=True), cc[["rh_x", "cl"]].assign(k=False)], ignore_index=True)
                dtt = INF.cluster_diff_test(both["rh_x"].to_numpy(float), both["k"].to_numpy(bool), both["cl"].to_numpy(), reps=reps_wild, seed=SEED)
                out["comparators"][f"{name}|{side:+d}|{tf}"] = {"n": int(len(cc)), "mean_rh_x": float(cc["rh_x"].mean()),
                                                               "ci95": t.get("ci95"), "A_minus_comparator": dtt.get("delta"),
                                                               "A_minus_comparator_ci95": dtt.get("ci95")}
    out["decisions"] = apply_decisions(out["cells"], tmed)
    return out


# ----------------------------------------------------------------------------- run

def prepare():
    h1 = {s: DG.load(s, "1H") for s in UNIVERSE}
    return X.liquidity_panel(h1), {s: h1[s].index[0] for s in UNIVERSE}


def _commit_ledger(tid):
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    msg = (f"V6 ledger: record trial {tid} (before its computation)\n\n"
           "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
           "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25")
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=ROOT, check=True)
    LG.verify_against_git(LG.LEDGER)


def run():
    mode = GT.require_v6_ready()
    v = MF.verify(ROOT / GT.MANIFEST)
    if any(v.values()):
        raise SystemExit(f"cache differs from the manifest: {v}")
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    from hcmtf import data as HD
    extra = [str(HD.DATA_DIR / f"{s}_{k}.csv.gz") for s in UNIVERSE for k in ("funding", "perp1h") if f"{s}_{k}.csv.gz" in m["files"]]
    data_files = sorted({str(Path(p)) for s in UNIVERSE for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)} | set(extra))
    LG.verify_against_git(LG.LEDGER)
    liq, first = prepare()
    results = []
    for tf in TFS:
        for cfg in CFG_IDS:
            tid = f"v6-{cfg}-{tf}"
            LG.record(tid, "V6-P" if cfg == "P" else "V6-S", ["exploration"],
                      {"config": CONFIG, "cfg": cfg, "tf": tf, "mode": mode,
                       "cells": [cell_key(c, g, s, t) for c, g, s, t in cells() if g == cfg and t == tf]},
                      CODE_FILES, ["rh_x", "delta", "random_entry", "removal", "per_pair", "trading"], True, CONFIG,
                      data_files, notes=f"exploration; review mode {mode}")
            _commit_ledger(tid)
        with ProcessPoolExecutor(8) as ex:
            results += list(ex.map(worker, [(s, tf, liq[s], first[s]) for s in UNIVERSE]))
        print(f"[{tf}] computed {len(UNIVERSE)} pairs", flush=True)
    ev = evaluate(results)
    ev["meta"] = {"mode": mode, "config": CONFIG, "universe": list(UNIVERSE), "manifest_combined_sha256": m["combined_sha256"],
                  "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(_clean(ev), indent=1, default=str))
    print("stage:", ev["decisions"]["primary"]["stage"], "| all-cell Holm:", ev["decisions"]["all_cell_holm"]["stage"])


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return [_clean(v) for v in o.tolist()]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, pd.Timestamp):
        return o.isoformat()
    return o


# ----------------------------------------------------------------------------- render

def _f(x, nd=3, sign=False):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "–"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def render():
    R = json.loads(OUT.read_text())
    meta, D = R["meta"], R["decisions"]
    L = ["# HC-MTF 6.0 stage 1: continuation models A–D on crypto 1H/4H (results)", "",
         f"**EXPLORATORY ONLY. Review mode: `{meta['mode']}`.** Every candle read was examined in earlier studies; nothing here",
         "is out-of-sample, independent confirmation, or evidence of an edge. A stage-1 success does not authorise a Pine release.",
         f"Configuration `{meta['config']}` (frozen); run at `{meta['git_head'][:7]}`; manifest `{meta['manifest_combined_sha256'][:16]}…`.", "",
         f"## Stage-1 outcome: **{D['primary']['stage']}** (primary, Holm within family) · {D['all_cell_holm']['stage']} (Holm across all 112 cells)", ""]
    for scope in ("primary", "all_cell_holm"):
        for s, v in D[scope]["sides"].items():
            q = v["qualifies"]
            L.append(f"* {scope} · side {s}: A {'qualifies' if q['C0']['qualifies'] else 'does not qualify'}; "
                     f"RSI {q['C1']['qualifies']}; MACD {q['C2']['qualifies']}; extension {q['C3']['qualifies']}; success routes {v['success_routes']}")
    L += ["", "**Disagreements between the two correction scopes:** " + (json.dumps(D["disagreements"]) if D["disagreements"] else "none."), "",
          "## Decision cells (signal quality: `rh_x` in ATR after costs, minus the pair's past same-state mean)", "",
          "| cell | n (kept/removed) | pairs | estimate [t-CI] | eq-pair | qual. pairs | median pair | share>0 | altcoin | trim5 | drop best | control (p97.5) | G | p | Holm fam | Holm all | verdict | verdict (all-cell) |",
          "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|"]
    for k, c in R["cells"].items():
        d = D["cells"][k]
        if k.startswith("C0"):
            t = c.get("test") or {}
            est = "–" if c.get("mean") is None else f"{_f(c['mean'], 3, True)} [{_f((t.get('ci95') or [None])[0], 3, True)}, {_f((t.get('ci95') or [None, None])[1], 3, True)}]"
            ctrl = "–" if not c.get("random_entry") else f"rh {_f(c['rh_mean'], 3, True)} vs {_f(c['random_entry']['p97.5'], 3, True)}"
            L.append(f"| {k} | {c.get('n', 0)} | {c.get('pairs', 0)} | {est} | {_f(c.get('eq_pair_mean'), 3, True)} | {c.get('qualifying_pairs', '–')} | "
                     f"{_f(c.get('median_pair'), 3, True)} | {_f(c.get('positive_share'), 2)} | {_f(c.get('altcoin_mean'), 3, True)} | {_f(c.get('trim5'), 3, True)} | "
                     f"{_f(c.get('drop_best'), 3, True)} | {ctrl} | {c.get('G', '–')} | {_f(c.get('p'), 4)} | {_f(d['p_holm_family'], 4)} | {_f(d['p_holm_all'], 4)} | **{d['verdict']}** | {d['verdict_all_cell_holm']} |")
        else:
            t = c.get("test") or {}
            est = "–" if c.get("delta") is None else f"{_f(c['delta'], 3, True)} [{_f(t['ci95'][0], 3, True)}, {_f(t['ci95'][1], 3, True)}]"
            ctrl = "–" if not c.get("removal") else f"{_f(c['mean_kept'], 3, True)} vs {_f(c['removal']['p97.5'], 3, True)}"
            L.append(f"| {k} | {c.get('n_kept', 0)}/{c.get('n_removed', 0)} | {c.get('pairs', 0)} | {est} | {_f(c.get('eq_pair_delta'), 3, True)} | "
                     f"{c.get('qualifying_pairs', '–')} | {_f(c.get('median_pair_delta'), 3, True)} | {_f(c.get('positive_share'), 2)} | {_f(c.get('altcoin_delta'), 3, True)} | "
                     f"{_f(c.get('trim5'), 3, True)} | {_f(c.get('drop_best'), 3, True)} | {ctrl} | {c.get('G', '–')} | {_f(c.get('p'), 4)} | "
                     f"{_f(d['p_holm_family'], 4)} | {_f(d['p_holm_all'], 4)} | **{d['verdict']}** | {d['verdict_all_cell_holm']} |")
    L += ["", "## Net trading results, config P (separate from signal quality; never decisive)", "",
          "Fees 20 bp + slippage 10/20 bp round trip by liquidity rank; shorts pay funding (observed or 10%/yr estimated). Stop = pullback extreme ∓ 0.5 ATR; time exit 2H.", "",
          "| model · side · TF | trades | net mean | net median | pair median of mean net | pairs > 0 | slip ×0 / ×2 mean | MAE p50/p95 | top 1% trades share | top 5 pairs share | book median log ret / max DD | cost sources |",
          "|---|---:|---:|---:|---:|---|---|---|---:|---:|---|---|"]
    for k, tr in R["trading"].items():
        x = tr["targets"]
        if not x.get("trades"):
            L.append(f"| {k} | 0 | | | | | | | | | | |")
            continue
        b = tr["books"]
        L.append(f"| {k} | {x['trades']} | {_f(x['net_mean'], 4, True)} | {_f(x['net_median'], 4, True)} | {_f(x['pair_median_of_mean_net'], 4, True)} | "
                 f"{x['pairs_positive']}/{x['pairs']} | {_f(x['net_mean_slip0'], 4, True)} / {_f(x['net_mean_slip2'], 4, True)} | "
                 f"{_f(x['mae_pct'][1], 3)} / {_f(x['mae_pct'][2], 3)} | {_f(x['top1pct_trades_share_of_total'], 2)} | {_f(x['top5_pairs_share_of_total'], 2)} | "
                 f"{_f(b.get('median_total_log_return'), 2, True)} / {_f(b.get('median_max_drawdown'), 2, True)} | {x['cost_sources']} |")
        for key, nm in (("short_primary_perp_pairs", "perp pairs"), ("short_perp_unverified", "perp unverified")):
            y = tr.get(key)
            if y and y.get("trades"):
                L.append(f"| {k} · {nm} | {y['trades']} | {_f(y['net_mean'], 4, True)} | {_f(y['net_median'], 4, True)} | {_f(y['pair_median_of_mean_net'], 4, True)} | "
                         f"{y['pairs_positive']}/{y['pairs']} | | | | | | {y['cost_sources']} |")
    L += ["", "## Comparators (signal quality, config-P benchmark)", "", "| comparator · side · TF | n | mean rh_x [t-CI] | A − comparator [t-CI] |", "|---|---:|---|---|"]
    for k, c in R["comparators"].items():
        ci, dci = c.get("ci95") or [None, None], c.get("A_minus_comparator_ci95") or [None, None]
        L.append(f"| {k} | {c['n']} | {_f(c['mean_rh_x'], 3, True)} [{_f(ci[0], 3, True)}, {_f(ci[1], 3, True)}] | "
                 f"{_f(c.get('A_minus_comparator'), 3, True)} [{_f(dci[0], 3, True)}, {_f(dci[1], 3, True)}] |")
    L += ["", "## C vs A (reported, not decided)", ""]
    for k, c in R["contrast_C_vs_A"].items():
        if c:
            L.append(f"* {k}: Δ {_f(c.get('delta'), 3, True)} CI {c['test'].get('ci95')} (kept {c['n_kept']}, removed {c['n_removed']})")
    L += ["", "## Regimes (descriptive, config P: mean rh_x by volatility tercile and by year)", ""]
    for k, r in R["regimes"].items():
        L.append(f"* {k}: vol {[(x['vol'], x['count'], round(x['mean'], 3) if x['mean'] is not None else None) for x in r['by_vol_tercile']]}; "
                 f"years {[(x['year'], x['count'], round(x['mean'], 3) if x['mean'] is not None else None) for x in r['by_year']]}")
    L += ["", "## BTCUSDT (separate; never pooled or decided)", ""]
    for k, b in R["btc"].items():
        L.append(f"* {k}: n {b['n']}, mean rh_x {_f(b['mean_rh_x'], 3, True)}, net mean {_f(b['trading'].get('net_mean'), 4, True)}")
    L += ["", "## Exclusions (counted, never hidden)", "", "```", json.dumps({tf: e["signals"] for tf, e in R["exclusions"].items()}, indent=1), "```"]
    MD.write_text("\n".join(L) + "\n")
    P = ["# HC-MTF 6.0 stage 1: per-pair results (exploratory)", ""]
    for k, c in R["cells"].items():
        if not c.get("per_pair"):
            continue
        P += [f"## {k}", ""]
        if k.startswith("C0"):
            P += ["| pair | n | mean rh_x |", "|---|---:|---:|"] + [f"| {r['sym']} | {r['count']} | {_f(r['mean'], 3, True)} |" for r in c["per_pair"]]
        else:
            P += ["| pair | n kept | n removed | mean kept | mean removed | Δ |", "|---|---:|---:|---:|---:|---:|"]
            P += [f"| {r['sym']} | {r['n_k']} | {r['n_r']} | {_f(r['mean_k'], 3, True)} | {_f(r['mean_r'], 3, True)} | {_f(r['delta'], 3, True)} |" for r in c["per_pair"]]
        P.append("")
    MD_PAIRS.write_text("\n".join(P) + "\n")
    print("wrote", MD, MD_PAIRS)


if __name__ == "__main__":
    {"run": run, "render": render}[sys.argv[1]]()
