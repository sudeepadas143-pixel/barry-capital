"""V4.1 research code: event definitions, causality, and the bootstrap with re-estimated benchmarks."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf import engine as G  # noqa: E402
from hcmtf.data import _resample  # noqa: E402
from research import v41 as V  # noqa: E402
from test_engine_v2 import minute_bars  # noqa: E402


def test_compression_event_fires_on_first_close_outside_the_box():
    n = 40
    h = np.full(n, 101.0)
    l = np.full(n, 99.0)
    c = np.full(n, 100.0)
    vr = np.full(n, 10.0)            # compressed everywhere
    vr[:5] = 50.0                    # not compressed before candle 5
    c[20], h[20] = 101.5, 101.6      # first close above the box (box high 101.0)
    ev = V.compression_events(h, l, c, vr, k=10)
    assert list(ev["i"]) == [20] and list(ev["dir"]) == [1]
    assert ev["box_hi"].iloc[0] == 101.0 and ev["box_lo"].iloc[0] == 99.0 and ev["run"].iloc[0] == 15
    # too short a run: no event
    assert len(V.compression_events(h, l, c, vr, k=16)) == 0
    # downside, and one event per episode
    c2 = c.copy(); l2 = l.copy()
    c2[20], l2[20] = 98.5, 98.4
    c2[21], l2[21] = 98.0, 97.9
    ev = V.compression_events(h, l2, c2, vr, k=10)
    assert list(ev["i"]) == [20] and list(ev["dir"]) == [-1]


def test_state_matches_engine_classes():
    t1 = np.array([1, 1, 0, -1, 1, np.nan, 0])
    t2 = np.array([1, 0, 1, 1, -1, 1, np.nan])
    assert list(V.state_rel(t1, t2, 1)) == ["with", "with", "with", "against", "against", "with", "neutral"]
    assert list(V.state_rel(t1, t2, -1)) == ["against", "against", "against", "against", "against", "against", "neutral"]


def _frames(m15, cut=None):
    m = m15 if cut is None else m15[m15.index + pd.Timedelta(minutes=15) <= cut]
    r = lambda rule: _resample(m, rule, label="left", closed="left")
    chart = r("1h")
    if cut is not None:
        chart = chart[chart.index + pd.Timedelta(hours=1) <= cut]
    return G.Ctx(chart, r("4h"), r("1D"), None, True, True)


def test_states_and_events_never_change_when_the_future_is_removed():
    m = minute_bars(n15=16000, seed=3)
    full = G.features(_frames(m), G.DEFAULTS["1H"])
    ev_full = V.compression_events(full.h, full.l, full.c, full.vol_rank, 24)
    for cut in (m.index[6000], m.index[9001], m.index[12345]):
        cut = cut.floor("h")
        f = G.features(_frames(m, cut), G.DEFAULTS["1H"])
        n = len(f.c)
        for d in (1, -1):
            assert (V.state_rel(f.t1, f.t2, d) == V.state_rel(full.t1[:n], full.t2[:n], d)).all()
        np.testing.assert_array_equal(np.isnan(f.vol_rank), np.isnan(full.vol_rank[:n]))
        ev = V.compression_events(f.h, f.l, f.c, f.vol_rank, 24)
        e2 = ev_full[ev_full["i"] < n]
        assert list(ev["i"]) == list(e2["i"]) and list(ev["dir"]) == list(e2["dir"])
        rel_b, rel_s = V.state_rel(f.t1, f.t2, 1), V.state_rel(f.t1, f.t2, -1)
        rf = V.roc_events(full.c, V.state_rel(full.t1, full.t2, 1), V.state_rel(full.t1, full.t2, -1))
        rt = V.roc_events(f.c, rel_b, rel_s)
        assert sorted(map(tuple, rt[["i", "dir"]].to_numpy())) == sorted(map(tuple, rf[rf["i"] < n][["i", "dir"]].to_numpy()))


def test_bootstrap_point_and_reestimated_benchmark():
    rng = np.random.default_rng(0)
    rows = []
    for s in ("A", "B", "C"):
        for c in range(12):
            x = rng.normal(0.1 if s == "A" else -0.1, 1, 50)
            rows.append(pd.DataFrame({"sym": s, "cl": c, "r": x}))
    allc = pd.concat(rows, ignore_index=True)
    bench = allc.groupby(["sym", "cl"])["r"].agg(["sum", "count"]).reset_index().assign(st=0)
    clusters = np.arange(12)
    W = V.weights(clusters, reps=200)
    # units = all candles → excess is exactly 0, in every replicate
    reps, point, pu = V.boot_excess(allc, bench, "r", None, W, clusters)
    assert abs(point) < 1e-12 and np.nanmax(np.abs(reps)) < 1e-9
    # a subset: point equals the direct calculation
    sub = allc[allc["r"] > 0.5]
    reps, point, pu = V.boot_excess(sub, bench, "r", None, W, clusters)
    mu = allc.groupby("sym")["r"].mean()
    direct = (sub["r"] - sub["sym"].map(mu)).mean()
    assert abs(point - direct) < 1e-12 and abs(pu.mean() - direct) < 1e-12
    assert np.nanpercentile(reps, 2.5) < point < np.nanpercentile(reps, 97.5)
