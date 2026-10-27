"""Higher-timeframe context without look-ahead.

Pine reference, used by the indicator:

    request.security(syminfo.tickerid, tf, f()[1], lookahead = barmerge.lookahead_on)

On a chart bar that opens inside higher-timeframe period N this returns f() evaluated on
the COMPLETED period N - 1, on historical and realtime bars alike, so it never repaints.
``align`` reproduces it: find the HTF bar whose open time is at or before the chart bar's
open time, then take the value of the HTF bar before that one.

The two reference repos that use request.security get this wrong in different ways:
``expr`` with lookahead_off (no offset) repaints on realtime bars, and ``expr[1]`` with
lookahead_off is non-repainting but lags one extra HTF bar on history. Both are covered
in the README.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import ta

# Context timeframes for each chart timeframe: (near, anchor).
CONTEXT = {
    "1H": ("4H", "1D"),
    "4H": ("1D", "1W"),
    "1D": ("1W", "1M"),
    "1W": ("1M", "3M"),
}


def trend_state(df: pd.DataFrame, n: int = 21) -> np.ndarray:
    """+1 up, -1 down, 0 neutral: close vs EMA(n) and the EMA's own slope must agree."""
    c = df["close"].to_numpy()
    e = ta.ema(c, n)
    pe = ta.shift(e)
    up = (c > e) & (e > pe)
    dn = (c < e) & (e < pe)
    out = np.where(up, 1.0, np.where(dn, -1.0, 0.0))
    out[np.isnan(pe)] = np.nan
    return out


def align(chart_index: pd.DatetimeIndex, htf_index: pd.DatetimeIndex, values: np.ndarray) -> np.ndarray:
    """Value of the last COMPLETED higher-timeframe bar, for every chart bar."""
    prev = np.concatenate([[np.nan], np.asarray(values, float)[:-1]])  # f()[1]
    pos = htf_index.searchsorted(chart_index, side="right") - 1        # period containing bar
    out = np.full(len(chart_index), np.nan)
    ok = pos >= 0
    out[ok] = prev[pos[ok]]
    return out
