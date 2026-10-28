"""HC-MTF 6.0 stage 1 (reports/V6_CONT_CONFIG.md): signal definitions, causality, cost
vectorisation, decision rules, gate and a synthetic end-to-end run. Synthetic data only."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf.data import _resample  # noqa: E402
from research import v5_costs as CO, v5_eval as EV, v5_gate as GT, v6_signals as S6  # noqa: E402
from test_engine_v2 import minute_bars  # noqa: E402

spec = importlib.util.spec_from_file_location("v6_cont_explore", ROOT / "scripts" / "v6_cont_explore.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def frames(m15, cut=None):
    m = m15 if cut is None else m15[m15.index + pd.Timedelta(minutes=15) <= cut]
    r = lambda rule: _resample(m, rule, label="left", closed="left")
    ch = r("1h")
    if cut is not None:
        ch = ch[ch.index + pd.Timedelta(hours=1) <= cut]
    return ch, r("4h"), r("1D")


# ----------------------------------------------------------------------------- state machine on hand-built inputs

def _ind(c, h, l, ef, em):
    n = len(c)
    nanless = lambda x: np.asarray(x, float)
    return {"c": nanless(c), "h": nanless(h), "l": nanless(l), "ef": nanless(ef), "em": nanless(em),
            "es": np.zeros(n), "rsi": np.full(n, 50.0), "hist": np.zeros(n), "line": np.zeros(n), "sig": np.zeros(n),
            "atr": np.ones(n), "o": nanless(c)}


def test_model_a_long_start_trigger_one_per_pullback_and_rearm():
    # ef = 10 everywhere, em = 8; trend up throughout
    c = [11, 10.5, 10.2, 10.6, 10.9, 10.4, 10.5, 11.2, 11.5, 9.9, 10.8]
    h = [11.2, 10.8, 10.4, 10.7, 11.0, 10.6, 10.6, 11.3, 11.6, 10.2, 11.0]
    l = [10.5, 10.1, 9.9, 10.3, 10.6, 10.1, 9.8, 10.9, 11.2, 9.7, 10.4]
    n = len(c)
    ind = _ind(c, h, l, [10] * n, [8] * n)
    tr = np.array([S6.UP] * n, object)
    a = S6.model_a(ind, tr, np.zeros(n, bool), 1, W=10)
    # k0 arms (low 10.5 > 10); k2 touches (low 9.9) -> pullback j=2; k3 close 10.6 > 10 and > high[2]=10.4 -> signal (3,2)
    # k4 low 10.6 > 10 re-arms; k6 low 9.8 touches -> j=6; k7 close 11.2 > high[6] -> signal (7,6)
    # k8 re-arms; k9 low 9.7 -> j=9; k10 close 10.8 < high[9]? 10.8 > 10.2 and > 10 -> signal (10,9)
    assert list(map(tuple, a[["i", "j"]].to_numpy())) == [(3, 2), (7, 6), (10, 9)]


def test_model_a_invalidation_window_gap_and_no_rearm_without_leaving_ema():
    n = 8
    ef, em = [10] * n, [8] * n
    # touch at 1, close below EMA_m at 2 -> pullback ends, no trigger; never re-armed (lows stay <= ef) -> no signal
    c = [11, 10.0, 7.5, 10.5, 10.6, 10.7, 10.8, 10.9]
    h = [11.2, 10.3, 9.0, 10.6, 10.7, 10.8, 10.9, 11.0]
    l = [10.5, 9.9, 7.0, 9.5, 9.6, 9.7, 9.8, 9.9]
    a = S6.model_a(_ind(c, h, l, ef, em), np.array([S6.UP] * n, object), np.zeros(n, bool), 1, W=10)
    assert len(a) == 0
    # window: touch at 1, no trigger possible within W=2 (closes below prior highs), trigger at 4 is too late
    c2 = [11, 10.1, 10.0, 9.95, 12.0, 12.0, 12, 12]
    h2 = [11.2, 10.5, 10.4, 10.3, 12.1, 12.1, 12.1, 12.1]
    l2 = [10.5, 9.9, 9.8, 9.7, 11.5, 11.5, 11.5, 11.5]
    a2 = S6.model_a(_ind(c2, h2, l2, ef, em), np.array([S6.UP] * n, object), np.zeros(n, bool), 1, W=2)
    assert len(a2) == 0
    a3 = S6.model_a(_ind(c2, h2, l2, ef, em), np.array([S6.UP] * n, object), np.zeros(n, bool), 1, W=3)
    assert list(a3["i"]) == [4]
    g = np.zeros(n, bool); g[4] = True                                          # gap before the trigger candle
    assert len(S6.model_a(_ind(c2, h2, l2, ef, em), np.array([S6.UP] * n, object), g, 1, W=3)) == 0


def test_short_side_is_its_own_machine():
    n = 5
    c = [9, 9.6, 9.3, 8.5, 8.4]
    h = [9.5, 10.2, 9.8, 9.0, 8.9]
    l = [8.8, 9.4, 9.2, 8.4, 8.3]
    ind = _ind(c, h, l, [10] * n, [12] * n)
    a = S6.model_a(ind, np.array([S6.DOWN] * n, object), np.zeros(n, bool), -1, W=10)
    # k0 armed (high 9.5 < 10); k1 high 10.2 >= 10 -> j=1; k2 close 9.3 < 10 but not < low[1]=9.4? 9.3 < 9.4 -> signal (2,1)
    assert list(map(tuple, a[["i", "j"]].to_numpy())) == [(2, 1)]
    assert len(S6.model_a(ind, np.array([S6.UP] * n, object), np.zeros(n, bool), -1, W=10)) == 0


def test_filters_rsi_macd_extension():
    a = pd.DataFrame({"i": [5], "j": [2]})
    n = 6
    ind = {"rsi": np.array([60, 55, 48, 44, 47, 52.0]), "hist": np.array([0, 0, 0, 0, -1, -0.5]),
           "line": np.zeros(n), "sig": np.zeros(n), "c": np.full(n, 12.0), "em": np.full(n, 10.0), "atr": np.ones(n)}
    f = S6.filters(ind, a, 1, S6.P)
    assert f["B"].iat[0] and f["C"].iat[0] and f["D"].iat[0]                    # min RSI 44 <= 45, 52 >= 50 rising; hist up; ext 2 <= 3
    f2 = S6.filters(dict(ind, c=np.full(n, 13.5)), a, 1, S6.P)
    assert not f2["D"].iat[0]                                                   # ext 3.5 > 3
    f3 = S6.filters(dict(ind, rsi=np.array([60, 55, 48, 46, 47, 52.0])), a, 1, S6.P)
    assert not f3["B"].iat[0] and not f3["C"].iat[0]                            # dip not deep enough; C needs B
    f4 = S6.filters(dict(ind, rsi=np.array([60, 55, np.nan, 44, 47, 52.0])), a, 1, S6.P)
    assert not f4["B"].iat[0]                                                   # undefined input in the window


# ----------------------------------------------------------------------------- causality

@pytest.fixture(scope="module")
def m15():
    return minute_bars(n15=40000, seed=61)


def test_every_config_and_side_is_causal_under_truncation(m15):
    full = frames(m15)[0]
    ref = {(k, s): S6.signals(full, "1H", cfg, s)[0] for k, cfg in S6.CONFIGS.items() for s in (1, -1)}
    assert sum(len(v) for v in ref.values()) > 200                             # not vacuous
    for cut in (m15.index[15001], m15.index[27777], m15.index[39000]):
        part = frames(m15, cut.floor("h"))[0]
        n = len(part)
        for (k, s), r in ref.items():
            got = S6.signals(part, "1H", S6.CONFIGS[k], s)[0]
            exp = r[r["i"] < n]
            # a pullback still open at the cut can only differ in signals at or after the cut
            pd.testing.assert_frame_equal(got.reset_index(drop=True), exp.reset_index(drop=True), check_dtype=False)


def test_signal_module_reads_no_labels_or_evaluator():
    src = (ROOT / "research" / "v6_signals.py").read_text()
    imports = [ln for ln in src.splitlines() if ln.lstrip().startswith(("import ", "from "))]
    assert not any("v5_labels" in ln or "v5_eval" in ln for ln in imports), imports


# ----------------------------------------------------------------------------- costs and timing

def test_vectorised_costs_and_close_times_equal_the_reference():
    idx = pd.date_range("2021-01-01", periods=1500, freq="1h", tz="UTC").delete(range(700, 720))
    ft = pd.date_range("2021-01-01 08:00", "2021-03-30", freq="8h", tz="UTC")
    ft = ft[(ft < pd.Timestamp("2021-01-20", tz="UTC")) | (ft > pd.Timestamp("2021-01-24", tz="UTC"))]
    f = pd.DataFrame({"rate": np.random.default_rng(2).normal(1e-4, 3e-4, len(ft))}, index=ft)
    ct = M.close_times(idx)
    for k in (0, 5, 699, 700, 1000, len(idx) - 1):
        assert ct[k] == EV._close_time(idx, k)
    cost, src = M.short_cost_vector(idx, 30, f)
    for i in list(range(0, 1440, 41)):
        ref, rsrc = CO.short_holding_cost("crypto", idx[i + 1], EV._close_time(idx, i + 30), f)
        assert np.isclose(cost[i], ref, rtol=1e-9, atol=1e-15) and src[i] == rsrc


def test_window_gap_flags_spans_over_125pct():
    idx = pd.date_range("2021-01-01", periods=200, freq="1h", tz="UTC").delete(range(100, 110))
    g = M.window_gap(idx, "1H", 24)
    assert g[80] and not g[10] and not g[150]


# ----------------------------------------------------------------------------- decisions

def _c0(**kw):
    c = {"evaluable": True, "mean": 0.2, "rh_mean": 0.5, "random_entry": {"p97.5": 0.4}, "eq_pair_mean": 0.1, "qualifying_pairs": 9,
         "median_pair": 0.1, "positive_share": 0.6, "altcoin_mean": 0.1, "trim5": 0.05, "drop_best": 0.1, "test": {"ci95": [0.05, 0.3]}}
    c.update(kw)
    return c


def _cd(**kw):
    c = {"evaluable": True, "delta": 0.2, "mean_kept": 0.3, "removal": {"p97.5": 0.25}, "eq_pair_delta": 0.1, "qualifying_pairs": 8,
         "median_pair_delta": 0.05, "positive_share": 0.6, "altcoin_delta": 0.1, "trim5": 0.01, "drop_best": 0.02, "test": {"ci95": [0.01, 0.4]}}
    c.update(kw)
    return c


def test_decision_rules():
    assert M.decide("C0", _c0(), 0.01) == "BEATS BASELINE"
    assert M.decide("C0", _c0(rh_mean=0.4), 0.01) == "INCONCLUSIVE"            # must beat random entry p97.5
    assert M.decide("C0", _c0(trim5=-0.01), 0.01) == "INCONCLUSIVE"
    assert M.decide("C0", _c0(mean=-0.1, eq_pair_mean=-0.1), 0.9) == "NO VALUE"
    assert M.decide("C1", _cd(), 0.049) == "ADDS VALUE"
    for bad in ({"drop_best": 0.0}, {"positive_share": 0.59}, {"qualifying_pairs": 7}, {"altcoin_delta": None}, {"mean_kept": 0.25}):
        assert M.decide("C1", _cd(**bad), 0.01) == "INCONCLUSIVE", bad
    assert M.decide("C2", _cd(evaluable=False), 0.0) == "INCONCLUSIVE (underpowered)"
    assert M.decide("C3", _cd(test={"ci95": [-0.3, -0.01]}, delta=-0.1), 0.9) == "NO VALUE"


def test_families_qualification_and_stage_outcome():
    cells = {M.cell_key(*k): {"evaluable": False} for k in M.cells()}
    assert len(cells) == 112
    k0 = M.cell_key("C0", "P", 1, "1H"); k1 = M.cell_key("C1", "P", 1, "1H"); k2 = M.cell_key("C2", "P", 1, "1H")
    cells[k0] = _c0(p=0.0001); cells[k1] = _cd(p=0.0001); cells[k2] = _cd(p=0.0001)
    d = M.apply_decisions(cells, {("B", 1, "1H"): 0.001, ("C", 1, "1H"): -0.001})
    assert np.isclose(d["cells"][k0]["p_holm_family"], 0.0001 * 20) and np.isclose(d["cells"][k1]["p_holm_family"], 0.0001 * 28)
    assert np.isclose(d["cells"][k2]["p_holm_family"], 0.0001 * 36) and np.isclose(d["cells"][k0]["p_holm_all"], 0.0001 * 112)
    q = d["primary"]["sides"]["+1"]["qualifies"]
    assert q["C0"]["qualifies"] and q["C1"]["qualifies"] and q["C2"]["qualifies"] and not q["C3"]["qualifies"]
    assert d["primary"]["stage"] == "SUCCESS (exploratory)"
    assert [r["model"] for r in d["primary"]["sides"]["+1"]["success_routes"]] == ["B"]     # C fails the trading median
    # MACD cannot qualify without RSI
    cells[k1] = _cd(p=0.9)
    d = M.apply_decisions(cells, {})
    assert not d["primary"]["sides"]["+1"]["qualifies"]["C2"]["qualifies"]
    # an alternative config never rescues the primary
    cells[M.cell_key("C1", "R1", 1, "1H")] = _cd(p=0.0)
    d = M.apply_decisions(cells, {("B", 1, "1H"): 0.01})
    assert not d["primary"]["sides"]["+1"]["qualifies"]["C1"]["qualifies"]
    # a primary pass that fails the all-cell correction is disclosed
    cells[k1] = _cd(p=0.0005)                                                   # x28 = 0.014 passes; x112 = 0.056 fails
    d = M.apply_decisions(cells, {("B", 1, "1H"): 0.01})
    assert d["cells"][k1]["verdict"] == "ADDS VALUE" and d["cells"][k1]["verdict_all_cell_holm"] == "INCONCLUSIVE"
    assert any(x.get("cell") == k1 for x in d["disagreements"])


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


def test_v6_gate(tmp_path):
    waiver = ("External review: UNAVAILABLE\nSelf-audit: COMPLETED\nScope: EXPLORATION ONLY\n"
              "Self-audit report: reports/V5_SELF_AUDIT.md\n")
    base = {GT.BASELINES: "x", GT.MANIFEST: '{"files": {}}', GT.WAIVER: waiver, GT.SELF_AUDIT: "s", **{f: "x" for f in GT.V6_CODE}}
    r1 = tmp_path / "a"; r1.mkdir(); _repo(r1, {**base, GT.V6_CONFIG: "Status: DRAFT\n"})
    assert any(b.startswith("V1") for b in GT.v6_blockers(r1, check_cache=False))
    r2 = tmp_path / "b"; r2.mkdir(); _repo(r2, {**base, GT.V6_CONFIG: "Status: FROZEN\n"})
    assert GT.v6_blockers(r2, check_cache=False) == []
    (r2 / GT.V6_CODE[0]).write_text("changed")
    assert any(b.startswith("V2") for b in GT.v6_blockers(r2, check_cache=False))
    assert GT.confirmatory_blockers(r2)


def test_runner_refuses_when_the_gate_is_closed(monkeypatch):
    monkeypatch.setattr(M.GT, "v6_blockers", lambda *a, **k: ["V1: test"])
    with pytest.raises(M.GT.NotReady):
        M.run()


# ----------------------------------------------------------------------------- end to end (synthetic)

SYMS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "SOLUSDT"]


@pytest.fixture(scope="module")
def synthetic():
    out = {}
    for k, s in enumerate(SYMS):
        m = minute_bars(n15=4 * 24 * 640, seed=300 + k, start="2018-06-01")
        r = lambda rule: _resample(m, rule, label="left", closed="left")
        d1 = r("1D")
        out[s] = {"1H": r("1h"), "4H": r("4h"), "1D": d1, "1W": _resample(d1, "W-MON", label="left", closed="left")}
    return out


def test_runner_pipeline_on_synthetic_data(monkeypatch, synthetic, tmp_path):
    monkeypatch.setattr(M.DG, "load", lambda sym, tf: synthetic[sym][tf])
    monkeypatch.setattr(M.DG, "load_funding", lambda sym: None)
    monkeypatch.setattr(M.X, "perp_start", lambda sym: pd.Timestamp("2018-06-01", tz="UTC") if sym == "ETHUSDT" else None)
    monkeypatch.setattr(M, "UNIVERSE", tuple(SYMS))
    monkeypatch.setattr(M, "START", pd.Timestamp("2019-07-01", tz="UTC"))
    monkeypatch.setattr(M, "REPS_RAND", 5)
    liq, first = M.prepare()
    results = [M.worker((s, tf, liq[s], first[s])) for tf in M.TFS for s in SYMS]
    U = pd.concat([r["units"] for r in results], ignore_index=True)
    assert U["in_S"].any() and (U["trade_status"] == "ok").any()
    assert not U.loc[U["eligible"], "t"].lt(M.START).any()
    ok = U[U["trade_status"] == "ok"]
    assert ((ok["slip"] == M.SLIP_TOP) | (ok["slip"] == M.SLIP_REST)).all()
    ev = M.evaluate(results, reps_wild=99, reps_removal=10)
    assert len(ev["cells"]) == 112 and set(ev["decisions"]["cells"]) == set(ev["cells"])
    ev["meta"] = {"mode": "synthetic-test", "config": M.CONFIG, "universe": SYMS, "manifest_combined_sha256": "0" * 64, "git_head": "0" * 40}
    for k, v in (("OUT", tmp_path / "r.json"), ("MD", tmp_path / "r.md"), ("MD_PAIRS", tmp_path / "p.md")):
        monkeypatch.setattr(M, k, v)
    (tmp_path / "r.json").write_text(json.dumps(M._clean(ev), default=str))
    M.render()
    md = (tmp_path / "r.md").read_text()
    assert "EXPLORATORY ONLY" in md and "Holm across all 112 cells" in md
