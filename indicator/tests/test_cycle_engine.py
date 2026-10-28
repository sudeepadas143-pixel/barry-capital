"""Cycle engine CY-1 (reports/CYCLE_CONFIG.md): causality of features and alerts, Pine-equivalent
primitives, no label access, gate, and a synthetic end-to-end dry run. Synthetic data only."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf.engine import percentrank as engine_percentrank  # noqa: E402
from research import cycle_features as CF, v5_gate as GT  # noqa: E402

spec = importlib.util.spec_from_file_location("cycle_research", ROOT / "scripts" / "cycle_research.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def daily(start="2005-01-03", end="2026-10-23", seed=1):
    idx = pd.date_range(start, end, freq="1D", tz="UTC")
    rng = np.random.default_rng(seed)
    n = len(idx)
    drift = np.repeat(rng.normal(0, 0.004, n // 120 + 1), 120)[:n]
    c = 100 * np.exp(np.cumsum(drift + rng.normal(0, 0.02, n)))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.008, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.008, n)))
    v = rng.lognormal(10, 0.5, n) * (1 + 3 * (np.abs(c / o - 1) > 0.04))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}, index=idx)


def rs(df, rule):
    a = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    return df.resample(rule, label="left", closed="left").agg(a).dropna()


# ----------------------------------------------------------------------------- primitives and causality

def test_primitives_match_pine_semantics():
    x = np.array([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5.0])
    assert list(CF.highest(x, 3)[2:5]) == [4, 4, 5]
    assert CF.bars_since_extreme(x, 4, True)[5] == 0 and CF.bars_since_extreme(x, 4, True)[7] == 2
    y = np.random.default_rng(0).normal(size=400)
    a, b = CF.percentrank(y, 100), engine_percentrank(y, 100)
    assert np.allclose(a[~np.isnan(b)], b[~np.isnan(b)]) and np.isnan(a).sum() == np.isnan(b).sum()


def test_features_and_alerts_are_causal_under_truncation():
    df = daily("2015-01-01", "2020-12-31", 3)
    full = CF.features(df, "1D", True)
    p_full = 1 / (1 + np.exp(-(full["ext_c"] - 2).to_numpy()))
    on_full = CF.zone_onsets(p_full, 0.5, 15)
    for cut in (900, 1500, 2100):
        part = CF.features(df.iloc[:cut], "1D", True)
        pd.testing.assert_frame_equal(part, full.iloc[:cut], check_dtype=False)
        p = 1 / (1 + np.exp(-(part["ext_c"] - 2).to_numpy()))
        assert list(CF.zone_onsets(p, 0.5, 15)) == [i for i in on_full if i < cut]
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    args = lambda n: (o[:n], h[:n], l[:n], c[:n], full["_rsi"].to_numpy()[:n], full["_hist"].to_numpy()[:n],
                      full["_ema_f"].to_numpy()[:n], full["_atr"].to_numpy()[:n], 63, 8.0)
    dv, cf = CF.developing_and_confirmed(on_full, -1, *args(len(c)))
    assert len(on_full) > 5
    for cut in (1200, 1800):
        d2, c2 = CF.developing_and_confirmed(on_full[on_full < cut], -1, *args(cut))
        assert list(d2) == [i for i in dv if i < cut] and list(c2) == [i for i in cf if i < cut]


def test_missing_volume_is_nan_never_zero():
    df = daily("2018-01-01", "2020-01-01", 4)
    f = CF.features(df, "1D", False)
    assert f[CF.VOL].isna().all().all() and f["i_ext_relvol"].isna().all()
    df2 = df.copy(); df2.iloc[300:310, df2.columns.get_loc("volume")] = 0.0
    g = CF.features(df2, "1D", True)
    assert g["relvol"].iloc[300:310].isna().all()


def test_cycle_features_reads_no_labels():
    src = (ROOT / "research" / "cycle_features.py").read_text()
    imports = [ln for ln in src.splitlines() if ln.lstrip().startswith(("import ", "from "))]
    assert not any("v5_labels" in ln or "v5_eval" in ln for ln in imports)


# ----------------------------------------------------------------------------- gate

def _repo(tmp, files):
    for cmd in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], cwd=tmp, check=True)
    for rel, text in files.items():
        p = tmp / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=tmp, check=True)


def test_cy_gate(tmp_path):
    w = "External review: UNAVAILABLE\nSelf-audit: COMPLETED\nScope: EXPLORATION ONLY\nSelf-audit report: reports/V5_SELF_AUDIT.md\n"
    base = {GT.BASELINES: "x", GT.MANIFEST: '{"files": {}}', GT.WAIVER: w, GT.SELF_AUDIT: "s", **{f: "x" for f in GT.CY_CODE}}
    a = tmp_path / "a"; a.mkdir(); _repo(a, {**base, GT.CY_CONFIG: "Status: DRAFT\n"})
    assert any(x.startswith("Y1") for x in GT.cy_blockers(a, check_cache=False))
    b = tmp_path / "b"; b.mkdir(); _repo(b, {**base, GT.CY_CONFIG: "Status: FROZEN\n"})
    assert GT.cy_blockers(b, check_cache=False) == []


def test_runner_refuses_when_gate_closed(monkeypatch):
    monkeypatch.setattr(M.GT, "cy_blockers", lambda *a, **k: ["Y1: test"])
    with pytest.raises(M.GT.NotReady):
        M.run(("1D",))


# ----------------------------------------------------------------------------- synthetic end-to-end dry run

SYMS = ["SPY", "QQQ", "AAPL", "MSFT", "JPM", "XOM", "GLD", "TLT", "EURUSD=X"]


def test_pipeline_dry_run_on_synthetic_daily(monkeypatch):
    frames = {}
    for k, s in enumerate(SYMS):
        d = daily(seed=10 + k)
        if s == "EURUSD=X":
            d["volume"] = 0.0
        frames[s] = {"1D": d, "1W": rs(d, "W-MON"), "1M": rs(d, "MS"), "4H": d}
    monkeypatch.setattr(M.DG, "load", lambda sym, tf: frames[sym][tf])
    res = [M.build((s, "1D")) for s in SYMS]
    assert all(r is not None for r in res) and sum(r["vol"] for r in res) == len(SYMS) - 1
    M.add_breadth(res)
    shipped, thetas, cands = {}, {}, {}
    for d in M.DIRS:
        M.with_breadth(res, d)
        cg = {}
        for g in ("vol", "novol"):
            lg = {}
            spec, cg[g] = M.select(res, d, g, lg)
            th, cal = M.calibrate_theta(res if g == "novol" else [r for r in res if r["vol"]], spec, d, "1D")
            shipped[(d, g)], thetas[(d, g)] = spec, th
            assert lg["selected_core"] in M.ORDER and 0.5 * cal["target_onsets_per_asset_year"] < cal["achieved"] < 2 * cal["target_onsets_per_asset_year"]
        for name in M.ORDER:
            if name in M.BASE:
                sp = {"kind": "base", "feature": M.BASE[name], "sign": 1.0 if d == "top" else -1.0}
            else:
                g = "vol" if name in ("L_vol", "L_int") else "novol"
                T = M.table(res, d, M.MODELS[name], g)
                sp = M.fit_logit(T[T["_sp"] != "test"], M.MODELS[name], cg[g][name][1]["C"])
            pool = [r for r in res if (r["vol"] or name not in ("L_vol", "L_int"))]
            cands[(d, name)] = (sp, M.calibrate_theta(pool, sp, d, "1D")[0])
    ev = M.evaluate_tf(res, {"shipped": shipped, "candidates": cands}, thetas, "1D", reps_wild=99)
    for d in M.DIRS:
        sh = ev[d]["models"]["SHIPPED"]
        assert sh["zone"] is not None and sh["confirmed"] is not None and "move_confirmed" in sh
        assert set(ev[d]["models"]) >= {"SHIPPED", "B_ext", "L_price", "L_mom"}
    R = {"tfs": {"1D": {"evaluation": ev}}}
    M.decide(R)
    assert set(R["primary"]) == {"1D|top", "1D|bot"}


def test_restated_scales_equal_the_frozen_label_table():
    from research.v5_labels import BOTTOM_PARAMS, TOP_PARAMS
    for tf, (L, F, D) in M.LABEL.items():
        for P in (TOP_PARAMS, BOTTOM_PARAMS):
            assert P[tf] == {"L": L, "F": F, "D": D}
        assert CF.SCALE[tf] == {"L": L, "D": D}


# ----------------------------------------------------------------------------- Pine generator

def _gen():
    s = importlib.util.spec_from_file_location("cycle_export_pine", ROOT / "scripts" / "cycle_export_pine.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_pine_generator_writes_every_shipped_coefficient_and_refuses_unportable_features():
    X = _gen()
    logit = {"kind": "logit", "features": ["ext_c", "rsi_gap_hi", "htf_rng"], "mu": [0.1, 0.2, 0.5], "sd": [1.5, 0.1, 0.3],
             "coef": [0.7, -1.25, 0.33], "intercept": -2.5, "theta": 0.61, "C": 0.1}
    base = {"kind": "base", "feature": "rsi", "sign": -1.0, "theta": -0.3}
    S = {"tfs": {tf: {"models": {"top|vol": logit, "top|novol": base, "bot|vol": base, "bot|novol": logit}} for tf in ("1W", "1D", "4H", "1H")}}
    src = X.generate(S)
    for tok in ("0.7 * z(fExtC, 0.1, 1.5)", "-1.25 * z(fRsiGapHi, 0.2, 0.1)", "0.33 * z(fHtfRng, 0.5, 0.3)", "sig(-2.5",
                "th := 0.61", "-1 * fRsi", "th := -0.3", "lookahead = barmerge.lookahead_on", "barstate.isconfirmed"):
        assert tok in src, tok
    assert "__SCORES__" not in src and "__HTF__" not in src and src.startswith("//@version=6")
    S["tfs"]["1D"]["models"]["top|vol"] = dict(logit, features=["breadth", "ext_c", "rsi_gap_hi"])
    with pytest.raises(ValueError):
        X.generate(S)
    # every research feature has a Pine definition with the same name map
    assert set(CF.PRICE + CF.MOM + CF.VOL + CF.INTER + ["htf_rng"]) == set(X.PINE_FEAT)


def test_pine_score_matches_python_score():
    """The generated expression is the research score: evaluate both on the same feature values."""
    import math
    X = _gen()
    spec = {"kind": "logit", "features": ["ext_c", "rsi", "relvol"], "mu": [0.5, 0.55, 0.0], "sd": [2.0, 0.1, 0.4],
            "coef": [0.9, 1.1, -0.4], "intercept": -1.2, "theta": 0.6}
    vals = {"ext_c": 3.1, "rsi": 0.78, "relvol": 2.9}
    py = float(M.score(spec, pd.DataFrame([vals]))[0])
    e = X.expr(spec)
    env = {"sig": lambda x: 1 / (1 + math.exp(-x)), "z": lambda x, mu, sd: max(-5.0, min(5.0, (x - mu) / sd)),
           **{X.PINE_FEAT[k]: v for k, v in vals.items()}}
    assert eval(e, env) == pytest.approx(py, rel=1e-9)


def test_committed_pine_is_generated_from_the_committed_spec():
    import json
    spec_path, pine_path = ROOT / "reports" / "cycle_model_spec.json", ROOT / "pine" / "HC_CycleEngine.pine"
    if not spec_path.exists() or not pine_path.exists():
        pytest.skip("no shipped spec yet")
    assert _gen().generate(json.loads(spec_path.read_text())) == pine_path.read_text()
