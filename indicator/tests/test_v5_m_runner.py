"""Workstream M runner (scripts/v5_m_explore.py) on SYNTHETIC data: cost/time vectorisation
equals the reference code, the frozen §9 decision rules are applied mechanically, and the
pipeline runs end to end. Nothing here reads real outcomes."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf.data import _resample  # noqa: E402
from research import v5_baselines as B, v5_costs as CO, v5_eval as EV, v5_state as ST  # noqa: E402
from test_engine_v2 import minute_bars  # noqa: E402

spec = importlib.util.spec_from_file_location("v5_m_explore", ROOT / "scripts" / "v5_m_explore.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


# ----------------------------------------------------------------------------- vectorisation

def test_close_times_equal_v5_eval():
    idx = pd.date_range("2021-01-01", periods=300, freq="1h", tz="UTC").delete([50, 51, 52, 200])
    ct = M.close_times(idx)
    for k in (0, 1, 49, 50, 120, 196, len(idx) - 1):
        assert ct[k] == EV._close_time(idx, k), k


def test_short_cost_vector_equals_v5_costs_including_funding_gaps():
    idx = pd.date_range("2021-01-01", periods=2000, freq="1h", tz="UTC").delete(range(900, 930))
    ft = pd.date_range("2021-01-01 08:00", "2021-03-30", freq="8h", tz="UTC")
    ft = ft[(ft < pd.Timestamp("2021-01-30", tz="UTC")) | (ft > pd.Timestamp("2021-02-03", tz="UTC"))]   # 4-day hole
    f = pd.DataFrame({"rate": np.random.default_rng(1).normal(1e-4, 3e-4, len(ft))}, index=ft)
    for hold in (24, 30):
        cost, src = M.short_cost_vector(idx, hold, f)
        for i in list(range(0, 1900, 37)) + [len(idx) - hold - 1]:
            ref, rsrc = CO.short_holding_cost("crypto", idx[i + 1], EV._close_time(idx, i + hold), f)
            assert np.isclose(cost[i], ref, rtol=1e-9, atol=1e-15) and src[i] == rsrc, (hold, i)
        assert np.isnan(cost[len(idx) - hold:]).all()
        assert {"observed_funding", "estimated_crypto_10pct"} <= set(src[: len(idx) - hold])
    c2, s2 = M.short_cost_vector(idx, 24, None)
    assert set(s2[:-24]) == {"estimated_crypto_10pct"}


def test_engine_reversal_signal_equals_the_baseline_module():
    m = minute_bars(n15=24000, seed=4)
    r = lambda rule: _resample(m, rule, label="left", closed="left")
    df, h1, h2 = r("1h"), r("4h"), r("1D")
    sig = M.engine_signals(df, h1, h2, "1H")
    for side in (1, -1):
        assert list(sig[(M.REV, side)]) == list(B.counter_reversal(df, h1, h2, "1H", side))
        assert len(sig[("S-eng", side)]) > 0


# ----------------------------------------------------------------------------- §9 decisions

def _cell(**kw):
    c = {"evaluable": True, "delta": 0.1, "eq_weight_delta": 0.05, "qualifying_pairs": 10, "median_pair_delta": 0.02,
         "positive_pair_share": 0.6, "mean_K": 0.2, "removal": {"p97.5": 0.15}, "altcoin_delta": 0.01,
         "test_calendar": {"ci95": [0.01, 0.2]}, "test_episode": {"ci95": [0.0, 0.2]}}
    c.update(kw)
    return c


def test_cell_decision_rules_are_mechanical():
    assert M.decide(_cell(), 0.04) == "ADDS VALUE"
    assert M.decide(_cell(), 0.05) == "INCONCLUSIVE"                       # Holm p must be < 0.05
    assert M.decide(_cell(positive_pair_share=0.59), 0.01) == "INCONCLUSIVE"   # 60% rule
    assert M.decide(_cell(qualifying_pairs=7), 0.01) == "INCONCLUSIVE"         # >= 8 qualifying pairs
    assert M.decide(_cell(altcoin_delta=None), 0.01) == "INCONCLUSIVE"         # altcoin tier must be defined
    assert M.decide(_cell(altcoin_delta=-0.01), 0.01) == "INCONCLUSIVE"
    assert M.decide(_cell(mean_K=0.15), 0.01) == "INCONCLUSIVE"                # must beat removal p97.5
    assert M.decide(_cell(eq_weight_delta=0.0), 0.01) == "INCONCLUSIVE"
    assert M.decide(_cell(delta=-0.1, eq_weight_delta=-0.01), 0.9) == "NO VALUE"
    assert M.decide(_cell(test_episode={"ci95": [-0.3, -0.01]}, delta=0.01), 0.9) == "NO VALUE"
    assert M.decide(_cell(evaluable=False), 0.0) == "NOT EVALUABLE"


def test_hypothesis_verdicts_and_holm_scopes():
    v = {"M-B1|S-ema|+1|1H": "ADDS VALUE", "M-B1|S-ema|+1|4H": "INCONCLUSIVE"}
    assert M.hypothesis_verdict(v) == "SUPPORTED"
    v["M-B1|S-ema|+1|4H"] = "NO VALUE"
    assert M.hypothesis_verdict(v) == "INCONCLUSIVE"
    assert M.hypothesis_verdict({"a|b|+1|1H": "NO VALUE", "a|b|+1|4H": "NOT EVALUABLE"}) == "REJECTED"
    assert M.hypothesis_verdict({"a|b|+1|1H": "NOT EVALUABLE"}) == "NOT EVALUABLE"
    # Holm: non-evaluable cells enter with p = 1 and keep the family size fixed
    cells = {M.cell_key(h, s, d, tf): _cell(p_decisive=0.001) for h, s, d in M.cells() for tf in ("1H", "4H")}
    assert len(cells) == 36
    for k in list(cells)[1:]:
        cells[k] = _cell(evaluable=False, p_decisive=None)
    d = M.apply_decisions(cells)
    k0 = list(cells)[0]
    fam = sum(1 for k in cells if k.startswith(k0.split("|")[0] + "|"))
    assert np.isclose(d["cells"][k0]["p_holm_within"], 0.001 * fam)
    assert np.isclose(d["cells"][k0]["p_holm_all"], 0.001 * 36)
    assert d["cells"][k0]["verdict"] == "ADDS VALUE" and d["cells"][k0]["verdict_all_cell_holm"] == "ADDS VALUE"
    cells[k0] = _cell(p_decisive=0.004)                    # passes within (x8 = 0.032), fails across 36 (0.144)
    d = M.apply_decisions(cells)
    assert d["cells"][k0]["verdict"] == "ADDS VALUE" and d["cells"][k0]["verdict_all_cell_holm"] == "INCONCLUSIVE"
    assert any(x.get("cell") == k0 for x in d["disagreements"])


# ----------------------------------------------------------------------------- end to end (synthetic)

SYMS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "SOLUSDT"]


@pytest.fixture(scope="module")
def synthetic():
    out = {}
    for k, s in enumerate(SYMS):
        m = minute_bars(n15=4 * 24 * 640, seed=200 + k, start="2018-06-01")
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
    monkeypatch.setattr(M, "REPS_THIN", 3)
    results, eps = [], {}
    for tf in M.TFS:
        btc, liq, first = M.prepare(tf)
        eps.update(M.episodes_for(btc, tf))
        results += [M.worker((s, tf, btc, liq[s], first[s])) for s in SYMS]
    U = pd.concat([r["units"] for r in results], ignore_index=True)
    assert U["eligible"].any() and U["in_S"].any()
    assert (U.loc[(U["sym"] != "BTCUSDT") & U["eligible"], "btc_dir"] != M.X.UNAVAILABLE).all()   # E7 enforced
    assert not U.loc[U["eligible"], "t"].lt(M.START).any()
    ev = M.evaluate(results, eps, reps_wild=99, reps_removal=10)
    assert len(ev["stage_b"]) == 36 and set(ev["decisions"]["hypotheses"]) == {"M-B1", "M-B2", "M-B3", "M-B4"}
    assert all(v["verdict"] in ("ADDS VALUE", "NO VALUE", "INCONCLUSIVE", "NOT EVALUABLE") for v in ev["decisions"]["cells"].values())
    for k in ev["stage_b"]:
        assert f"B|{k}" in ev["trading"]
    ev["meta"] = {"mode": "synthetic-test", "config": M.CONFIG, "universe": SYMS, "manifest_combined_sha256": "0" * 64, "git_head": "0" * 40}
    monkeypatch.setattr(M, "OUT", tmp_path / "r.json")
    monkeypatch.setattr(M, "MD", tmp_path / "r.md")
    monkeypatch.setattr(M, "MD_PAIRS", tmp_path / "p.md")
    (tmp_path / "r.json").write_text(json.dumps(M._clean(ev), default=str))
    M.render()
    md = (tmp_path / "r.md").read_text()
    assert "EXPLORATORY ONLY" in md and "Holm across all 36 cells" in md and "BTC episodes" in md


def test_runner_refuses_when_the_gate_is_closed(monkeypatch):
    monkeypatch.setattr(M.GT, "m_blockers", lambda *a, **k: ["M1: test"])
    with pytest.raises(M.GT.NotReady):
        M.run()
