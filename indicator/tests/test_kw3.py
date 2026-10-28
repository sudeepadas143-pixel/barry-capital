"""KW-3 weekly SELL recovery: causality of candidates, classification semantics, BUY untouched.
Synthetic data only."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kenny_sim as KSIM, kenny_weekly_sell as WS  # noqa: E402
from test_cycle_engine import daily, rs  # noqa: E402

SPEC = json.loads((ROOT / "reports" / "cycle2_model_spec.json").read_text())


def _w(seed=3):
    return rs(daily("1998-01-01", "2026-10-01", seed=seed), "W-MON")


def _all(df):
    f = WS.features(df)
    st = KSIM.states(df, "1W", SPEC)
    low = df["low"].to_numpy(float)
    return {"A": WS.cand_A(f, 10.0), "B": WS.cand_B(f, "sma40"), "C": WS.cand_C_signals(f, st["top"]["K_S"], 6.0, low),
            "SMA40x": WS.base_sma40_cross(f), "RSI70": WS.base_rsi70(f)}


def test_sell_candidates_are_causal_under_truncation():
    w = _w()
    full = _all(w)
    for cut in (800, 1200):
        part = _all(w.iloc[:cut])
        for k in full:
            assert np.array_equal(part[k], full[k][full[k] < cut]), k


def test_classification_semantics():
    n = 60
    c = np.full(n, 100.0); h = c + 0.5; l = c - 0.5; atr = np.ones(n)
    l2 = l.copy(); l2[10] = 96.0                                    # falls 3 ATR first, no new high -> useful
    assert WS.classify(h, l2, c, atr, 5, 0.0) == "useful"
    h2 = h.copy(); h2[8] = 104.0                                    # rises 3 ATR first -> premature
    assert WS.classify(h2, l2, c, atr, 5, 0.0) == "premature"
    h3 = h.copy(); h3[20] = 101.0                                   # falls, then regains the signal-week high -> false reversal
    assert WS.classify(h3, l2, c, atr, 5, 0.0) == "false_reversal"
    assert WS.classify(h, l2, c, atr, 5, 3.5) == "late"
    assert WS.classify(h, l, c, atr, 5, 0.0) == "flat"


def test_weekly_buy_and_other_timeframes_are_unchanged_by_sell_module():
    w = _w(8)
    b0, _, _ = KSIM.shipped_signals(w, "1W", SPEC)
    import research.kenny_weekly_sell  # noqa: F401  (import has no side effects on the shipped path)
    b1, _, _ = KSIM.shipped_signals(w, "1W", SPEC)
    assert np.array_equal(b0, b1)
