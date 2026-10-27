"""End-to-end smoke test of scripts/v5_c_explore.py on SYNTHETIC frames (the guarded loader is
patched to serve synthetic data). Checks the pipeline executes and reports every variant and
baseline; it computes nothing on real data."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf.data import _resample  # noqa: E402
from test_engine_v2 import minute_bars  # noqa: E402

spec = importlib.util.spec_from_file_location("v5_c_explore", ROOT / "scripts" / "v5_c_explore.py")
X = importlib.util.module_from_spec(spec)
spec.loader.exec_module(X)

SYMS = ["SPY", "QQQ", "IWM", "BTCUSDT", "ETHUSDT", "XRPUSDT"]


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    frames = {}
    for k, s in enumerate(SYMS):
        m = minute_bars(n15=60000, seed=100 + k, start="2020-06-01")
        r = lambda rule: _resample(m, rule, label="left", closed="left")
        d1 = r("1D")
        frames[s] = {"1H": r("1h"), "4H": r("4h"), "1D": d1, "1W": _resample(d1, "W-MON", label="left", closed="left")}
    return frames


def test_runner_pipeline_on_synthetic_data(monkeypatch, synthetic, tmp_path):
    monkeypatch.setattr(X.DG, "load", lambda sym, tf: synthetic[sym][tf])
    monkeypatch.setattr(X.DG, "load_funding", lambda sym: None)
    monkeypatch.setattr(X, "REPS_THIN", 5)
    results = [X.worker((s, tf)) for tf in X.TFS for s in SYMS]
    ev = X.evaluate(results)
    # every variant x kind x TF x group present, plus every unthinned baseline
    for tf in X.TFS:
        for d, kind in X.WARN_TRIALS + X.CONF_TRIALS:
            assert f"{tf}|pooled|{d}|{kind}" in ev["cells"]
            assert f"{tf}|equities|{d}|{kind}" in ev["cells"] and f"{tf}|crypto|{d}|{kind}" in ev["cells"]
        for b in X.B.BASELINES:
            assert f"{tf}|pooled|{b}" in ev["baselines_unthinned"]
    c = ev["cells"]["1H|pooled|C5b|confirmation"]
    assert set(c["matched_baselines"]) == set(X.B.BASELINES) and "trades" in c["trading"]
    assert len(ev["rejection"]) == len(X.WARN_TRIALS + X.CONF_TRIALS)
    ev["meta"] = {"mode": "synthetic-test", "config": X.CONFIG, "universe": SYMS, "manifest_combined_sha256": "0" * 64,
                  "git_head": "0" * 40, "instruments_per_group": {}}
    monkeypatch.setattr(X, "OUT", tmp_path / "r.json")
    monkeypatch.setattr(X, "MD", tmp_path / "r.md")
    (tmp_path / "r.json").write_text(json.dumps(X._clean(ev)))
    X.render()
    md = (tmp_path / "r.md").read_text()
    for d in X.DC.DETECTORS:
        assert f"| {d} |" in md
    for b in X.B.BASELINES:
        assert f"| {b} |" in md
    assert "EXPLORATORY ONLY" in md


def test_runner_refuses_when_the_gate_is_closed(monkeypatch):
    monkeypatch.setattr(X.GT, "c_blockers", lambda *a, **k: ["B1: test"])
    with pytest.raises(X.GT.NotReady):
        X.run()
