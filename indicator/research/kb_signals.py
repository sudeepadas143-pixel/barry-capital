"""Benchmark signal families for Kenny's Divergence Indicator (reports/KB_CONFIG.md).

Rule-based reference families, re-implemented from their published descriptions (no code copied):
multi-oscillator regular divergence (DIV), hidden divergence (HID), price-action reversals (PA),
trend-continuation pullbacks (TREND) and the classic RSI 30/70 re-cross (RSIX). Parameters are the
references' defaults, fixed before any evaluation. Every signal index is the first closed candle
on which the signal is knowable (pivots are reported on their confirming candle), so nothing uses
future data. Returns per direction ("top" = SELL, "bot" = BUY) integer candle indices.
"""

from __future__ import annotations

import numpy as np

from hcmtf import ta

from .cycle_features import highest, lowest

PIV_L, PIV_R = 5, 5          # pivot left/right bars (RSI/MACD divergence references: 5)
GAP_MIN, GAP_MAX = 5, 60     # previous pivot searched 5..60 candles back, nearest first
DIV_MIN = 2                  # "Minimum Number of Divergence" (example value in reference 1)


def _lag(x, k=1):
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


def oscillators(o, h, l, c, v) -> dict[str, np.ndarray]:
    """Reference oscillators with default parameters. OBV only for feeds with volume."""
    rsi = ta.rsi(c, 14)
    mline, _, hist = ta.macd(c, 12, 26, 9)
    ll, hh = lowest(l, 14), highest(h, 14)
    with np.errstate(invalid="ignore", divide="ignore"):
        k = ta.sma(np.where(hh > ll, 100 * (c - ll) / (hh - ll), np.nan), 3)
        tp = (h + l + c) / 3
        sm = ta.sma(tp, 20)
        md = np.full(len(c), np.nan)
        if len(c) >= 20:
            w = np.lib.stride_tricks.sliding_window_view(tp, 20)       # ta.dev: mean |x - sma| over 20
            md[19:] = np.mean(np.abs(w - sm[19:, None]), axis=1)
        cci = (tp - sm) / (0.015 * md)
    out = {"rsi": rsi, "macd": mline, "hist": hist, "stoch": k, "cci": cci, "mom": c - _lag(c, 10)}
    if v is not None:
        out["obv"] = np.cumsum(np.nan_to_num(np.sign(c - _lag(c, 1)) * v))
    return out


def _pivot_idx(h, l):
    ph, pl = ta.pivots(h, l, PIV_L, PIV_R)
    return np.flatnonzero(np.isfinite(ph)), np.flatnonzero(np.isfinite(pl))


def divergences(o, h, l, c, v):
    """Count of oscillators with regular / hidden divergence at each confirmed pivot.
    Returns {"reg": {"top": cnt, "bot": cnt}, "hid": {...}} as per-candle arrays (0 elsewhere)."""
    n = len(c)
    osc = oscillators(o, h, l, c, v)
    hi_conf, lo_conf = _pivot_idx(h, l)
    out = {k: {"top": np.zeros(n, int), "bot": np.zeros(n, int)} for k in ("reg", "hid")}
    for d, conf, px in (("top", hi_conf, h), ("bot", lo_conf, l)):
        piv = conf - PIV_R                                   # pivot candle; known at conf
        for j, (p, at) in enumerate(zip(piv, conf)):
            prev = [q for q in piv[:j][::-1] if GAP_MIN <= p - q <= GAP_MAX]
            if not prev:
                continue
            q = prev[0]
            for x in osc.values():
                if not (np.isfinite(x[p]) and np.isfinite(x[q])):
                    continue
                if d == "top":
                    if px[p] > px[q] and x[p] < x[q]:
                        out["reg"][d][at] += 1
                    elif px[p] < px[q] and x[p] > x[q]:
                        out["hid"][d][at] += 1
                else:
                    if px[p] < px[q] and x[p] > x[q]:
                        out["reg"][d][at] += 1
                    elif px[p] > px[q] and x[p] < x[q]:
                        out["hid"][d][at] += 1
    return out


def price_action(o, h, l, c, L: int):
    """Failed breakout (swing-failure), engulfing and pin bar at the L-candle range extreme."""
    hh, ll = _lag(highest(h, L), 1), _lag(lowest(l, L), 1)
    rng = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        pos_prev = _lag((c - lowest(l, L)) / (highest(h, L) - lowest(l, L)), 1)
        wu = np.where(rng > 0, (h - np.maximum(o, c)) / rng, 0.0)
        wd = np.where(rng > 0, (np.minimum(o, c) - l) / rng, 0.0)
        o1, c1 = _lag(o), _lag(c)
        top = ((h > hh) & (c < hh)) \
            | ((c < o) & (c1 > o1) & (o >= c1) & (c <= o1) & (pos_prev >= 0.9)) \
            | ((wu >= 0.6) & (h >= hh))
        bot = ((l < ll) & (c > ll)) \
            | ((c > o) & (c1 < o1) & (o <= c1) & (c >= o1) & (pos_prev <= 0.1)) \
            | ((wd >= 0.6) & (l <= ll))
    return {"top": np.flatnonzero(top), "bot": np.flatnonzero(bot)}


def trend_pullback(c):
    """Trend continuation: EMA50 vs EMA200 trend, close on the trend side of EMA200, RSI re-crosses
    40 upward (BUY) / 60 downward (SELL)."""
    e50, e200, r = ta.ema(c, 50), ta.ema(c, 200), ta.rsi(c, 14)
    r1 = _lag(r)
    with np.errstate(invalid="ignore"):
        bot = (e50 > e200) & (c > e200) & (r > 40) & (r1 <= 40)
        top = (e50 < e200) & (c < e200) & (r < 60) & (r1 >= 60)
    return {"top": np.flatnonzero(top), "bot": np.flatnonzero(bot)}


def rsi_recross(c):
    """Classic baseline: RSI14 re-crosses 30 upward (BUY) / 70 downward (SELL)."""
    r = ta.rsi(c, 14)
    r1 = _lag(r)
    with np.errstate(invalid="ignore"):
        return {"top": np.flatnonzero((r < 70) & (r1 >= 70)), "bot": np.flatnonzero((r > 30) & (r1 <= 30))}


def cooldown(idx: np.ndarray, c: int) -> np.ndarray:
    """Drop a signal when the same family fired in the previous c candles (as zone onsets)."""
    keep, last = [], -10**9
    for i in np.sort(np.asarray(idx, int)):
        if i - last > c:
            keep.append(i)
        last = i
    return np.array(keep, int)


def families(o, h, l, c, v, L: int, cd: int) -> dict[str, dict[str, np.ndarray]]:
    dv = divergences(o, h, l, c, v)
    out = {"DIV1": {d: np.flatnonzero(dv["reg"][d] >= 1) for d in ("top", "bot")},
           "DIV2": {d: np.flatnonzero(dv["reg"][d] >= DIV_MIN) for d in ("top", "bot")},
           "HID": {d: np.flatnonzero(dv["hid"][d] >= DIV_MIN) for d in ("top", "bot")},
           "PA": price_action(o, h, l, c, L), "TREND": trend_pullback(c), "RSIX": rsi_recross(c)}
    return {k: {d: cooldown(a, cd) for d, a in v_.items()} for k, v_ in out.items()}


def after_zone(onsets: np.ndarray, sig: np.ndarray, m: int) -> np.ndarray:
    """First signal in (s, s+m] after each zone onset s (Kenny zone + reference trigger)."""
    sig = np.sort(np.asarray(sig, int))
    out = []
    for s in onsets:
        k = sig[(sig > s) & (sig <= s + m)]
        if len(k):
            out.append(int(k[0]))
    return np.unique(np.array(out, int))


def dedupe_final(buy: np.ndarray, sell: np.ndarray, c: int):
    """As shipped: drop candles where BUY and SELL fire together, then same-direction repeats
    within c candles."""
    both = np.intersect1d(buy, sell)
    return cooldown(np.setdiff1d(buy, both), c), cooldown(np.setdiff1d(sell, both), c)
