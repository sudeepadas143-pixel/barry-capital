"""Regression tests for the V5 independent audit (reports/V5_INDEPENDENT_AUDIT.md). One or more per fix.

Synthetic data only; no evaluation outcome is computed.
"""

import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import hcmtf.data as D  # noqa: E402
from hcmtf import ta  # noqa: E402
from research import v5_costs as C, v5_data as DG, v5_eval as EV, v5_ledger as LG, v5_state as ST  # noqa: E402
from research.v5_labels import TOP_PARAMS, major_tops  # noqa: E402
from research.v5_reserve import FREEZE, V5_RESERVE  # noqa: E402


# ----------------------------------------------------------------------------- A1 closed-candle freeze

def test_A1_weekly_monthly_candles_cannot_absorb_post_freeze_prices(monkeypatch, tmp_path):
    """A week/month/quarter that opens before the freeze but would be built from forward daily
    candles must be dropped (before the fix the planted high of 10,000 leaked into 1W and 1M)."""
    idx = pd.date_range(pd.Timestamp("2024-01-01", tz="UTC"), FREEZE.normalize() + pd.Timedelta(days=20), freq="D")
    c = np.linspace(100, 120, len(idx))
    hi = c + 1
    hi[idx > FREEZE] = 10_000.0
    df = pd.DataFrame({"open": c, "high": hi, "low": c - 1, "close": c, "volume": 1.0}, index=idx)
    monkeypatch.setattr(D, "DATA_DIR", tmp_path)
    df.to_csv(tmp_path / "BTCUSDT_1d.csv.gz", compression="gzip")
    for tf in ("1D", "1W", "1M", "3M"):
        out = DG.load("BTCUSDT", tf)
        assert out["high"].max() < 10_000.0, tf
        assert out.index.max() <= FREEZE


# ----------------------------------------------------------------------------- A2 feed-consistent extension

def _chart_and_htf(seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=3000, freq="4h", tz="UTC")
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(idx))))
    ch = pd.DataFrame({"open": c, "high": c * 1.005, "low": c * 0.995, "close": c, "volume": 1.0}, index=idx)
    d = D._resample(ch, "1D", label="left", closed="left")
    w = D._resample(ch, "W-MON", label="left", closed="left")
    return ch, d, w


def test_A2_extension_does_not_depend_on_the_htf_feed_price_level():
    """A dividend-adjusted daily feed is the hourly feed scaled by a factor; extension must not move."""
    ch, d, w = _chart_and_htf()
    a = ST.classify(ch, d, w)
    d2 = d.copy()
    d2[["open", "high", "low", "close"]] *= 1.016
    b = ST.classify(ch, d2, w)
    np.testing.assert_allclose(a["extension_atr"], b["extension_atr"], equal_nan=True)
    assert (a["direction_label"] == b["direction_label"]).all()      # trend state is scale-free too


# ----------------------------------------------------------------------------- A3 incomplete RTH 4H edge

def test_A3_incomplete_trailing_rth_4h_candle_is_dropped(monkeypatch, tmp_path):
    days = pd.bdate_range("2026-09-01", "2026-10-20", tz="America/New_York")
    hours = [d + pd.Timedelta(hours=9, minutes=30) + pd.Timedelta(hours=k) for d in days for k in range(7)]
    hours = pd.DatetimeIndex(hours).tz_convert("UTC")
    hours = hours[:-4]                                    # last session stops after its 12:30 ET bar
    c = np.linspace(100, 110, len(hours))
    h1 = pd.DataFrame({"open": c, "high": c + 0.5, "low": c - 0.5, "close": c, "volume": 1.0}, index=hours)
    d1 = D._resample(h1, "1D", label="left", closed="left")
    d1.index = d1.index.normalize()
    monkeypatch.setattr(D, "DATA_DIR", tmp_path)
    (tmp_path / "SPY_1h.csv.gz").write_text("x")
    (tmp_path / "SPY_1d.csv.gz").write_text("x")
    real = D.to_4h

    def fake_load(sym, tf):
        if tf == "1H":
            return h1
        if tf == "4H":
            return real(h1, D.BY_SYMBOL["SPY"])
        return d1
    monkeypatch.setattr(D, "load", fake_load)
    full = real(h1, D.BY_SYMBOL["SPY"])
    out = DG.load("SPY", "4H")
    assert len(out) == len(full) - 1 and out.index[-1] < full.index[-1]


# ----------------------------------------------------------------------------- A4 causal gap_steps

def test_A4_gap_steps_do_not_depend_on_future_spacing():
    ch, d, w = _chart_and_htf(1)
    a = ST.classify(ch, d, w)
    # future candles arrive at irregular spacing (e.g. a feed outage pattern later on)
    # (most candles are in the future, so a whole-series median would move: the old defect)
    k = 1000
    later = ch.iloc[k:].copy()
    later.index = ch.index[k] + pd.to_timedelta(np.arange(len(later)) * 7, unit="h")
    ch2 = pd.concat([ch.iloc[:k], later])
    b = ST.classify(ch2, d, w)
    np.testing.assert_array_equal(a["gap_steps"].iloc[:k + 1], b["gap_steps"].iloc[:k + 1])
    assert (a["gap_steps"].iloc[1:k] == 0).all()


# ----------------------------------------------------------------------------- B evaluation fixes

def test_B1_audit_duplicate_btc_is_not_pooled():
    assert "BTC-USD" in DG.EXPLORATION and "BTC-USD" not in DG.EVAL_SYMBOLS
    assert "BTCUSDT" in DG.EVAL_SYMBOLS and len(DG.EVAL_SYMBOLS) == len(set(DG.EVAL_SYMBOLS)) == 108


def test_B2_labels_always_use_atr14_computed_internally():
    rng = np.random.default_rng(3)
    c = 100 + np.cumsum(rng.normal(0, 1, 2500))
    h, l = c + np.abs(rng.normal(0, .5, len(c))), c - np.abs(rng.normal(0, .5, len(c)))
    idx = pd.date_range("2015-01-01", periods=len(c), freq="D", tz="UTC")
    r = EV.score_instrument("SPY", h, l, c, [], "top", "warning", "1D", idx)
    p = TOP_PARAMS["1D"]
    ev = major_tops(h, l, ta.atr(h, l, c, 14), **p)
    lo, hi = p["L"], len(c) - 1 - max(p["L"], p["F"])
    assert list(r["events"]) == [t for t in ev if lo <= t <= hi]


def test_B3_evaluation_refuses_reserved_and_unknown_symbols():
    idx = pd.date_range("2020-01-01", periods=50, freq="D", tz="UTC")
    x = np.ones(50)
    for sym in (V5_RESERVE["equities"][0], "NOT_A_SYMBOL"):
        with pytest.raises(DG.ReservedDataError):
            EV.candle_table(sym, idx, "1D", 5, {}, {"r_h": x})
        with pytest.raises(DG.ReservedDataError):
            EV.score_instrument(sym, x, x, x, [], "top", "warning", "1D", idx)


def test_B4_outcome_window_end_and_overlap_rule():
    idx = pd.date_range("2020-01-01", periods=100, freq="D", tz="UTC")
    ct = EV.candle_table("SPY", idx, "1D", 10, {}, {"r_h": np.zeros(100)})
    # outcome of candle 5 ends at the close of candle 15 = open of candle 16
    assert ct.loc[5, "t_end"] == idx[16].value // 1000 * 1000 or ct.loc[5, "t_end"] == idx.as_unit("ns").asi8[16]
    u = pd.DataFrame({"sym": "SPY", "i": [0, 10, 19, 30]})
    o = EV.overlap(u, 10)
    assert o["overlap_share"] == pytest.approx(1 / 4)      # only 10 -> 19 overlaps (9 < 10)
    assert o["effective_n"] == 3                           # 0, 10, 30


def test_B5_units_without_benchmark_are_excluded_consistently():
    idx = pd.date_range("2020-01-01", periods=600, freq="D", tz="UTC")
    rng = np.random.default_rng(2)
    tabs = []
    for s in ("SPY", "QQQ", "IWM"):
        st = np.where(np.arange(600) < 590, "a", "b")
        tabs.append(EV.candle_table(s, idx, "1D", 5, {"vol_regime": st}, {"r_h": rng.normal(0, 1, 600)}))
    ct = pd.concat(tabs, ignore_index=True)
    ct.attrs.update(tabs[0].attrs)
    bench = EV.bench_table(ct[ct["vol_regime"] == "a"], "r_h", ["vol_regime"])  # no benchmark for "b"
    u = EV.units_from(ct, ct[ct["i"] % 7 == 0][["sym", "i"]], ["vol_regime"])
    res = EV.excess(u, bench, "r_h", 5, (int(ct["t"].min()), int(ct["t"].max())), reps=100)
    nb = int((u["vol_regime"] == "b").sum())
    assert nb > 0 and res["units_without_benchmark"] == nb and res["n"] == len(u) - nb
    assert res["mean_value"] == pytest.approx(u.loc[u["vol_regime"] == "a", "r_h"].mean())


# ----------------------------------------------------------------------------- C1 causal benchmark

def test_C1_causal_benchmark_uses_only_completed_past_outcomes():
    idx = pd.date_range("2020-01-01", periods=400, freq="D", tz="UTC")
    rng = np.random.default_rng(4)
    st = rng.choice(["x", "y"], 400)
    r = rng.normal(0, 1, 400)
    ct = EV.candle_table("SPY", idx, "1D", 10, {"vol_regime": st}, {"r_h": r})
    b = EV.causal_benchmark(ct, "r_h", ["vol_regime"], 10, min_history=20)
    i = 300
    exp = r[: i - 10 + 1][st[: i - 10 + 1] == st[i]].mean()
    assert b[i] == pytest.approx(exp)
    # adversarial: changing outcomes that are not yet known at i (candles i-9 .. end) changes nothing up to i
    r2 = r.copy()
    r2[i - 9:] += 100.0
    ct2 = EV.candle_table("SPY", idx, "1D", 10, {"vol_regime": st}, {"r_h": r2})
    b2 = EV.causal_benchmark(ct2, "r_h", ["vol_regime"], 10, min_history=20)
    np.testing.assert_array_equal(b[: i + 1], b2[: i + 1])
    assert np.isnan(b[:25]).all()                          # min_history enforced
    ct["cb"] = b
    res = EV.excess_causal(ct, "r_h", "cb", 10, (int(ct["t"].min()), int(ct["t"].max())), reps=200)
    assert res["n"] == int(np.isfinite(b).sum()) and res["lo"] <= res["mean_excess"] <= res["hi"]


# ----------------------------------------------------------------------------- E costs and holding time

def test_E1_unavailable_costs_are_never_zero():
    n = 30
    idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    c = np.full(n, 1.1)
    t = EV.trade(c, c + .01, c - .01, c, idx, 5, -1, 5, None, "fx")
    assert np.isnan(t["holding_cost"]) and np.isnan(t["net"]) and t["cost_complete"] is False
    assert EV.cost_sources([t]) == {"unavailable_fx_carry": 1, "incomplete": 1}
    with pytest.raises(ValueError):
        EV.sequential_daily(c, c, idx, [t])
    d = EV.sequential_daily(c, c, idx, [t], unavailable_cost_as_zero=True)
    assert np.isfinite(d).all()


def test_E2_holding_time_excludes_the_overnight_gap_after_the_exit_candle():
    days = pd.bdate_range("2024-03-04", periods=5, tz="America/New_York")
    idx = pd.DatetimeIndex([d + pd.Timedelta(hours=9, minutes=30) + pd.Timedelta(hours=k) for d in days for k in range(7)]).tz_convert("UTC")
    c = np.full(len(idx), 100.0)
    # signal at the 1st bar of day 1; entry 2nd bar; 5-bar hold exits at the 6th bar (14:30 ET), closes 15:30
    t = EV.trade(c, c + 1, c - 1, c, idx, 0, -1, 5, None, "equity")
    hours = (t["holding_cost"] / C.BORROW_GC_ANNUAL) * 365.25 * 24
    assert hours == pytest.approx(5.0)
    # exit on the session's last bar: charged to its close (16:00 ET), not the next morning's open
    t2 = EV.trade(c, c + 1, c - 1, c, idx, 1, -1, 5, None, "equity")
    hours2 = (t2["holding_cost"] / C.BORROW_GC_ANNUAL) * 365.25 * 24
    assert hours2 == pytest.approx(5.0)


# ----------------------------------------------------------------------------- L ledger

CFG = "research/v5_labels.py"     # frozen and committed (test P2), so always clean: stands in for a config file


def _rec(path, tid, **kw):
    data = path.parent / "d.bin"
    data.write_bytes(b"x") if not data.exists() else None
    args = dict(hypothesis_id="C1", partitions=["exploration"], config={}, code_files=["research/v5_eval.py"],
                metrics_requested=["recall"], outcomes_accessed=False, config_file=CFG, data_files=[str(data)], path=path)
    args.update(kw)
    return LG.record(tid, **args)


def test_L1_config_must_be_committed_and_data_is_fingerprinted(tmp_path):
    p = tmp_path / "l.jsonl"
    with pytest.raises(LG.LedgerError):
        _rec(p, "t-001", config_file="reports/DOES_NOT_EXIST.md")
    with pytest.raises(LG.LedgerError):
        _rec(p, "t-002", data_files=[])
    r = _rec(p, "t-003")
    assert r["config_file"] == CFG and len(r["config_file_sha256"]) == 64 and list(r["data"].values())[0] == LG.sha(b"x")


def test_L2_prereg_must_be_a_committed_v5_prereg_naming_the_hypothesis(tmp_path):
    p = tmp_path / "l.jsonl"
    for bad in ("README.md", "reports/V5_VALIDATION_PROTOCOL.md", "reports/V4_1_PREREGISTRATION.md"):
        with pytest.raises(LG.LedgerError):
            _rec(p, "t-010", partitions=["forward"], confirmatory_prereg=bad)


def _git_init(d: Path):
    for cmd in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], cwd=d, check=True)


def test_L3_truncating_a_committed_ledger_is_detected(tmp_path):
    _git_init(tmp_path)
    led = tmp_path / "ledger.jsonl"
    led.write_text('{"a":1}\n{"b":2}\n')
    subprocess.run(["git", "add", "ledger.jsonl"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "l"], cwd=tmp_path, check=True)
    LG.verify_against_git(led, root=tmp_path)                 # unchanged: fine
    led.write_text('{"a":1}\n{"b":2}\n{"c":3}\n')
    LG.verify_against_git(led, root=tmp_path)                 # appended: fine
    led.write_text('{"a":1}\n')
    with pytest.raises(LG.LedgerError):
        LG.verify_against_git(led, root=tmp_path)             # newest committed record deleted


def _worker(args):
    path, tid = args
    return _rec(Path(path), tid)["trial_id"]


def test_L4_concurrent_appends_keep_one_valid_chain(tmp_path):
    p = tmp_path / "l.jsonl"
    with ProcessPoolExecutor(4) as ex:
        ids = list(ex.map(_worker, [(str(p), f"par-{k:03d}") for k in range(12)]))
    recs = LG.verify(p)
    assert sorted(r["trial_id"] for r in recs) == sorted(ids) and len(recs) == 12


# ----------------------------------------------------------------------------- P protection

def test_P1_only_the_evaluator_reads_the_retrospective_labels():
    allowed = {"research/v5_eval.py", "research/v5_labels.py", "scripts/v5_label_counts.py"}
    out = subprocess.run(["git", "grep", "-l", "v5_labels", "--", "research", "scripts", "hcmtf", "pine"],
                         cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert set(out) <= allowed, out


def test_P2_frozen_label_definitions_are_byte_identical_to_their_registration_commit():
    reg = subprocess.run(["git", "show", "7fc7e68:indicator/research/v5_labels.py"], cwd=ROOT,
                         capture_output=True, text=True)
    assert reg.returncode == 0 and (ROOT / "research" / "v5_labels.py").read_text() == reg.stdout
