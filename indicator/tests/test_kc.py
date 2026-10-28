"""KC cluster layer (reports/KC_CONFIG.md): causality, redundancy, decay, opposite evidence, no
simultaneous BUY/SELL, gate, and the Python twin of the shipped signals. Synthetic data only."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kenny_cluster as KC, kenny_sim as KSIM, v5_gate as GT  # noqa: E402
from test_cycle_engine import daily, rs  # noqa: E402

SPEC = json.loads((ROOT / "reports" / "cycle2_model_spec.json").read_text())


def _ev(n, **fam):
    z = {f: np.zeros(n) for f in KC.FAMS}
    out = {"trend": np.zeros(n), "top": {**z, "active": np.ones(n, bool)}, "bot": {**{f: np.zeros(n) for f in KC.FAMS}, "active": np.ones(n, bool)}}
    for key, (d, idx, val) in fam.items():
        out[d][key.split("_")[0]][idx] = val
    return out


def test_redundant_repeats_add_less_than_new_independent_evidence():
    n = 12
    rep = _ev(n, div_a=("bot", [2, 3, 4], 1.0))                      # same family three candles running
    new = _ev(n, div_a=("bot", [2], 1.0), pa_b=("bot", [3], 1.0), vv_c=("bot", [4], 1.0))
    _, _, s_rep = KC.run_clusters(rep, "1D", 1 / 8, 99.0, True)
    _, _, s_new = KC.run_clusters(new, "1D", 1 / 8, 99.0, True)
    assert s_new["bot"][4] > s_rep["bot"][4] + 1.0
    assert s_rep["bot"][4] <= KC.WEIGHTS["div"] + 1e-9                 # bounded by the family weight
    _, _, s_off = KC.run_clusters(rep, "1D", 1 / 8, 99.0, False)
    assert s_off["bot"][4] > s_rep["bot"][4]                            # control: plain sum keeps growing


def test_decay_and_opposite_evidence_weaken_the_cluster():
    a = _ev(30, div_a=("bot", [2], 1.0))
    _, _, s = KC.run_clusters(a, "1D", 1 / 8, 99.0, True)
    hl = 63 / 8
    assert abs(s["bot"][2 + 8] / s["bot"][2] - 0.5 ** (8 / hl)) < 1e-9
    b = _ev(30, div_a=("bot", [2], 1.0), div_b=("top", [3], 1.0))
    _, _, s2 = KC.run_clusters(b, "1D", 1 / 8, 99.0, True)
    assert s2["bot"][3] < s["bot"][3]


def test_every_qualifying_candle_signals_and_sides_never_share_a_candle():
    e = _ev(20, ext_a=("bot", [3], 1.0), div_a=("bot", [4], 1.0), pa_a=("bot", [5], 1.0), ext_b=("top", [5], 1.0))
    buy, sell, sc = KC.run_clusters(e, "1D", 1 / 8, 1.5, True)
    assert list(buy) == [4, 5] and len(np.intersect1d(buy, sell)) == 0   # repeats allowed, no cooldown
    e2 = _ev(20, ext_a=("bot", [3], 1.0), div_a=("bot", [4], 1.0))
    e2["bot"]["active"][:] = False                                     # outside Kenny's zone nothing qualifies
    assert len(KC.run_clusters(e2, "1D", 1 / 8, 1.5, True)[0]) == 0


def test_evidence_and_clusters_are_causal_under_truncation():
    d = daily("2012-01-01", "2020-12-31", 11)
    w = rs(d, "W-MON")
    full_st = KSIM.states(d, "1D", SPEC)
    full = KC.run_clusters(KC.evidence(d, "1D", full_st, w), "1D", 1 / 8, 1.5, True)
    for cut in (1200, 2500):
        part_d = d.iloc[:cut]
        st = KSIM.states(part_d, "1D", SPEC)
        part = KC.run_clusters(KC.evidence(part_d, "1D", st, w[w.index <= part_d.index[-1]]), "1D", 1 / 8, 1.5, True)
        for k in (0, 1):
            assert np.array_equal(part[k], full[k][full[k] < cut])


def test_kc_gate(tmp_path):
    import subprocess
    w = "External review: UNAVAILABLE\nSelf-audit: COMPLETED\nScope: EXPLORATION ONLY\nSelf-audit report: reports/V5_SELF_AUDIT.md\n"
    files = {GT.BASELINES: "x", GT.MANIFEST: '{"files": {}}', GT.WAIVER: w, GT.SELF_AUDIT: "s", GT.KC_CONFIG: "Status: FROZEN\n",
             **{f: "x" for f in GT.KC_CODE}}
    for cmd in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], cwd=tmp_path, check=True)
    for rel, t in files.items():
        p = tmp_path / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=tmp_path, check=True)
    assert GT.kc_blockers(tmp_path, check_cache=False) == []
    (tmp_path / "research" / "kenny_cluster.py").write_text("changed")
    assert any(b.startswith("Y2") for b in GT.kc_blockers(tmp_path, check_cache=False))
