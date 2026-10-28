"""KF outcome/base-rate semantics and option causality. Synthetic data only."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kenny_freq as KF, kenny_sim as KSIM  # noqa: E402
from test_cycle_engine import daily  # noqa: E402


def test_outcome_and_base_rate():
    c = np.array([1, 2, 3, 2, 1, 2.0])
    assert list(KF.outcome(c, np.array([0, 2]), 2, 1)) == [1.0, 0.0]
    assert list(KF.outcome(c, np.array([2]), 2, -1)) == [1.0]
    assert np.isnan(KF.outcome(c, np.array([5]), 2, 1)[0])
    assert KF.base_rate(c, 2, 1, np.ones(6, bool)) == 0.5


def test_options_are_causal():
    spec = json.loads((ROOT / "reports" / "cycle2_model_spec.json").read_text())
    d = daily("2008-01-01", "2020-12-31", 2)
    full = {**KF.options(d, KSIM.states(d, "1D", spec), "1D", -1), **KF.breakdown_options(d, "1D")}
    cut = 2400
    p = d.iloc[:cut]
    part = {**KF.options(p, KSIM.states(p, "1D", spec), "1D", -1), **KF.breakdown_options(p, "1D")}
    for k in full:
        assert np.array_equal(part[k], full[k][full[k] < cut]), k
