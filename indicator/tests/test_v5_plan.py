"""V5 planning safeguards (non-production): frozen V4.1 forward test, reserved data, label definitions."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.v5_labels import major_bottoms, major_tops, remaining_fraction  # noqa: E402
from research.v5_reserve import FREEZE, FROZEN_V41, V5_RESERVE, exploration_only  # noqa: E402


def test_frozen_v41_forward_test_files_are_unchanged():
    m = json.loads((ROOT / "reports" / "V4_1_DATA_MANIFEST.json").read_text())["config_hash"]
    for f in FROZEN_V41:
        assert hashlib.sha256((ROOT / f).read_bytes()).hexdigest() == m[f], f


def test_reserved_instruments_are_unused_and_not_cached():
    from hcmtf.universe import BY_SYMBOL
    import research.universe41  # noqa: F401  registers V4.1 holdout symbols
    reserve = [s for g in V5_RESERVE.values() for s in g]
    assert len(reserve) == len(set(reserve))
    assert not set(reserve) & set(BY_SYMBOL)
    data = ROOT / "data"
    if data.exists():
        cached = {p.name.rsplit("_", 1)[0] for p in data.glob("*.csv.gz")}
        assert not {s.replace("=", "_") for s in reserve} & cached
    # referenced only by the reserve module, this test and the V5 planning reports
    allowed = {"research/v5_reserve.py", "tests/test_v5_plan.py"}
    for s in reserve:
        out = subprocess.run(["git", "grep", "-I", "-l", "-w", s, "--", "."], cwd=ROOT, capture_output=True, text=True).stdout.split()
        assert set(out) <= allowed | {f for f in out if f.startswith("reports/V5_")}, (s, out)


def test_exploration_cache_has_no_forward_candles():
    data = ROOT / "data"
    files = sorted(data.glob("*.csv.gz")) if data.exists() else []
    if not files:
        pytest.skip("no cached data")
    for p in files:
        last = pd.to_datetime(pd.read_csv(p, usecols=[0]).iloc[-1, 0], utc=True, format="ISO8601")
        assert last <= FREEZE, f"{p.name} has candles after the freeze ({last}); forward data must live outside data/"


def test_exploration_guard_drops_forward_candles():
    idx = pd.date_range("2026-10-26", periods=72, freq="1h", tz="UTC")
    df = pd.DataFrame({"close": np.arange(72.0)}, index=idx)
    assert exploration_only(df).index.max() <= FREEZE
    assert len(exploration_only(df)) == 48


def test_labels_are_not_used_by_production_or_engine_code():
    for d in ("pine", "hcmtf"):
        for p in (ROOT / d).rglob("*"):
            if p.is_file() and p.suffix in (".py", ".pine"):
                assert "v5_labels" not in p.read_text(errors="ignore"), p


def _path(segments):
    """Piecewise-linear close path with high/low = close ± 0.2 and ATR = 1."""
    c = np.concatenate([np.linspace(a, b, n, endpoint=False) for a, b, n in segments] + [[segments[-1][1]]])
    return c + 0.2, c - 0.2, np.ones(len(c))


def test_major_top_and_bottom_labels():
    # rally 0 → 20 over 60 candles, decline to 0 over 60, recovery to 15 over 40
    h, l, a = _path([(0, 20, 60), (20, 0, 60), (0, 15, 40)])
    assert list(major_tops(h, l, a, L=30, F=40, D=8.0)) == [60]
    assert list(major_bottoms(h, l, a, L=30, F=40, D=8.0)) == [120]
    # too small a decline: no top
    h2, l2, a2 = _path([(0, 20, 60), (20, 15, 60)])
    assert len(major_tops(h2, l2, a2, L=30, F=40, D=8.0)) == 0
    # a higher high (outside the radius, inside the forward window) before the decline target voids the top
    h3, l3, a3 = _path([(0, 20, 60), (20, 18.5, 10), (18.5, 30, 30), (30, 10, 60)])
    t3 = major_tops(h3, l3, a3, L=8, F=60, D=3.0)
    assert 60 not in t3 and 100 in t3
    # the same shape with the dip deep enough first keeps the top
    h4, l4, a4 = _path([(0, 20, 60), (20, 16, 10), (16, 30, 30), (30, 10, 60)])
    assert 60 in major_tops(h4, l4, a4, L=8, F=60, D=3.0)


def test_remaining_fraction():
    assert remaining_fraction(100, 100, 80) == 1.0
    assert remaining_fraction(100, 90, 80) == 0.5
    assert remaining_fraction(100, 75, 80) == -0.25
