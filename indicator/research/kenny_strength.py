"""KS: signal strength ("weight") for Kenny's arrows (reports/KS_CONFIG.md).

Strength of an arrow at candle s = M + E + H (0..5), all from closed candles <= s:
  M  margin   : the setup is >= 10% beyond its threshold (score models); weekly SELL (Candidate A):
                rally from the 52-week low >= 9 ATR (1.5x A's minimum).
  E  evidence : number of independent witnesses (0..3), one per role, same side:
                RSI/MACD-histogram regular divergence confirmed in the last 8 candles,
                price-action reversal in the last 3 candles, volatility/volume burst with a
                reversal-side wick in the last 3 candles (research/kenny_cluster.py definitions).
  H  HTF      : the completed higher-timeframe trend agrees (up for BUY, down for SELL).
"""

from __future__ import annotations

import numpy as np

from . import cycle_features as CF, kenny_cluster as KC


def _recent(x, n):
    x = np.asarray(x, float)
    return np.convolve(np.nan_to_num(x), np.ones(n), "full")[:len(x)] > 0


def components(df, tf, st, htf, side, idx, kind, thr=None, wsf=None):
    """Per arrow: dict of M, E, H and strength. kind = 'score' (uses p vs thr) or 'A' (weekly SELL)."""
    d = "bot" if side > 0 else "top"
    L = CF.SCALE[tf]["L"]
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    dv = KC.divergence(h, l, c)[d] > 0
    pa = KC.price_action(o, h, l, c, L)[d] > 0
    vb = KC.vol_burst(o, h, l, c, st["F"]["relvol"].to_numpy(float), L)[d] > 0
    ev = _recent(dv, 8).astype(int) + _recent(pa, 3).astype(int) + _recent(vb, 3).astype(int)
    trend = KC.htf_trend(df, htf)
    idx = np.asarray(idx, int)
    if kind == "A":
        with np.errstate(invalid="ignore"):
            M = np.nan_to_num(wsf["rally52"]) >= 9.0
    else:
        p = st[d]["p"]
        with np.errstate(invalid="ignore"):
            M = np.nan_to_num(p, nan=-np.inf) >= 1.1 * thr
    H = (trend > 0) if side > 0 else (trend < 0)
    m, e, hh = M[idx].astype(int), ev[idx], H[idx].astype(int)
    return {"M": m, "E": e, "H": hh, "S": m + e + hh}
