"""V5 shared research infrastructure: state classifier, evaluation primitives, costs, ledger, data guard.

Synthetic data only. Nothing here produces or resembles an empirical result.
"""

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf.data import _resample  # noqa: E402
from research import v5_costs as C, v5_data as DG, v5_eval as EV, v5_ledger as LG, v5_state as ST  # noqa: E402
from research.v41 import state_rel  # noqa: E402
from research.v5_reserve import FREEZE, V5_RESERVE  # noqa: E402
from test_engine_v2 import minute_bars  # noqa: E402


# ----------------------------------------------------------------------------- helpers

def frames(m15, cut=None):
    """Chart 1H + HTF 4H/1D as known at `cut`: forming HTF candles built from partial data."""
    m = m15 if cut is None else m15[m15.index + pd.Timedelta(minutes=15) <= cut]
    r = lambda rule: _resample(m, rule, label="left", closed="left")
    ch = r("1h")
    if cut is not None:
        ch = ch[ch.index + pd.Timedelta(hours=1) <= cut]
    return ch, r("4h"), r("1D")


@pytest.fixture(scope="module")
def m15():
    return minute_bars(n15=24000, seed=11)


def same_rows(a: pd.DataFrame, b: pd.DataFrame):
    pd.testing.assert_frame_equal(a.reset_index(drop=True), b.reset_index(drop=True), check_exact=True)


# ----------------------------------------------------------------------------- state classifier

def test_state_never_changes_when_future_candles_are_removed(m15):
    full = ST.classify(*frames(m15))
    for cut in (m15.index[7001], m15.index[12345], m15.index[20000]):
        cut = cut.floor("h")
        part = ST.classify(*frames(m15, cut))
        same_rows(part, full.iloc[: len(part)])


def test_state_ignores_adversarial_future_and_forming_htf_candle(m15):
    ch, h1, h2 = frames(m15)
    base = ST.classify(ch, h1, h2)
    k = 3000
    ch2 = ch.copy()
    ch2.iloc[k + 1:, :4] *= 7.0                      # wild future
    same_rows(ST.classify(ch2, h1, h2).iloc[: k + 1], base.iloc[: k + 1])
    # corrupt the HTF1 candle that contains chart candle k (it is still forming at k's close)
    j = h1.index.searchsorted(ch.index[k], side="right") - 1
    h1b = h1.copy()
    h1b.iloc[j:, :4] *= 0.1
    inside = (ch.index >= h1.index[j]) & (ch.index < h1.index[j] + pd.Timedelta(hours=4))
    same_rows(ST.classify(ch, h1b, h2)[inside], base[inside])


def test_state_alignment_reads_previous_completed_htf_candle():
    idx = pd.date_range("2024-01-01", periods=400, freq="4h", tz="UTC")
    htf = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": np.r_[np.full(100, 1.0), np.linspace(1, 50, 300)],
                        "volume": 1.0}, index=idx)
    ch_idx = pd.date_range("2024-01-01", periods=1600, freq="1h", tz="UTC")
    rng = np.random.default_rng(0)
    c = 100 + np.cumsum(rng.normal(0, 1, len(ch_idx)))
    ch = pd.DataFrame({"open": c, "high": c + 1, "low": c - 1, "close": c, "volume": 1.0}, index=ch_idx)
    s = ST.classify(ch, htf, None)
    from hcmtf.htf import trend_state
    ts = trend_state(htf)
    for k in (500, 801, 1203):      # chart candle k opens inside HTF candle j = k // 4
        j = k // 4
        assert s["t1"].iloc[k] == ts[j - 1] or (np.isnan(s["t1"].iloc[k]) and np.isnan(ts[j - 1]))
    # the chart candle that opens exactly at an HTF boundary uses the candle that just completed
    k = 4 * 200
    assert ch.index[k] == htf.index[200] and s["t1"].iloc[k] == ts[199]


def test_state_direction_matches_engine_semantics(m15):
    s = ST.classify(*frames(m15))
    t1, t2 = s["t1"].to_numpy(), s["t2"].to_numpy()
    ok = ~np.isnan(t1)
    exp = np.where(state_rel(t1, t2, 1) == "with", 1, np.where(state_rel(t1, t2, -1) == "with", -1, 0))
    assert (s["direction"].to_numpy()[ok] == exp[ok]).all()
    assert (s["direction_label"][~ok] == ST.UNKNOWN).all()


def test_state_warmup_missing_candles_and_gaps(m15):
    ch, h1, h2 = frames(m15)
    s = ST.classify(ch, h1, h2)
    assert not s["warm"].iloc[:200].any()               # 200 prior ATR% values needed
    assert s["warm"].iloc[-500:].all()
    # a candle with missing OHLC is unknown; earlier rows are untouched
    k = 2500
    ch2 = ch.copy()
    ch2.iloc[k, :4] = np.nan
    s2 = ST.classify(ch2, h1, h2)
    same_rows(s2.iloc[:k], s.iloc[:k])
    row = s2.iloc[k]
    assert row["direction_label"] == row["strength"] == row["vol_regime"] == row["ext_bucket"] == ST.UNKNOWN
    assert not row["warm"]
    # dropped candles (a gap) are reported, not filled, and earlier rows are unchanged
    ch3 = ch.drop(ch.index[k:k + 5])
    s3 = ST.classify(ch3, h1, h2)
    assert s3["gap_steps"].iloc[k] == pytest.approx(5.0)
    same_rows(s3.iloc[:k], s.iloc[:k])
    # no HTF history: direction unknown, never guessed
    s4 = ST.classify(ch, h1.iloc[:0], None)
    assert (s4["direction_label"] == ST.UNKNOWN).all() and not s4["warm"].any()


def test_state_is_deterministic_and_does_not_mutate_inputs(m15):
    ch, h1, h2 = frames(m15)
    snap = (ch.copy(), h1.copy(), h2.copy())
    a, b = ST.classify(ch, h1, h2), ST.classify(ch, h1, h2)
    same_rows(a, b)
    for x, y in zip((ch, h1, h2), snap):
        pd.testing.assert_frame_equal(x, y)
    with pytest.raises(ValueError):
        ST.classify(ch.iloc[::-1], h1, h2)


# ----------------------------------------------------------------------------- alert matching

def brute_max_matching(alerts, events, kind, K, W):
    """Maximum bipartite matching by augmenting paths (reference for the greedy)."""
    adj = {s: [t for t in events if EV.eligible_range(s, kind, K, W)[0] <= t <= EV.eligible_range(s, kind, K, W)[1]]
           for s in alerts}
    match = {}

    def aug(s, seen):
        for t in adj[s]:
            if t in seen:
                continue
            seen.add(t)
            if t not in match or aug(match[t], seen):
                match[t] = s
                return True
        return False
    return sum(aug(s, set()) for s in alerts)


def test_greedy_matching_is_maximum_and_one_to_one():
    rng = np.random.default_rng(5)
    for _ in range(400):
        kind = ["warning", "confirmation"][rng.integers(2)]
        K, W = int(rng.integers(1, 8)), int(rng.integers(1, 6))
        events = sorted(set(rng.integers(0, 60, rng.integers(0, 8)).tolist()))
        alerts = sorted(set(rng.integers(0, 60, rng.integers(0, 12)).tolist()))
        pairs, status = EV.match_alerts(alerts, events, kind, K, W)
        assert len(pairs) == brute_max_matching(alerts, events, kind, K, W)
        assert len({t for _, t in pairs}) == len(pairs) and len({s for s, _ in pairs}) == len(pairs)
        for s, t in pairs:
            lo, hi = EV.eligible_range(s, kind, K, W)
            assert lo <= t <= hi


def test_repeated_alerts_cannot_claim_one_event_twice():
    pairs, status = EV.match_alerts([100, 101, 102, 103, 104, 104, 104], [100], "warning", K=10, W=5)
    assert pairs == [(100, 100)]
    assert list(status.values()).count("duplicate") == 4 and list(status.values()).count("matched") == 1


def test_overlapping_event_windows_and_kind_semantics():
    # one alert eligible for two events claims only the earliest; the second stays for a later alert
    pairs, _ = EV.match_alerts([50], [45, 52], "warning", K=10, W=5)
    assert pairs == [(50, 45)]
    pairs, _ = EV.match_alerts([50, 51], [45, 52], "warning", K=10, W=5)
    assert pairs == [(50, 45), (51, 52)]
    # a confirmation can never claim an event that has not happened yet; a warning can
    assert EV.match_alerts([40], [45], "confirmation", K=10, W=5)[0] == []
    assert EV.match_alerts([40], [45], "warning", K=10, W=5)[0] == [(40, 45)]
    _, st = EV.match_alerts([10], [45], "warning", K=10, W=5)
    assert st[10] == "false_alarm"


def test_near_event_vectorised_equals_loop():
    rng = np.random.default_rng(1)
    ev = np.sort(rng.choice(500, 20, replace=False))
    for kind in ("warning", "confirmation"):
        v = EV.near_event(500, ev, kind, 30, 15)
        loop = [float(any(EV.eligible_range(s, kind, 30, 15)[0] <= t <= EV.eligible_range(s, kind, 30, 15)[1] for t in ev))
                for s in range(500)]
        assert v.tolist() == loop


# ----------------------------------------------------------------------------- detection scoring

def path(segments, start="2021-01-04"):
    c = np.concatenate([np.linspace(a, b, n, endpoint=False) for a, b, n in segments] + [[segments[-1][1]]])
    idx = pd.date_range(start, periods=len(c), freq="D", tz="UTC")
    return c + 0.2, c - 0.2, c, np.ones(len(c)), idx


def test_score_instrument_lead_remaining_and_censoring():
    # 1D labels: L=63, F=126, D=8 ATR. Top at 150, bottom at 300; long tail so both are observable.
    h, l, c, a, idx = path([(0, 30, 150), (30, 0, 150), (0, 30, 150), (30, 30, 200)])
    r = EV.score_instrument("SPY", h, l, c, [140, 141, 160, 400], "top", "warning", "1D", idx)
    assert list(r["events"]) == [150]
    assert r["pairs"] == [(140, 150)] and r["status"][141] == "duplicate" and r["status"][160] == "duplicate"
    assert r["status"][400] == "false_alarm"
    assert r["leads"].tolist() == [10.0]
    final = l[150:150 + 127].min()
    assert r["remaining"][0] == pytest.approx((c[140] - final) / (h[150] - final))
    # censoring: cut the series so the top's forward window is incomplete → censored, not a miss
    n = 150 + 100
    r2 = EV.score_instrument("SPY", h[:n], l[:n], c[:n], [140], "top", "warning", "1D", idx[:n])
    assert r2["events_censored"] == 1 and 150 not in list(r2["events"])
    assert r2["alerts_censored"] == 1 and len(r2["alerts"]) == 0


def test_detection_report_pools_without_double_counting():
    h, l, c, a, idx = path([(0, 30, 150), (30, 0, 150), (0, 30, 150), (30, 30, 200)])
    r = EV.score_instrument("SPY", h, l, c, [140, 141, 400], "top", "warning", "1D", idx)
    rep = EV.detection_report({"X": r, "Y": r}, {"X": idx, "Y": idx}, "1D", "warning", reps=200)
    assert rep["events"] == 2 and rep["alerts"] == 6 and rep["matched"] == 2
    assert rep["duplicates"] == 2 and rep["false_alarms"] == 2
    assert rep["recall"][0] == 1.0 and rep["precision"][0] == pytest.approx(2 / 6)
    assert rep["precision_excluding_duplicates"] == pytest.approx(2 / 4)
    assert rep["evaluable"] is False                 # 2 events, 2 instruments: below the minimums


def test_lift_is_exactly_one_for_alerts_on_every_scorable_candle():
    h, l, c, a, idx = path([(0, 30, 150), (30, 0, 150), (0, 30, 150), (30, 30, 200)])
    n = len(c)
    r0 = EV.score_instrument("SPY", h, l, c, [], "top", "warning", "1D", idx)
    lo, hi = r0["L"], n - 1 - max(r0["L"], r0["F"])
    every = [s for s in range(n) if s - r0["K"] >= lo and s + r0["W"] <= hi]
    r = EV.score_instrument("SPY", h, l, c, every, "top", "warning", "1D", idx)
    out = EV.lift_report({"SPY": {"index": idx, "score": r, "state": np.full(n, "s")}}, "1D", "warning", reps=100)
    assert out["lift"] == pytest.approx(1.0) and abs(out["mean_excess"]) < 1e-12
    on = EV.score_instrument("SPY", h, l, c, [150], "top", "warning", "1D", idx)
    out2 = EV.lift_report({"SPY": {"index": idx, "score": on, "state": np.full(n, "s")}}, "1D", "warning", reps=100)
    assert out2["lift"] > 1.0


def test_evaluation_refuses_forward_candles_and_other_partitions():
    idx = pd.date_range(FREEZE - pd.Timedelta(days=5), periods=10, freq="D", tz="UTC")
    with pytest.raises(DG.ReservedDataError):
        EV.check_partition(idx, "1D")
    with pytest.raises(DG.ReservedDataError):
        EV.check_partition(idx[:3], "1D", partition="forward")
    with pytest.raises(DG.ReservedDataError):
        EV.candle_table("SPY", idx, "1D", 5, {}, {})
    h = np.ones(10)
    with pytest.raises(DG.ReservedDataError):
        EV.score_instrument("SPY", h, h, h, [], "top", "warning", "1D", idx)


# ----------------------------------------------------------------------------- continuation / excess

SYMS = ["SPY", "QQQ", "IWM", "EFA"]


def synthetic_candles(n_sym=4, n=3000, seed=0):
    rng = np.random.default_rng(seed)
    tabs = []
    for k in range(n_sym):
        idx = pd.date_range("2020-01-01", periods=n, freq="4h", tz="UTC")
        state = np.where(rng.random(n) < 0.5, "bull", "bear")
        vol = rng.choice(["low", "mid", "high"], n)
        r = rng.normal(0, 1, n)
        tabs.append(EV.candle_table(SYMS[k], idx, "4H", 30, {"direction_label": state, "vol_regime": vol}, {"r_h": r}))
    out = pd.concat(tabs, ignore_index=True)
    out.attrs.update(tabs[0].attrs)
    return out


def test_matching_only_on_declared_causal_columns():
    idx = pd.date_range("2020-01-01", periods=50, freq="D", tz="UTC")
    with pytest.raises(EV.MatchingError):
        EV.candle_table("SPY", idx, "1D", 5, {"r_h": np.zeros(50)}, {})
    ct = synthetic_candles(1, 200)
    with pytest.raises(EV.MatchingError):
        EV.bench_table(ct, "r_h", ["r_h"])
    with pytest.raises(EV.MatchingError):
        EV.bench_table(ct, "r_h", ["i"])            # identifiers are not declared causal
    with pytest.raises(EV.MatchingError):
        EV.continuation_report(ct, ct.iloc[:5], ct.iloc[:5], "r_h", "direction_label", "bull", ["mfe"], 30, (0, 1))


def test_excess_is_zero_when_units_are_the_benchmark_and_dependence_is_reported():
    ct = synthetic_candles()
    b = EV.bench_table(ct, "r_h", ["vol_regime"])
    u = EV.units_from(ct, ct[["sym", "i"]], ["vol_regime"])
    res = EV.excess(u, b, "r_h", 30, (int(ct["t"].min()), int(ct["t"].max())), reps=200)
    assert abs(res["mean_excess"]) < 1e-12 and res["lo"] <= 0 <= res["hi"]
    assert res["overlap_share"] == pytest.approx(1 - 4 / len(u)) and res["effective_n"] == 4 * 100     # windows i+1..i+30: units 30 apart do not overlap
    assert res["leave_one_instrument_out"] is not None and res["largest_instrument"] in set(SYMS)


def test_continuation_report_pairs_comparisons_and_counts_excluded_signals():
    ct = synthetic_candles(seed=3)
    bull = ct[ct["direction_label"] == "bull"]
    # signals: the bull candles with the highest outcomes (a deliberately leaky selection, to check
    # the sign of the machinery, NOT a result), duplicated, plus some bear-state candles
    sig = pd.concat([bull.nlargest(300, "r_h")[["sym", "i"]]] * 2 +
                    [ct[ct["direction_label"] == "bear"].head(50)[["sym", "i"]]])
    mom = bull.sample(300, random_state=1)[["sym", "i"]]
    rep = EV.continuation_report(ct, sig, mom, "r_h", "direction_label", "bull", ["vol_regime"], 30,
                                 (int(ct["t"].min()), int(ct["t"].max())), reps=300)
    assert rep["signals_total"] == 350 and rep["signals_outside_state_or_not_warm"] == 50
    assert rep["vs_state"]["n"] == 300 and rep["vs_state"]["mean_excess"] > 1.0
    assert rep["signal_minus_momentum"]["mean"] == pytest.approx(
        rep["vs_state"]["mean_excess"] - rep["momentum_vs_state"]["mean_excess"])


# ----------------------------------------------------------------------------- costs

T0 = pd.Timestamp("2024-01-01", tz="UTC")


def test_short_costs_units_and_annualisation():
    one_year = T0 + pd.Timedelta(days=365.25)
    assert C.short_holding_cost("equity", T0, one_year) == (pytest.approx(0.01), "estimated_gc_borrow_1pct")
    c, src = C.short_holding_cost("equity_index", T0, T0 + pd.Timedelta(days=1))
    assert c == pytest.approx(0.01 / 365.25) and src == "estimated_gc_borrow_1pct"
    c_fx, s_fx = C.short_holding_cost("fx", T0, one_year)
    assert np.isnan(c_fx) and s_fx == "unavailable_fx_carry"            # never a silent zero
    assert C.short_holding_cost("crypto", T0, one_year) == (pytest.approx(0.10), "estimated_crypto_10pct")
    assert C.holding_cost(1, "crypto", T0, one_year) == (0.0, "none_long_spot")
    with pytest.raises(ValueError):
        C.short_holding_cost("equity", one_year, T0)
    with pytest.raises(ValueError):
        C.short_holding_cost("weather", T0, one_year)


def test_short_funding_observed_vs_estimated():
    idx = pd.date_range("2023-12-01", "2024-03-01", freq="8h", tz="UTC")
    f = pd.DataFrame({"rate": np.full(len(idx), 0.0001)}, index=idx)
    entry, exit_ = T0 + pd.Timedelta(hours=1), T0 + pd.Timedelta(days=10, hours=1)
    cost, src = C.short_holding_cost("crypto", entry, exit_, f)
    assert src == "observed_funding" and cost == pytest.approx(-0.0001 * 30)     # shorts receive positive funding
    # funding series ends during the trade → estimated, never silently zero
    cost, src = C.short_holding_cost("crypto", entry, T0 + pd.Timedelta(days=120), f)
    assert src == "estimated_crypto_10pct" and cost > 0
    # a stale gap inside the holding period → estimated
    g = f.drop(f.index[(f.index > T0 + pd.Timedelta(days=2)) & (f.index < T0 + pd.Timedelta(days=6))])
    assert C.short_holding_cost("crypto", entry, exit_, g)[1] == "estimated_crypto_10pct"


# ----------------------------------------------------------------------------- trades

def test_trade_stops_time_exit_costs_and_data_end():
    n = 40
    idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    c = np.full(n, 100.0); o = c.copy(); h = c + 1; l = c - 1
    o[12], l[12], c[12] = 90.0, 89.0, 90.0                    # gap down through a long stop at 95
    t = EV.trade(o, h, l, c, idx, 10, 1, 10, 95.0, "equity")
    assert t["reason"] == "stop_gap" and t["gross"] == pytest.approx(90 / 100 - 1)
    assert t["net"] == pytest.approx(t["gross"] - 0.0006) and t["holding_cost_source"] == "none_long_spot"
    t2 = EV.trade(o, h, l, c, idx, 20, -1, 5, None, "equity")
    assert t2["reason"] == "time" and t2["exit_i"] == 25 and t2["holding_cost_source"] == "estimated_gc_borrow_1pct"
    assert t2["holding_cost"] == pytest.approx(0.01 * 5 / 365.25)
    assert EV.trade(o, h, l, c, idx, n - 3, 1, 5, None, "equity") is None
    d = EV.sequential_daily(o, c, idx, [t, EV.trade(o, h, l, c, idx, 11, 1, 3, None, "equity"), t2])
    assert len(d) == n and np.isfinite(d).all()


# ----------------------------------------------------------------------------- ledger

CFG = "research/v5_labels.py"     # frozen and committed (test P2), so always clean: stands in for a config file


def rec(path, tid, **kw):
    data = path.parent / "data.bin"
    if not data.exists():
        data.write_bytes(b"candles")
    args = dict(hypothesis_id="C1", partitions=["exploration"], config={"x": 1},
                code_files=["research/v5_eval.py"], metrics_requested=["recall"], outcomes_accessed=False,
                config_file=CFG, data_files=[str(data)], path=path)
    args.update(kw)
    return LG.record(tid, **args)


def test_ledger_chain_no_overwrite_and_tamper_detection(tmp_path):
    p = tmp_path / "ledger.jsonl"
    r1 = rec(p, "c1-explore-001")
    rec(p, "c1-explore-002", outcomes_accessed=True)
    first = p.read_text().splitlines()[0]
    with pytest.raises(LG.LedgerError):
        rec(p, "c1-explore-001", config={"x": 2})        # no silent overwrite
    rec(p, "d1-explore-001", hypothesis_id="D1")
    assert p.read_text().splitlines()[0] == first      # append-only
    recs = LG.verify(p)
    assert [r["trial_id"] for r in recs] == ["c1-explore-001", "c1-explore-002", "d1-explore-001"]
    assert recs[1]["prev_hash"] == r1["record_hash"] and recs[1]["outcomes_accessed"] is True
    assert set(recs[0]["code"]) >= {"files", "git_head", "uncommitted_changes"}
    # tamper with an earlier record → verify and record both refuse
    lines = p.read_text().splitlines()
    bad = json.loads(lines[0]); bad["outcomes_accessed"] = True
    p.write_text("\n".join([json.dumps(bad, sort_keys=True)] + lines[1:]) + "\n")
    with pytest.raises(LG.LedgerError):
        LG.verify(p)
    with pytest.raises(LG.LedgerError):
        rec(p, "c1-explore-003")


def test_ledger_rejects_unregistered_hypotheses_and_reserved_partitions(tmp_path):
    p = tmp_path / "l.jsonl"
    with pytest.raises(LG.LedgerError):
        rec(p, "x-001", hypothesis_id="Z9")
    with pytest.raises(LG.LedgerError):
        rec(p, "x-002", partitions=["forward"])
    with pytest.raises(LG.LedgerError):
        rec(p, "x-003", partitions=["reserve_xs"], confirmatory_prereg="reports/NOPE.md")
    with pytest.raises(LG.LedgerError):
        rec(p, "x-004", outcomes_accessed="no")
    assert not p.exists() or p.read_text() == ""


# ----------------------------------------------------------------------------- data guard

def test_guard_refuses_reserved_unknown_and_uncached(monkeypatch, tmp_path):
    with pytest.raises(DG.ReservedDataError):
        DG.load(V5_RESERVE["crypto"][0], "1D")           # a V5 reserve instrument
    with pytest.raises(DG.ReservedDataError):
        DG.load("NOTASYMBOL", "1D")
    # an exploration symbol whose cache is missing must raise, never download
    import hcmtf.data as D
    monkeypatch.setattr(D, "DATA_DIR", tmp_path)
    monkeypatch.setattr(D, "_yahoo", lambda *a, **k: (_ for _ in ()).throw(AssertionError("download attempted")))
    monkeypatch.setattr(D, "_binance", lambda *a, **k: (_ for _ in ()).throw(AssertionError("download attempted")))
    with pytest.raises(DG.ReservedDataError):
        DG.load("SPY", "1D")
    with pytest.raises(DG.ReservedDataError):
        DG.load("BTCUSDT", "4H")


def test_guard_cuts_forward_candles_even_if_the_cache_contains_them(monkeypatch, tmp_path):
    import hcmtf.data as D
    idx = pd.date_range(FREEZE - pd.Timedelta(days=400), FREEZE + pd.Timedelta(days=30), freq="D", tz="UTC")
    df = pd.DataFrame({"open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": 1.0}, index=idx)
    monkeypatch.setattr(D, "DATA_DIR", tmp_path)
    (tmp_path / "SPY_1d.csv.gz").write_text("x")       # cache present
    monkeypatch.setattr(D, "load", lambda sym, tf: df)
    out = DG.load("SPY", "1D")
    closes = idx + pd.Timedelta("1D")
    assert out.index.max() <= FREEZE and len(out) == int((closes <= FREEZE + pd.Timedelta(seconds=1)).sum())
