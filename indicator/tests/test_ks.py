"""KS strength components: bounded, causal under truncation. Synthetic data only."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kenny_sim as KSIM, kenny_strength as KST  # noqa: E402
from test_cycle_engine import daily, rs  # noqa: E402

SPEC = json.loads((ROOT / "reports" / "cycle2_model_spec.json").read_text())


def test_strength_is_bounded_and_causal():
    d = daily("2008-01-01", "2020-12-31", 4)
    w = rs(d, "W-MON")
    st = KSIM.states(d, "1D", SPEC)
    thr = st["bot"]["theta"]["high"]
    idx = np.arange(300, len(d), 37)
    full = KST.components(d, "1D", st, w, 1, idx, "score", thr)
    assert full["S"].min() >= 0 and full["S"].max() <= 5 and set(np.unique(full["E"])) <= {0, 1, 2, 3}
    cut = 2500
    pd_ = d.iloc[:cut]
    pst = KSIM.states(pd_, "1D", SPEC)
    k = idx[idx < cut]
    part = KST.components(pd_, "1D", pst, w[w.index <= pd_.index[-1]], 1, k, "score", thr)
    for key in ("M", "E", "H", "S"):
        assert np.array_equal(part[key], full[key][:len(k)]), key
