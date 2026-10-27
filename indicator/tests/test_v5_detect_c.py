"""Family C detectors (research/v5_detect_c.py) against the frozen configuration. Synthetic data only."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf.data import _resample  # noqa: E402
from hcmtf.universe import BY_SYMBOL  # noqa: E402
from research import v5_detect_c as DC, v5_state as ST  # noqa: E402
from test_engine_v2 import minute_bars  # noqa: E402

START = pd.Timestamp("2000-01-01", tz="UTC")
ASSET = BY_SYMBOL["BTCUSDT"]


def frames(m15, cut=None):
    m = m15 if cut is None else m15[m15.index + pd.Timedelta(minutes=15) <= cut]
    r = lambda rule: _resample(m, rule, label="left", closed="left")
    ch = r("1h")
    if cut is not None:
        ch = ch[ch.index + pd.Timedelta(hours=1) <= cut]
    return ch, r("4h"), r("1D")


def run(ch, h1, h2):
    st = ST.classify(ch, h1, h2)
    return DC.detect_all(ch, h1, h2, st, "1H", ASSET, START), st


@pytest.fixture(scope="module")
def m15():
    return minute_bars(n15=28000, seed=33)


def test_every_variant_is_causal_under_truncation(m15):
    full, _ = run(*frames(m15))
    assert set(full) == set(DC.DETECTORS)
    for cut in (m15.index[10001], m15.index[17777], m15.index[24000]):
        cut = cut.floor("h")
        part, _ = run(*frames(m15, cut))
        n = len(frames(m15, cut)[0])
        for k in DC.DETECTORS:
            assert list(part[k]) == [i for i in full[k] if i < n], (k, cut)


def test_alerts_are_unique_sorted_eligible_and_c5a_is_c5b_after_a_warning(m15):
    out, st = run(*frames(m15))
    warm = st["warm"].to_numpy(bool)
    for k, a in out.items():
        assert (np.diff(a) > 0).all() and warm[a].all(), k
    assert set(out["C5a"]) <= set(out["C5b"])
    warn = np.unique(np.concatenate([out[k] for k in DC.WARNINGS]))
    for i in out["C5b"]:
        has = bool(((warn >= i - 50) & (warn <= i - 1)).any())
        assert has == (i in set(out["C5a"]))
    # the synthetic series is long enough that most variants fire (the check is not vacuous)
    assert sum(len(a) > 0 for a in out.values()) >= 5


def _state(ext, lab, vp=None):
    n = len(ext)
    return pd.DataFrame({"extension_atr": np.asarray(ext, float), "direction_label": np.asarray(lab, object),
                         "vol_pct": np.asarray(vp if vp is not None else np.full(n, np.nan), float),
                         "warm": np.ones(n, bool)},
                        index=pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"))


def test_c1a_cross_only_in_bull_state():
    ext = [0, 2, 3.5, 4, 2, 3.0, np.nan, 3.5, 3.6]
    lab = ["bull", "bull", "bull", "bull", "bull", "bull", "bull", "bull", "neutral"]
    assert list(DC.c1a(_state(ext, lab))) == [2, 5]          # not 7 (previous NaN), not 3 (no cross)
    assert len(DC.c1a(_state(ext, ["bear"] * 9))) == 0


def test_c1b_percentile_onset_needs_500_prior_values():
    ext = np.r_[np.linspace(0, 1, 600), [5, 5, 5, 0, 6]]
    lab = np.full(len(ext), "bull", object)
    a = DC.c1b(_state(ext, lab))
    # rising series: condition true from 500 (first defined) through 602 -> one onset; 603 false; 604 new onset
    assert list(a) == [500, 604]
    ext2 = ext.copy(); ext2[300] = np.nan                      # a hole inside every later 500-candle window
    assert len(DC.c1b(_state(ext2, lab))) == 0                 # percentile undefined -> never fires


def _ohlc(c, wick=0.1):
    c = np.asarray(c, float)
    o = np.r_[c[0], c[:-1]]
    idx = pd.date_range("2024-01-01", periods=len(c), freq="1h", tz="UTC")
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) + wick, "low": np.minimum(o, c) - wick, "close": c,
                         "volume": 1.0}, index=idx)


def test_c3_failed_breakout_rules():
    # pivot high at 10 (price 10), confirmed at 13; breakout at 20; failure at 23 -> one alert at 23
    c = np.r_[np.linspace(5, 10, 11), np.linspace(9.5, 7, 7), np.linspace(8, 10.5, 3), [10.8, 10.2, 9.5, 9.4, 9.0]]
    df = _ohlc(c, wick=0.0)
    a = DC.c3(df)
    assert list(a) == [23]
    # failure after more than 5 candles: no alert
    c2 = np.r_[np.linspace(5, 10, 11), np.linspace(9.5, 7, 7), np.linspace(8, 10.5, 3), [10.8, 10.9, 11, 11.1, 11.2, 10.4, 9.0]]
    assert len(DC.c3(_ohlc(c2, wick=0.0))) == 0


def test_c4_requires_extension_down_candle_and_volatility_jump():
    n = 12
    ext = np.full(n, 2.0)
    vp = np.r_[np.full(6, 10.0), [50, 50, 50, 50, 50, 50]]
    st = _state(ext, np.full(n, "bull", object), vp)
    c = np.r_[np.full(6, 10.0), [9, 11, 9, 9, 9, 9]]
    df = _ohlc(c)
    df["open"] = np.r_[np.full(6, 10.0), [10, 10, 10, 10, 10, 10]]
    a = DC.c4(df, st)
    assert list(a) == [6, 8, 9, 10]          # 7 is an up candle; 11: vp[6] = 50 so the jump is 0
    st2 = _state(np.full(n, 0.5), np.full(n, "bull", object), vp)
    assert len(DC.c4(df, st2)) == 0          # no prior extension


def test_eligibility_drops_cold_and_pre_window_candles():
    st = _state(np.zeros(10), np.full(10, "bull", object))
    st.loc[st.index[:3], "warm"] = False
    a = DC.eligible([0, 1, 2, 3, 5, 5, 9], st, st.index[5])
    assert list(a) == [5, 9]
    assert len(DC.eligible([], st, START)) == 0


def test_detectors_do_not_read_labels():
    src = (Path(__file__).resolve().parent.parent / "research" / "v5_detect_c.py").read_text()
    imports = [ln for ln in src.splitlines() if ln.lstrip().startswith(("import ", "from "))]
    assert not any("v5_labels" in ln or "v5_eval" in ln for ln in imports), imports
