"""KWB: weekly BUY that catches cycle bottoms on high-volatility assets (reports/KWB_CONFIG.md).

Problem: the shipped weekly BUY measures extension (close - EMA26) in ATR14 units. In a crash ATR14
balloons, so extension in ATR14 units stays small and the BUY never fires (BTC: none). Variant
families measure extension against SLOW volatility that does not inflate during the crash:
  V1(k): (close - EMA26) / ATR52  <= -k        onsets, same cooldown as shipped
  V2(k): shipped BUY  OR  V1(k)
All causal (closed weekly candles <= i).
"""

from __future__ import annotations

import numpy as np

from hcmtf import ta

from . import cycle_features as CF
from .kb_signals import cooldown

KS = (2.5, 3.0, 3.5)


def slow_ext(df):
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    with np.errstate(invalid="ignore", divide="ignore"):
        return (c - ta.ema(c, 26)) / ta.atr(h, l, c, 52)


def v1(df, k):
    c = CF.q_of(26)
    return cooldown(CF.zone_onsets(-slow_ext(df), k, c), c)


def v2(df, k, shipped):
    return np.union1d(np.asarray(shipped, int), v1(df, k))


# ----------------------------------------------------------------------------- KWB-2 (reports/KWB2_CONFIG.md)

KS2 = (1.0, 1.25, 1.5)


def dd_sigma(df, n=104):
    """Drawdown from the n-week high in units of the asset's own annual volatility:
    -log(close / highest(high, n)) / (stdev of weekly log returns over n weeks * sqrt(52))."""
    h, c = df["high"].to_numpy(float), df["close"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.log(c / np.r_[np.nan, c[:-1]])
        import pandas as pd
        sd = pd.Series(r).rolling(n, min_periods=n).std(ddof=0).to_numpy()
        return -np.log(c / CF.highest(h, n)) / (sd * np.sqrt(52))


def d1(df, k):
    c = CF.q_of(26)
    return cooldown(CF.zone_onsets(dd_sigma(df), k, c), c)


def d2(df, k, shipped):
    return np.union1d(np.asarray(shipped, int), d1(df, k))
