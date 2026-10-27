"""Regression tests for the V5 self-audit (reports/V5_SELF_AUDIT.md) and the gate's review modes."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research import v5_baselines as B, v5_eval as EV, v5_gate as GT  # noqa: E402


def test_SA1_no_baseline_alert_from_a_missing_data_candle():
    idx = pd.date_range("2024-01-01", periods=400, freq="1h", tz="UTC")
    c = 100 + np.cumsum(np.random.default_rng(0).normal(0, 1, 400))
    df = pd.DataFrame({"open": c, "high": c + 1, "low": c - 1, "close": c, "volume": 1.0}, index=idx)
    df.iloc[200, :4] = np.nan
    for side in (-1, 1):
        for f in (B.ema_cross, B.supertrend_flip):
            a = f(df, side)
            assert (a >= 0).all() and (a < len(df)).all() and 200 not in set(a)


def _path():
    seg = [(0, 30, 300), (30, 0, 300), (0, 30, 300), (30, 30, 400)]
    c = np.concatenate([np.linspace(a, b, n, endpoint=False) for a, b, n in seg] + [[30.0]])
    idx = pd.date_range("2021-01-04", periods=len(c), freq="4h", tz="UTC")
    return c + 0.2, c - 0.2, c, idx


def test_SA4_cached_labels_score_exactly_like_score_instrument():
    h, l, c, idx = _path()
    lab = EV.frozen_labels("SPY", h, l, c, "top", "4H", idx)
    rng = np.random.default_rng(1)
    for kind in ("warning", "confirmation"):
        al = rng.choice(len(c), 60, replace=False)
        a = EV.score_instrument("SPY", h, l, c, al, "top", kind, "4H", idx)
        b = EV.score_alerts(lab, al, kind)
        assert list(a["events"]) == list(b["events"]) and a["pairs"] == b["pairs"] and a["status"] == b["status"]
    # start_i censors earlier events and alerts whose range begins before it
    late = EV.score_alerts(lab, al, "warning", start_i=400)
    assert all(t >= 400 for t in late["events"]) and late["lo"] == 400
    assert all(s - late["K"] >= 400 for s in late["alerts"])
    with pytest.raises(Exception):
        EV.frozen_labels("JNJ", h, l, c, "top", "4H", idx)          # reserve symbol


def test_SA3_lift_units_use_only_warm_scorable_candles():
    h, l, c, idx = _path()
    lab = EV.frozen_labels("SPY", h, l, c, "top", "4H", idx)
    n = len(c)
    warm = np.ones(n, bool)
    warm[:500] = False
    state = np.where(np.arange(n) % 2 == 0, "bull", "neutral")
    sc = EV.score_alerts(lab, np.arange(n), "warning")
    u = EV.lift_units(lab, sc, "warning", state, warm)
    assert (u["i"] >= 500).all()                                    # no unit on a cold candle
    # alerts on every eligible candle: mean excess is exactly 0 within each state
    assert abs(u.groupby("state")["excess"].mean()).max() < 1e-12


def _repo(tmp: Path, files: dict):
    for cmd in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], cwd=tmp, check=True)
    for rel, text in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=tmp, check=True)


WAIVER_OK = ("External review: UNAVAILABLE\nSelf-audit: COMPLETED\nScope: EXPLORATION ONLY\n"
             "Self-audit report: reports/V5_SELF_AUDIT.md\n")


def test_gate_review_modes_and_confirmatory_refusal(tmp_path):
    base = {GT.BASELINES: "x", GT.CONFIG: "Status: FROZEN\n", GT.DETECTORS: "x",
            GT.MANIFEST: '{"files": {}}', "reports/V5_PROTOCOL_AMENDMENT_1.md": "CONFIRMATORY SCOPE: NOT ADOPTED\n"}
    # 1. no review, no waiver -> blocked
    r1 = tmp_path / "r1"; r1.mkdir()
    _repo(r1, base)
    assert GT.review_mode(r1) is None and any(b.startswith("B1") for b in GT.c_blockers(r1, check_cache=False))
    # 2. waiver without the self-audit report -> still blocked
    r2 = tmp_path / "r2"; r2.mkdir()
    _repo(r2, {**base, GT.WAIVER: WAIVER_OK})
    assert GT.review_mode(r2) is None
    # 3. waiver + self-audit -> exploration allowed, labelled; confirmatory refused
    r3 = tmp_path / "r3"; r3.mkdir()
    _repo(r3, {**base, GT.WAIVER: WAIVER_OK, GT.SELF_AUDIT: "self audit"})
    assert GT.review_mode(r3) == "self_audited_exploration_only"
    assert GT.c_blockers(r3, check_cache=False) == []
    cb = GT.confirmatory_blockers(r3)
    assert any(b.startswith("B1") for b in cb) and any(b.startswith("S1") for b in cb)
    # 4. a waiver that claims less than required is refused
    r4 = tmp_path / "r4"; r4.mkdir()
    _repo(r4, {**base, GT.WAIVER: WAIVER_OK.replace("EXPLORATION ONLY", "ALL"), GT.SELF_AUDIT: "s"})
    assert GT.review_mode(r4) is None
    # 5. an independent approval -> independent mode (confirmatory still needs the amendment)
    r5 = tmp_path / "r5"; r5.mkdir()
    _repo(r5, {**base, GT.REVIEW: "Decision: APPROVED\nReviewer is not the author: yes\nReviewed commit: abc\n"})
    assert GT.review_mode(r5) == "independent" and GT.confirmatory_blockers(r5) == [
        "S1: protocol Amendment 1 is not adopted for confirmatory scope"]
