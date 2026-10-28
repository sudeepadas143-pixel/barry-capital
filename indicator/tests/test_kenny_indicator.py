"""Kenny's Divergence Indicator (pine/Kenny_Divergence_Indicator.pine), generated from the CY-2 spec:
tree parity (Pine arrays read back from the generated source vs sklearn), feature coverage,
non-repainting constructs, and committed file == generator(committed spec). Synthetic data only."""

import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research import cycle2_features as C2, cycle_features as CF  # noqa: E402


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


K = _load("kenny_export_pine", "scripts/kenny_export_pine.py")
R2 = _load("cycle2_research", "scripts/cycle2_research.py")
PINE = ROOT / "pine" / "Kenny_Divergence_Indicator.pine"


def _gb_spec(seed=0, nfeat=None):
    from sklearn.ensemble import HistGradientBoostingClassifier
    feats = R2.ALLF
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(5000, len(feats)))
    X[rng.random(X.shape) < 0.1] = np.nan
    y = ((np.nan_to_num(X[:, 0]) - np.nan_to_num(X[:, 9]) * np.nan_to_num(X[:, 25]) + rng.normal(0, 0.5, 5000)) > 0.4).astype(int)
    m = HistGradientBoostingClassifier(random_state=1, **R2.PRIMARY).fit(X, y)
    return m, {"kind": "gb", "model": "GBZ", "features": feats, **R2.export_gb(m),
               "theta": {"warning": 0.2, "standard": 0.3, "high": 0.45}}


def _spec():
    m, gb = _gb_spec()
    base = {"kind": "base", "feature": "ext_c", "sign": -1.0, "model": "B_ext", "theta": {"warning": 1.0, "standard": 2.0, "high": 3.0}}
    tfs = {tf: {"L": CF.SCALE[tf]["L"], "models": {"top": gb, "bot": base}} for tf in ("1W", "1D", "4H", "1H")}
    return m, {"tfs": tfs}


def test_pine_tree_arrays_reproduce_sklearn():
    m, S = _spec()
    src = K.generate(S)
    rng = np.random.default_rng(5)
    Xt = rng.normal(size=(400, len(R2.ALLF)))
    Xt[rng.random(Xt.shape) < 0.2] = np.nan
    ref = m.decision_function(Xt)
    for b in (3, 0):
        fl = K.parse_arrays(src, "top", b)                    # exactly what the Pine script loads
        got = np.array([K.flat_logodds(fl, list(x)) for x in Xt])
        assert np.allclose(got, ref, atol=1e-9)
    assert 'th{}W := 0.2'.format("Top") in src and "gbBot := false" in src and "signBot := -1.0" in src


def test_every_model_feature_is_defined_in_pine_in_research_order():
    _, S = _spec()
    src = K.generate(S)
    assert set(K.PINE_FEAT) == set(CF.PRICE + CF.MOM + CF.VOL + CF.INTER + C2.NEW + ["htf_rng"])
    for f in R2.ALLF:
        assert re.search(rf"^{K.PINE_FEAT[f]}\s+=", src, re.M), f
    fv = re.search(r"^fv = array\.from\((.*)\)$", src, re.M).group(1).split(", ")
    assert fv == [K.PINE_FEAT[f] for f in R2.ALLF]
    bad = json.loads(json.dumps(S))
    bad["tfs"]["1D"]["models"]["top"]["features"] = ["breadth"] + R2.ALLF[1:]
    with pytest.raises(ValueError):
        K.generate(bad)


def test_names_states_and_non_repainting_constructs():
    _, S = _spec()
    src = K.generate(S)
    assert src.startswith("//@version=6")
    assert 'indicator("Kenny\'s Divergence Indicator", shorttitle = "Kenny Div"' in src
    assert "HC-Cycle" not in src and "__" not in src.replace("__FV__", "")
    for s in ("Early Warning", "High Conviction", "Confirmed"):
        assert f"Kenny Div: {s} top" in src and f"Kenny Div: {s} bottom" in src
    assert "barstate.isconfirmed and not na(p)" in src
    sec = [ln for ln in src.splitlines() if "request.security(" in ln and not ln.lstrip().startswith("//")]
    assert sec and all("[1], lookahead = barmerge.lookahead_on" in ln for ln in sec)


def test_flat_arrays_handle_missing_like_sklearn_for_all_nan_row():
    m, S = _spec()
    fl = K.flatten(S["tfs"]["1W"]["models"]["top"])
    x = np.full((1, len(R2.ALLF)), np.nan)
    assert K.flat_logodds(fl, list(x[0])) == pytest.approx(m.decision_function(x)[0], abs=1e-9)


def test_committed_pine_is_generated_from_the_committed_spec():
    spec = ROOT / "reports" / "cycle2_model_spec.json"
    if not PINE.exists():
        pytest.skip("indicator not generated yet")
    res = ROOT / "reports" / "cycle2_results.json"
    R = json.loads(res.read_text()) if res.exists() else None
    assert K.generate(json.loads(spec.read_text()), R) == PINE.read_text()


def test_default_chart_is_only_buy_and_sell_triangles():
    _, S = _spec()
    src = K.generate(S)
    plots = [ln for ln in src.splitlines() if ln.startswith(("plotshape(", "plot(", "bgcolor(", "plotchar(", "plotarrow("))]
    on_by_default = [ln for ln in plots if "showStates" not in ln and "showBg" not in ln]
    assert on_by_default == [
        'plotshape(showBuy and buySig, "BUY", shape.triangleup, location.belowbar, cBuy, size = size.small)',
        'plotshape(showSell and sellSig, "SELL", shape.triangledown, location.abovebar, cSell, size = size.small)']
    for ln in src.splitlines():                        # every label/line/box/table draw is behind an off-by-default input
        if "label.new(" in ln or "line.new(" in ln or "box.new(" in ln:
            prev = src.splitlines()[src.splitlines().index(ln) - 1]
            assert "showStates" in prev, ln
    for flag in ("showStates", "showBg", "showTbl"):
        assert re.search(rf"^{flag}\s+= input\.bool\(false", src, re.M), flag
    assert 'input.string("Confirmed", "BUY/SELL signal"' in src
    assert "buySig := bar_index - lastBuy > Q" in src and "not (rawBuy and rawSell)" in src


def test_pine_dedupe_matches_research_dedupe():
    """Python twin of the Pine BUY/SELL de-duplication block equals kb_signals.dedupe_final."""
    from research import kb_signals as KS
    rng = np.random.default_rng(3)
    for _ in range(50):
        n, Q = 300, int(rng.integers(2, 20))
        rb, rs_ = rng.random(n) < 0.08, rng.random(n) < 0.08
        lb = ls = -10**6
        buy, sell = [], []
        for i in range(n):
            if rb[i] and rs_[i]:
                continue
            if rb[i]:
                if i - lb > Q:
                    buy.append(i)
                lb = i
            if rs_[i]:
                if i - ls > Q:
                    sell.append(i)
                ls = i
        b, s = KS.dedupe_final(np.flatnonzero(rb), np.flatnonzero(rs_), Q)
        assert list(b) == buy and list(s) == sell
