"""CY-2 (reports/CYCLE2_CONFIG.md): causal new features, barrier target, exported-tree parity with
sklearn, gate, synthetic walk-forward dry run. Synthetic data only."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import cycle2_features as C2, v5_gate as GT  # noqa: E402
from test_cycle_engine import daily, rs  # noqa: E402

spec = importlib.util.spec_from_file_location("cycle2_research", ROOT / "scripts" / "cycle2_research.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def test_new_features_are_causal_and_portable_quantities():
    df = daily("2016-01-01", "2020-12-31", 7)
    rv = np.random.default_rng(1).normal(size=len(df))
    full = C2.features(df, "1D", rv)
    for cut in (700, 1300):
        part = C2.features(df.iloc[:cut], "1D", rv[:cut])
        pd.testing.assert_frame_equal(part, full.iloc[:cut], check_dtype=False)
    assert set(full.columns) == set(C2.NEW)
    assert C2.features(df, "1D", None)["climax"].isna().all()            # no volume -> NaN, never 0
    td = C2.td_count(np.array([1, 2, 3, 4, 5, 6, 7, 8, 1, 9.0]), True)
    assert list(td[4:8] * 13) == [1, 2, 3, 4] and td[8] == 0


def test_barrier_target_stop_first_and_censoring():
    o = np.array([10, 10, 10, 10, 10, 10.0]); c = o.copy()
    h = np.array([10, 10, 13, 10, 10, 10.0]); l = np.array([10, 10, 7, 10, 10, 10.0])
    atr = np.ones(6)
    b = C2.barrier_target(o, h, l, c, atr, 1, 3, 2.0, 1.0)
    assert b[0] == 0.0 and b[1] == 0.0                                    # same-candle hit: stop counts
    assert np.isnan(b[-1]) and np.isnan(b[-3])                            # window past the data
    h2 = h.copy(); l2 = l.copy(); l2[2] = 9.5
    assert C2.barrier_target(o, h2, l2, c, atr, 1, 3, 2.0, 1.0)[0] == 1.0


def test_exported_trees_reproduce_sklearn_exactly():
    from sklearn.ensemble import HistGradientBoostingClassifier
    rng = np.random.default_rng(0)
    X = rng.normal(size=(4000, 6))
    X[rng.random(X.shape) < 0.1] = np.nan
    y = ((np.nan_to_num(X[:, 0]) + np.nan_to_num(X[:, 1]) * np.nan_to_num(X[:, 2]) + rng.normal(0, 0.5, 4000)) > 0.5).astype(int)
    m = HistGradientBoostingClassifier(random_state=1, **M.PRIMARY).fit(X, y)
    sp = M.export_gb(m)
    Xt = rng.normal(size=(300, 6))
    Xt[rng.random(Xt.shape) < 0.15] = np.nan
    assert np.allclose(M.gb_logodds(sp, Xt), m.decision_function(Xt), atol=1e-9)


def test_cy2_gate(tmp_path):
    import subprocess
    w = "External review: UNAVAILABLE\nSelf-audit: COMPLETED\nScope: EXPLORATION ONLY\nSelf-audit report: reports/V5_SELF_AUDIT.md\n"
    files = {GT.BASELINES: "x", GT.MANIFEST: '{"files": {}}', GT.WAIVER: w, GT.SELF_AUDIT: "s", GT.CY2_CONFIG: "Status: FROZEN\n",
             **{f: "x" for f in GT.CY2_CODE}}
    for cmd in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], cwd=tmp_path, check=True)
    for rel, t in files.items():
        p = tmp_path / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=tmp_path, check=True)
    assert GT.cy2_blockers(tmp_path, check_cache=False) == []
    (tmp_path / GT.CY2_CODE[-1]).write_text("changed")
    assert any(b.startswith("Y2") for b in GT.cy2_blockers(tmp_path, check_cache=False))


SYMS = ["SPY", "QQQ", "AAPL", "MSFT", "JPM", "XOM", "GLD", "TLT", "EURUSD=X"]


def test_walk_forward_dry_run(monkeypatch):
    frames = {}
    for k, s in enumerate(SYMS):
        d = daily(seed=30 + k)
        if s == "EURUSD=X":
            d["volume"] = 0.0
        frames[s] = {"1D": d, "1W": rs(d, "W-MON"), "1M": rs(d, "MS")}
    monkeypatch.setattr(M.DG, "load", lambda sym, tf: frames[sym][tf])
    monkeypatch.setattr(M.CR.DG, "load", lambda sym, tf: frames[sym][tf])
    monkeypatch.setattr(M, "YEARS", {**M.YEARS, "1D": [2016, 2018, 2020, 2022]})
    monkeypatch.setattr(M, "VARIANTS", {"d2": M.VARIANTS["d2"]})
    res = [M.build((s, "1D")) for s in SYMS]
    assert all(r is not None for r in res)
    al = M.walk_forward(res, "1D", "bot", "GBB")
    n = sum(len(v["standard"]) for v in al.values())
    assert n > 0
    # every out-of-time alert lies inside the walk-forward test span
    for r in res:
        for t in M.TIERS:
            a = al[r["sym"]][t]
            assert (r["idx"][a] >= pd.Timestamp("2016-01-01", tz="UTC")).all()
    ev = M.evaluate(res, "1D", "bot", {s: v["standard"] for s, v in al.items()}, reps=99)
    assert ev["det"] is not None and "trade" in ev
    cmp_ = M.compare(ev, M.evaluate(res, "1D", "bot", {s: v["standard"] for s, v in M.walk_forward(res, "1D", "bot", "B_ext").items()}, reps=99), reps=99)
    assert "near" in cmp_ and "net" in cmp_
    fm = M.final_models(res, "1D", {"top": {"vs_B_ext": {"GBZ": {"promoted": False}, "GBB": {"promoted": False}}},
                                    "bot": {"vs_B_ext": {"GBZ": {"promoted": False}, "GBB": {"promoted": True, "standard": {"net": {"delta": 0.1}}}}}})
    assert fm["top"]["model"] == "B_ext" and fm["bot"]["kind"] == "gb" and set(fm["bot"]["theta"]) == set(M.TIERS)
