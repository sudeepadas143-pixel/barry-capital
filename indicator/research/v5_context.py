"""V5 workstream M: crypto BTC-regime context, point-in-time eligibility and BTC episodes
(reports/V5_M_B_CONFIG.md, FROZEN; section numbers below refer to it).

Context and eligibility only: nothing here reads outcomes or labels (no import of v5_labels or
v5_eval), and nothing downloads data.

* btc_context (§2, E7): the BTC state row with the SAME open time as each target candle; both
  candles close at the same instant and the signal executes at the next open. A missing or
  unwarm BTC row is "unavailable", never a gate value.
* liquidity tables (§1.1 E2-E4): daily quote volume = sum over the UTC day's 1H candles of
  volume x close (a missing candle adds 0); medians over days D-29..D where D(t) = UTC date of
  t minus one day (the last day that ended at or before the candle's OPEN).
* eligibility (§1.1): E1-E7 flags, the first failing rule per candle in the order E5, E6, E1, E2,
  E3, E4, E7.
* episodes (§2): runs of a BTC field on warm BTC candles of the signal window; a run shorter than
  H candles is appended to the preceding episode (or prepended to the next if none precedes).
* gate (§5): the kept-set rule of each hypothesis; "unavailable" is never kept.
* matched_removal_means (§5, comparison 2): random subsets of S with K's count per stratum.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .v5_data import EVAL_SYMBOLS, EXPLORATION, check_symbol
from .v5_reserve import FREEZE

BTC = "BTCUSDT"
TARGETS = tuple(s for s in EVAL_SYMBOLS if EXPLORATION[s].cls == "crypto" and s != BTC)
MAJORS = ("ETHUSDT", "SOLUSDT")
PERP_PAIRS = ("ADAUSDT", "BNBUSDT", "DOGEUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "SOLUSDT", "TRXUSDT", "XRPUSDT")
UNAVAILABLE = "unavailable"

HISTORY_DAYS = 365          # E1
LIQ_DAYS = 30               # E2-E4 window
LIQ_MIN = 5_000_000.0       # E2 (USD)
RANK_MAX = 25               # E3
COMPLETE_MIN = 684          # E4: 95% of 720
RULE_ORDER = ("E5", "E6", "E1", "E2", "E3", "E4", "E7")


def tier(sym: str) -> str:
    return "majors" if sym in MAJORS else ("btc" if sym == BTC else "altcoins")


# ----------------------------------------------------------------------------- BTC context

def btc_context(target_index: pd.DatetimeIndex, btc_state: pd.DataFrame) -> pd.DataFrame:
    """BTC regime per target candle, aligned by identical open time (§2, E7).

    btc_state: v5_state.classify output for BTCUSDT on the same TF (indexed by open time).
    Returns columns available (bool), btc_dir (bull/bear/neutral/unavailable) and btc_unstable
    ("yes"/"no"/unavailable)."""
    s = btc_state.reindex(target_index)
    warm = s["warm"].fillna(False).to_numpy(bool) if "warm" in s else np.zeros(len(target_index), bool)
    dl = s["direction_label"].to_numpy(object)
    vr = s["vol_regime"].to_numpy(object)
    ok = warm & np.isin(dl, ["bull", "bear", "neutral"]) & np.isin(vr, ["low", "mid", "high"])
    btc_dir = np.where(ok, dl, UNAVAILABLE).astype(object)
    unstable = np.where(ok, np.where(vr == "high", "yes", "no"), UNAVAILABLE).astype(object)
    return pd.DataFrame({"available": ok, "btc_dir": btc_dir, "btc_unstable": unstable}, index=target_index)


GATES = {
    # hypothesis -> (field, rule(value, side) -> kept)
    "M-B1": ("btc_dir", lambda v, side: v == "bull"),
    "M-B2": ("btc_dir", lambda v, side: v == "bear"),
    "M-B3": ("btc_unstable", lambda v, side: v == "no"),
    "M-B4": ("btc_dir", lambda v, side: (v != "bull") if side < 0 else (v != "bear")),
}


def gate(hyp: str, values, side: int) -> np.ndarray:
    """Kept flag per unit (§5). An "unavailable" value is never kept; callers drop such units
    before comparing (E7), this is a second guard."""
    _, rule = GATES[hyp]
    v = np.asarray(values, object)
    return np.array([(x != UNAVAILABLE) and bool(rule(x, side)) for x in v], bool)


# ----------------------------------------------------------------------------- liquidity (E2-E4)

def daily_quote(h1: pd.DataFrame) -> pd.DataFrame:
    """Per full UTC day from the first FULL day of data (a day that starts at or after the first
    cached candle's open) to the day of the last candle: quote volume and candle count."""
    if len(h1) == 0:
        return pd.DataFrame(columns=["qv", "n"], dtype=float)
    first = h1.index[0]
    d0 = first.normalize() if first == first.normalize() else first.normalize() + pd.Timedelta(days=1)
    days = pd.date_range(d0, h1.index[-1].normalize(), freq="1D")
    qv = (h1["volume"].astype(float) * h1["close"].astype(float)).fillna(0.0)
    g = qv.groupby(h1.index.normalize())
    out = pd.DataFrame({"qv": g.sum(), "n": g.size().astype(float)}).reindex(days).fillna(0.0)
    out.index.name = "day"
    return out


def liquidity_panel(h1_frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Per symbol, per day D: med30 (median daily quote volume of D-29..D, NaN unless all 30
    days lie inside the full-day range), n30 (1H candles present in D-29..D), rank (E3, among
    the non-BTC TARGETS with a defined med30 on D; 1 = largest; ties by symbol name)."""
    per = {}
    for sym, h1 in h1_frames.items():
        dq = daily_quote(h1)
        med = dq["qv"].rolling(LIQ_DAYS, min_periods=LIQ_DAYS).median()
        n30 = dq["n"].rolling(LIQ_DAYS, min_periods=LIQ_DAYS).sum()
        per[sym] = pd.DataFrame({"med30": med, "n30": n30})
    rows = [p.assign(sym=s).reset_index() for s, p in per.items() if s in TARGETS]
    if rows:
        allp = pd.concat(rows, ignore_index=True)
        allp = allp[allp["med30"].notna()].sort_values(["day", "med30", "sym"], ascending=[True, False, True])
        allp["rank"] = allp.groupby("day").cumcount() + 1
        rk = allp.set_index(["sym", "day"])["rank"]
    else:
        rk = pd.Series(dtype=float)
    for s, p in per.items():
        p["rank"] = rk.loc[s].reindex(p.index).to_numpy(float) if s in rk.index.get_level_values(0) else np.nan
    return per


def reference_day(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """D(t) = UTC date of t minus one day: the last day ending at or before the open t."""
    return index.normalize() - pd.Timedelta(days=1)


# ----------------------------------------------------------------------------- eligibility

def eligibility(sym: str, index: pd.DatetimeIndex, first_h1_open: pd.Timestamp, liq: pd.DataFrame,
                warm, btc_available=None) -> pd.DataFrame:
    """E1-E7 per candle (§1.1) plus eligible and first_fail. E5 is enforced by v5_data.load (the
    frame ends before an integrity cut), so every loaded candle passes it. E3 and E7 are not
    applied to BTCUSDT (btc_available must then be None)."""
    check_symbol(sym)
    n = len(index)
    D = reference_day(index)
    look = liq.reindex(D)
    med, n30, rank = (look[k].to_numpy(float) for k in ("med30", "n30", "rank"))
    e = {
        "E5": np.ones(n, bool),
        "E6": np.asarray(warm, bool),
        "E1": np.asarray(first_h1_open <= index - pd.Timedelta(days=HISTORY_DAYS), bool),
        "E2": np.nan_to_num(med, nan=-1.0) >= LIQ_MIN,
        "E3": np.ones(n, bool) if sym == BTC else np.nan_to_num(rank, nan=1e9) <= RANK_MAX,
        "E4": np.nan_to_num(n30, nan=-1.0) >= COMPLETE_MIN,
        "E7": np.ones(n, bool) if sym == BTC else np.asarray(btc_available, bool),
    }
    if sym != BTC and btc_available is None:
        raise ValueError("btc_available is required for non-BTC targets (E7)")
    out = pd.DataFrame(e, index=index)
    out["eligible"] = np.logical_and.reduce([out[k].to_numpy() for k in RULE_ORDER])
    ff = np.full(n, "", dtype=object)
    for k in reversed(RULE_ORDER):                   # earliest rule in RULE_ORDER wins
        ff[~out[k].to_numpy()] = k
    out["first_fail"] = ff
    out["rank"] = rank
    return out


# ----------------------------------------------------------------------------- episodes (§2)

def episodes(times: pd.DatetimeIndex, values, H: int) -> tuple[pd.Series, pd.DataFrame]:
    """Episode id per BTC candle time (warm candles of the signal window, in time order) and a
    table of episodes (value = value of the opening run, length, start, end, raw runs merged)."""
    v = np.asarray(values, object)
    if len(v) == 0:
        return pd.Series(dtype=int), pd.DataFrame(columns=["value", "length", "start", "end", "runs"])
    brk = np.r_[True, v[1:] != v[:-1]]
    run_id = np.cumsum(brk) - 1
    starts = np.flatnonzero(brk)
    lengths = np.diff(np.r_[starts, len(v)])
    ep_of_run = np.empty(len(starts), int)
    eps: list[dict] = []
    pending: list[int] = []                           # leading short runs waiting for a next run
    for r, (s, L) in enumerate(zip(starts, lengths)):
        if L < H and eps:
            ep_of_run[r] = len(eps) - 1
            eps[-1]["length"] += int(L); eps[-1]["runs"] += 1
            continue
        if L < H and not eps:
            pending.append(r)
            continue
        eps.append({"value": v[s], "length": int(L), "runs": 1})
        ep_of_run[r] = len(eps) - 1
        for q in pending:
            ep_of_run[q] = len(eps) - 1
            eps[-1]["length"] += int(lengths[q]); eps[-1]["runs"] += 1
        pending = []
    if pending:                                       # every run was short: one episode
        eps.append({"value": v[starts[pending[0]]], "length": int(sum(lengths[q] for q in pending)), "runs": len(pending)})
        for q in pending:
            ep_of_run[q] = len(eps) - 1
    ep = ep_of_run[run_id]
    table = pd.DataFrame(eps)
    t = pd.Series(times)
    table["start"] = t.groupby(ep).min().to_numpy()
    table["end"] = t.groupby(ep).max().to_numpy()
    return pd.Series(ep, index=times), table


# ----------------------------------------------------------------------------- matched removal (§5)

def matched_removal_means(x, strata, kept, reps: int = 200, seed: int = 20261027) -> np.ndarray:
    """Means of `reps` random subsets R of the units, drawing within each stratum exactly as many
    units as `kept` has there, uniformly without replacement. Uses no timestamps and no BTC values
    (only the kept COUNT per stratum)."""
    x = np.asarray(x, float)
    k = np.asarray(kept, bool)
    st = pd.Series(np.asarray(strata, object)).astype(str).to_numpy()
    if len(x) != len(k) or len(x) != len(st):
        raise ValueError("x, strata and kept must have one entry per unit")
    rng = np.random.default_rng(seed)
    sums = np.zeros(reps)
    total = int(k.sum())
    if total == 0:
        return np.full(reps, np.nan)
    for s in sorted(set(st)):
        idx = np.flatnonzero(st == s)
        m = int(k[idx].sum())
        if m == 0:
            continue
        xs = x[idx]
        for r in range(reps):
            sums[r] += xs[rng.choice(len(idx), m, replace=False)].sum()
    return sums / total


# ----------------------------------------------------------------------------- perps (§6)

def perp_start(sym: str) -> pd.Timestamp | None:
    """Open time of the first cached perp 1H candle (pre-freeze), or None if no perp is cached.
    Reads timestamps only."""
    check_symbol(sym)
    from hcmtf import data
    p = Path(data.DATA_DIR) / f"{sym}_perp1h.csv.gz"
    if not p.exists():
        return None
    first = pd.read_csv(p, usecols=[0], nrows=1).iloc[0, 0]
    t = pd.Timestamp(first)
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    return t if t <= FREEZE else None
