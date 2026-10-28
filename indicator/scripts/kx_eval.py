"""KX (reports/KX_CONFIG.md, FROZEN): context filters for crypto SELL/BUY and equity BUY. EXPLORATORY.

    python scripts/kx_eval.py run | render
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research import kenny_context as KX, kenny_freq as KF, kenny_retro as KR, kenny_sim as KSIM, v5_data as DG, v5_gate as GT  # noqa: E402
from research import v5_ledger as LG, v5_manifest as MF  # noqa: E402
from research.kb_signals import cooldown  # noqa: E402

_g = importlib.util.spec_from_file_location("kenny_export_pine", ROOT / "scripts" / "kenny_export_pine.py")
KG = importlib.util.module_from_spec(_g)
_g.loader.exec_module(KG)

OUT, MD = ROOT / "reports" / "kx_results.json", ROOT / "reports" / "KX_RESULTS.md"
SPEC = json.loads((ROOT / "reports" / "cycle2_model_spec.json").read_text())
CRYPTO_SPLIT, EQ_SPLIT = pd.Timestamp("2023-01-01", tz="UTC"), pd.Timestamp("2018-01-01", tz="UTC")
BUCKET = {"1W": 3, "1D": 2}


def shipped(df, tf, st):
    b = BUCKET[tf]
    c = KSIM.CF.q_of(KSIM.CF.SCALE[tf]["L"])
    buy = cooldown(KSIM.CF.zone_onsets(st["bot"]["p"], st["bot"]["theta"]["high"] * KG.KR_BUY_SCALE[b], c), c)
    sell = None
    if b == 2:
        state, sc = KG.KR_SELL[b]
        sell = cooldown(KSIM.CF.zone_onsets(st["top"]["p"], st["top"]["theta"]["high" if state == "H" else "warning"] * sc, c), c)
    return buy, sell


def score(df, tf, idx, side, split):
    idx = np.asarray(idx, int)
    if not len(idx):
        return []
    c = df["close"].to_numpy(float)
    H = KSIM.CF.SCALE[tf]["L"] // 2
    pre = np.asarray(df.index < split)
    base = {True: KF.base_rate(c, H, side, pre), False: KF.base_rate(c, H, side, ~pre)}
    sc = KR.score(df, tf, idx, side)
    out = KF.outcome(c, idx, H, side)
    return [{"per": "tune" if pre[s] else "check", "right": sc[j, 2], "excess": out[j] - base[bool(pre[s])] if np.isfinite(out[j]) else np.nan}
            for j, s in enumerate(idx)]


def summ(rows):
    T = pd.DataFrame(rows)
    res = {}
    for p in ("tune", "check"):
        t = T[T["per"] == p] if len(T) else T
        res[p] = {"n": int(len(t)), "right": float(np.nanmean(t["right"])) if len(t) else None,
                  "excess": float(np.nanmean(t["excess"])) if len(t) else None}
    return res


def run():
    mode = GT.require_kx_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)}) + ["data_ext/VIX_History.csv"]
    LG.verify_against_git(LG.LEDGER)
    LG.record("kx-all", "KX-1", ["exploration"], {"config": GT.KX_CONFIG, "mode": mode}, list(GT.KX_CODE),
              ["right_rate", "excess"], True, GT.KX_CONFIG, data_files, notes=f"exploration; review mode {mode}")
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "KX ledger: record trial kx-all (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    crypto = [s for s in DG.EVAL_SYMBOLS if DG.EXPLORATION[s].cls == "crypto"]
    frames = {}
    for s in crypto:
        try:
            frames[s] = DG.load(s, "1D")
        except Exception:
            pass
    breadth = KX.alt_breadth(frames)
    R = {"A": {"all": [], "ctx": []}, "B1": {"all": [], "ctx": []}, "B2": [], "C": {}, "dates": {}}
    for s in KX.PERPS:
        df = frames[s]
        st = KSIM.states(df, "1D", SPEC)
        buy, sell = shipped(df, "1D", st)
        cx = KX.crypto_context(s, df, breadth)
        top, bot = KX.top_context(cx), KX.bottom_context(cx)
        R["A"]["all"] += score(df, "1D", sell, -1, CRYPTO_SPLIT)
        R["A"]["ctx"] += score(df, "1D", sell[top[sell]], -1, CRYPTO_SPLIT)
        R["B1"]["all"] += score(df, "1D", buy, 1, CRYPTO_SPLIT)
        R["B1"]["ctx"] += score(df, "1D", buy[bot["two"][buy]], 1, CRYPTO_SPLIT)
        on = np.flatnonzero(bot["all"] & ~np.r_[False, bot["all"][:-1]])
        b2 = cooldown(on, 15)
        R["B2"] += score(df, "1D", b2, 1, CRYPTO_SPLIT)
        R["dates"][s] = [str(df.index[i].date()) for i in b2]
    eq = [s for s in DG.EVAL_SYMBOLS if DG.EXPLORATION[s].cls in ("equity", "equity_index")]
    for tf in ("1D", "1W"):
        allr, ctxr = [], []
        off = pd.Timedelta(days=1) if tf == "1D" else pd.Timedelta(days=7)
        for s in eq:
            try:
                df = DG.load(s, tf)
            except Exception:
                continue
            if len(df) < 400 and tf == "1D":
                continue
            st = KSIM.states(df, tf, SPEC)
            buy, _ = shipped(df, tf, st)
            vr = KX.vix_reversal(df.index, off)
            allr += score(df, tf, buy, 1, EQ_SPLIT)
            ctxr += score(df, tf, buy[vr[buy]], 1, EQ_SPLIT)
        R["C"][tf] = {"all": allr, "ctx": ctxr}
    out = {"A": {k: summ(v) for k, v in R["A"].items()}, "B1": {k: summ(v) for k, v in R["B1"].items()}, "B2": summ(R["B2"]),
           "C": {tf: {k: summ(v) for k, v in d.items()} for tf, d in R["C"].items()}, "b2_dates": R["dates"]}

    def filt_ok(x):
        return all(x["ctx"][p]["n"] >= 15 and x["ctx"][p]["right"] is not None and x["all"][p]["right"] is not None
                   and x["ctx"][p]["right"] >= x["all"][p]["right"] + 0.05 and x["ctx"][p]["excess"] >= x["all"][p]["excess"] + 0.03 for p in ("tune", "check"))
    out["adopt"] = {"A": filt_ok(out["A"]), "B1": filt_ok(out["B1"]), **{f"C_{tf}": filt_ok(v) for tf, v in out["C"].items()},
                    "B2": all(out["B2"][p]["n"] >= 10 and out["B2"][p]["excess"] >= 0.05 and out["B2"][p]["right"] >= out["B1"]["all"][p]["right"] - 0.03
                              for p in ("tune", "check"))}
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print("done", flush=True)


def render():
    out = json.loads(OUT.read_text())
    f = lambda v: f"n {v['n']}, right {v['right']:.2f}, excess {v['excess']:+.2f}" if v["n"] else "n 0"  # noqa: E731
    L = ["# KX: outside-the-chart context (EXPLORATORY)", "", "Right = KR rule; excess = KF rule (price the right way after L/2 vs the instrument's base rate). "
         "Crypto: tuning 2020–2022, check 2023+. Equities: tuning <2018, check 2018+. Small samples.", "",
         "| test | tuning | check | adopted |", "|---|---|---|---|"]
    rows = [("A crypto 1D SELL — all", out["A"]["all"], ""), ("A crypto 1D SELL — with top context", out["A"]["ctx"], out["adopt"]["A"]),
            ("B1 crypto 1D BUY — all", out["B1"]["all"], ""), ("B1 crypto 1D BUY — with bottom context", out["B1"]["ctx"], out["adopt"]["B1"]),
            ("B2 crypto standalone bottom (funding + OI flush + breadth)", out["B2"], out["adopt"]["B2"])]
    for tf, d in out["C"].items():
        rows += [(f"C equity {tf} BUY — all", d["all"], ""), (f"C equity {tf} BUY — with VIX reversal", d["ctx"], out["adopt"][f"C_{tf}"])]
    for name, v, a in rows:
        L.append(f"| {name} | {f(v['tune'])} | {f(v['check'])} | {'' if a == '' else ('**yes**' if a else 'no')} |")
    L += ["", "B2 standalone bottom dates (reported only):", ""] + [f"* {s}: {', '.join(d) or 'none'}" for s, d in out["b2_dates"].items()]
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"run": run, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
