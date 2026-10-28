"""KR retrospective scoring: zone/follow-through semantics, swing detection, option set. Synthetic only."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kenny_retro as KR, kenny_sim as KSIM  # noqa: E402
from test_cycle_engine import daily  # noqa: E402


def _v(prices):
    c = np.asarray(prices, float)
    idx = pd.date_range("2020-01-06", periods=len(c), freq="W-MON", tz="UTC")
    return pd.DataFrame({"open": c, "high": c + 0.1, "low": c - 0.1, "close": c, "volume": 1.0}, index=idx)


def test_right_needs_zone_and_follow_through():
    v = np.r_[np.linspace(100, 60, 30), np.linspace(60, 100, 30)]   # V bottom at candle 29 (L = 26 on 1W)
    df = _v(v)
    sc = KR.score(df, "1W", [29, 27, 45], 1)
    assert tuple(sc[0]) == (1.0, 1.0, 1.0)                          # at the low, then higher
    assert sc[1][0] == 1.0 and sc[1][2] == 1.0                      # near the low still counts
    assert sc[2][0] == 0.0 and sc[2][2] == 0.0                      # mid-rally is not in the bottom zone
    assert tuple(KR.score(df, "1W", [29], -1)[0])[2] == 0.0         # a SELL at a bottom is wrong
    assert np.isnan(KR.score(df, "1W", [2], 1)[0][2])               # window before the data -> not scored


def test_swings_and_options():
    v = np.r_[np.linspace(100, 60, 30), np.linspace(60, 100, 30)]
    assert 29 in KR.swings(_v(v), "1W", 1)
    spec = json.loads((ROOT / "reports" / "cycle2_model_spec.json").read_text())
    d = daily("2010-01-01", "2020-12-31", 3)
    st = KSIM.states(d, "1D", spec)
    opts = KR.options(d, st, "1D", 1)
    assert set(opts) == {f"{k}|{s}" for k in ("W", "H", "CONF") for s in (0.9, 1.0, 1.1)}
    b0, _, _ = KSIM.shipped_signals(d, "1D", spec)
    assert np.array_equal(opts["H|1.0"], b0) or len(np.setdiff1d(b0, opts["H|1.0"])) == 0   # current BUY reproduced
