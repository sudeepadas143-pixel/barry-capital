"""KCS Close Short: definition, causality, confluence placement. Synthetic data only."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kenny_closeshort as CS  # noqa: E402
from test_cycle_engine import daily  # noqa: E402


def test_close_short_fires_on_reclaim_in_downtrend_and_is_causal():
    c = np.r_[np.linspace(100, 60, 120), np.linspace(60, 66, 12)]
    df = pd.DataFrame({"open": c, "high": c + 0.5, "low": c - 0.5, "close": c}, index=pd.date_range("2020-01-01", periods=len(c), tz="UTC"))
    sig = CS.close_short(df)
    assert len(sig) >= 1 and sig[0] >= 120
    d = daily("2010-01-01", "2020-12-31", 4)
    full = CS.close_short(d)
    assert np.array_equal(CS.close_short(d.iloc[:2000]), full[full < 2000])


def test_confluence_is_placed_on_the_close_short_candle():
    assert list(CS.confluence([10, 50], [5, 13, 70], 6)) == [13]
