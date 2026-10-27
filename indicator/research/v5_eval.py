"""V5 evaluation primitives shared by all four signal families (V5_VALIDATION_PROTOCOL.md §3, §5).

Nothing here evaluates a detector on market data by itself; it scores whatever signals it is
given. Three kinds of output are kept apart on purpose:

1. EXCESS statistics (continuation, and the lift of top/bottom detectors): mean excess of a
   signal outcome over a benchmark built from candles of the SAME instrument and the SAME
   causal stratum, with a calendar-block cluster bootstrap in which the benchmark means are
   re-estimated in every replicate (research.v41.boot_excess, reused unchanged).
2. DETECTION metrics (tops/bottoms): recall, precision, false alarms per unit time, lead time and
   the share of the move remaining, from a one-to-one matching of alerts to frozen labels.
3. TRADING metrics: per-signal trades with costs (research.v5_costs) and a per-instrument
   sequential portfolio. These never feed the detection metrics.

Dependence (never treat candles, symbols or correlated assets as independent):
* clusters are calendar blocks shared by ALL instruments of a cell (1H 1 month, 4H 2, 1D 3, 1W 12,
  research.v41.CLUSTER_MONTHS); a bootstrap replicate resamples whole blocks, so co-moving assets
  and overlapping outcome windows inside a block move together;
* overlap share and an effective (non-overlapping) count are reported for every signal set;
* residual overlap across block edges is not removed (disclosed).

Matching (continuation benchmarks) uses only CAUSAL columns: a candle table declares its causal
columns in df.attrs["causal"]; asking to match on anything else raises MatchingError, and names
that look like outcomes are refused even if declared causal.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .v41 import CLUSTER_MONTHS, boot_excess, cluster_id, weights
from .v5_costs import holding_cost, round_trip
from .v5_data import ReservedDataError
from .v5_labels import BOTTOM_PARAMS, TOP_PARAMS, major_bottoms, major_tops, remaining_fraction
from .v5_reserve import FREEZE

REPS = 5000
SEED = 20261027
MIN_UNITS, MIN_INSTRUMENTS, MIN_CLUSTERS, MIN_EVENTS = 100, 3, 8, 30
OUTCOME_NAME = re.compile(r"^(r_|r$|rs$|rl$|ret|fwd|mfe|mae|barrier|outcome|label|future|y$|target)", re.I)


class MatchingError(ValueError):
    pass


def check_partition(index: pd.DatetimeIndex, partition: str = "exploration") -> None:
    """Exploration only until a confirmatory loader exists (protocol G2): any candle after FREEZE,
    or any other partition name, raises."""
    if partition != "exploration":
        raise ReservedDataError(f"partition {partition!r} is not available before a G2 pre-registration")
    if len(index) and index.max() > FREEZE:
        raise ReservedDataError("candles after the freeze reached an exploratory evaluation")


# ----------------------------------------------------------------------------- candle tables

def candle_table(sym: str, index: pd.DatetimeIndex, tf: str, horizon: int, causal: dict, outcomes: dict) -> pd.DataFrame:
    """One row per candle of one instrument: identifiers, causal columns, outcome columns.

    causal: column -> array known at the candle's close (state labels, buckets ...)
    outcomes: column -> array of forward outcomes (used only as values, never for matching)
    t_end is the open time of candle i+horizon (the end of the outcome window).
    """
    check_partition(index)
    n = len(index)
    t = index.as_unit("ns").asi8
    t_end = np.full(n, np.iinfo(np.int64).max)
    if horizon < n:
        t_end[: n - horizon] = t[horizon:]
    df = pd.DataFrame({"sym": sym, "i": np.arange(n), "t": t, "t_end": t_end, "cl": cluster_id(index, tf)})
    for k, v in causal.items():
        if OUTCOME_NAME.match(k):
            raise MatchingError(f"{k!r} looks like an outcome and cannot be declared causal")
        df[k] = v
    for k, v in outcomes.items():
        df[k] = v
    df.attrs["causal"] = tuple(causal)
    df.attrs["outcomes"] = tuple(outcomes)
    return df


def _check_keys(df: pd.DataFrame, keys) -> None:
    causal = set(df.attrs.get("causal", ()))
    for k in keys:
        if OUTCOME_NAME.match(k) or k in df.attrs.get("outcomes", ()):
            raise MatchingError(f"matching on outcome column {k!r} is not allowed")
        if k not in causal:
            raise MatchingError(f"{k!r} is not a declared causal column")


def stratum(df: pd.DataFrame, keys) -> pd.Series:
    _check_keys(df, keys)
    if not keys:
        return pd.Series("all", index=df.index)
    return df[list(keys)].astype(str).agg("|".join, axis=1)


def bench_table(candles: pd.DataFrame, value: str, keys) -> pd.DataFrame:
    """Benchmark sums/counts per (instrument, stratum, cluster) over the given candles."""
    st = stratum(candles, keys)
    x = candles[value]
    ok = x.notna()
    b = pd.DataFrame({"sym": candles["sym"][ok], "st": st[ok], "cl": candles["cl"][ok], "x": x[ok].astype(float)})
    return b.groupby(["sym", "st", "cl"])["x"].agg(["sum", "count"]).reset_index()


def units_from(candles: pd.DataFrame, rows: pd.DataFrame, keys) -> pd.DataFrame:
    """Signal units = the candle-table rows at (sym, i) of the signals, with their stratum.
    Several signals on one candle count once (one candle = one signal)."""
    u = rows[["sym", "i"]].drop_duplicates().merge(candles, on=["sym", "i"], how="inner", validate="many_to_one")
    u.attrs.update(candles.attrs)
    u["_st"] = stratum(u, keys).to_numpy() if len(u) else []
    return u


# ----------------------------------------------------------------------------- dependence

def overlap(units: pd.DataFrame, horizon: int) -> dict:
    """Share of units whose outcome window overlaps the next unit of the same instrument, and the
    greedy count of non-overlapping units (an effective sample size)."""
    if len(units) == 0:
        return {"overlap_share": None, "effective_n": 0}
    ov = eff = 0
    for _, g in units.groupby("sym"):
        i = np.sort(g["i"].to_numpy())
        ov += int(np.sum(np.diff(i) <= horizon))
        last = -10**12
        for x in i:
            if x > last + horizon:
                eff += 1
                last = x
    return {"overlap_share": ov / len(units), "effective_n": int(eff)}


# ----------------------------------------------------------------------------- excess statistics

def _clusters(*tables) -> np.ndarray:
    return np.array(sorted(set().union(*[set(t["cl"].unique()) for t in tables if len(t)])))


def excess(units: pd.DataFrame, bench: pd.DataFrame, value: str, horizon: int, window: tuple[int, int],
           clusters: np.ndarray | None = None, W: np.ndarray | None = None, reps: int = REPS, seed: int = SEED) -> dict:
    """Mean excess of units over their (instrument, stratum) benchmark, with dependence-aware CI.

    units need columns sym, i, t, t_end, cl, _st and `value`; bench from bench_table().
    window = (start_ns, end_ns) of the evaluation period, for the purged chronological spans.
    """
    u = units[units[value].notna()].copy()
    n = len(u)
    out = {"n": int(n), "instruments": int(u["sym"].nunique()) if n else 0,
           "clusters": int(u["cl"].nunique()) if n else 0}
    out.update(overlap(u, horizon))
    if n == 0:
        out["evaluable"] = False
        return out
    if clusters is None:
        clusters = _clusters(u, bench)
    if W is None:
        W = weights(clusters, reps, seed)
    reps_, point, per_unit = boot_excess(u.rename(columns={"_st": "_stratum"}), bench, value, "_stratum", W, clusters)
    ok = ~np.isnan(per_unit)
    pu = per_unit[ok]
    lo, hi = np.nanpercentile(reps_, [2.5, 97.5])
    srt = np.sort(pu)
    k1 = max(int(round(0.01 * len(srt))), 1)
    # purged chronological thirds
    a, z = window
    edges = [a + (z - a) * j // 3 for j in range(4)]
    tt, te = u["t"].to_numpy()[ok], u["t_end"].to_numpy()[ok]
    spans = []
    for j in range(3):
        m = (tt >= edges[j]) & (tt < edges[j + 1]) & (te < edges[j + 1])
        spans.append({"n": int(m.sum()), "mean_excess": float(pu[m].mean()) if m.any() else None})
    # instrument dependence
    sy = u["sym"].to_numpy()[ok]
    per_sym = pd.Series(pu).groupby(sy).agg(["sum", "count"])
    loo = [float((pu[sy != s]).mean()) for s in per_sym.index if (sy != s).any()]
    tot = per_sym["sum"].abs().sum()
    out.update({
        "mean_value": float(u[value].mean()), "median_value": float(u[value].median()),
        "mean_excess": point, "lo": float(lo), "hi": float(hi),
        "p_one_sided": float((1 + np.sum(reps_ <= 0)) / (len(reps_) + 1)),
        "median_excess": float(np.median(pu)) if len(pu) else None,
        "mean_excess_ex_top1": float(srt[:-k1].mean()) if len(srt) > k1 else None,
        "units_without_benchmark": int((~ok).sum()),
        "spans": spans, "spans_positive": int(sum(1 for s in spans if s["mean_excess"] is not None and s["mean_excess"] > 0)),
        "leave_one_instrument_out": [min(loo), max(loo)] if loo else None,
        "largest_instrument": str(per_sym["sum"].abs().idxmax()),
        "largest_instrument_share": float(per_sym["sum"].abs().max() / tot) if tot > 0 else None,
        "evaluable": bool(n >= MIN_UNITS and out["instruments"] >= MIN_INSTRUMENTS and out["clusters"] >= MIN_CLUSTERS),
    })
    out["_reps"] = reps_
    return out


def continuation_report(candles: pd.DataFrame, signals: pd.DataFrame, momentum: pd.DataFrame, value: str,
                        state_col: str, state_value, matched_keys, horizon: int, window: tuple[int, int],
                        reps: int = REPS, seed: int = SEED) -> dict:
    """Families A/B: signals vs (S) all candles in the same state, (matched) candles in the same
    state AND the same causal strata, and the simple momentum set M, for ONE side.

    candles: candle_table rows of every instrument, already restricted to warm candles, with
    `value` the side-adjusted outcome (e.g. r_h for longs or shorts). signals / momentum: frames
    with sym, i. Signals outside the state are counted and excluded (they cannot be compared
    with S). The same replicate weights are used for every comparison, so differences are paired.
    """
    _check_keys(candles, [state_col, *matched_keys])
    in_state = candles[candles[state_col] == state_value]
    in_state.attrs.update(candles.attrs)
    clusters = _clusters(in_state)
    W = weights(clusters, reps, seed)
    keys_s, keys_m = [state_col], [state_col, *matched_keys]
    bS, bM = bench_table(in_state, value, keys_s), bench_table(in_state, value, keys_m)
    sig_s, sig_m = units_from(in_state, signals, keys_s), units_from(in_state, signals, keys_m)
    mom_s = units_from(in_state, momentum, keys_s)
    n_sig = len(signals[["sym", "i"]].drop_duplicates())
    rep = {"signals_total": int(n_sig), "signals_outside_state_or_not_warm": int(n_sig - len(sig_s)),
           "vs_state": excess(sig_s, bS, value, horizon, window, clusters, W),
           "vs_matched": excess(sig_m, bM, value, horizon, window, clusters, W),
           "momentum_vs_state": excess(mom_s, bS, value, horizon, window, clusters, W),
           "matched_keys": list(keys_m)}
    a, b = rep["vs_state"].get("_reps"), rep["momentum_vs_state"].get("_reps")
    if a is not None and b is not None:
        d = a - b
        lo, hi = np.nanpercentile(d, [2.5, 97.5])
        rep["signal_minus_momentum"] = {"mean": rep["vs_state"]["mean_excess"] - rep["momentum_vs_state"]["mean_excess"],
                                        "lo": float(lo), "hi": float(hi),
                                        "p_one_sided": float((1 + np.sum(d <= 0)) / (len(d) + 1))}
    for k in ("vs_state", "vs_matched", "momentum_vs_state"):
        rep[k].pop("_reps", None)
    return rep


# ----------------------------------------------------------------------------- tops and bottoms

def windows(kind: str, L: int) -> tuple[int, int]:
    """(K, W) from register §2.2: K = L candles after the extreme, W = L/2 candles before it.
    A warning at s may claim an event t in [s-K, s+W]; a confirmation only t in [s-K, s]."""
    if kind not in ("warning", "confirmation"):
        raise ValueError(kind)
    return L, L // 2


def eligible_range(s: int, kind: str, K: int, W: int) -> tuple[int, int]:
    return (s - K, s + W) if kind == "warning" else (s - K, s)


def match_alerts(alerts, events, kind: str, K: int, W: int) -> tuple[list[tuple[int, int]], dict]:
    """One-to-one matching of alerts to events; each event can be claimed by at most one alert.

    Greedy in time: each alert, in order, takes the EARLIEST unclaimed event in its eligible
    range. Both ends of the eligible range increase with s, so this yields a maximum-cardinality
    matching (the interval-scheduling exchange argument; checked against brute force in tests).
    Returns the (alert, event)
    pairs and a status per alert: "matched", "duplicate" (its range contains only events already
    claimed) or "false_alarm" (no event in range).
    """
    a = np.unique(np.asarray(alerts, int))
    e = np.unique(np.asarray(events, int))
    claimed = np.zeros(len(e), bool)
    pairs, status = [], {}
    for s in a:
        lo, hi = eligible_range(int(s), kind, K, W)
        j0, j1 = np.searchsorted(e, lo, "left"), np.searchsorted(e, hi, "right")
        free = np.flatnonzero(~claimed[j0:j1])
        if len(free):
            j = j0 + free[0]
            claimed[j] = True
            pairs.append((int(s), int(e[j])))
            status[int(s)] = "matched"
        else:
            status[int(s)] = "duplicate" if j1 > j0 else "false_alarm"
    return pairs, status


def score_instrument(h, l, c, atr, alerts, family: str, kind: str, tf: str, index: pd.DatetimeIndex) -> dict:
    """Detection metrics for one instrument against the frozen labels (register §2.2).

    Censoring: labels need L candles before and max(L, F) after; events outside
    [L, n-1-max(L,F)] are censored (excluded from recall). An alert is scorable only if its whole
    eligible range lies inside that region; others are censored (excluded from precision).
    Alerts are de-duplicated by candle index first (one candle = one alert).
    """
    check_partition(index)
    if family not in ("top", "bottom"):
        raise ValueError(family)
    p = (TOP_PARAMS if family == "top" else BOTTOM_PARAMS)[tf]
    L, F = p["L"], p["F"]
    K, W = windows(kind, L)
    n = len(c)
    ev = (major_tops if family == "top" else major_bottoms)(h, l, atr, **p)
    lo, hi = L, n - 1 - max(L, F)
    ev_ok = ev[(ev >= lo) & (ev <= hi)]
    al = np.unique(np.asarray(alerts, int))
    rng = np.array([eligible_range(int(s), kind, K, W) for s in al]).reshape(-1, 2)
    al_ok = al[(rng[:, 0] >= lo) & (rng[:, 1] <= hi)] if len(al) else al
    pairs, status = match_alerts(al_ok, ev_ok, kind, K, W)
    leads, remain = [], []
    for s, t in pairs:
        leads.append(t - s)
        if family == "top":
            final = l[t:t + F + 1].min()
            remain.append(remaining_fraction(h[t], c[s], final))
        else:
            final = h[t:t + F + 1].max()
            remain.append(remaining_fraction(l[t], c[s], final))
    span = max(hi - lo + 1, 0)
    return {"events": ev_ok, "events_censored": int(len(ev) - len(ev_ok)), "alerts": al_ok,
            "alerts_censored": int(len(al) - len(al_ok)), "pairs": pairs, "status": status,
            "leads": np.array(leads, float), "remaining": np.array(remain, float), "scorable_candles": int(span),
            "L": L, "F": F, "K": K, "W": W}


def near_event(n: int, events, kind: str, K: int, W: int) -> np.ndarray:
    """Per candle s: 1 if any event lies in s's eligible range, else 0 (no one-to-one; the
    frequency-independent hit rate used for lift)."""
    e = np.sort(np.asarray(events, int))
    s = np.arange(n)
    lo, hi = s - K, (s + W if kind == "warning" else s)
    return (np.searchsorted(e, hi, "right") > np.searchsorted(e, lo, "left")).astype(float)


def lift_report(items: dict, tf: str, kind: str, reps: int = REPS, seed: int = SEED) -> dict:
    """Lift of alerts over random alerts at matched frequency in the same causal state.

    items: sym -> {"index": DatetimeIndex, "score": score_instrument(...), "state": array of a
    causal stratum per candle}. Unit value = 1 if any (scorable) event lies in the alert's eligible
    range (frequency-independent, no one-to-one); benchmark = the same rate over every scorable
    candle of the same instrument and state. lift = mean(alert) / mean(benchmark); lift > 1 exactly
    when the excess > 0, so the excess CI is the lift test (protocol §6).
    """
    cands, rows = [], []
    for sym, it in items.items():
        r = it["score"]
        n = len(it["index"])
        near = near_event(n, r["events"], kind, r["K"], r["W"])
        lo, hi = r["L"], n - 1 - max(r["L"], r["F"])
        s = np.arange(n)
        a, b = s - r["K"], (s + r["W"] if kind == "warning" else s)
        scorable = (a >= lo) & (b <= hi)
        ct = candle_table(sym, it["index"], tf, r["W"], {"state": np.asarray(it["state"], object)},
                          {"near": np.where(scorable, near, np.nan)})
        cands.append(ct)
        rows.append(pd.DataFrame({"sym": sym, "i": np.asarray(r["alerts"], int)}))
    ct = pd.concat(cands, ignore_index=True)
    ct.attrs.update(cands[0].attrs)
    bench = bench_table(ct, "near", ["state"])
    units = units_from(ct, pd.concat(rows, ignore_index=True), ["state"])
    a, z = int(ct["t"].min()), int(ct["t"].max())
    res = excess(units, bench, "near", max(r["W"] for r in (it["score"] for it in items.values())), (a, z), reps=reps, seed=seed)
    res.pop("_reps", None)
    base = res.get("mean_value", np.nan) - res.get("mean_excess", np.nan) if res.get("n") else np.nan
    res["lift"] = float(res["mean_value"] / base) if res.get("n") and base and base > 0 else None
    res["benchmark_rate"] = None if not res.get("n") else float(base)
    return res


def _ratio_ci(num: np.ndarray, den: np.ndarray, cl: np.ndarray, reps: int, seed: int):
    if len(num) == 0 or den.sum() == 0:
        return None, None, None
    u, inv = np.unique(cl, return_inverse=True)
    sn = np.bincount(inv, weights=num, minlength=len(u))
    sd = np.bincount(inv, weights=den, minlength=len(u))
    W = weights(u, reps, seed)
    with np.errstate(invalid="ignore", divide="ignore"):
        b = (W @ sn) / (W @ sd)
    lo, hi = np.nanpercentile(b, [2.5, 97.5])
    return float(sn.sum() / sd.sum()), float(lo), float(hi)


def _median_ci(x: np.ndarray, cl: np.ndarray, reps: int, seed: int):
    if len(x) == 0:
        return None, None, None
    u, inv = np.unique(cl, return_inverse=True)
    groups = [x[inv == k] for k in range(len(u))]
    rng = np.random.default_rng(seed)
    meds = []
    for _ in range(reps):
        pick = rng.integers(0, len(u), len(u))
        meds.append(np.median(np.concatenate([groups[k] for k in pick])))
    lo, hi = np.percentile(meds, [2.5, 97.5])
    return float(np.median(x)), float(lo), float(hi)


def detection_report(per_instrument: dict, times: dict, tf: str, kind: str, reps: int = 2000, seed: int = SEED) -> dict:
    """Pool score_instrument() results across instruments (one family, one alert kind).

    per_instrument: sym -> score_instrument(...) result; times: sym -> DatetimeIndex of its candles.
    Uncertainty: calendar-block cluster bootstrap shared across instruments (events clustered by
    the event candle, alerts by the alert candle). Detection only: no returns here.
    """
    ev_hit, ev_cl, al_hit, al_cl, lead, lead_cl, rem, rem_cl = ([] for _ in range(8))
    dup = fa = alerts = events = cens_e = cens_a = 0
    years = 0.0
    for sym, r in per_instrument.items():
        idx = times[sym]
        cl = cluster_id(idx, tf)
        hit_events = {t for _, t in r["pairs"]}
        ev_hit += [1.0 if t in hit_events else 0.0 for t in r["events"]]
        ev_cl += [cl[t] for t in r["events"]]
        st = r["status"]
        al_hit += [1.0 if st[int(s)] == "matched" else 0.0 for s in r["alerts"]]
        al_cl += [cl[int(s)] for s in r["alerts"]]
        dup += sum(1 for v in st.values() if v == "duplicate")
        fa += sum(1 for v in st.values() if v == "false_alarm")
        alerts += len(r["alerts"])
        events += len(r["events"])
        cens_e += r["events_censored"]
        cens_a += r["alerts_censored"]
        for (s, t), x, y in zip(r["pairs"], r["leads"], r["remaining"]):
            lead.append(x); lead_cl.append(cl[s]); rem.append(y); rem_cl.append(cl[s])
        if r["scorable_candles"] > 0:
            lo = r["L"]
            hi = lo + r["scorable_candles"] - 1
            years += (idx[hi] - idx[lo]).total_seconds() / (365.25 * 86400)
    f = lambda v: np.asarray(v, float)
    recall = _ratio_ci(f(ev_hit), np.ones(len(ev_hit)), np.asarray(ev_cl), reps, seed)
    precision = _ratio_ci(f(al_hit), np.ones(len(al_hit)), np.asarray(al_cl), reps, seed)
    scor = sum(r["scorable_candles"] for r in per_instrument.values())
    lead_m = _median_ci(f(lead), np.asarray(lead_cl), reps, seed)
    rem_a = f(rem)
    return {
        "kind": kind, "instruments": len(per_instrument), "events": int(events), "alerts": int(alerts),
        "events_censored": int(cens_e), "alerts_censored": int(cens_a),
        "event_clusters": int(len(set(ev_cl))), "alert_clusters": int(len(set(al_cl))),
        "recall": recall, "precision": precision,
        "matched": int(sum(al_hit)), "duplicates": int(dup), "false_alarms": int(fa),
        "precision_excluding_duplicates": (sum(al_hit) / (sum(al_hit) + fa)) if (sum(al_hit) + fa) else None,
        "false_alarms_per_100_candles": 100 * fa / scor if scor else None,
        "false_alarms_per_instrument_year": fa / years if years else None,
        "alerts_per_instrument_year": alerts / years if years else None,
        "lead_median": lead_m, "lead_iqr": [float(np.percentile(lead, 25)), float(np.percentile(lead, 75))] if lead else None,
        "remaining_median": float(np.median(rem_a)) if len(rem_a) else None,
        "remaining_share_gt_half": float(np.mean(rem_a > 0.5)) if len(rem_a) else None,
        "evaluable": bool(events >= MIN_EVENTS and len(per_instrument) >= MIN_INSTRUMENTS and len(set(ev_cl)) >= MIN_CLUSTERS),
    }


# ----------------------------------------------------------------------------- trading metrics

def trade(o, h, l, c, index, i: int, side: int, hold: int, stop: float | None, asset_cls: str,
          funding: pd.DataFrame | None = None) -> dict | None:
    """One trade for a signal known at the close of candle i: entry at open[i+1]; stop (gap
    fills at the open, intrabar touch fills at the stop); otherwise exit at the close of candle
    i+hold. Returns gross and net returns as fractions of notional, with cost sources. None if
    the data end before the exit."""
    e = i + 1
    x_last = i + hold
    if x_last >= len(c) or e >= len(c):
        return None
    px = o[e]
    exit_px, x, reason = c[x_last], x_last, "time"
    for k in range(e, x_last + 1):
        if stop is not None:
            if (side > 0 and o[k] <= stop) or (side < 0 and o[k] >= stop):
                exit_px, x, reason = o[k], k, "stop_gap"
                break
            if (side > 0 and l[k] <= stop) or (side < 0 and h[k] >= stop):
                exit_px, x, reason = stop, k, "stop"
                break
    gross = side * (exit_px / px - 1.0)
    rt = round_trip(asset_cls)
    exit_time = index[x] if reason == "stop_gap" else (index[x + 1] if x + 1 < len(index) else index[x])
    hc, src = holding_cost(side, asset_cls, index[e], exit_time, funding)
    return {"entry_i": e, "exit_i": x, "side": side, "reason": reason, "gross": gross, "round_trip": rt,
            "holding_cost": hc, "holding_cost_source": src, "net": gross - rt - hc}


def sequential_daily(o, c, index, trades: list[dict]) -> pd.Series:
    """Daily log returns of one instrument trading its trades one at a time (overlapping signals
    are skipped), marked to market close-to-close, costs charged at entry (round trip /2) and exit
    (round trip /2 + holding cost)."""
    r = np.zeros(len(c))
    busy_until = -1
    for t in sorted(trades, key=lambda z: z["entry_i"]):
        e, x, d = t["entry_i"], t["exit_i"], t["side"]
        if e <= busy_until:
            continue
        exit_px = o[e] * (1 + d * t["gross"])          # inverts gross = d * (exit / entry - 1)
        if x == e:
            r[e] += d * (exit_px / o[e] - 1)
        else:
            r[e] += d * (c[e] / o[e] - 1)
            if x > e + 1:
                r[e + 1:x] += d * (c[e + 1:x] / c[e:x - 1] - 1)
            r[x] += d * (exit_px / c[x - 1] - 1)
        r[e] -= t["round_trip"] / 2
        r[x] -= t["round_trip"] / 2 + t["holding_cost"]
        busy_until = x
    s = pd.Series(np.log1p(np.maximum(r, -0.9999)), index=index)
    return s.groupby(s.index.normalize()).sum()
