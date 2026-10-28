"""Signal-integrity tests: no repainting, no look-ahead, correct HTF alignment.

They run on synthetic data so they need no network and no cache.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf import evaluate as E, signals as S, ta  # noqa: E402
from hcmtf.data import _resample, to_4h, to_weekly  # noqa: E402
from hcmtf.htf import align, trend_state  # noqa: E402
from hcmtf.universe import Asset  # noqa: E402


def bars(n=1500, seed=1, freq="1h", start="2022-01-03", vol=True):
    rng = np.random.default_rng(seed)
    # regime-switching drift so there are real trends and reversals
    drift = np.repeat(rng.normal(0, 0.002, n // 100 + 1), 100)[:n]
    r = drift + rng.normal(0, 0.01, n)
    c = 100 * np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.002, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.004, n)))
    lo = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.004, n)))
    v = rng.lognormal(10, 0.5, n) if vol else np.zeros(n)
    idx = pd.date_range(start, periods=n, freq=freq, tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c, "volume": v}, index=idx)


def contexts(df):
    near = _resample(df, "4h", label="left", closed="left")
    anchor = _resample(df, "1D", label="left", closed="left")
    return near, anchor


def run_upto(df, k, p):
    """Signals as they would have been printed with data only up to bar k."""
    cut = df.iloc[: k + 1]
    # Higher-timeframe bars built from the truncated data: the last one is still forming
    # and holds partial values, exactly as it would in real time. The aligner must not use it.
    near = _resample(cut, "4h", label="left", closed="left")
    anchor = _resample(cut, "1D", label="left", closed="left")
    return S.run(cut, near, anchor, p, True)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_signals_never_change_after_they_print(seed):
    """Truncation test: the signal set up to bar k is identical whether the engine saw
    data up to k or the whole series. Any look-ahead or repainting would break this."""
    df = bars(seed=seed)
    p = S.DEFAULTS["1H"]
    near, anchor = contexts(df)
    _, trig_full, sig_full, warn_full = S.run(df, near, anchor, p, True)
    assert len(sig_full) > 5, "fixture should produce signals"
    for k in [400, 650, 901, 1200, 1499]:
        _, trig_k, sig_k, warn_k = run_upto(df, k, p)
        a = sig_full[sig_full["i"] <= k].reset_index(drop=True)
        b = sig_k.reset_index(drop=True)
        cols = ["i", "dir", "kind", "tier", "score", "available"] + S.COMPONENTS
        pd.testing.assert_frame_equal(a[cols], b[cols], check_dtype=False)
        wa = warn_full[warn_full["i"] <= k].reset_index(drop=True)
        pd.testing.assert_frame_equal(wa, warn_k.reset_index(drop=True), check_dtype=False)


def test_htf_alignment_uses_only_completed_bars():
    idx = pd.date_range("2024-01-01", periods=48, freq="1h", tz="UTC")
    htf_idx = pd.date_range("2024-01-01", periods=12, freq="4h", tz="UTC")
    vals = np.arange(12, dtype=float)  # value k belongs to the 4H bar opening at 4k hours
    out = align(idx, htf_idx, vals)
    for j, t in enumerate(idx):
        period = j // 4
        expected = np.nan if period == 0 else period - 1
        if np.isnan(expected):
            assert np.isnan(out[j])
        else:
            assert out[j] == expected, (t, out[j], expected)


def test_htf_trend_state_is_causal():
    df = bars(600, freq="1D")
    full = trend_state(df)
    for k in (100, 333, 599):
        part = trend_state(df.iloc[: k + 1])
        np.testing.assert_array_equal(full[: k + 1], part)


def test_pivots_are_reported_on_the_confirming_bar():
    h = np.array([1, 2, 3, 9, 3, 2, 1, 1, 1, 1], float)
    l = h - 0.5
    ph, _ = ta.pivots(h, l, 2, 2)
    assert np.isnan(ph[:5]).all() and ph[5] == 9  # peak at 3, known at 3 + 2


def test_ema_rma_match_pine_definition():
    x = np.arange(1, 31, dtype=float)
    e = ta.ema(x, 5)
    assert np.isnan(e[:4]).all() and e[4] == pytest.approx(3.0)
    a = 2 / 6
    assert e[5] == pytest.approx(a * 6 + (1 - a) * 3.0)
    r = ta.rma(x, 5)
    assert r[5] == pytest.approx(0.2 * 6 + 0.8 * 3.0)


def test_rsi_bounds_and_known_value():
    x = np.r_[np.arange(1, 20), np.arange(19, 0, -1)].astype(float)
    r = ta.rsi(x, 14)
    assert np.nanmin(r) >= 0 and np.nanmax(r) <= 100
    assert r[14] == pytest.approx(100.0)  # 14 straight gains


def test_cooldown_and_one_trigger_per_level():
    df = bars(seed=5)
    near, anchor = contexts(df)
    p = S.DEFAULTS["1H"]
    _, trig, sig, _ = S.run(df, near, anchor, p, True)
    i, d = sig["i"].to_numpy(), sig["dir"].to_numpy()
    for k in range(1, len(sig)):
        if d[k] == d[k - 1]:
            assert i[k] - i[k - 1] >= p.cooldown
    assert trig["i"].is_unique


def test_volume_missing_lowers_the_denominator():
    df = bars(seed=7, vol=False)
    near, anchor = contexts(df)
    _, trig, _, _ = S.run(df, near, anchor, S.DEFAULTS["1H"], vol_ok=False)
    warm = trig[~trig["near"].isna() & ~trig["anchor"].isna()]
    assert (warm["available"] == 5).all() and not warm["volume"].any()


def test_vectorised_outcomes_equal_the_reference_loop():
    df = bars(seed=11)
    near, anchor = contexts(df)
    f, trig, _, _ = S.run(df, near, anchor, S.DEFAULTS["1H"], True)
    a = E.outcomes(trig, f, 24, 10)
    b = E.lookup(trig, E.bar_outcomes(f, 24, 10))
    for k in ("ret_h", "r_h", "mfe", "mae", "barrier"):
        np.testing.assert_allclose(a[k].to_numpy(), b[k].to_numpy())


def test_outcomes_enter_on_next_open_not_signal_close():
    df = bars(seed=12)
    near, anchor = contexts(df)
    f, trig, _, _ = S.run(df, near, anchor, S.DEFAULTS["1H"], True)
    o = E.outcomes(trig.head(5), f, 24, 0)
    for _, row in o.iterrows():
        assert row["entry"] == f.o[int(row["i"]) + 1]


def test_simulated_stop_fills_at_open_when_gapped():
    n = 60
    idx = pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC")
    c = np.full(n, 100.0)
    c[40:] = 80.0                               # gap down through any long stop
    o = c.copy()
    h, l = c + 0.5, c - 0.5
    df = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": 1.0}, index=idx)
    f = S.features(df, None, None, S.DEFAULTS["1D"], True)
    ev = pd.DataFrame({"i": [30], "dir": [1]})
    t = E.simulate(ev, f, 0.0, max_hold=100)
    assert t.iloc[0]["exit"] == 80.0 and t.iloc[0]["reason"] == "stop"


def test_4h_bars_follow_the_us_session():
    idx = pd.DatetimeIndex(["2024-03-05 14:30", "2024-03-05 15:30", "2024-03-05 16:30",
                            "2024-03-05 17:30", "2024-03-05 18:30", "2024-03-05 19:30"], tz="UTC")
    h1 = pd.DataFrame({"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 1.0}, index=idx)
    out = to_4h(h1, Asset("X", "equity", "yahoo", True, "rth"))
    assert list(out.index) == [idx[0], idx[4]]
    assert out["volume"].tolist() == [4.0, 2.0]


def test_weeks_start_on_monday():
    d = bars(30, freq="1D", start="2024-01-03")  # a Wednesday
    w = to_weekly(d)
    assert all(t.dayofweek == 0 for t in w.index)


def test_last_bar_evidence_is_final_at_every_bar():
    """Bar-by-bar version of the truncation test, for the newest bar, where look-ahead
    and forming higher-timeframe bars would show up. The evidence on bar k computed with
    data up to k must equal the evidence on bar k computed with the full series."""
    df = bars(900, seed=3)
    p = S.DEFAULTS["1H"]
    near, anchor = contexts(df)
    full = S.features(df, near, anchor, p, True)
    ph_full, pl_full = ta.pivots(full.h, full.l, p.pivot_left, p.pivot_right)
    for k in range(250, 900, 3):
        cut = df.iloc[: k + 1]
        fk = S.features(cut, _resample(cut, "4h", label="left", closed="left"),
                        _resample(cut, "1D", label="left", closed="left"), p, True)
        for name in ("near", "anchor", "atr", "rsi", "hist", "adx", "pdi", "mdi", "rvol", "ema"):
            a, b = getattr(full, name)[k], getattr(fk, name)[k]
            assert (np.isnan(a) and np.isnan(b)) or a == pytest.approx(b), (name, k, a, b)
        phk, plk = ta.pivots(fk.h, fk.l, p.pivot_left, p.pivot_right)
        np.testing.assert_array_equal(ph_full[: k + 1], phk)
        np.testing.assert_array_equal(pl_full[: k + 1], plk)
