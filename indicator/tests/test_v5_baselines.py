"""Baselines, matched-frequency thinning, small-cluster inference, data manifest and readiness gate.

Synthetic data only (the manifest test reads cached files for hashes and timestamps, never
outcomes)."""

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf.data import _resample  # noqa: E402
from research import v5_baselines as B, v5_gate as GT, v5_inference as INF, v5_manifest as MF, v5_state as ST  # noqa: E402
from research.v41 import cluster_id  # noqa: E402
from test_engine_v2 import minute_bars  # noqa: E402


def frames(m15, cut=None):
    m = m15 if cut is None else m15[m15.index + pd.Timedelta(minutes=15) <= cut]
    r = lambda rule: _resample(m, rule, label="left", closed="left")
    ch = r("1h")
    if cut is not None:
        ch = ch[ch.index + pd.Timedelta(hours=1) <= cut]
    return ch, r("4h"), r("1D")


@pytest.fixture(scope="module")
def m15():
    return minute_bars(n15=24000, seed=21)


# ----------------------------------------------------------------------------- baselines

def _all(ch, h1, h2, side):
    return B.generate(ch, h1, h2, ST.classify(ch, h1, h2), "1H", side)


def test_baselines_fire_on_both_sides_and_are_unique_sorted(m15):
    ch, h1, h2 = frames(m15)
    for side in (-1, 1):
        out = _all(ch, h1, h2, side)
        assert set(out) == set(B.BASELINES)
        for name, idx in out.items():
            assert len(idx) > 0, (name, side)
            assert (np.diff(idx) > 0).all()            # one alert per candle, sorted
    with pytest.raises(ValueError):
        B.htf_flip(ST.classify(ch, h1, h2), 0)


def test_baselines_are_causal_under_truncation(m15):
    ch, h1, h2 = frames(m15)
    full = {s: _all(ch, h1, h2, s) for s in (-1, 1)}
    for cut in (m15.index[9001], m15.index[15555]):
        cut = cut.floor("h")
        c2, a2, b2 = frames(m15, cut)
        n = len(c2)
        for s in (-1, 1):
            part = _all(c2, a2, b2, s)
            for name in B.BASELINES:
                assert list(part[name]) == [i for i in full[s][name] if i < n], (name, s, cut)


def test_htf_flip_ignores_warmup_transitions_and_counts_real_flips():
    lab = np.array(["unknown", "unknown", "bear", "bear", "neutral", "bear", "bull", "bear", "bear"], object)
    st = pd.DataFrame({"direction_label": lab})
    assert list(B.htf_flip(st, -1)) == [5, 7]          # not 2 (that is unknown -> bear)
    assert list(B.htf_flip(st, 1)) == [6]


# ----------------------------------------------------------------------------- matched frequency

def _idx(n=2000):
    return pd.date_range("2022-01-01", periods=n, freq="4h", tz="UTC")


def test_thinning_matches_per_block_never_pads_and_is_reproducible():
    idx = _idx()
    cl = cluster_id(idx, "4H")
    rng = np.random.default_rng(0)
    base = np.sort(rng.choice(2000, 600, replace=False))
    det = np.sort(rng.choice(2000, 80, replace=False))
    out = B.thin(base, list(det) + list(det[:10]), idx, "4H", reps=20)     # duplicated detector alerts
    assert out["target"] == 80 and out["available"] == 600
    for r in out["replicates"]:
        assert set(r) <= set(base) and len(r) == len(set(r))
        for k in np.unique(cl):
            assert np.sum(cl[r] == k) == min(np.sum(cl[det] == k), np.sum(cl[base] == k))
    assert out["achieved"] == 80 and out["shortfall_blocks"] == []
    again = B.thin(base, det, idx, "4H", reps=20)
    assert all((a == b).all() for a, b in zip(out["replicates"], again["replicates"]))
    assert len({tuple(r) for r in out["replicates"]}) > 1      # replicates differ


def test_thinning_reports_shortfall_and_handles_edges():
    idx = _idx(300)
    sparse = np.array([5])
    dense = np.arange(0, 300, 3)
    out = B.thin(sparse, dense, idx, "4H", reps=5)
    assert out["achieved"] == 1 and len(out["shortfall_blocks"]) >= 1    # kept all, did not pad
    assert B.thin([], dense, idx, "4H", reps=3)["achieved"] == 0
    assert B.thin(dense, [], idx, "4H", reps=3)["achieved"] == 0         # no detector alerts -> none kept
    with pytest.raises(IndexError):
        B.thin([300], dense, idx, "4H")
    with pytest.raises(IndexError):
        B.thin(dense, [-1], idx, "4H")


# ----------------------------------------------------------------------------- small-cluster inference

def test_wild_cluster_test_holds_size_where_percentile_bootstrap_over_rejects():
    """Synthetic null (mean 0) with heavy-tailed shocks shared within clusters, G = 8. A method check,
    not an empirical result."""
    from research.v41 import weights
    rng = np.random.default_rng(0)
    rej_w = rej_p = 0
    sims = 300
    for s in range(sims):
        sizes = rng.integers(20, 200, 8)
        cl = np.repeat(np.arange(8), sizes)
        x = np.repeat(rng.standard_t(3, 8), sizes) + rng.normal(0, 1, len(cl))
        r = INF.cluster_mean_test(x, cl, reps=399, seed=s)
        rej_w += r["p_wild"] < 0.05
        u, inv = np.unique(cl, return_inverse=True)
        su, cn = np.bincount(inv, weights=x), np.bincount(inv).astype(float)
        b = (weights(u, 399, s) @ su) / (weights(u, 399, s) @ cn)
        rej_p += (1 + np.sum(b <= 0)) / 400 < 0.05
    assert rej_w / sims <= 0.08
    assert rej_p / sims > rej_w / sims


def test_wild_cluster_test_details():
    rng = np.random.default_rng(1)
    cl = np.repeat(np.arange(25), 40)
    x = 0.5 + np.repeat(rng.normal(0, 0.2, 25), 40) + rng.normal(0, 1, len(cl))
    r = INF.cluster_mean_test(x, cl, reps=999)
    assert r["clusters"] == 25 and r["df"] == 24 and r["wild_weights"] == "rademacher" and r["valid"]
    assert r["p_wild"] < 0.01 and r["ci95"][0] < r["mean"] < r["ci95"][1]
    small = INF.cluster_mean_test(x[:200], cl[:200], reps=99)          # 5 clusters
    assert small["wild_weights"] == "webb" and small["valid"] is False
    assert INF.cluster_mean_test([1.0, 2.0], [0, 0])["valid"] is False
    with pytest.raises(ValueError):
        INF.cluster_mean_test(x, cl, alternative="less")


# ----------------------------------------------------------------------------- data manifest

def test_manifest_verify_detects_changes_and_extras(tmp_path):
    src = Path(__import__("hcmtf.data", fromlist=["DATA_DIR"]).DATA_DIR)
    files = sorted(src.glob("SPY_1*.csv.gz"))
    if not files:
        pytest.skip("no cached data")
    d = tmp_path / "data"
    d.mkdir()
    for f in files:
        shutil.copy(f, d / f.name)
    m = MF.build(d, coverage=False)
    assert MF.verify(m, d) == {"missing": [], "changed": [], "extra": []}
    raw = (d / files[0].name).read_bytes()
    (d / files[0].name).write_bytes(raw + b"\x00")
    shutil.copy(files[0], d / "QQQ_1d.csv.gz")
    v = MF.verify(m, d)
    assert v["changed"] == [files[0].name] and v["extra"] == ["QQQ_1d.csv.gz"]
    (d / "FETUSDT_1d.csv.gz").write_bytes(raw)                          # a reserved instrument
    with pytest.raises(RuntimeError):
        MF.build(d, coverage=False)


def test_committed_manifest_matches_the_cache():
    p = ROOT / "reports" / "V5_EXPLORATION_DATA_MANIFEST.json"
    m = json.loads(p.read_text())
    assert m["excluded_from_pooling"] == ["BTC-USD"] and m["file_count"] == len(m["files"])
    if not any(Path(__import__("hcmtf.data", fromlist=["DATA_DIR"]).DATA_DIR).glob("*.csv.gz")):
        pytest.skip("no cached data")
    assert MF.verify(m) == {"missing": [], "changed": [], "extra": []}


# ----------------------------------------------------------------------------- readiness gate

def test_family_c_gate_state_is_honest():
    """Without an independent review the gate may open only in the exploration-only waiver mode,
    and confirmatory runs stay blocked (the earlier "blocked" state ended when the configuration
    was frozen and the detectors committed under the documented waiver)."""
    b = GT.c_blockers(check_cache=False)
    mode = GT.review_mode()
    if not b:
        assert mode in ("independent", "self_audited_exploration_only")
    if mode != "independent":
        assert GT.confirmatory_blockers()                   # never unlocked by the waiver
        assert any(x.startswith("B1") for x in GT.confirmatory_blockers())
