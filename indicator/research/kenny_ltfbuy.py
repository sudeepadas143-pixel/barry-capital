"""KLB: better-placed BUY arrows on 4H and 1H (reports/KLB_CONFIG.md).

The user's complaint about 4H/1H BUYs: too early (price keeps falling), in the middle of nowhere,
and missing real lows. Candidate BUY definitions (closed candles <= signal candle only; p = Kenny's
bottom score, th = its thresholds, L = cycle length, Q = L/4, c = cooldown Q):

  H|s     current family: onset of p >= th_high * s
  LOC|s   H|s and the close is in the lowest 25% of the trailing L-candle high-low range
  TRIG|s  setup = onset of p >= th_warning * s; within the next Q candles, the first candle that
          closes above the highest high of the previous 3 candles, while the lowest low since the
          setup is the lowest low of the trailing L candles and the close is in the lowest 35% of
          the trailing L range (a turn up from a fresh low)
  PIV|s   a swing low k (lowest low of k-L/2..k) confirmed when the next k_p = max(3, Q // 8)
          candles all have higher lows; drawn on the confirmation candle k + k_p, which must close
          above close[k]; requires max p over k-k_p..k >= th_warning * s
"""

from __future__ import annotations

import numpy as np

from hcmtf import ta

from . import cycle_features as CF
from .cycle_features import highest, lowest
from .kb_signals import cooldown


def _pos(h, l, c, n):
    hh, ll = highest(h, n), lowest(l, n)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(hh > ll, (c - ll) / (hh - ll), np.nan), ll


def options(df, st, tf, scales=(0.8, 1.0)):
    L = CF.SCALE[tf]["L"]
    Q = CF.q_of(L)
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    n = len(c)
    p, th = st["bot"]["p"], st["bot"]["theta"]
    pos, llL = _pos(h, l, c, L)
    hh3 = np.r_[np.nan, highest(h, 3)[:-1]]                          # highest high of the previous 3 candles
    kp = max(3, Q // 8)
    out = {}
    for sc in sorted(set(scales) | {1.1}):
        out[f"H|{sc}"] = cooldown(CF.zone_onsets(p, th["high"] * sc, Q), Q)
    for sc in scales:
        on = CF.zone_onsets(p, th["high"] * sc, Q)
        out[f"LOC|{sc}"] = cooldown(on[np.nan_to_num(pos[on], nan=1.0) <= 0.25], Q)
        trig = []
        for s0 in CF.zone_onsets(p, th["warning"] * sc, Q):
            lo = l[s0]
            for i in range(s0 + 1, min(n, s0 + Q + 1)):
                lo = min(lo, l[i])
                if np.isfinite(hh3[i]) and c[i] > hh3[i] and lo <= llL[i] and np.nan_to_num(pos[i], nan=1.0) <= 0.35:
                    trig.append(i)
                    break
        out[f"TRIG|{sc}"] = cooldown(np.array(sorted(set(trig)), int), Q)
        piv = []
        llH = lowest(l, L // 2 + 1)
        pw = highest(np.nan_to_num(p, nan=-np.inf), kp + 1)
        for k in range(L // 2, n - kp):
            i = k + kp
            if l[k] == llH[k] and (l[k + 1:i + 1] > l[k]).all() and c[i] > c[k] and pw[k] >= th["warning"] * sc:
                piv.append(i)
        out[f"PIV|{sc}"] = cooldown(np.array(piv, int), Q)
    return out


def follow_up(df, idx, Q):
    """Per signal: invalidated (a low below the signal candle's low within Q) and further drop in ATR."""
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    atr = ta.atr(h, l, c, 14)
    inv, dd = [], []
    for s in np.asarray(idx, int):
        if s + Q >= len(c) or not np.isfinite(atr[s]):
            inv.append(np.nan), dd.append(np.nan)
            continue
        m = l[s + 1:s + Q + 1].min()
        inv.append(float(m < l[s]))
        dd.append(max(0.0, (c[s] - m) / atr[s]))
    return np.array(inv), np.array(dd)
