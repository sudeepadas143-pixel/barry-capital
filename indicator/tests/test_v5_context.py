"""Workstream M context module and difference test (reports/V5_M_B_CONFIG.md §1.1, §2, §5, §7,
§10). Synthetic data only."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf.data import _resample  # noqa: E402
from research import v5_context as X, v5_gate as GT, v5_inference as INF, v5_state as ST  # noqa: E402
from test_engine_v2 import minute_bars  # noqa: E402


def frames(m15, cut=None):
    m = m15 if cut is None else m15[m15.index + pd.Timedelta(minutes=15) <= cut]
    r = lambda rule: _resample(m, rule, label="left", closed="left")
    ch = r("1h")
    if cut is not None:
        ch = ch[ch.index + pd.Timedelta(hours=1) <= cut]
    return ch, r("4h"), r("1D")


# ----------------------------------------------------------------------------- BTC context, E7

def _btc_state(idx, labels, vol, warm=None):
    return pd.DataFrame({"direction_label": np.asarray(labels, object), "vol_regime": np.asarray(vol, object),
                         "warm": np.ones(len(idx), bool) if warm is None else np.asarray(warm, bool)}, index=idx)


def test_btc_context_aligns_by_identical_open_time_and_never_maps_missing_to_neutral():
    bidx = pd.date_range("2021-01-01", periods=6, freq="1h", tz="UTC")
    st = _btc_state(bidx, ["bull", "bear", "neutral", "unknown", "bull", "bear"], ["high", "low", "mid", "mid", "unknown", "high"],
                    warm=[True, True, True, False, False, True])
    tidx = bidx.delete(5).append(pd.DatetimeIndex([bidx[5] + pd.Timedelta(minutes=30)]))   # last target has no BTC row
    ctx = X.btc_context(tidx, st)
    assert list(ctx["available"]) == [True, True, True, False, False, False]
    assert list(ctx["btc_dir"]) == ["bull", "bear", "neutral", X.UNAVAILABLE, X.UNAVAILABLE, X.UNAVAILABLE]
    assert list(ctx["btc_unstable"]) == ["yes", "no", "no", X.UNAVAILABLE, X.UNAVAILABLE, X.UNAVAILABLE]


def test_gates_never_keep_unavailable_and_follow_the_config():
    v = np.array(["bull", "bear", "neutral", X.UNAVAILABLE], object)
    assert list(X.gate("M-B1", v, 1)) == [True, False, False, False]
    assert list(X.gate("M-B2", v, -1)) == [False, True, False, False]
    assert list(X.gate("M-B4", v, -1)) == [False, True, True, False]          # tops: BTC not bull
    assert list(X.gate("M-B4", v, 1)) == [True, False, True, False]           # bottoms: BTC not bear
    assert list(X.gate("M-B3", np.array(["no", "yes", X.UNAVAILABLE], object), 1)) == [True, False, False]


# ----------------------------------------------------------------------------- liquidity, E1-E7

def _h1(start, days, qv_per_candle=1.0, drop=()):
    idx = pd.date_range(start, periods=24 * days, freq="1h", tz="UTC")
    df = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": float(qv_per_candle)}, index=idx)
    return df.drop(index=[idx[k] for k in drop])


def test_daily_quote_skips_the_partial_first_day_and_missing_candles_add_zero():
    h = _h1("2021-01-01 05:00", 3, 2.0, drop=(30,))
    dq = X.daily_quote(h)
    assert dq.index[0] == pd.Timestamp("2021-01-02", tz="UTC")                # 01-01 is partial
    assert dq.loc["2021-01-02", "qv"] == 2.0 * 23 and dq.loc["2021-01-02", "n"] == 23     # one candle missing


def test_liquidity_rank_median_window_and_tie_break():
    syms = list(X.TARGETS[:3])
    h = {syms[0]: _h1("2021-01-01", 40, 10.0), syms[1]: _h1("2021-01-01", 40, 10.0), syms[2]: _h1("2021-01-01", 40, 20.0)}
    p = X.liquidity_panel(h)
    d29, d30 = pd.Timestamp("2021-01-29", tz="UTC"), pd.Timestamp("2021-01-30", tz="UTC")
    assert np.isnan(p[syms[0]].loc[d29, "med30"]) and p[syms[0]].loc[d30, "med30"] == 240.0
    assert p[syms[2]].loc[d30, "rank"] == 1
    first, second = sorted(syms[:2])
    assert p[first].loc[d30, "rank"] == 2 and p[second].loc[d30, "rank"] == 3      # ties by symbol name
    assert p[syms[0]].loc[d30, "n30"] == 720


def test_reference_day_is_the_last_day_ended_by_the_open():
    t = pd.DatetimeIndex(["2021-03-10 00:00", "2021-03-10 23:00"], tz="UTC")
    assert list(X.reference_day(t)) == [pd.Timestamp("2021-03-09", tz="UTC")] * 2


def test_eligibility_rules_and_first_fail_order():
    sym = X.TARGETS[0]
    idx = pd.date_range("2022-02-01", periods=5, freq="1h", tz="UTC")
    D = X.reference_day(idx)[0]
    liq = pd.DataFrame({"med30": [6e6], "n30": [700.0], "rank": [3.0]}, index=pd.DatetimeIndex([D]))
    first = pd.Timestamp("2021-01-01", tz="UTC")
    warm = [True, False, True, True, True]
    avail = [True, True, False, True, True]
    e = X.eligibility(sym, idx, first, liq, warm, avail)
    assert list(e["eligible"]) == [True, False, False, True, True]
    assert list(e["first_fail"]) == ["", "E6", "E7", "", ""]
    e2 = X.eligibility(sym, idx, first, liq.assign(rank=26.0, n30=600.0), warm, avail)
    assert e2["first_fail"].iat[0] == "E3"                                    # E3 before E4
    e3 = X.eligibility(sym, idx, pd.Timestamp("2021-06-01", tz="UTC"), liq, warm, avail)
    assert e3["first_fail"].iat[0] == "E1"
    with pytest.raises(ValueError):
        X.eligibility(sym, idx, first, liq, warm, None)                       # E7 needs the BTC context
    with pytest.raises(Exception):
        X.eligibility("NOTASYMBOL", idx, first, liq, warm, avail)


def test_context_and_eligibility_are_causal_under_truncation():
    """BTC regime and every E-rule at candle i are unchanged when all data after i are removed
    from BOTH the BTC and the target series (§10.1)."""
    bm, tm = minute_bars(n15=4 * 24 * 420, seed=5, start="2021-01-01"), minute_bars(n15=4 * 24 * 420, seed=6, start="2021-01-01")
    sym = X.TARGETS[0]

    def compute(cut):
        b, b4, b1 = frames(bm, cut)
        t, t4, t1 = frames(tm, cut)
        bst = ST.classify(b, b4, b1)
        tst = ST.classify(t, t4, t1)
        ctx = X.btc_context(t.index, bst)
        liq = X.liquidity_panel({sym: t, X.BTC: b})[sym]
        el = X.eligibility(sym, t.index, t.index[0], liq, tst["warm"].to_numpy(), ctx["available"].to_numpy())
        return ctx, el

    full_ctx, full_el = compute(None)
    for cut in (pd.Timestamp("2021-09-17 13:00", tz="UTC"), pd.Timestamp("2022-01-29 07:00", tz="UTC")):
        c, e = compute(cut)
        n = len(c)
        pd.testing.assert_frame_equal(c, full_ctx.iloc[:n])
        pd.testing.assert_frame_equal(e.drop(columns="rank"), full_el.iloc[:n].drop(columns="rank"))
    assert full_el["eligible"].sum() > 1000 and full_ctx["available"].sum() > 1000     # not vacuous


# ----------------------------------------------------------------------------- episodes

def test_episode_merging_rules():
    t = pd.date_range("2021-01-01", periods=14, freq="1h", tz="UTC")
    v = ["a", "a", "b", "b", "b", "b", "c", "b", "b", "b", "a", "a", "a", "a"]
    ids, tab = X.episodes(t, v, H=3)
    # run "a"(2) is a leading short run -> prepended to "b"(4); "c"(1) short -> appended to it;
    # "b"(3) opens a new episode; "a"(4) another
    assert list(ids) == [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2]
    assert list(tab["value"]) == ["b", "b", "a"] and list(tab["length"]) == [7, 3, 4] and list(tab["runs"]) == [3, 1, 1]
    ids2, tab2 = X.episodes(t[:3], ["a", "b", "a"], H=5)                       # all short: one episode
    assert list(ids2) == [0, 0, 0] and tab2["value"].iat[0] == "a"


# ----------------------------------------------------------------------------- matched removal

def test_matched_removal_draws_exact_counts_per_stratum():
    strata = np.array(["p|bull"] * 50 + ["p|bear"] * 30 + ["q|bull"] * 20)
    kept = np.zeros(100, bool)
    kept[[0, 1, 2, 3, 50, 51, 80]] = True                          # 4, 2, 1 per stratum
    # x = stratum code: every replicate mean equals the kept composition exactly
    code = {"p|bull": 1.0, "p|bear": 10.0, "q|bull": 100.0}
    x = np.array([code[s] for s in strata])
    m = X.matched_removal_means(x, strata, kept, reps=30, seed=1)
    assert np.allclose(m, (4 * 1 + 2 * 10 + 1 * 100) / 7)
    y = np.random.default_rng(0).normal(size=100)
    a, b = X.matched_removal_means(y, strata, kept, 30, 7), X.matched_removal_means(y, strata, kept, 30, 7)
    assert np.array_equal(a, b) and a.std() > 0


def test_context_module_reads_no_labels_or_outcomes():
    src = (ROOT / "research" / "v5_context.py").read_text()
    imports = [ln for ln in src.splitlines() if ln.lstrip().startswith(("import ", "from "))]
    assert not any("v5_labels" in ln or "v5_eval" in ln for ln in imports), imports


# ----------------------------------------------------------------------------- difference test

def test_cluster_diff_test_matches_the_explicit_sandwich():
    rng = np.random.default_rng(3)
    cl = np.repeat(np.arange(25), 40)
    k = rng.random(1000) < 0.35
    x = rng.normal(size=1000) + 0.2 * k + np.repeat(rng.normal(0, 0.5, 25), 40)
    r = INF.cluster_diff_test(x, k, cl, reps=499)
    assert np.isclose(r["delta"], x[k].mean() - x[~k].mean())
    X_ = np.c_[np.ones(1000), k]
    b = np.linalg.lstsq(X_, x, rcond=None)[0]
    e = x - X_ @ b
    A = np.linalg.inv(X_.T @ X_)
    meat = sum(np.outer(X_[cl == g].T @ e[cl == g], X_[cl == g].T @ e[cl == g]) for g in range(25))
    assert np.isclose(np.sqrt((25 / 24 * A @ meat @ A)[1, 1]), r["se_cr1"])
    assert r["valid"] and r["wild_weights"] == "rademacher"
    assert INF.cluster_diff_test(x, np.ones(1000, bool), cl)["valid"] is False


def test_cluster_diff_test_holds_size_when_the_gate_is_constant_within_time_clusters():
    """Null: no gate effect, but heavy period shocks shared by every pair in a cluster, and the
    gate switches only between clusters (as a BTC regime does). Pairs are not independent."""
    rng = np.random.default_rng(0)
    rej = 0
    sims = 200
    for s in range(sims):
        G_, pairs, per = 20, 15, 6
        shock = rng.standard_t(3, G_)
        gate_c = rng.random(G_) < 0.5
        cl = np.repeat(np.arange(G_), pairs * per)
        x = shock[cl] + rng.normal(0, 1, len(cl))
        r = INF.cluster_diff_test(x, gate_c[cl], cl, reps=199, seed=s)
        rej += r.get("p_wild", 1) < 0.05
    assert rej / sims <= 0.09


# ----------------------------------------------------------------------------- gate

def _repo(tmp: Path, files: dict):
    for cmd in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], cwd=tmp, check=True)
    for rel, text in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=tmp, check=True)


WAIVER = ("External review: UNAVAILABLE\nSelf-audit: COMPLETED\nScope: EXPLORATION ONLY\n"
          "Self-audit report: reports/V5_SELF_AUDIT.md\n")


def test_m_gate_needs_a_frozen_config_and_committed_code(tmp_path):
    base = {GT.BASELINES: "x", GT.MANIFEST: '{"files": {}}', GT.WAIVER: WAIVER, GT.SELF_AUDIT: "s",
            **{f: "x" for f in GT.M_CODE}}
    r1 = tmp_path / "r1"; r1.mkdir()
    _repo(r1, {**base, GT.M_CONFIG: "Status: DRAFT\n"})
    assert any(b.startswith("M1") for b in GT.m_blockers(r1, check_cache=False))
    r2 = tmp_path / "r2"; r2.mkdir()
    _repo(r2, {**base, GT.M_CONFIG: "Status: FROZEN\n"})
    assert GT.m_blockers(r2, check_cache=False) == []
    (r2 / GT.M_CODE[0]).write_text("changed")                                  # uncommitted change
    assert any(b.startswith("M2") for b in GT.m_blockers(r2, check_cache=False))
    assert GT.confirmatory_blockers(r2)                                        # never unlocked by the waiver
