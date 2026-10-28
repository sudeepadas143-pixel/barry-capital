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
