"""KF: balance arrow frequency against accuracy (reports/KF_CONFIG.md).

An arrow at candle s WORKS OUT when price is higher (BUY) / lower (SELL, breakdown) H = L/2 candles
later. Its EXCESS is that 0/1 outcome minus the instrument's own base rate over the same period
(share of all candles where price was higher / lower H candles later): beating a random entry.
Signal generation is causal; outcomes use future candles (evaluation only).
"""

from __future__ import annotations

import numpy as np

from . import cycle_features as CF, kenny_types as KT
from .kb_signals import cooldown

SCALES = (0.7, 0.8, 0.9, 1.0, 1.1)


def outcome(c, s, H, side):
    return np.where(s + H < len(c), (side * (c[np.minimum(s + H, len(c) - 1)] - c[s]) > 0).astype(float), np.nan)


def base_rate(c, H, side, mask):
    t = np.flatnonzero(mask)
    t = t[t + H < len(c)]
    return float(np.mean(side * (c[t + H] - c[t]) > 0)) if len(t) else np.nan


def options(df, st, tf, side):
    """Kenny states W (warning), S (standard), H (high), CONF (confirmed) x threshold scales."""
    d = "bot" if side > 0 else "top"
    L, D = CF.SCALE[tf]["L"], CF.SCALE[tf]["D"]
    c = CF.q_of(L)
    p, th = st[d]["p"], st[d]["theta"]
    F = st["F"]
    o, h, l, cl = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    out = {}
    for sc in SCALES:
        s_on = CF.zone_onsets(p, th["standard"] * sc, c)
        for name, tier in (("W", "warning"), ("S", "standard"), ("H", "high")):
            out[f"{name}|{sc}"] = cooldown(CF.zone_onsets(p, th[tier] * sc, c), c)
        _, conf = CF.developing_and_confirmed(s_on, side, o, h, l, cl, F["_rsi"].to_numpy(float), F["_hist"].to_numpy(float),
                                              F["_ema_f"].to_numpy(float), F["_atr"].to_numpy(float), L, D)
        out[f"CONF|{sc}"] = cooldown(conf, c)
    return out


def breakdown_options(df, tf):
    """Breakdown / exit variants: current; quicker re-arm (first close below in L/4); faster average
    (SMA_L instead of SMA_1.5L); both."""
    b = KT.base(df, tf)
    out = {"BRK": KT.breakdown(b)}
    L = b["L"]
    n = len(b["c"])
    from hcmtf import ta
    for name, ma, win in (("BRK_q", b["sma15"], L // 4), ("BRK_L", ta.sma(b["c"], L), L // 2), ("BRK_qL", ta.sma(b["c"], L), L // 4)):
        with np.errstate(invalid="ignore", divide="ignore"):
            below = b["c"] < ma
            prev = np.convolve(KT._lag(below.astype(float)), np.ones(win), "full")[:n]
            first = below & ~(np.nan_to_num(prev) > 0) & np.isfinite(ma)
            dd = np.nan_to_num((b["hh2"] - b["c"]) / b["atr"], nan=99)
            out[name] = np.flatnonzero(first & KT._mature(b) & (np.nan_to_num(b["hist"], nan=1) < 0) & (dd < 8.0))
    return out
