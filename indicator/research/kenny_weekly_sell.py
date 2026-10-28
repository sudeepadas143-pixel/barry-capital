"""Weekly SELL recovery for Kenny's Divergence Indicator (reports/KW3_DIAG_CONFIG.md, KW3_CONFIG.md).

Weekly SELL only; weekly BUY and all other timeframes are untouched. Every value at candle i uses
closed weekly candles <= i. Outcome functions (classification, forward moves) use FUTURE candles and
are for evaluation only.

Units: price moves are measured in weekly ATR14 at the signal (asset-agnostic); MOVE = 3 ATR is a
"meaningful" move.
"""

from __future__ import annotations

import numpy as np

from hcmtf import ta

from .cycle_features import highest, lowest

MOVE = 3.0          # meaningful move, in ATR at the signal
H = 26              # classification horizon (weeks)


def _lag(x, k=1):
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


def tsmom(c, n=52):
    r = np.sign(c - _lag(c))
    s = np.full(len(c), np.nan)
    cs = np.cumsum(np.nan_to_num(r))
    s[n:] = (cs[n:] - cs[:-n]) / np.sqrt(n)
    return s


def bear_div(h, c, left=5, right=2, gmin=4, gmax=52):
    """1 on the confirming candle of a pivot high that is higher than the nearest previous pivot high
    (4..52 weeks back) while RSI14 is lower."""
    rsi = ta.rsi(c, 14)
    ph, _ = ta.pivots(h, h, left, right)
    conf = np.flatnonzero(np.isfinite(ph))
    piv = conf - right
    out = np.zeros(len(c))
    for j in range(len(piv)):
        p = piv[j]
        q = next((q for q in piv[:j][::-1] if gmin <= p - q <= gmax), None)
        if q is not None and h[p] > h[q] and np.isfinite(rsi[p]) and np.isfinite(rsi[q]) and rsi[p] < rsi[q]:
            out[conf[j]] = 1.0
    return out


def features(df):
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    atr = ta.atr(h, l, c, 14)
    rsi = ta.rsi(c, 14)
    _, _, hist = ta.macd(c, 12, 26, 9)
    sma40, ema26 = ta.sma(c, 40), ta.ema(c, 26)
    hh52_prev = _lag(highest(h, 52), 1)
    rg = h - l
    body = np.abs(c - o)
    with np.errstate(invalid="ignore", divide="ignore"):
        f = {
            "close": c, "atr": atr, "rsi": rsi, "hist": hist, "sma40": sma40, "ema26": ema26,
            "ext26": (c - ema26) / atr, "ext40": (c - sma40) / atr,
            "dd52": (highest(h, 52) - c) / atr, "rally52": (c - lowest(l, 52)) / atr,
            "tsm": tsmom(c), "roc13": (c - _lag(c, 13)) / atr, "roc13_acc": (c - _lag(c, 13)) / atr - _lag((c - _lag(c, 13)) / atr, 4),
            "rsi_max8": highest(rsi, 8), "vratio": np.log(ta.atr(h, l, c, 5) / ta.atr(h, l, c, 26)),
            "wick_up": np.where(rg > 0, (h - np.maximum(o, c)) / rg, 0.0),
            "star": (h - np.maximum(o, c) >= 2 * body) & ((h - np.maximum(o, c)) >= 0.5 * rg),
            "engulf": (c < o) & (_lag(c) > _lag(o)) & (o >= _lag(c)) & (c <= _lag(o)),
            "failed_high": (h > hh52_prev) & (c < hh52_prev),
            "slope40": (sma40 - _lag(sma40, 4)) / atr,
            "div": bear_div(h, c),
        }
    return f


# ----------------------------------------------------------------------------- candidates (KW3_CONFIG.md)

def _first_in_window(cond, arm, window):
    """Indices where cond holds within `window` candles after an arm event (first per arm)."""
    out = []
    arm_idx = np.flatnonzero(arm)
    cidx = np.flatnonzero(cond)
    for a in arm_idx:
        k = cidx[(cidx >= a) & (cidx <= a + window)]
        if len(k):
            out.append(int(k[0]))
    return np.unique(np.array(out, int))


def cand_A(f, R):
    """Exhaustion and reversal (major-top warning): an extended advance (rally from the 52-week low
    >= R ATR, TSMOM >= 0.5, RSI reached >= 65 in the last 8 weeks) gets a reversal candle (shooting
    star / bearish engulfing) or a failed new 52-week high while still within 2 ATR of that high and
    with RSI at least 5 points off its 8-week max (momentum no longer accelerating)."""
    with np.errstate(invalid="ignore"):
        ext = (np.nan_to_num(f["rally52"]) >= R) & (np.nan_to_num(f["tsm"]) >= 0.5) & (np.nan_to_num(f["rsi_max8"]) >= 65)
        weak = np.nan_to_num(f["rsi"], nan=99) <= np.nan_to_num(f["rsi_max8"]) - 5
        near = np.nan_to_num(f["dd52"], nan=99) <= 2.0
        rev = f["star"] | f["engulf"] | f["failed_high"]
        sig = ext & weak & near & rev
    return np.flatnonzero(sig)


def cand_B(f, dlim):
    """Trend breakdown (downside confirmation): a mature uptrend (TSMOM >= 0.5 and within 2 ATR of the
    52-week high at some point in the last 13 weeks) closes below SMA40 for the first time in 13
    weeks with the MACD histogram < 0, while the drawdown from the 52-week high is < dlim ATR."""
    n = len(f["atr"])
    with np.errstate(invalid="ignore"):
        mature_now = (np.nan_to_num(f["tsm"]) >= 0.5) & (np.nan_to_num(f["dd52"], nan=99) <= 2.0)
        mature = np.convolve(mature_now.astype(float), np.ones(13), "full")[:n] > 0
        below = f["close"] < f["sma40"]
        prev_below = np.convolve(_lag(below.astype(float)), np.ones(13), "full")[:n]
        first = below & ~(np.nan_to_num(prev_below) > 0)
        sig = first & mature & (np.nan_to_num(f["hist"]) < 0) & (np.nan_to_num(f["dd52"], nan=99) < dlim)
    return np.flatnonzero(sig)


def cand_C_signals(f, zone_onsets, dmax, low):
    """Two-stage: stage 1 (internal, not drawn) = an extended advance with RSI >= 65 in the last 8 weeks
    (as in A, without the reversal) or Kenny's weekly top zone (GBZ standard onset); stage 2 within
    13 weeks = close below the lowest low of the previous 4 weeks while the drawdown from the 52-week
    high is < dmax ATR (structure break, not late)."""
    with np.errstate(invalid="ignore"):
        arm = (np.nan_to_num(f["rally52"]) >= 6.0) & (np.nan_to_num(f["tsm"]) >= 0.5) & (np.nan_to_num(f["rsi_max8"]) >= 65)
        arm[np.asarray(zone_onsets, int)] = True
        ll4 = _lag(lowest(low, 4), 1)
        brk = (f["close"] < ll4) & (np.nan_to_num(f["dd52"], nan=99) < dmax)
    return _first_in_window(brk, arm, 13)


def base_sma40_cross(f):
    """Simple baseline: first weekly close below SMA40 after >= 13 weeks above."""
    n = len(f["atr"])
    with np.errstate(invalid="ignore"):
        close = f["close"]
        below = close < f["sma40"]
        prev = np.convolve(_lag(below.astype(float)), np.ones(13), "full")[:n]
    return np.flatnonzero(below & ~(np.nan_to_num(prev) > 0) & np.isfinite(f["sma40"]))


def base_rsi70(f):
    """Simple baseline: weekly RSI14 re-crosses 70 downward."""
    r = f["rsi"]
    with np.errstate(invalid="ignore"):
        return np.flatnonzero((r < 70) & (_lag(r) >= 70))


# ----------------------------------------------------------------------------- outcomes (evaluation only)

def classify(h, l, c, atr, s, prior_dd):
    """Premature / useful / late / false_reversal / flat for a SELL at candle s (uses future candles).
    late    : at the signal price is already >= MOVE ATR below its 26-week high (prior_dd)
    premature: price rises MOVE ATR above the signal close before falling MOVE ATR (within H)
    useful  : falls MOVE ATR first and does not regain the signal-week high within H
    false_reversal: falls MOVE ATR first but regains the signal-week high within H
    flat    : neither move within H."""
    n = len(c)
    a = atr[s]
    if not np.isfinite(a) or a <= 0 or s + 1 >= n:
        return "na"
    if prior_dd >= MOVE:
        return "late"
    up, dn = c[s] + MOVE * a, c[s] - MOVE * a
    end = min(n, s + H + 1)
    for k in range(s + 1, end):
        if h[k] >= up and l[k] <= dn:
            return "premature"
        if h[k] >= up:
            return "premature"
        if l[k] <= dn:
            return "false_reversal" if (h[k + 1:end] > h[s]).any() else "useful"
    return "flat" if end - s - 1 >= H else "na"


def decline_within(h, l, c, atr, s, horizon):
    """True if price falls MOVE ATR below the signal close within `horizon` weeks (any order)."""
    end = min(len(c), s + horizon + 1)
    if end - s - 1 < horizon or not np.isfinite(atr[s]):
        return np.nan
    return float((l[s + 1:end] <= c[s] - MOVE * atr[s]).any())
