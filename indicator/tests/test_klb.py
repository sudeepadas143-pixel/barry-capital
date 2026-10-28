"""KLB candidate BUYs: causality and basic placement. Synthetic data only."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kenny_ltfbuy as LB  # noqa: E402
from test_cycle_engine import daily  # noqa: E402


def _st(n, seed=0):
    rng = np.random.default_rng(seed)
    return {"bot": {"p": rng.normal(0, 3, n), "theta": {"warning": 2.0, "standard": 3.0, "high": 4.0}}}


def test_options_are_causal():
    d = daily("2010-01-01", "2020-12-31", 4)
    st = _st(len(d))
    full = LB.options(d, st, "4H")
    cut = 2000
    part = LB.options(d.iloc[:cut], {"bot": {"p": st["bot"]["p"][:cut], "theta": st["bot"]["theta"]}}, "4H")
    for k in full:
        assert np.array_equal(part[k], full[k][full[k] < cut]), k


def test_follow_up_counts_new_lows():
    d = daily("2010-01-01", "2012-12-31", 4)
    inv, dd = LB.follow_up(d, [100, len(d) - 2], 10)
    assert inv[0] in (0.0, 1.0) and dd[0] >= 0 and np.isnan(inv[1])
