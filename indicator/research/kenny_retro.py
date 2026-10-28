"""KR: 'right enough in retrospect' scoring and option set for Kenny's BUY/SELL (reports/KR_CONFIG.md).

A signal at candle s on a chart with cycle length L is RIGHT when
  * zone: its close sits in the lowest 25% (BUY) / highest 25% (SELL) of the high-low range of the
    candles s - L/2 .. s + L/2, and
  * follow-through: close[s + L/4] is above (BUY) / below (SELL) close[s].
Coverage: share of meaningful swing lows/highs (the extreme of its +-L/2 window, with that window's
range >= 4 ATR) that have a RIGHT signal of that side within +-L/4 candles.
The scoring uses FUTURE candles (evaluation only). Signal generation is causal (kenny_sim).
"""

from __future__ import annotations

import numpy as np

from hcmtf import ta

from . import cycle_features as CF
from .kb_signals import cooldown

ZONE = 0.25
SWING_ATR = 4.0


def score(df, tf, idx, side):
    """Per signal: (in_zone, follow, right); NaN where the windows run past the data."""
    L = CF.SCALE[tf]["L"]
    W, F = L // 2, L // 4
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    n = len(c)
    out = []
    for s in np.asarray(idx, int):
        if s - W < 0 or s + W >= n:
            out.append((np.nan, np.nan, np.nan))
            continue
        lo, hi = l[s - W:s + W + 1].min(), h[s - W:s + W + 1].max()
        if hi <= lo:
            out.append((np.nan, np.nan, np.nan))
            continue
        pos = (c[s] - lo) / (hi - lo)
        zone = pos <= ZONE if side > 0 else pos >= 1 - ZONE
        follow = c[s + F] > c[s] if side > 0 else c[s + F] < c[s]
        out.append((float(zone), float(follow), float(zone and follow)))
    return np.array(out).reshape(-1, 3)


def swings(df, tf, side):
    """Meaningful swing lows (side > 0) / highs (side < 0): extreme of its +-L/2 window with range >= 4 ATR."""
    L = CF.SCALE[tf]["L"]
    W = L // 2
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    atr = ta.atr(h, l, c, 14)
    n = len(c)
    out = []
    for k in range(W, n - W):
        a, b = k - W, k + W + 1
        if not np.isfinite(atr[k]) or h[a:b].max() - l[a:b].min() < SWING_ATR * atr[k]:
            continue
        if side > 0 and l[k] == l[a:b].min():
            out.append(k)
        if side < 0 and h[k] == h[a:b].max():
            out.append(k)
    return np.array(sorted(set(out)), int)


def options(df, st, tf, side):
    """Candidate signal sets for one side from Kenny's internal states (Early Warning W, High
    Conviction H, Confirmed CONF) with the shipped thresholds scaled by {0.9, 1.0, 1.1}. Same-side
    repeats within c candles are dropped, as shipped."""
    d = "bot" if side > 0 else "top"
    L, D = CF.SCALE[tf]["L"], CF.SCALE[tf]["D"]
    c = CF.q_of(L)
    p, th = st[d]["p"], st[d]["theta"]
    F = st["F"]
    o, h, l, cl = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    out = {}
    for sc in (0.9, 1.0, 1.1):
        w = CF.zone_onsets(p, th["warning"] * sc, c)
        s = CF.zone_onsets(p, th["standard"] * sc, c)
        hh = CF.zone_onsets(p, th["high"] * sc, c)
        _, conf = CF.developing_and_confirmed(s, side, o, h, l, cl, F["_rsi"].to_numpy(float), F["_hist"].to_numpy(float),
                                              F["_ema_f"].to_numpy(float), F["_atr"].to_numpy(float), L, D)
        out[f"W|{sc}"], out[f"H|{sc}"], out[f"CONF|{sc}"] = cooldown(w, c), cooldown(hh, c), cooldown(conf, c)
    return out
