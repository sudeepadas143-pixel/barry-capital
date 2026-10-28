"""KX context: as-of alignment never uses later data; context flags are causal. Synthetic data only."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research import kenny_context as KX  # noqa: E402


def test_asof_uses_only_values_known_at_candle_close():
    s = pd.Series([1.0, 2.0, 3.0], index=pd.to_datetime(["2024-01-01 12:00", "2024-01-02 06:00", "2024-01-03 23:00"], utc=True))
    idx = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    out = KX._asof(s, idx, pd.Timedelta(days=1))
    assert list(out) == [1.0, 2.0, 3.0]                                 # each day sees prints up to its close (open + 1 day)
    out2 = KX._asof(s, idx, pd.Timedelta(hours=20))                     # a candle closing at 20:00 must not see the 23:00 print
    assert list(out2) == [1.0, 2.0, 2.0]


def test_bottom_context_flush_window_is_backward_looking():
    n = 40
    cx = {"f7": np.full(n, -0.001), "pf": np.full(n, 0.05), "oi14": np.zeros(n), "p14": np.zeros(n), "br": np.full(n, 0.1), "br20": np.full(n, 0.1)}
    cx["oi14"][20] = -0.2
    cx["p14"][20] = -0.2
    b = KX.bottom_context(cx)
    assert not b["flush14"][19] and b["flush14"][20] and b["flush14"][33] and not b["flush14"][34]
