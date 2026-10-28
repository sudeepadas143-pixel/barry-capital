"""KT: four additional signal types for Kenny's Divergence Indicator (reports/KT_CONFIG.md).

Each type has one job, a causal definition (closed candles <= s), its own success test (future
candles, evaluation only) and a plain baseline population the test is compared against.
L = the chart's cycle length (26 1W, 63 1D, 126 4H, 168 1H); Q = L/4.

  CAU  caution / take profit  : exhaustion near the high of an advance (KW-3 Candidate A
                                generalised from weekly to L: rally from the 2L low >= 6 ATR,
                                sign-momentum over 2L >= 0.5, RSI reached >= 65 in the last
                                max(8, Q) candles and is >= 5 off that max, within 2 ATR of the 2L
                                high, plus a shooting star / bearish engulfing / failed new 2L high)
     test: a pullback of >= 1.5 ATR below the signal close within Q candles
     baseline: every candle within 2 ATR of the 2L high
  CONT trend-continuation BUY  : EMA50 > EMA200, close > EMA200, RSI14 re-crosses 40 upward
     test: close[s+Q] > close[s] and no low below the pullback low (lowest low of the last Q
           candles) within Q candles
     baseline: every candle with EMA50 > EMA200 and close > EMA200
  BRK  breakdown / exit        : a mature uptrend (within 2 ATR of the 2L high in the last L/2
                                candles) closes below SMA(1.5L) for the first time in L/2 candles,
                                MACD histogram < 0, drawdown from the 2L high < 8 ATR
     test: close[s+Q] < close[s] and no close above the signal candle's high within Q candles
     baseline: every candle closing below SMA(1.5L) after being within 2 ATR of the 2L high in the
               last L/2 candles
  EARLY bottom forming (early) : onset of Kenny's bottom score at its warning threshold x scale
                                (scale in {0.9, 1.0, 1.1}, tuned)
     test: the lowest low of s-L/2..s+L/2 occurs in s-Q..s+Q (the swing low is near) and that
           window's range is >= 2 ATR
     baseline: every candle closing >= 1 ATR below EMA_L
"""

from __future__ import annotations

import numpy as np

from hcmtf import ta

from . import cycle_features as CF
from .cycle_features import highest, lowest


def _lag(x, k=1):
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


def _recent(mask, n):
    m = np.asarray(mask, float)
    return np.convolve(np.nan_to_num(m), np.ones(n), "full")[:len(m)] > 0


def base(df, tf):
    L = CF.SCALE[tf]["L"]
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    atr = ta.atr(h, l, c, 14)
    rsi = ta.rsi(c, 14)
    _, _, hist = ta.macd(c, 12, 26, 9)
    n2 = 2 * L
    sgn = np.sign(c - _lag(c))
    cs = np.cumsum(np.nan_to_num(sgn))
    tsm = np.full(len(c), np.nan)
    tsm[n2:] = (cs[n2:] - cs[:-n2]) / np.sqrt(n2)
    with np.errstate(invalid="ignore", divide="ignore"):
        return {"L": L, "Q": max(2, L // 4), "o": o, "h": h, "l": l, "c": c, "atr": atr, "rsi": rsi, "hist": hist, "tsm": tsm,
                "hh2": highest(h, n2), "ll2": lowest(l, n2), "hh2p": _lag(highest(h, n2), 1),
                "ema50": ta.ema(c, 50), "ema200": ta.ema(c, 200), "emaL": ta.ema(c, L), "sma15": ta.sma(c, int(round(1.5 * L)))}


def caution(b):
    L, Q = b["L"], b["Q"]
    o, h, l, c, atr, rsi = b["o"], b["h"], b["l"], b["c"], b["atr"], b["rsi"]
    nr = max(8, Q)
    rg = h - l
    body = np.abs(c - o)
    up = h - np.maximum(o, c)
    with np.errstate(invalid="ignore", divide="ignore"):
        rmax = highest(rsi, nr)
        ext = (np.nan_to_num((c - b["ll2"]) / atr) >= 6.0) & (np.nan_to_num(b["tsm"]) >= 0.5) & (np.nan_to_num(rmax) >= 65)
        weak = np.nan_to_num(rsi, nan=99) <= np.nan_to_num(rmax) - 5
        near = np.nan_to_num((b["hh2"] - c) / atr, nan=99) <= 2.0
        rev = ((up >= 2 * body) & (up >= 0.5 * rg)) | ((c < o) & (_lag(c) > _lag(o)) & (o >= _lag(c)) & (c <= _lag(o))) \
            | ((h > b["hh2p"]) & (c < b["hh2p"]))
    return np.flatnonzero(ext & weak & near & rev)


def continuation(b):
    r, r1 = b["rsi"], _lag(b["rsi"])
    with np.errstate(invalid="ignore"):
        return np.flatnonzero((b["ema50"] > b["ema200"]) & (b["c"] > b["ema200"]) & (r > 40) & (r1 <= 40))


def _mature(b):
    with np.errstate(invalid="ignore", divide="ignore"):
        near = np.nan_to_num((b["hh2"] - b["c"]) / b["atr"], nan=99) <= 2.0
    return _recent(near, b["L"] // 2)


def breakdown(b):
    L = b["L"]
    n = len(b["c"])
    with np.errstate(invalid="ignore", divide="ignore"):
        below = b["c"] < b["sma15"]
        prev = np.convolve(_lag(below.astype(float)), np.ones(L // 2), "full")[:n]
        first = below & ~(np.nan_to_num(prev) > 0) & np.isfinite(b["sma15"])
        dd = np.nan_to_num((b["hh2"] - b["c"]) / b["atr"], nan=99)
        sig = first & _mature(b) & (np.nan_to_num(b["hist"], nan=1) < 0) & (dd < 8.0)
    return np.flatnonzero(sig)


def early(st, tf, scale):
    from .kb_signals import cooldown
    L = CF.SCALE[tf]["L"]
    c = CF.q_of(L)
    return cooldown(CF.zone_onsets(st["bot"]["p"], st["bot"]["theta"]["warning"] * scale, c), c)


# ----------------------------------------------------------------------------- tests and baselines (future candles)

def test(kind, b, s):
    L, Q = b["L"], b["Q"]
    h, l, c, atr = b["h"], b["l"], b["c"], b["atr"]
    n = len(c)
    if s + Q >= n or s - L // 2 < 0 or not np.isfinite(atr[s]):
        return np.nan
    if kind == "CAU":
        return float(l[s + 1:s + Q + 1].min() <= c[s] - 1.5 * atr[s])
    if kind == "CONT":
        return float(c[s + Q] > c[s] and l[s + 1:s + Q + 1].min() > l[s - Q + 1:s + 1].min())
    if kind == "BRK":
        return float(c[s + Q] < c[s] and not (c[s + 1:s + Q + 1] > h[s]).any())
    if kind == "EARLY":
        W = L // 2
        if s + W >= n:
            return np.nan
        a, z = s - W, s + W + 1
        k = a + int(np.argmin(l[a:z]))
        return float(abs(k - s) <= Q and h[a:z].max() - l[a:z].min() >= 2 * atr[s])
    raise ValueError(kind)


def baseline_mask(kind, b):
    with np.errstate(invalid="ignore", divide="ignore"):
        if kind == "CAU":
            return np.nan_to_num((b["hh2"] - b["c"]) / b["atr"], nan=99) <= 2.0
        if kind == "CONT":
            return (b["ema50"] > b["ema200"]) & (b["c"] > b["ema200"])
        if kind == "BRK":
            return (b["c"] < b["sma15"]) & _mature(b)
        if kind == "EARLY":
            return b["c"] <= b["emaL"] - b["atr"]
    raise ValueError(kind)
