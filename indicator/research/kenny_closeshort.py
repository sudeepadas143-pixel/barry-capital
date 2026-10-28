"""KCS: Close Short and BUY + Close Short confluence (reports/KCS_CONFIG.md).

Close Short (our own transparent rule; TBO's rules are not public): in a downtrend (EMA20 < EMA50),
the first close back above EMA20 after >= 5 consecutive closes below it. Closed candles <= s only.
Confluence: a Close Short within Q = L/4 candles after a shipped BUY arrow; the confluence event is
placed on the Close Short candle (knowable only then).
"""

from __future__ import annotations

import numpy as np

from hcmtf import ta


def close_short(df):
    c = df["close"].to_numpy(float)
    e20, e50 = ta.ema(c, 20), ta.ema(c, 50)
    n = len(c)
    with np.errstate(invalid="ignore"):
        below = c < e20
        down = e20 < e50
    run = np.zeros(n, int)
    for i in range(1, n):
        run[i] = run[i - 1] + 1 if below[i - 1] else 0                 # consecutive closes below EMA20 up to i-1
    with np.errstate(invalid="ignore"):
        sig = (~below) & (c > e20) & down & (run >= 5) & np.isfinite(e50)
    return np.flatnonzero(sig)


def confluence(buy, cs, Q):
    buy, cs = np.asarray(buy, int), np.asarray(cs, int)
    out = []
    for b in buy:
        k = cs[(cs >= b) & (cs <= b + Q)]
        if len(k):
            out.append(int(k[0]))
    return np.unique(np.array(out, int))


def invalidated(df, idx, Q):
    """1 if price makes a new low below the signal candle's low within Q candles."""
    l = df["low"].to_numpy(float)
    out = []
    for s in np.asarray(idx, int):
        out.append(np.nan if s + Q >= len(l) else float(l[s + 1:s + Q + 1].min() < l[s]))
    return np.array(out)
