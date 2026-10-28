"""Workstream M, stages A and B (crypto price-only reference and BTC-regime context), 1H/4H
EXPLORATION, exactly as frozen in reports/V5_M_B_CONFIG.md (section numbers refer to it).

    python scripts/v5_m_explore.py run      # gate, manifest check, ledger trials, compute, results json
    python scripts/v5_m_explore.py render   # reports/V5_M_B_RESULTS.md (+ per-pair appendix) from the json

Exploratory only: every candle read was examined before. Results are stamped with the review mode
from research.v5_gate.require_m_ready(). Nothing here changes a threshold, a gate, a signal or a
decision rule of the frozen configuration.
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
from research.v41 import cluster_id  # noqa: E402
from research.v5_costs import CRYPTO_SHORT_FALLBACK_ANNUAL, FUNDING_EDGE, FUNDING_STALE, YEAR_SECONDS, round_trip  # noqa: E402

CONFIG = "reports/V5_M_B_CONFIG.md"
OUT = ROOT / "reports" / "v5_m_b_results.json"
MD = ROOT / "reports" / "V5_M_B_RESULTS.md"
MD_PAIRS = ROOT / "reports" / "V5_M_B_PER_PAIR.md"
START = pd.Timestamp("2020-01-01", tz="UTC")                                   # §1, D1
TFS = {"1H": {"H": 24, "hold": 48, "step": pd.Timedelta(hours=1)},
       "4H": {"H": 30, "hold": 60, "step": pd.Timedelta(hours=4)}}             # §3
CONT = ("S-eng", "S-htf", "S-ema", "S-st")                                     # §4
REV = "R-cr"
COMPARATORS = ("htf_flip", "ema_cross", "supertrend_flip")                     # §4/§5 comparison 3
SEED = 20261027
REPS_REMOVAL, REPS_THIN, REPS_WILD = 200, 50, 9999
SLIPPAGE_SENS = 0.0010                                                         # §6: +10 bp, rank > 10
GAP_FACTOR = 1.25                                                              # §1.1 evaluation-only exclusion
UNIVERSE = (*X.TARGETS, X.BTC)
CODE_FILES = ["research/v5_context.py", "research/v5_eval.py", "research/v5_baselines.py", "research/v5_state.py",
              "research/v5_data.py", "research/v5_inference.py", "research/v5_costs.py",
              "research/v5_gate.py", "scripts/v5_m_explore.py"]


def cells() -> list[tuple[str, str, int]]:
    """The 36 stage-B cells per TF pair (§5): (hypothesis, signal, side)."""
    out = [("M-B1", s, 1) for s in CONT] + [("M-B2", s, -1) for s in CONT]
    out += [("M-B3", s, d) for s in CONT for d in (1, -1)]
    out += [("M-B4", REV, d) for d in (-1, 1)]
    return out


def cell_key(hyp, sig, side, tf) -> str:
    return f"{hyp}|{sig}|{side:+d}|{tf}"


# ----------------------------------------------------------------------------- costs and outcomes

def close_times(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Vectorised v5_eval._close_time: min(next open, open + median of the previous <= 50 spacings)."""
    n = len(index)
    t = index.as_unit("ns").asi8
    d = np.diff(t).astype(float)
    med = pd.Series(d).rolling(50, min_periods=1).median().to_numpy()       # median of spacings ending at k
    step = np.r_[0.0, med]
    cap = t + step.astype(np.int64)
    nxt = np.r_[t[1:], np.iinfo(np.int64).max]
    return pd.DatetimeIndex(np.minimum(nxt, cap).astype("datetime64[ns]")).tz_localize("UTC")


def short_cost_vector(index: pd.DatetimeIndex, hold: int, funding: pd.DataFrame | None):
    """Short holding cost (fraction of notional) and its source for a trade on EVERY candle i,
    entry = open of i+1, exit = close time of i+hold; equal to v5_costs.short_holding_cost
    (tested). NaN / "" where i+hold is past the data."""
    n = len(index)
    cost = np.full(n, np.nan)
    src = np.full(n, "", dtype=object)
    m = n - hold
    if m <= 0:
        return cost, src
    ct = close_times(index)
    entry = index[1:m + 1]
    exit_ = ct[hold:hold + m]
    yrs = (exit_ - entry).total_seconds().to_numpy() / YEAR_SECONDS
    est = CRYPTO_SHORT_FALLBACK_ANNUAL * yrs
    cost[:m], src[:m] = est, "estimated_crypto_10pct"
    if funding is None or len(funding) == 0:
        return cost, src
    ft = funding.index.as_unit("ns").asi8
    rate = funding["rate"].to_numpy(float)
    e, x = entry.as_unit("ns").asi8, exit_.as_unit("ns").asi8
    edge, stale = FUNDING_EDGE.value, FUNDING_STALE.value
    lo = np.searchsorted(ft, e - edge, "right")                  # first print > entry - edge
    hi = np.searchsorted(ft, x, "right")                         # prints < hi are <= exit
    has = hi > lo
    cov = (ft[0] <= e) & (ft[-1] >= x - edge)
    first_gap = np.where(has, ft[np.minimum(lo, len(ft) - 1)] - np.maximum(e - edge, ft[0]), 0)
    g = np.r_[0, np.diff(ft)] > stale                            # gap before print j is stale
    gc = np.r_[0, np.cumsum(g)]
    internal_bad = gc[hi] - gc[np.minimum(lo + 1, hi)]           # stale gaps before prints lo+1 .. hi-1
    ok = cov & np.where(has, (first_gap <= stale) & (internal_bad == 0), (x - e) < edge)
    cs = np.r_[0.0, np.cumsum(rate)]
    a = np.searchsorted(ft, e, "right")
    paid = cs[hi] - cs[np.minimum(a, hi)]
    cost[:m] = np.where(ok, -paid, est)
    src[:m] = np.where(ok, "observed_funding", "estimated_crypto_10pct")
    return cost, src


class _F:
    pass


def outcomes(df: pd.DataFrame, tf: str, funding) -> dict:
    """§3 signal-quality outcomes per side for every candle (rh after costs in ATR, MFE, MAE,
    barrier) and the evaluation-only gap flag."""
    H, step = TFS[tf]["H"], TFS[tf]["step"]
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    f = _F(); f.o, f.h, f.l, f.c = o, h, l, c; f.atr = ta.atr(h, l, c, 14)
    bo = bar_outcomes(f, H, round_trip("crypto") * 1e4)
    hc, src = short_cost_vector(df.index, H, funding)
    n = len(c)
    px = np.r_[o[1:], np.nan]
    with np.errstate(divide="ignore", invalid="ignore"):
        hc_atr = hc * px / f.atr
    out = {1: dict(bo[1]), -1: dict(bo[-1])}
    out[1]["rh"] = bo[1]["r_h"]
    out[-1]["rh"] = bo[-1]["r_h"] - hc_atr
    gap = np.zeros(n, bool)
    if n > H:
        t = df.index
        span = (t[H:] + step) - t[1:n - H + 1]                   # open of i+1 .. close of i+H
        gap[:n - H] = span.to_numpy() > (GAP_FACTOR * H * step).to_timedelta64()
    out["gap"] = gap
    out["short_cost_src"] = src
    return out


def trade_mae(h, l, side, px, e, x) -> float:
    if side > 0:
        return float((px - np.min(l[e:x + 1])) / px)
    return float((np.max(h[e:x + 1]) - px) / px)


# ----------------------------------------------------------------------------- per-pair worker

def engine_signals(df, htf1, htf2, tf) -> dict:
    """S-eng and R-cr per side from one engine pass (as v5_baselines.counter_reversal)."""
    p = G.DEFAULTS[tf]
    t = G.breaks(G.features(G.Ctx(df, htf1, htf2, None, False, False), p), p)
    out = {}
    for side in (1, -1):
        for name, cls in (("S-eng", "continuation"), (REV, "counter_reversal")):
            if len(t) == 0:
                out[(name, side)] = np.array([], int)
                continue
            s = t[t["warm"] & (t["cls"] == cls) & (t["dir"] == side)]
            out[(name, side)] = np.unique(s["i"].to_numpy(int))
    return out


def all_signals(df, htf1, htf2, st, tf) -> dict:
    sig = engine_signals(df, htf1, htf2, tf)
    for side in (1, -1):
        sig[("S-htf", side)] = B.htf_flip(st, side)
        sig[("S-ema", side)] = B.ema_cross(df, side)
        sig[("S-st", side)] = B.supertrend_flip(df, side)
    return sig


def _book(o, c, idx, trades) -> dict:
    if not trades:
        return {"trades": 0}
    s = EV.sequential_daily(o, c, idx, trades)
    cum = s.cumsum()
    return {"trades": len(trades), "total_log_return": float(cum.iloc[-1]),
            "max_drawdown": float((cum - cum.cummax()).min()), "worst_trade": float(min(t["net"] for t in trades))}


def worker(args):
    sym, tf, btc_state, liq, first_open = args
    _, h1n, h2n = G.LADDER[tf]
    df, htf1, htf2 = DG.load(sym, tf), DG.load(sym, h1n), DG.load(sym, h2n)
    st = ST.classify(df, htf1, htf2)
    idx = df.index
    n = len(idx)
    start_i = int(idx.searchsorted(START))
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    dl = st["direction_label"].to_numpy(object)
    warm = st["warm"].to_numpy(bool)
    cl = cluster_id(idx, tf)
    H, hold = TFS[tf]["H"], TFS[tf]["hold"]
    is_btc = sym == X.BTC
    ctx = None if is_btc else X.btc_context(idx, btc_state)
    el = X.eligibility(sym, idx, first_open, liq, warm, None if is_btc else ctx["available"].to_numpy())
    funding = DG.load_funding(sym)
    oc = outcomes(df, tf, funding)
    rhx = {}
    for side in (1, -1):
        r = np.where(warm, oc[side]["rh"], np.nan)
        ct = EV.candle_table(sym, idx, tf, H, {"direction_label": dl}, {"r_h": r})
        rhx[side] = oc[side]["rh"] - EV.causal_benchmark(ct, "r_h", ["direction_label"], H, 200)
    sig = all_signals(df, htf1, htf2, st, tf)
    elig = el["eligible"].to_numpy(bool) & (np.arange(n) >= start_i)
    pstart = X.perp_start(sym)
    rank = el["rank"].to_numpy(float)
    rows, scores, books = [], {}, {}
    for (name, side), ii in sig.items():
        for i in ii:
            i = int(i)
            no_exit = i + H >= n
            rows.append({"sym": sym, "sig": name, "side": side, "i": i, "t": idx[i], "cl": int(cl[i]),
                         "dl": dl[i], "window": i >= start_i, "first_fail": el["first_fail"].iat[i],
                         "eligible": bool(elig[i]), "rank": rank[i],
                         "btc_dir": X.UNAVAILABLE if is_btc else ctx["btc_dir"].iat[i],
                         "btc_unstable": X.UNAVAILABLE if is_btc else ctx["btc_unstable"].iat[i],
                         "no_exit": bool(no_exit), "gap": bool(oc["gap"][i]),
                         "rh": oc[side]["rh"][i], "rh_x": rhx[side][i], "mfe": oc[side]["mfe"][i],
                         "mae": oc[side]["mae"][i], "barrier": oc[side]["barrier"][i],
                         "perp_ok": bool(sym in X.PERP_PAIRS and pstart is not None and idx[i] >= pstart)})
    u = pd.DataFrame(rows)
    if len(u):
        u["metric_ok"] = u["eligible"] & ~u["no_exit"] & ~u["gap"] & u["rh_x"].notna()
        u["near"] = np.nan
    # R-cr: frozen labels, scorable alerts (§3 event quality)
    lab = {}
    for side in (1, -1):
        fam = "top" if side < 0 else "bottom"
        lab[side] = EV.frozen_labels(sym, h, l, c, fam, tf, idx)
        al = np.array([i for i in sig[(REV, side)] if elig[i]], int)
        sc = EV.score_alerts(lab[side], al, "confirmation", start_i)
        lu = EV.lift_units(lab[side], sc, "confirmation", dl, warm, start_i)
        if len(u) and len(lu):
            m = (u["sig"] == REV) & (u["side"] == side)
            u.loc[m, "near"] = u.loc[m, "i"].map(lu.set_index("i")["near"]).to_numpy(float)
        scores[("S", side)] = sc
        s_units = lu["i"].to_numpy(int)
        gen = {"htf_flip": B.htf_flip(st, side), "ema_cross": B.ema_cross(df, side), "supertrend_flip": B.supertrend_flip(df, side)}
        base = {b: np.array([i for i in gen[b] if elig[i]], int) for b in COMPARATORS}
        sets = {"S": s_units}
        if not is_btc:
            k = X.gate("M-B4", ctx["btc_dir"].to_numpy(object)[s_units], side) if len(s_units) else np.array([], bool)
            sets["K"], sets["SK"] = s_units[k], s_units[~k]
            scores[("K", side)] = EV.score_alerts(lab[side], sets["K"], "confirmation", start_i)
            scores[("SK", side)] = EV.score_alerts(lab[side], sets["SK"], "confirmation", start_i)
        for target in ("S", "K"):
            if target not in sets:
                continue
            for b in COMPARATORS:
                th = B.thin(base[b], sets[target], idx, tf, reps=REPS_THIN, seed=SEED)
                reps = []
                for r in th["replicates"]:
                    s2 = EV.score_alerts(lab[side], r, "confirmation", start_i)
                    stt = list(s2["status"].values())
                    reps.append({"events": len(s2["events"]), "matched": len(s2["pairs"]), "alerts": len(s2["alerts"]),
                                 "fa": stt.count("false_alarm"), "dup": stt.count("duplicate")})
                scores[("thin", target, b, side)] = {"reps": reps, "target": th["target"], "available": th["available"],
                                                     "shortfall_blocks": len(th["shortfall_blocks"])}
    # trades for every unit of every S (§3 trading outcome), then per-subset books
    if len(u):
        u["net"] = np.nan; u["gross"] = np.nan; u["trade_mae"] = np.nan; u["cost_src"] = ""
        in_s = np.where(u["sig"] == REV, u["near"].notna() & u["eligible"], u["metric_ok"])
        u["in_S"] = in_s
        trades = {}
        for k in np.flatnonzero(in_s):
            i, side = int(u.at[k, "i"]), int(u.at[k, "side"])
            stop = float(np.min(l[max(0, i - 19):i + 1])) if side > 0 else float(np.max(h[max(0, i - 19):i + 1]))
            t = EV.trade(o, h, l, c, idx, i, side, hold, stop, "crypto", funding)
            if t is None:
                u.at[k, "cost_src"] = "no_exit_in_data"
                continue
            u.at[k, "net"], u.at[k, "gross"], u.at[k, "cost_src"] = t["net"], t["gross"], t["holding_cost_source"]
            u.at[k, "trade_mae"] = trade_mae(h, l, side, o[t["entry_i"]], t["entry_i"], t["exit_i"])
            trades[k] = t
        for (name, side) in sig:
            m = (u["sig"] == name) & (u["side"] == side) & u["in_S"]
            subs = {"S": m}
            if not is_btc:
                for hyp in ("M-B1", "M-B2", "M-B3", "M-B4"):
                    field = X.GATES[hyp][0]
                    kept = X.gate(hyp, u[field].to_numpy(object), side)
                    subs[(hyp, "K")], subs[(hyp, "SK")] = m & kept, m & ~kept
            for key, mm in subs.items():
                books[(name, side, key)] = _book(o, c, idx, [trades[k] for k in np.flatnonzero(mm.to_numpy()) if k in trades])
    return {"sym": sym, "tf": tf, "units": u, "scores": scores, "books": books, "index": idx, "start_i": start_i,
            "candles_in_window": int(n - start_i), "eligible_candles": int(elig.sum()),
            "first_fail_counts": el["first_fail"][np.arange(n) >= start_i].value_counts().to_dict(),
            "context_unavailable_candles": 0 if is_btc else int((~ctx["available"].to_numpy()[start_i:]).sum())}


# ----------------------------------------------------------------------------- aggregation

def _num(x):
    return None if x is None or not np.isfinite(x) else float(x)


def per_pair(S: pd.DataFrame, metric: str, kept: np.ndarray) -> pd.DataFrame:
    d = S.assign(_k=kept)
    g = d.groupby("sym")
    out = pd.DataFrame({"n_k": g["_k"].sum().astype(int), "n_r": g["_k"].apply(lambda s: int((~s).sum()))})
    out["mean_k"] = d[d["_k"]].groupby("sym")[metric].mean()
    out["mean_r"] = d[~d["_k"]].groupby("sym")[metric].mean()
    out["delta"] = out["mean_k"] - out["mean_r"]
    out["qualifying"] = (out["n_k"] >= 20) & (out["n_r"] >= 20)
    out["tier"] = [X.tier(s) for s in out.index]
    return out


def _tier_delta(S, metric, kept, names) -> float | None:
    m = S["sym"].isin(names).to_numpy()
    a, b = S[metric].to_numpy(float)[m & kept], S[metric].to_numpy(float)[m & ~kept]
    return float(a.mean() - b.mean()) if len(a) and len(b) else None


def cell_stats(S: pd.DataFrame, metric: str, hyp: str, side: int, ep_ids: pd.Series, ep_table: pd.DataFrame,
               reps_wild: int = REPS_WILD, reps_removal: int = REPS_REMOVAL) -> dict:
    """Every §5/§7/§8 quantity of one cell (decision itself in decide())."""
    field = X.GATES[hyp][0]
    kept = X.gate(hyp, S[field].to_numpy(object), side)
    x = S[metric].to_numpy(float)
    ep = ep_ids.reindex(pd.DatetimeIndex(S["t"])).to_numpy()
    if np.isnan(ep.astype(float)).any():
        raise RuntimeError("a unit has no BTC episode (E7 should have excluded it)")
    t_cal = INF.cluster_diff_test(x, kept, S["cl"].to_numpy(), reps=reps_wild, seed=SEED)
    t_ep = INF.cluster_diff_test(x, kept, ep.astype(int), reps=reps_wild, seed=SEED)
    pp = per_pair(S, metric, kept)
    q = pp[pp["qualifying"]]
    defined = pp["delta"].notna()
    rem = X.matched_removal_means(x, S["sym"].astype(str) + "|" + S["dl"].astype(str), kept, reps_removal, SEED)
    eps_with = pd.unique(ep.astype(int))
    vals = ep_table.loc[eps_with, "value"].to_numpy(object)
    sat = X.gate(hyp, vals, side)
    within = {}
    for s in ("bull", "bear", "neutral"):
        m = S["dl"].to_numpy(object) == s
        a, b = x[m & kept], x[m & ~kept]
        within[s] = {"n_k": int(len(a)), "n_r": int(len(b)), "delta": float(a.mean() - b.mean()) if len(a) and len(b) else None}
    n_k, n_r = int(kept.sum()), int((~kept).sum())
    pairs_both = int(((pp["n_k"] > 0) & (pp["n_r"] > 0)).sum())
    out = {
        "n_S": int(len(S)), "n_K": n_k, "n_SK": n_r, "pairs": int(S["sym"].nunique()), "pairs_both": pairs_both,
        "mean_S": _num(x.mean()) if len(x) else None, "mean_K": _num(x[kept].mean()) if n_k else None,
        "mean_SK": _num(x[~kept].mean()) if n_r else None,
        "delta": t_cal.get("delta"), "test_calendar": t_cal, "test_episode": t_ep,
        "G_calendar": t_cal["clusters"], "G_episode": t_ep["clusters"],
        "episodes_gate": int(sat.sum()), "episodes_complement": int((~sat).sum()),
        "eq_weight_delta": _num(pp.loc[defined, "delta"].mean()) if defined.any() else None,
        "qualifying_pairs": int(len(q)), "median_pair_delta": _num(q["delta"].median()) if len(q) else None,
        "positive_pair_share": float((q["delta"] > 0).sum() / len(q)) if len(q) else None,
        "altcoin_delta": _tier_delta(S, metric, kept, [s for s in X.TARGETS if s not in X.MAJORS]),
        "majors_delta": _tier_delta(S, metric, kept, list(X.MAJORS)),
        "removal": {"p2.5": _num(np.nanpercentile(rem, 2.5)), "p50": _num(np.nanpercentile(rem, 50)),
                    "p97.5": _num(np.nanpercentile(rem, 97.5))} if n_k else None,
        "within_own_state": within,
        "per_pair": pp.reset_index().rename(columns={"index": "sym"}).to_dict("records"),
    }
    vt = [t_cal.get("valid"), t_ep.get("valid")]
    out["evaluable"] = bool(n_k >= 100 and n_r >= 100 and pairs_both >= 10 and t_cal["clusters"] >= 10
                            and t_ep["clusters"] >= 10 and all(vt) and out["episodes_gate"] >= 3
                            and out["episodes_complement"] >= 3)
    out["p_decisive"] = max(t_cal["p_wild"], t_ep["p_wild"]) if out["evaluable"] else None
    return out


def decide(c: dict, p_holm: float) -> str:
    """§9 per-cell verdict with the given Holm-adjusted decisive p."""
    if not c["evaluable"]:
        return "NOT EVALUABLE"
    pos = lambda v: v is not None and v > 0
    adds = (pos(c["delta"]) and pos(c["eq_weight_delta"])
            and c["qualifying_pairs"] >= 8 and pos(c["median_pair_delta"])
            and c["positive_pair_share"] is not None and c["positive_pair_share"] >= 0.60
            and p_holm < 0.05
            and c["removal"] is not None and c["mean_K"] is not None and c["mean_K"] > c["removal"]["p97.5"]
            and pos(c["altcoin_delta"]))
    if adds:
        return "ADDS VALUE"
    ci_le0 = any(t["ci95"][1] <= 0 for t in (c["test_calendar"], c["test_episode"]))
    both_le0 = (c["delta"] is not None and c["delta"] <= 0) and (c["eq_weight_delta"] is not None and c["eq_weight_delta"] <= 0)
    return "NO VALUE" if (ci_le0 or both_le0) else "INCONCLUSIVE"


def hypothesis_verdict(verdicts: dict) -> str:
    """§9 per hypothesis. verdicts: cell_key -> verdict for ONE hypothesis. SUPPORTED needs >= 1
    ADDS VALUE cell and no ADDS VALUE cell whose same signal x side at the other TF is NO VALUE."""
    ev = {k: v for k, v in verdicts.items() if v != "NOT EVALUABLE"}
    if not ev:
        return "NOT EVALUABLE"
    adds = [k for k, v in ev.items() if v == "ADDS VALUE"]
    if adds:
        def other(k):
            h, s, d, tf = k.split("|")
            return f"{h}|{s}|{d}|{'4H' if tf == '1H' else '1H'}"
        if all(verdicts.get(other(k)) != "NO VALUE" for k in adds):
            return "SUPPORTED"
        return "INCONCLUSIVE"
    if all(v == "NO VALUE" for v in ev.values()):
        return "REJECTED"
    return "INCONCLUSIVE"


def apply_decisions(cellres: dict) -> dict:
    """Holm within each hypothesis (primary) and across all cells (sensitivity), non-evaluable
    cells entering with p = 1 (§7); verdicts under both; hypothesis verdicts; disagreements."""
    ps = {k: (c["p_decisive"] if c["evaluable"] else 1.0) for k, c in cellres.items()}
    within = {}
    for hyp in ("M-B1", "M-B2", "M-B3", "M-B4"):
        within.update(holm({k: p for k, p in ps.items() if k.startswith(hyp + "|")}))
    glob = holm(ps)
    out = {"cells": {}, "hypotheses": {}, "hypotheses_sensitivity": {}, "disagreements": []}
    for k, c in cellres.items():
        v1, v2 = decide(c, within[k]), decide(c, glob[k])
        out["cells"][k] = {"p_holm_within": within[k], "p_holm_all": glob[k], "verdict": v1, "verdict_all_cell_holm": v2}
        if v1 != v2:
            out["disagreements"].append({"cell": k, "primary": v1, "all_cell_holm": v2})
    for hyp in ("M-B1", "M-B2", "M-B3", "M-B4"):
        ks = [k for k in cellres if k.startswith(hyp + "|")]
        out["hypotheses"][hyp] = hypothesis_verdict({k: out["cells"][k]["verdict"] for k in ks})
        out["hypotheses_sensitivity"][hyp] = hypothesis_verdict({k: out["cells"][k]["verdict_all_cell_holm"] for k in ks})
        if out["hypotheses"][hyp] != out["hypotheses_sensitivity"][hyp]:
            out["disagreements"].append({"hypothesis": hyp, "primary": out["hypotheses"][hyp],
                                         "all_cell_holm": out["hypotheses_sensitivity"][hyp]})
    return out


def trading_summary(d: pd.DataFrame) -> dict:
    ok = d[d["net"].notna()]
    out = {"units": int(len(d)), "trades": int(len(ok)), "cost_sources": d["cost_src"].value_counts().to_dict()}
    if len(ok):
        net = ok["net"].to_numpy(float)
        slip = net - np.where(ok["rank"].to_numpy(float) > 10, SLIPPAGE_SENS, 0.0)
        out.update({"net_mean": float(net.mean()), "net_median": float(np.median(net)),
                    "net_mean_slippage_sensitivity": float(slip.mean()),
                    "trade_mae_p5_p50_p95": [float(v) for v in np.percentile(ok["trade_mae"], [5, 50, 95])],
                    "worst_trade": float(net.min())})
    return out


def stage_a(S: pd.DataFrame, metric: str) -> dict:
    x = S[metric].to_numpy(float)
    out = {"n": int(len(S)), "pairs": int(S["sym"].nunique())}
    if len(S) == 0:
        return out
    out.update({"mean": float(x.mean()), "median": float(np.median(x)),
                "rh_mean": float(S["rh"].mean()), "rh_median": float(S["rh"].median()),
                "mfe_mean": float(S["mfe"].mean()), "mae_mean": float(S["mae"].mean()),
                "barrier_win_rate": float((S["barrier"] == 1).mean())})
    t = INF.cluster_mean_test(x, S["cl"].to_numpy(), reps=REPS_WILD, seed=SEED)
    out["test"] = {k: t.get(k) for k in ("mean", "ci95", "p_wild", "clusters", "valid")}
    pp = S.groupby("sym")[metric].agg(["count", "mean", "median"])
    out["per_pair"] = pp.reset_index().to_dict("records")
    out["pair_median_of_means"] = float(pp["mean"].median())
    return out


def matched_summary(rs, key) -> dict:
    agg = []
    for k in range(REPS_THIN):
        m = [r["scores"][key]["reps"][k] for r in rs if key in r["scores"]]
        ev, mt, al, fa = (sum(x[f] for x in m) for f in ("events", "matched", "alerts", "fa"))
        agg.append({"recall": mt / ev if ev else np.nan, "precision_excl_dup": mt / (mt + fa) if (mt + fa) else np.nan,
                    "alerts": al})
    out = {}
    for f in agg[0] if agg else []:
        v = np.array([a[f] for a in agg], float)
        out[f] = [float(np.nanmean(v)), float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))] if np.isfinite(v).any() else None
    out["target_alerts"] = int(sum(r["scores"][key]["target"] for r in rs if key in r["scores"]))
    out["shortfall_blocks"] = int(sum(r["scores"][key]["shortfall_blocks"] for r in rs if key in r["scores"]))
    return out


def _books_summary(results, key) -> dict:
    b = [r["books"][key] for r in results if key in r["books"] and r["books"][key].get("trades")]
    if not b:
        return {"pairs": 0}
    return {"pairs": len(b), "median_total_log_return": float(np.median([x["total_log_return"] for x in b])),
            "median_max_drawdown": float(np.median([x["max_drawdown"] for x in b])),
            "pairs_positive": int(sum(x["total_log_return"] > 0 for x in b))}


def evaluate(results: list[dict], episodes: dict, reps_wild: int = REPS_WILD, reps_removal: int = REPS_REMOVAL) -> dict:
    """episodes: (tf, field) -> (ids Series indexed by BTC candle time, table)."""
    out = {"stage_a": {}, "stage_b": {}, "trading": {}, "detection": {}, "exclusions": {}, "episodes": {}}
    for (tf, field), (_, tab) in episodes.items():
        out["episodes"][f"{tf}|{field}"] = {
            "episodes": int(len(tab)), "raw_runs": int(tab["runs"].sum()) if len(tab) else 0,
            "by_value": tab.groupby("value")["length"].agg(["count", "median", "min", "max"]).reset_index().to_dict("records") if len(tab) else []}
    for tf in TFS:
        rs = [r for r in results if r["tf"] == tf]
        U = pd.concat([r["units"] for r in rs if len(r["units"])], ignore_index=True)
        tgt = U[U["sym"] != X.BTC]
        out["exclusions"][tf] = {
            f"{s}|{d:+d}": {
                "in_window": int(((tgt["sig"] == s) & (tgt["side"] == d) & tgt["window"]).sum()),
                "first_fail": tgt[(tgt["sig"] == s) & (tgt["side"] == d) & tgt["window"]]["first_fail"].replace("", "pass").value_counts().to_dict(),
                "no_exit": int(((tgt["sig"] == s) & (tgt["side"] == d) & tgt["eligible"] & tgt["no_exit"]).sum()),
                "gap": int(((tgt["sig"] == s) & (tgt["side"] == d) & tgt["eligible"] & tgt["gap"]).sum()),
                "no_benchmark": int(((tgt["sig"] == s) & (tgt["side"] == d) & tgt["eligible"] & ~tgt["no_exit"] & ~tgt["gap"] & tgt["rh_x"].isna()).sum()),
                "in_S": int(((tgt["sig"] == s) & (tgt["side"] == d) & tgt["in_S"]).sum())}
            for s in (*CONT, REV) for d in (1, -1)}
        out["exclusions"][tf]["candles"] = {r["sym"]: {"in_window": r["candles_in_window"], "eligible": r["eligible_candles"],
                                                       "context_unavailable": r["context_unavailable_candles"],
                                                       "first_fail": r["first_fail_counts"]} for r in rs}
        # stage A
        for s in (*CONT, REV):
            for d in (1, -1):
                metric = "near" if s == REV else "rh_x"
                base = U[(U["sig"] == s) & (U["side"] == d) & U["in_S"]]
                out["stage_a"][f"{s}|{d:+d}|{tf}"] = {"targets": stage_a(base[base["sym"] != X.BTC], metric),
                                                      "btc": stage_a(base[base["sym"] == X.BTC], metric)}
                out["trading"][f"A|{s}|{d:+d}|{tf}"] = {
                    "targets": trading_summary(base[base["sym"] != X.BTC]), "btc": trading_summary(base[base["sym"] == X.BTC]),
                    "short_primary_perp_pairs": trading_summary(base[(base["sym"] != X.BTC) & base["perp_ok"]]) if d < 0 else None,
                    "short_perp_unverified": trading_summary(base[(base["sym"] != X.BTC) & ~base["perp_ok"]]) if d < 0 else None,
                    "books": _books_summary([r for r in rs if r["sym"] != X.BTC], (s, d, "S"))}
        # R-cr detection (stage A and M-B4 comparison 3)
        times = {r["sym"]: r["index"] for r in rs}
        for d in (1, -1):
            tg = [r for r in rs if r["sym"] != X.BTC]
            det = {k: EV.detection_report({r["sym"]: r["scores"][(k, d)] for r in tg}, times, tf, "confirmation", reps=2000)
                   for k in ("S", "K", "SK")}
            det["btc_S"] = EV.detection_report({X.BTC: r["scores"][("S", d)] for r in rs if r["sym"] == X.BTC}, times, tf,
                                               "confirmation", reps=2000) if any(r["sym"] == X.BTC for r in rs) else None
            det["baselines_matched_to_S"] = {b: matched_summary(tg, ("thin", "S", b, d)) for b in COMPARATORS}
            det["baselines_matched_to_K"] = {b: matched_summary(tg, ("thin", "K", b, d)) for b in COMPARATORS}
            out["detection"][f"{REV}|{d:+d}|{tf}"] = det
        # stage B
        for hyp, s, d in cells():
            metric = "near" if s == REV else "rh_x"
            S = tgt[(tgt["sig"] == s) & (tgt["side"] == d) & tgt["in_S"]].reset_index(drop=True)
            field = X.GATES[hyp][0]
            ids, tab = episodes[(tf, field)]
            k = cell_key(hyp, s, d, tf)
            c = cell_stats(S, metric, hyp, d, ids, tab, reps_wild, reps_removal) if len(S) else {"evaluable": False, "n_S": 0}
            c.setdefault("p_decisive", None)
            out["stage_b"][k] = c
            kept = X.gate(hyp, S[field].to_numpy(object), d) if len(S) else np.array([], bool)
            tr = {"S": trading_summary(S), "K": trading_summary(S[kept]), "SK": trading_summary(S[~kept]),
                  "books_K": _books_summary(rs, (s, d, (hyp, "K"))), "books_SK": _books_summary(rs, (s, d, (hyp, "SK")))}
            okn = S["net"].notna().to_numpy() if len(S) else np.array([], bool)
            if okn.sum() > 1 and kept[okn].any() and (~kept[okn]).any():
                tt = INF.cluster_diff_test(S["net"].to_numpy(float)[okn], kept[okn], S["cl"].to_numpy()[okn], reps=reps_wild, seed=SEED)
                tr["net_delta_information_only"] = {kk: tt.get(kk) for kk in ("delta", "ci95", "p_wild", "clusters")}
            if d < 0 and len(S):
                pm = S["perp_ok"].to_numpy(bool)
                tr["short_primary_perp_pairs"] = {"K": trading_summary(S[kept & pm]), "SK": trading_summary(S[~kept & pm])}
            out["trading"][f"B|{k}"] = tr
    for k, c in out["stage_b"].items():
        if "evaluable" not in c:
            c["evaluable"] = False
    out["decisions"] = apply_decisions({k: c for k, c in out["stage_b"].items()})
    return out


# ----------------------------------------------------------------------------- run

def episodes_for(btc_state: pd.DataFrame, tf: str) -> dict:
    s = btc_state[(btc_state.index >= START) & btc_state["warm"].to_numpy(bool)]
    out = {}
    vals = {"btc_dir": s["direction_label"].to_numpy(object),
            "btc_unstable": np.where(s["vol_regime"].to_numpy(object) == "high", "yes", "no")}
    for field, v in vals.items():
        out[(tf, field)] = X.episodes(s.index, v, TFS[tf]["H"])
    return out


def prepare(tf: str):
    """BTC state for the TF, liquidity panel (all pairs), first 1H open per pair. No outcomes."""
    _, h1n, h2n = G.LADDER[tf]
    btc = ST.classify(DG.load(X.BTC, tf), DG.load(X.BTC, h1n), DG.load(X.BTC, h2n))
    h1 = {s: DG.load(s, "1H") for s in UNIVERSE}
    liq = X.liquidity_panel(h1)
    first = {s: h1[s].index[0] for s in UNIVERSE}
    return btc[["direction_label", "vol_regime", "warm"]], liq, first


def _commit_ledger(tid):
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    msg = (f"V5 ledger: record trial {tid} (before its computation)\n\n"
           "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
           "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25")
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=ROOT, check=True)
    LG.verify_against_git(LG.LEDGER)


TRIALS = (("m-a-ref", "M-A"), ("m-b1", "M-B1"), ("m-b2", "M-B2"), ("m-b3", "M-B3"), ("m-b4", "M-B4"))


def run():
    mode = GT.require_m_ready()
    v = MF.verify(ROOT / GT.MANIFEST)
    if any(v.values()):
        raise SystemExit(f"cache differs from the manifest: {v}")
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    from hcmtf import data as HD
    extra = [str(HD.DATA_DIR / f"{s}_{k}.csv.gz") for s in UNIVERSE for k in ("funding", "perp1h")
             if f"{s}_{k}.csv.gz" in m["files"]]
    data_files = sorted({str(Path(p)) for s in UNIVERSE for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)} | set(extra))
    LG.verify_against_git(LG.LEDGER)
    results, eps = [], {}
    for tf in TFS:
        for prefix, hyp in TRIALS:
            tid = f"{prefix}-{tf}"
            LG.record(tid, hyp, ["exploration"], {"config": CONFIG, "tf": tf, "mode": mode,
                                                  "cells": [cell_key(h, s, d, tf) for h, s, d in cells() if h == hyp]},
                      CODE_FILES, ["rh_x", "near", "delta", "removal", "per_pair", "trading", "detection"], True, CONFIG,
                      data_files, notes=f"exploration; review mode {mode}")
            _commit_ledger(tid)
        btc, liq, first = prepare(tf)
        eps.update(episodes_for(btc, tf))
        with ProcessPoolExecutor(8) as ex:
            results += list(ex.map(worker, [(s, tf, btc, liq[s], first[s]) for s in UNIVERSE]))
        print(f"[{tf}] computed {len(UNIVERSE)} pairs", flush=True)
    ev = evaluate(results, eps)
    ev["meta"] = {"mode": mode, "config": CONFIG, "universe": list(UNIVERSE), "manifest_combined_sha256": m["combined_sha256"],
                  "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(_clean(ev), indent=1, default=str))
    print("hypotheses:", ev["decisions"]["hypotheses"], "| all-cell Holm:", ev["decisions"]["hypotheses_sensitivity"])


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return [_clean(v) for v in o.tolist()]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
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
    L = ["# V5 workstream M, stages A/B: BTC-regime context on crypto 1H/4H (results)", "",
         f"**EXPLORATORY ONLY. Review mode: `{meta['mode']}`.** Every candle read was examined in earlier studies.",
         "Nothing here is independent confirmation or evidence of a predictive edge.",
         f"Configuration `{meta['config']}` (frozen); run at commit `{meta['git_head'][:7]}`; manifest `{meta['manifest_combined_sha256'][:16]}…`.",
         "Survivorship: the 35 pairs were chosen with hindsight from coins that became large; coins liquid in 2020–2021 "
         "but not cached are absent. Eligibility rules E1–E4 remove hindsight only within the set.", "",
         "## Hypothesis verdicts", "",
         "| hypothesis | primary (Holm within hypothesis) | stricter sensitivity (Holm across all 36 cells) |", "|---|---|---|"]
    for h, v in D["hypotheses"].items():
        L.append(f"| {h} | **{v}** | {D['hypotheses_sensitivity'][h]} |")
    L += ["", "The primary column is the decision. The sensitivity column never replaces it."]
    if D["disagreements"]:
        L += ["", "**Where the two scopes disagree** (the primary decision does not survive the stricter all-cell correction):", ""]
        L += [f"* {json.dumps(x)}" for x in D["disagreements"]]
    else:
        L += ["", "The two correction scopes agree on every cell and hypothesis."]
    L += ["", "## Stage B cells", "",
          "Δ = mean(K) − mean(S∖K) (`rh_x` in ATR for M-B1–B3; `near` for M-B4). p = one-sided wild cluster restricted bootstrap; "
          "decisive p = larger of calendar-block and BTC-episode clustering. Removal = matched random removal (no BTC information).", "",
          "| cell | n K / S∖K | pairs | Δ [t-CI calendar] | eq-pair Δ | qual. pairs | median pair Δ | share > 0 | altcoin Δ | mean K vs removal p97.5 | G cal / ep | episodes gate / not | p cal / ep | Holm within | Holm all | verdict | verdict (all-cell Holm) |",
          "|---|---|---:|---|---:|---:|---:|---:|---:|---|---|---|---|---:|---:|---|---|"]
    for k, c in R["stage_b"].items():
        d = D["cells"][k]
        if not c.get("n_S"):
            L.append(f"| {k} | 0 | | | | | | | | | | | | | | {d['verdict']} | {d['verdict_all_cell_holm']} |")
            continue
        tc, te = c["test_calendar"], c["test_episode"]
        ci = "–" if tc.get("ci95") is None else f"{_f(c['delta'], 4, True)} [{_f(tc['ci95'][0], 4, True)}, {_f(tc['ci95'][1], 4, True)}]"
        rm = c.get("removal") or {}
        L.append(f"| {k} | {c['n_K']} / {c['n_SK']} | {c['pairs']} | {ci} | {_f(c['eq_weight_delta'], 4, True)} | {c['qualifying_pairs']} | "
                 f"{_f(c['median_pair_delta'], 4, True)} | {_f(c['positive_pair_share'], 2)} | {_f(c['altcoin_delta'], 4, True)} | "
                 f"{_f(c['mean_K'], 4, True)} vs {_f(rm.get('p97.5'), 4, True)} | {c['G_calendar']} / {c['G_episode']} | "
                 f"{c['episodes_gate']} / {c['episodes_complement']} | {_f(tc.get('p_wild'), 4)} / {_f(te.get('p_wild'), 4)} | "
                 f"{_f(d['p_holm_within'], 4)} | {_f(d['p_holm_all'], 4)} | **{d['verdict']}** | {d['verdict_all_cell_holm']} |")
    L += ["", "## BTC episodes (effective number of distinct market regimes)", "", "| TF · field | episodes | raw runs | by value (count, median/min/max length in candles) |", "|---|---:|---:|---|"]
    for k, e in R["episodes"].items():
        bv = "; ".join(f"{x['value']}: {x['count']} ({x['median']:.0f}/{x['min']}/{x['max']})" for x in e["by_value"])
        L.append(f"| {k} | {e['episodes']} | {e['raw_runs']} | {bv} |")
    L += ["", "## Stage A: price-only reference (non-BTC pairs; BTC separately)", "",
          "| signal · side · TF | n | pairs | mean [t-CI] (rh_x or near) | p wild | median | pair median of means | BTC n | BTC mean |", "|---|---:|---:|---|---:|---:|---:|---:|---:|"]
    for k, a in R["stage_a"].items():
        t, b = a["targets"], a["btc"]
        tt = t.get("test") or {}
        ci = "–" if not tt.get("ci95") else f"{_f(t['mean'], 4, True)} [{_f(tt['ci95'][0], 4, True)}, {_f(tt['ci95'][1], 4, True)}]"
        L.append(f"| {k} | {t['n']} | {t['pairs']} | {ci} | {_f(tt.get('p_wild'), 4)} | {_f(t.get('median'), 4, True)} | "
                 f"{_f(t.get('pair_median_of_means'), 4, True)} | {b['n']} | {_f(b.get('mean'), 4, True)} |")
    L += ["", "## R-cr detection (major tops for side −1, bottoms for +1): S, K, S∖K and matched-frequency baselines", "",
          "| side · TF | set | alerts | recall | precision* |", "|---|---|---:|---|---:|"]
    for k, det in R["detection"].items():
        for s in ("S", "K", "SK"):
            x = det[s]
            L.append(f"| {k} | {s} | {x['alerts']} | {_f(x['recall'][0])} | {_f(x['precision_excluding_duplicates'])} |")
        for b, m in det["baselines_matched_to_K"].items():
            L.append(f"| {k} | {b} matched to K | {m['target_alerts']} target, {m['shortfall_blocks']} shortfall blocks | "
                     f"{_f((m.get('recall') or [None])[0])} | {_f((m.get('precision_excl_dup') or [None])[0])} |")
    L += ["", "## Trading outcomes (separate from signal quality; never decisive)", "",
          "Net = fraction of notional after 20 bp round trip and short holding cost; slippage not modelled (sensitivity: +10 bp for pairs ranked > 10).", "",
          "| set | trades | net mean | net median | net mean +slippage | MAE p5/p50/p95 | cost sources |", "|---|---:|---:|---:|---:|---|---|"]
    for k, tr in R["trading"].items():
        sets = {"targets": tr.get("targets"), "S": tr.get("S"), "K": tr.get("K"), "S∖K": tr.get("SK")}
        for name, x in sets.items():
            if not x or not x.get("trades"):
                continue
            L.append(f"| {k} · {name} | {x['trades']} | {_f(x['net_mean'], 4, True)} | {_f(x['net_median'], 4, True)} | "
                     f"{_f(x['net_mean_slippage_sensitivity'], 4, True)} | {'/'.join(_f(v, 3) for v in x['trade_mae_p5_p50_p95'])} | {x['cost_sources']} |")
    L += ["", "## Exclusions (counted, never hidden)", "", "```", json.dumps({tf: {k: v for k, v in e.items() if k != 'candles'}
                                                                          for tf, e in R["exclusions"].items()}, indent=1), "```"]
    MD.write_text("\n".join(L) + "\n")
    P = ["# V5 workstream M, stage B: per-pair results (exploratory)", ""]
    for k, c in R["stage_b"].items():
        if not c.get("per_pair"):
            continue
        P += [f"## {k}", "", "| pair | tier | n K | n S∖K | mean K | mean S∖K | Δ | qualifying |", "|---|---|---:|---:|---:|---:|---:|---|"]
        for r in c["per_pair"]:
            P.append(f"| {r['sym']} | {r['tier']} | {r['n_k']} | {r['n_r']} | {_f(r['mean_k'], 4, True)} | {_f(r['mean_r'], 4, True)} | "
                     f"{_f(r['delta'], 4, True)} | {'yes' if r['qualifying'] else 'no'} |")
        P.append("")
    MD_PAIRS.write_text("\n".join(P) + "\n")
    print("wrote", MD, MD_PAIRS)


if __name__ == "__main__":
    {"run": run, "render": render}[sys.argv[1]]()
