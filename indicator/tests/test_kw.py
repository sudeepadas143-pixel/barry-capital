"""KW weekly engine (reports/KW_CONFIG.md): causality, asymmetric BUY/SELL gates, TSMOM definition,
cluster repeats, gate. Synthetic data only."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kenny_sim as KSIM, kenny_weekly as KWK, v5_gate as GT  # noqa: E402
from test_cycle_engine import daily, rs  # noqa: E402

SPEC = json.loads((ROOT / "reports" / "cycle2_model_spec.json").read_text())


def _w(seed=9):
    return rs(daily("2000-01-01", "2026-10-01", seed=seed), "W-MON")


def test_tsmom_is_the_normalised_sum_of_return_signs():
    c = np.r_[np.arange(1.0, 60.0), np.arange(59.0, 40.0, -1)]
    s = KWK.tsmom(c, 52)
    assert np.isnan(s[51]) and s[52] == 52 / np.sqrt(52)
    assert abs(s[-1] - np.sign(np.diff(c))[-52:].sum() / np.sqrt(52)) < 1e-12


def test_weekly_signals_are_causal_under_truncation():
    w = _w()
    st = KSIM.states(w, "1W", SPEC)
    for v in ("W1", "W2"):
        full = KWK.run(KWK.evidence(w, st, v), 8, {"bot": 1.5, "top": 1.5})
        for cut in (700, 1100):
            part_w = w.iloc[:cut]
            part = KWK.run(KWK.evidence(part_w, KSIM.states(part_w, "1W", SPEC), v), 8, {"bot": 1.5, "top": 1.5})
            for k in (0, 1):
                assert np.array_equal(part[k], full[k][full[k] < cut]), (v, k)


def test_buy_and_sell_logic_are_asymmetric_and_never_share_a_candle():
    w = _w(4)
    st = KSIM.states(w, "1W", SPEC)
    ev = KWK.evidence(w, st, "W2")
    assert set(ev["bot"]["fam"]) != set(ev["top"]["fam"])
    assert "dd" in ev["bot"]["fam"] and "rally" in ev["top"]["fam"]
    b, s, _ = KWK.run(ev, 8, {"bot": 1.0, "top": 1.0})
    assert len(np.intersect1d(b, s)) == 0
    b2, s2, _ = KWK.run(ev, 8, {"bot": 1.0, "top": 99.0})                 # thresholds are per side
    assert len(s2) == 0 and len(b2) >= len(b)


def test_kw_gate(tmp_path):
    import subprocess
    w = "External review: UNAVAILABLE\nSelf-audit: COMPLETED\nScope: EXPLORATION ONLY\nSelf-audit report: reports/V5_SELF_AUDIT.md\n"
    files = {GT.BASELINES: "x", GT.MANIFEST: '{"files": {}}', GT.WAIVER: w, GT.SELF_AUDIT: "s", GT.KW_CONFIG: "Status: FROZEN\n",
             **{f: "x" for f in GT.KW_CODE}}
    for cmd in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], cwd=tmp_path, check=True)
    for rel, t in files.items():
        p = tmp_path / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=tmp_path, check=True)
    assert GT.kw_blockers(tmp_path, check_cache=False) == []
    (tmp_path / "research" / "kenny_weekly.py").write_text("changed")
    assert any(b.startswith("Y2") for b in GT.kw_blockers(tmp_path, check_cache=False))


def test_kw2_sell_guard_and_percentile_buy_are_causal_and_asset_agnostic():
    w = _w(6)
    st = KSIM.states(w, "1W", SPEC)
    full_s = KWK.kw2_sell(w, st, "X1", 4.0)
    full_b = KWK.kw2_buy(w, st, "Y1", 0.05)
    assert set(full_b) >= set(st["bot"]["K_H"])                          # Y1 keeps every current BUY
    dd = KWK.drawdown_atr(w)
    assert not (dd[full_s] >= 4.0).any()                                 # guard removes SELLs deep in a drawdown
    cut = 900
    pw = w.iloc[:cut]
    pst = KSIM.states(pw, "1W", SPEC)
    assert np.array_equal(KWK.kw2_sell(pw, pst, "X1", 4.0), full_s[full_s < cut])
    assert np.array_equal(KWK.kw2_buy(pw, pst, "Y1", 0.05), full_b[full_b < cut])
    w2 = w.copy()
    w2[["open", "high", "low", "close"]] *= 37.0                          # price scale does not change signals
    st2 = KSIM.states(w2, "1W", SPEC)
    assert np.array_equal(KWK.kw2_buy(w2, st2, "Y2", 0.05), KWK.kw2_buy(w, st, "Y2", 0.05))
