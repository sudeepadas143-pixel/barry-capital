"""V5 target events: objective, ex-post labels for major tops and major bottoms.

These labels USE FUTURE DATA by construction. They exist only to score detectors (lead time,
recall, false alarms, move remaining after confirmation). A detector must never import this
module; tests/test_v5_plan.py checks that pine/ and hcmtf/ do not reference it.

Definitions (reports/V5_HYPOTHESIS_REGISTER.md §2, frozen before any label was counted):

MAJOR TOP at candle t on a timeframe with radius L, forward window F and size D (in ATR14[t]):
  (a) high[t] is the highest high of candles t-L .. t+L (first occurrence wins ties);
  (b) prior advance: high[t] - min(low[t-L .. t]) >= D * ATR14[t];
  (c) subsequent decline: within t+1 .. t+F, price falls to high[t] - D * ATR14[t] BEFORE any
      high exceeds high[t].
MAJOR BOTTOM: defined separately with its own parameter table, same structure on lows.

Parameters were fixed a priori (one week / three weeks / three months / six months of radius;
forward window 2L; D set to several typical candle ranges). Tops and bottoms currently use the
same numbers; that is a registered starting choice, not an assumption that the two behave alike,
and either table may be changed only by a logged amendment before confirmatory data is used.
"""

from __future__ import annotations

import numpy as np

TOP_PARAMS = {"1H": {"L": 168, "F": 336, "D": 8.0}, "4H": {"L": 126, "F": 252, "D": 8.0},
              "1D": {"L": 63, "F": 126, "D": 8.0}, "1W": {"L": 26, "F": 52, "D": 5.0}}
BOTTOM_PARAMS = {"1H": {"L": 168, "F": 336, "D": 8.0}, "4H": {"L": 126, "F": 252, "D": 8.0},
                 "1D": {"L": 63, "F": 126, "D": 8.0}, "1W": {"L": 26, "F": 52, "D": 5.0}}


def major_tops(h, l, atr, L: int, F: int, D: float) -> np.ndarray:
    """Indices of major tops (see module docstring). Uses future data."""
    h, l, atr = (np.asarray(x, float) for x in (h, l, atr))
    n = len(h)
    out = []
    for t in range(L, n - 1):
        a = atr[t]
        if not np.isfinite(a) or a <= 0:
            continue
        win = h[t - L:min(n, t + L + 1)]
        if h[t] < win.max() or int(np.argmax(win)) != L:   # highest, first occurrence
            continue
        if h[t] - l[t - L:t + 1].min() < D * a:
            continue
        target = h[t] - D * a
        for k in range(t + 1, min(n, t + F + 1)):
            if h[k] > h[t]:
                break
            if l[k] <= target:
                out.append(t)
                break
    return np.array(out, int)


def major_bottoms(h, l, atr, L: int, F: int, D: float) -> np.ndarray:
    """Indices of major bottoms (separate definition, same structure on lows). Uses future data."""
    h, l, atr = (np.asarray(x, float) for x in (h, l, atr))
    n = len(l)
    out = []
    for t in range(L, n - 1):
        a = atr[t]
        if not np.isfinite(a) or a <= 0:
            continue
        win = l[t - L:min(n, t + L + 1)]
        if l[t] > win.min() or int(np.argmin(win)) != L:
            continue
        if h[t - L:t + 1].max() - l[t] < D * a:
            continue
        target = l[t] + D * a
        for k in range(t + 1, min(n, t + F + 1)):
            if l[k] < l[t]:
                break
            if h[k] >= target:
                out.append(t)
                break
    return np.array(out, int)


def remaining_fraction(extreme: float, at_signal: float, final: float) -> float:
    """Share of the move from a labelled extreme to its subsequent final extreme still ahead at the
    signal price: 1 = signalled at the extreme, 0 = at the end, < 0 = after the move finished."""
    total = extreme - final
    return np.nan if total == 0 else (at_signal - final) / total
