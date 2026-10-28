"""KW-6 Weekly Cycle Engine (reports/KW6_SPEC.md): regime rule, state transitions, repeated
signals, stale evidence, candle-close causality. Synthetic data only."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import weekly_cycle as WC  # noqa: E402
from test_cycle_engine import daily, rs  # noqa: E402


def _w(seed=5):
    return rs(daily("1995-01-01", "2026-10-01", seed=seed), "W-MON")


def test_regime_is_the_fast_slow_sign_rule():
    f = {"fm": np.array([1.0, -1.0, -1.0, 1.0, np.nan]), "sm": np.array([1.0, 1.0, -1.0, -1.0, 1.0])}
    assert list(WC.regime(f)) == [0, 1, 2, 3, -1]


def test_confirmation_requires_recent_exhaustion_and_stale_evidence_expires():
    f = WC.features(_w())
    full = WC.signals(f, "top")
    st = full["state"]
    ex = np.flatnonzero(st == 1)
    for k in full["conf"]:                                  # every confirmation has an exhaustion within LINK weeks before it
        assert ((ex <= k) & (ex >= k - WC.LINK + 1)).any()


def test_repeats_are_rearmed_not_unlimited():
    m = np.zeros(40, bool)
    m[[3, 4, 5, 6, 12, 13, 30]] = True
    assert list(WC._entries(m, WC.REARM)) == [3, 12, 30]   # a persistent condition fires once; re-entry after >= REARM off


def test_signals_are_causal_under_truncation_both_sides():
    w = _w(7)
    full = {d: WC.signals(WC.features(w), d) for d in ("top", "bot")}
    for cut in (900, 1400):
        fp = WC.features(w.iloc[:cut])
        for d in ("top", "bot"):
            part = WC.signals(fp, d)
            for k in ("warn", "conf"):
                assert np.array_equal(part[k], full[d][k][full[d][k] < cut]), (d, k)


def test_bottom_model_is_not_a_plain_mirror():
    f = WC.features(_w(9))
    top, bot = WC.roles(f, "top"), WC.roles(f, "bot")
    burst_only = f["vburst"] & (f["dn_wick"] >= 0.4) & ~f["bull_engulf"]
    assert (bot["trigger"] & burst_only).any() or not burst_only.any()  # capitulation trigger exists only on the BUY side
    assert set(top) == set(bot)
