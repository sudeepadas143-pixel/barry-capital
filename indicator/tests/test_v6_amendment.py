"""Regression tests for amendment V6-A1 (four implementation clarifications of
reports/V6_CONT_CONFIG.md, recorded in the register and protocol before any V6 outcome).
Synthetic data only."""

import importlib.util
import inspect
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf.data import _resample  # noqa: E402
from research import v5_eval as EV, v6_signals as S6  # noqa: E402
from test_engine_v2 import minute_bars  # noqa: E402

spec = importlib.util.spec_from_file_location("v6_cont_explore_a1", ROOT / "scripts" / "v6_cont_explore.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


# ----------------------------------------------------------------------------- item 1: trading-median test

def test_item1_pair_median_of_mean_net_is_per_pair_mean_then_median_and_distinct_from_pooled():
    ok = pd.DataFrame({"sym": ["AAA"] * 4 + ["BBB"] + ["CCC"],
                       "net": [0.10, -0.01, -0.01, -0.01, -0.001, -0.002],
                       "slip": 0.001, "trade_status": "ok", "mae_trade": 0.0, "cost_src": "none_long_spot"})
    # per-pair means: AAA +0.0175, BBB -0.001, CCC -0.002 -> median -0.001
    assert M.pair_median_of_mean_net(ok) == pytest.approx(-0.001)
    s = M.trading_summary(ok)
    assert s["pair_median_of_mean_net"] == pytest.approx(-0.001)
    assert s["net_mean"] > 0 > s["pair_median_of_mean_net"]           # pooled mean says positive; the test says no
    assert s["net_median"] == pytest.approx(-0.006)                     # pooled per-trade median is a different quantity
    assert M.pair_median_of_mean_net(ok.iloc[:0]) is None
    # computed on 'net' (primary costs, slippage already charged); the x0/x2 sensitivities never enter it
    s2 = M.trading_summary(ok.assign(slip=0.05))
    assert s2["pair_median_of_mean_net"] == s["pair_median_of_mean_net"]
    # pairs without a completed trade are not counted
    s3 = M.trading_summary(pd.concat([ok, pd.DataFrame({"sym": ["DDD"], "net": [np.nan], "slip": [0.001],
                                                        "trade_status": ["no_exit_in_data"], "mae_trade": [np.nan], "cost_src": [""]})]))
    assert s3["pairs"] == 3 and s3["pair_median_of_mean_net"] == pytest.approx(-0.001)


# ----------------------------------------------------------------------------- item 2: gap at the touch candle

def test_item2_gap_detection_threshold():
    t1 = pd.DatetimeIndex(["2021-01-01 00:00", "2021-01-01 01:00", "2021-01-01 02:30", "2021-01-01 04:31"], tz="UTC")
    assert list(S6.gaps(t1, "1H")) == [False, False, False, True]         # 1.5 h is not a gap; 2.02 h is
    t4 = pd.DatetimeIndex(["2021-01-01 00:00", "2021-01-01 04:00", "2021-01-01 12:00"], tz="UTC")
    assert list(S6.gaps(t4, "4H")) == [False, False, True]                # 8 h > 6 h


def _ind(c, h, l):
    n = len(c)
    return {"c": np.asarray(c, float), "h": np.asarray(h, float), "l": np.asarray(l, float), "ef": np.full(n, 10.0),
            "em": np.full(n, 8.0)}


def test_item2_a_gap_before_the_touch_candle_starts_and_ends_the_pullback_and_disarms():
    #          0     1     2(gap,touch) 3(touch)  4(re-arm) 5(touch) 6(trigger)
    c = [11.0, 10.8, 10.6, 10.7, 11.0, 10.5, 11.4]
    h = [11.2, 11.0, 10.9, 10.95, 11.1, 10.9, 11.5]
    l = [10.5, 10.4, 9.9, 9.95, 10.6, 9.9, 10.9]
    tr = np.array([S6.UP] * 7, object)
    gap = np.zeros(7, bool); gap[2] = True
    a = S6.model_a(_ind(c, h, l), tr, gap, 1, W=10)
    # candle 2 would trigger on its own (close 10.6 > 10 but not > high[1] 11.0) - irrelevant: its pullback ends at once;
    # candle 3 touches but the pair is disarmed, so no pullback; 4 re-arms; 5 starts; 6 triggers (11.4 > 10.9)
    assert list(map(tuple, a[["i", "j"]].to_numpy())) == [(6, 5)]
    # without the gap the touch at 2 opens a pullback and 3 cannot trigger (10.7 < 10.9), 4 triggers? 11.0 > 10.95 -> (4, 2)
    a0 = S6.model_a(_ind(c, h, l), tr, np.zeros(7, bool), 1, W=10)
    assert list(map(tuple, a0[["i", "j"]].to_numpy()))[0] == (4, 2)


def test_item2_a_touch_candle_with_a_gap_never_triggers_itself():
    c = [11.0, 12.5]
    h = [11.2, 12.6]
    l = [10.5, 9.8]                                      # candle 1 touches and closes above high[0]
    gap = np.array([False, True])
    tr = np.array([S6.UP, S6.UP], object)
    assert len(S6.model_a(_ind(c, h, l), tr, gap, 1, W=10)) == 0
    assert list(S6.model_a(_ind(c, h, l), tr, np.zeros(2, bool), 1, W=10)["i"]) == [1]


# ----------------------------------------------------------------------------- items 3 and 4 on a synthetic run

SYMS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT"]


@pytest.fixture(scope="module")
def synth():
    out = {}
    for k, s in enumerate(SYMS):
        m = minute_bars(n15=4 * 24 * 560, seed=400 + k, start="2018-06-01")
        r = lambda rule: _resample(m, rule, label="left", closed="left")
        d1 = r("1D")
        out[s] = {"1H": r("1h"), "4H": r("4h"), "1D": d1, "1W": _resample(d1, "W-MON", label="left", closed="left")}
    return out


def _patch(monkeypatch, synth, universe):
    monkeypatch.setattr(M.DG, "load", lambda sym, tf: synth[sym][tf])
    monkeypatch.setattr(M.DG, "load_funding", lambda sym: None)
    monkeypatch.setattr(M.X, "perp_start", lambda sym: None)
    monkeypatch.setattr(M, "UNIVERSE", tuple(universe))
    monkeypatch.setattr(M, "START", pd.Timestamp("2019-07-01", tz="UTC"))
    monkeypatch.setattr(M, "REPS_RAND", 7)


def test_item3_seeding_is_named_deterministic_and_order_independent(monkeypatch, synth):
    a = M.rng_for("ETHUSDT", "P", 1, "1H").random(5)
    assert np.array_equal(a, M.rng_for("ETHUSDT", "P", 1, "1H").random(5))
    for other in (("XRPUSDT", "P", 1, "1H"), ("ETHUSDT", "E1", 1, "1H"), ("ETHUSDT", "P", -1, "1H"), ("ETHUSDT", "P", 1, "4H")):
        assert not np.array_equal(a, M.rng_for(*other).random(5)), other
    src = inspect.getsource(M.worker)
    assert "rng_for(sym, cfg_id, side, tf)" in src and "sorted(cnt.items())" in src
    # same pair, different universe order and processing order -> identical random-entry replicates
    _patch(monkeypatch, synth, SYMS)
    liq, first = M.prepare()
    r1 = M.worker(("ETHUSDT", "1H", liq["ETHUSDT"], first["ETHUSDT"]))
    _patch(monkeypatch, synth, list(reversed(SYMS)))
    liq2, first2 = M.prepare()
    M.worker(("ADAUSDT", "1H", liq2["ADAUSDT"], first2["ADAUSDT"]))       # another pair first
    r2 = M.worker(("ETHUSDT", "1H", liq2["ETHUSDT"], first2["ETHUSDT"]))
    assert r1["rand"].keys() == r2["rand"].keys() and len(r1["rand"]) > 0
    assert any(v["counts"][0] > 0 for v in r1["rand"].values())           # not vacuous
    for k in r1["rand"]:
        assert np.array_equal(r1["rand"][k]["sums"], r2["rand"][k]["sums"]), k


def test_item4_shared_trades_are_config_free_and_identical_across_configs(monkeypatch, synth):
    params = list(inspect.signature(M.shared_trade).parameters)
    assert params == ["o", "h", "l", "c", "idx", "atr", "funding", "i", "j", "side", "hold", "tgap", "slip"]
    _patch(monkeypatch, synth, SYMS)
    liq, first = M.prepare()
    r = M.worker(("XRPUSDT", "1H", liq["XRPUSDT"], first["XRPUSDT"]))
    U = r["units"]
    ok = U[U["trade_status"] == "ok"]
    assert len(ok) > 50
    g = ok.groupby(["i", "j", "side"])
    shared = g.filter(lambda d: d["cfg"].nunique() > 1)
    assert len(shared) > 0                                                # keys really are shared across configs
    for col in ("net", "gross", "mae_trade", "cost_src"):
        assert (shared.groupby(["i", "j", "side"])[col].nunique(dropna=False) == 1).all(), col
    # configuration-specific flags (B, C, D) differ within shared keys, yet the trade does not
    assert (shared.groupby(["i", "j", "side"])[["B", "C", "D"]].nunique() > 1).any().any()
    # recomputing directly from (i, j, side) reproduces every stored trade
    df = synth["XRPUSDT"]["1H"]
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    from hcmtf import ta
    atr = ta.atr(h, l, c, 14)
    tg = M.window_gap(df.index, "1H", M.TFS["1H"]["hold"])
    for row in ok.drop_duplicates(["i", "j", "side"]).head(40).itertuples():
        t = M.shared_trade(o, h, l, c, df.index, atr, None, row.i, row.j, row.side, M.TFS["1H"]["hold"], bool(tg[row.i]), row.slip)
        assert t["net"] - t["slip"] == pytest.approx(row.net) and t["gross"] == pytest.approx(row.gross)
        ref = EV.trade(o, h, l, c, df.index, row.i, row.side, M.TFS["1H"]["hold"], t["stop"], "crypto", None)
        assert ref["net"] == pytest.approx(t["net"])
