"""KB benchmark (reports/KB_CONFIG.md): causal reference families, divergence definition, combo and
de-duplication semantics, gate, and a synthetic end-to-end dry run. Synthetic data only."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from research import kb_signals as KS, v5_gate as GT  # noqa: E402
from test_cycle_engine import daily, rs  # noqa: E402

spec = importlib.util.spec_from_file_location("kb_bench", ROOT / "scripts" / "kb_bench.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


def _ohlcv(df):
    return tuple(df[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))


def test_families_are_causal_under_truncation():
    df = daily("2015-01-01", "2020-12-31", 3)
    o, h, l, c, v = _ohlcv(df)
    full = KS.families(o, h, l, c, v, 63, 15)
    for cut in (600, 1500):
        part = KS.families(o[:cut], h[:cut], l[:cut], c[:cut], v[:cut], 63, 15)
        for f in full:
            for d in ("top", "bot"):
                assert np.array_equal(part[f][d], full[f][d][full[f][d] < cut]), (f, d)


def test_regular_bullish_divergence_reported_on_confirming_candle():
    # decline into a low, bounce, a slower decline to a LOWER low (momentum higher), then a rally
    c = np.r_[np.linspace(100, 80, 30), np.linspace(80, 90, 10), np.linspace(90, 79, 25), np.linspace(79, 95, 20)]
    o = np.r_[c[0], c[:-1]]
    h, l = np.maximum(o, c) + 0.2, np.minimum(o, c) - 0.2
    dv = KS.divergences(o, h, l, c, None)
    at = np.flatnonzero(dv["reg"]["bot"])
    assert len(at) and at[0] == 64 + KS.PIV_R          # second low at candle 64, known 5 candles later
    assert dv["reg"]["bot"][at[0]] >= 2


def test_combo_and_dedupe_semantics():
    assert list(KS.after_zone(np.array([10, 50]), np.array([5, 12, 14, 70]), 10)) == [12]
    buy, sell = KS.dedupe_final(np.array([5, 7, 30]), np.array([7, 40]), 4)
    assert list(buy) == [5, 30] and list(sell) == [40]
    assert list(KS.cooldown(np.array([1, 3, 5, 20]), 2)) == [1, 20]


def test_kb_gate(tmp_path):
    import subprocess
    w = "External review: UNAVAILABLE\nSelf-audit: COMPLETED\nScope: EXPLORATION ONLY\nSelf-audit report: reports/V5_SELF_AUDIT.md\n"
    files = {GT.BASELINES: "x", GT.MANIFEST: '{"files": {}}', GT.WAIVER: w, GT.SELF_AUDIT: "s", GT.KB_CONFIG: "Status: FROZEN\n",
             **{f: "x" for f in GT.KB_CODE}}
    for cmd in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], cwd=tmp_path, check=True)
    for rel, t in files.items():
        p = tmp_path / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=tmp_path, check=True)
    assert GT.kb_blockers(tmp_path, check_cache=False) == []
    (tmp_path / "scripts" / "kb_bench.py").write_text("changed")
    assert any(b.startswith("Y2") for b in GT.kb_blockers(tmp_path, check_cache=False))


SYMS = ["SPY", "QQQ", "AAPL", "MSFT", "JPM", "XOM", "GLD", "TLT", "EURUSD=X"]


def test_full_run_tf_dry_run(monkeypatch):
    frames = {}
    for k, s in enumerate(SYMS):
        d = daily(seed=80 + k)
        if s == "EURUSD=X":
            d["volume"] = 0.0
        frames[s] = {"1D": d, "1W": rs(d, "W-MON"), "1M": rs(d, "MS")}
    C = B.C
    for mod in (C.DG, C.CR.DG, B.DG):
        monkeypatch.setattr(mod, "load", lambda sym, tf: frames[sym][tf])
    monkeypatch.setattr(B.DG, "EVAL_SYMBOLS", tuple(SYMS))
    monkeypatch.setattr(C, "YEARS", {**C.YEARS, "1D": [2016, 2019, 2022]})
    monkeypatch.setattr(B.LG, "record", lambda *a, **k: None)
    monkeypatch.setattr(B, "_commit_ledger", lambda tid: None)
    monkeypatch.setattr(B, "REPS", 99)

    class _Pool:
        def __init__(self, *a): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def map(self, f, it): return map(f, it)
    monkeypatch.setattr(B, "ProcessPoolExecutor", _Pool)
    sp = {"tfs": {"1D": {"models": {"top": {"model": "B_ext"}, "bot": {"model": "GBZ"}}}}}
    res = B.run_tf("1D", ["x"], "test", sp)
    names = set(B.KENNY + B.COMBOS + B.REFS)
    for d in ("top", "bot"):
        assert set(res[d]) == names
        assert all("vs_ref" in v for n, v in res[d].items() if n != B.REF)
        assert res[d]["K_CONF"]["rate"] is not None
    import json
    R = json.loads(json.dumps(B.C.CR._clean({"tfs": {"1D": res}}), default=str))      # as stored on disk
    dec = B.decide(R)
    assert dec["default"] in B.KENNY + B.COMBOS
