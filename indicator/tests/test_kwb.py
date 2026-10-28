"""KWB weekly BUY variants: causal, scale-free, V2 contains the shipped BUY. Synthetic data only."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kenny_wbuy as WB  # noqa: E402
from test_cycle_engine import daily, rs  # noqa: E402


def test_variants_causal_and_scale_free():
    w = rs(daily("1995-01-01", "2026-10-01", 13), "W-MON")
    full = WB.v1(w, 3.0)
    part = WB.v1(w.iloc[:900], 3.0)
    assert np.array_equal(part, full[full < 900])
    w2 = w.copy()
    w2[["open", "high", "low", "close"]] *= 250.0
    assert np.array_equal(WB.v1(w2, 3.0), full)
    assert set(WB.v2(w, 3.0, np.array([5, 7]))) >= {5, 7}
