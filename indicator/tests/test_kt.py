"""KT signal types: causality under truncation and test semantics. Synthetic data only."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kenny_sim as KSIM, kenny_types as KT  # noqa: E402
from test_cycle_engine import daily  # noqa: E402

SPEC = json.loads((ROOT / "reports" / "cycle2_model_spec.json").read_text())


def _sets(df):
    b = KT.base(df, "1D")
    st = KSIM.states(df, "1D", SPEC)
    return {"CAU": KT.caution(b), "CONT": KT.continuation(b), "BRK": KT.breakdown(b), "EARLY": KT.early(st, "1D", 1.0)}


def test_types_are_causal_under_truncation():
    d = daily("2008-01-01", "2020-12-31", 6)
    full = _sets(d)
    assert all(len(v) for v in full.values())
    for cut in (2000, 3500):
        part = _sets(d.iloc[:cut])
        for k in full:
            assert np.array_equal(part[k], full[k][full[k] < cut]), k


def test_success_tests_semantics():
    n = 200
    c = np.full(n, 100.0)
    b = {"L": 63, "Q": 15, "h": c + 0.5, "l": c - 0.5, "c": c.copy(), "atr": np.ones(n)}
    assert KT.test("CAU", b, 100) == 0.0
    b["l"] = b["l"].copy(); b["l"][105] = 97.0
    assert KT.test("CAU", b, 100) == 1.0                                # 1.5 ATR pullback within Q
    assert np.isnan(KT.test("CAU", b, n - 5))
