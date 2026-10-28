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


def _pine_twin(df, tf, st, htf, hl, theta):
    """Bar-by-bar transliteration of the Pine cluster block (pivots by highest/lowest windows,
    pivot arrays pruned at 60 candles, traces updated on closed candles)."""
    from hcmtf import ta
    from research.cycle_features import SCALE, q_of
    L = SCALE[tf]["L"]
    Q, M = q_of(L), L // 2
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    n = len(c)
    r, hst = ta.rsi(c, 14), ta.macd(c, 12, 26, 9)[2]
    F = st["F"]
    relv, vr = F["relvol"].to_numpy(float), F["vratio"].to_numpy(float)
    trend = KC.htf_trend(df, htf)
    pa = KC.price_action(o, h, l, c, L)
    lam = 0.5 ** (1.0 / max(1.0, L * hl))
    W = [KC.WEIGHTS[f] for f in KC.FAMS]
    piv = {"top": [], "bot": []}
    tr = {"top": [0.0] * 5, "bot": [0.0] * 5}
    last_std = {"top": -10**6, "bot": -10**6}
    on = {d: {k: set(st[d][k].tolist()) for k in ("K_W", "K_S", "K_H", "K_CONF")} for d in ("top", "bot")}
    buy, sell = [], []
    for i in range(n):
        e = {}
        for d in ("top", "bot"):
            px = h if d == "top" else l
            isp = i >= 10 and ((px[i - 5] > px[i - 10:i - 5].max() and px[i - 5] >= px[i - 4:i + 1].max()) if d == "top"
                               else (px[i - 5] < px[i - 10:i - 5].min() and px[i - 5] <= px[i - 4:i + 1].min()))
            ediv = 0.0
            if isp:
                p = i - 5
                arr = piv[d]
                while arr and p - arr[0][0] > 60:
                    arr.pop(0)
                for (q, pq, rq, hq) in reversed(arr):
                    if p - q >= 5:
                        pxd = px[p] > pq if d == "top" else px[p] < pq
                        k = 0.0
                        for x, xq in ((r[p], rq), (hst[p], hq)):
                            if pxd and np.isfinite(x) and np.isfinite(xq) and ((x < xq) if d == "top" else (x > xq)):
                                k += 0.5
                        ediv = k
                        break
                arr.append((p, px[p], r[p], hst[p]))
            rg = h[i] - l[i]
            wu = (h[i] - max(o[i], c[i])) / rg if rg > 0 else 0.0
            wd = (min(o[i], c[i]) - l[i]) / rg if rg > 0 else 0.0
            burst = (relv[i] >= 1.0 if np.isfinite(relv[i]) else False) or (vr[i] >= 0.5 if np.isfinite(vr[i]) else False)
            ext = 1.0 if i in on[d]["K_H"] else 0.7 if i in on[d]["K_S"] else 0.4 if i in on[d]["K_W"] else 0.0
            if i in on[d]["K_S"]:
                last_std[d] = i
            p_, thw = st[d]["p"], st[d]["theta"]["warning"]
            warm = any(np.isfinite(p_[j]) and p_[j] >= thw for j in range(max(0, i - Q + 1), i + 1)) and i >= Q - 1
            e[d] = ([ext, 1.0 if i in on[d]["K_CONF"] else 0.0, ediv, pa[d][i], 1.0 if burst and (wu if d == "top" else wd) >= 0.4 else 0.0],
                    warm or i - last_std[d] <= M)
        new, score = {}, {}
        for d, od in (("top", "bot"), ("bot", "top")):
            opp = max(e[od][0])
            add = 0.0
            for k in range(5):
                t = tr[d][k] * lam * (1.0 - 0.5 * opp)
                inc = max(0.0, W[k] * e[d][0][k] * (1.0 - t / W[k]))
                tr[d][k] = min(t + inc, W[k])
                add += inc
            new[d] = add
        for d in ("top", "bot"):
            score[d] = sum(tr[d]) * (1.2 if (d == "bot" and trend[i] > 0) or (d == "top" and trend[i] < 0) else 1.0)
        qT = e["top"][1] and new["top"] >= 0.15 and score["top"] >= theta
        qB = e["bot"][1] and new["bot"] >= 0.15 and score["bot"] >= theta
        if qB and not (qT and score["top"] >= score["bot"]):
            buy.append(i)
        if qT and not (qB and score["bot"] >= score["top"]):
            sell.append(i)
    return np.array(buy, int), np.array(sell, int)


def test_pine_cluster_algorithm_matches_the_research_reference():
    d = daily("2010-01-01", "2020-12-31", 21)
    w = rs(d, "W-MON")
    st = KSIM.states(d, "1D", SPEC)
    ref = KC.run_clusters(KC.evidence(d, "1D", st, w), "1D", 1 / 8, 1.5, True)
    tw = _pine_twin(d, "1D", st, w, 1 / 8, 1.5)
    assert len(ref[0]) + len(ref[1]) > 20
    # the Pine warm-up of ta.highest (na for the first Q-1 candles) is the only intended difference
    Q = 15
    assert np.array_equal(tw[0], ref[0][ref[0] >= Q - 1]) and np.array_equal(tw[1], ref[1][ref[1] >= Q - 1])
