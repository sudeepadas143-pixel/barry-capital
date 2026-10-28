"""KWB (reports/KWB_CONFIG.md, FROZEN). EXPLORATORY.

    python scripts/kwb_eval.py run | render
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research import kenny_freq as KF, kenny_retro as KR, kenny_sim as KSIM, kenny_wbuy as WB, v5_data as DG, v5_gate as GT  # noqa: E402
from research import v5_ledger as LG, v5_manifest as MF  # noqa: E402
from research.kb_signals import cooldown  # noqa: E402

_s = importlib.util.spec_from_file_location("kr_eval", ROOT / "scripts" / "kr_eval.py")
KE = importlib.util.module_from_spec(_s)
_s.loader.exec_module(KE)

OUT, MD = ROOT / "reports" / "kwb_results.json", ROOT / "reports" / "KWB_RESULTS.md"
SPLIT = pd.Timestamp("2018-01-01", tz="UTC")
REPS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def one(sym):
    try:
        df = DG.load(sym, "1W")
    except Exception:
        return None
    if len(df) < 200:
        return None
    spec = json.loads(KE.SPEC.read_text())
    st = KSIM.states(df, "1W", spec)
    c26 = KSIM.CF.q_of(26)
    shipped = cooldown(KSIM.CF.zone_onsets(st["bot"]["p"], st["bot"]["theta"]["high"] * 1.1, c26), c26)
    sets = {"SHIPPED": shipped, **{f"V1|{k}": WB.v1(df, k) for k in WB.KS}, **{f"V2|{k}": WB.v2(df, k, shipped) for k in WB.KS}}
    c = df["close"].to_numpy(float)
    pre = np.asarray(df.index < SPLIT)
    grp = KE.GRP.get(DG.EXPLORATION[sym].cls, "other")
    base = {"tune": KF.base_rate(c, 13, 1, pre), "check": KF.base_rate(c, 13, 1, ~pre)}
    rows, cov = [], []
    sw = KR.swings(df, "1W", 1)
    for name, idx in sets.items():
        idx = np.asarray(idx, int)
        sc = KR.score(df, "1W", idx, 1)
        out = KF.outcome(c, idx, 13, 1)
        for j, s in enumerate(idx):
            per = "tune" if pre[s] else "check"
            rows.append({"opt": name, "per": per, "grp": grp, "right": sc[j, 2], "excess": out[j] - base[per] if np.isfinite(out[j]) else np.nan})
        right_idx = idx[np.nan_to_num(sc[:, 2]) > 0] if len(idx) else idx
        for k in sw:
            cov.append({"opt": name, "per": "tune" if pre[k] else "check", "grp": grp, "hit": bool(((right_idx >= k - 6) & (right_idx <= k + 6)).any())})
    rep = {n: [str(df.index[s].date()) for s in sets[n]] for n in sets} if sym in REPS else None
    yrs = {"tune": max(0.0, (min(SPLIT, df.index[-1]) - df.index[0]).total_seconds() / 3.15576e7),
           "check": max(0.0, (df.index[-1] - max(SPLIT, df.index[0])).total_seconds() / 3.15576e7)}
    return {"sym": sym, "rows": rows, "cov": cov, "rep": rep, "yrs": yrs}


def summ(T, Cv, yrs, opt, per, grp=None):
    t, c = T[(T["opt"] == opt) & (T["per"] == per)], Cv[(Cv["opt"] == opt) & (Cv["per"] == per)]
    if grp:
        t, c = t[t["grp"] == grp], c[c["grp"] == grp]
    return {"n": int(len(t)), "rate": len(t) / yrs if yrs else 0.0, "right": float(np.nanmean(t["right"])) if len(t) else None,
            "excess": float(np.nanmean(t["excess"])) if len(t) else None, "coverage": float(c["hit"].mean()) if len(c) else None, "swings": int(len(c))}


def run():
    mode = GT.require_kwb_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    LG.record("kwb-1W", "KWB-1", ["exploration"], {"config": GT.KWB_CONFIG, "mode": mode}, list(GT.KWB_CODE),
              ["right_rate", "excess", "coverage", "rate"], True, GT.KWB_CONFIG, data_files, notes=f"exploration; review mode {mode}")
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "KWB ledger: record trial kwb-1W (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    with ProcessPoolExecutor(4) as ex:
        res = [x for x in ex.map(one, DG.EVAL_SYMBOLS) if x]
    T = pd.DataFrame([r for x in res for r in x["rows"]])
    Cv = pd.DataFrame([r for x in res for r in x["cov"]])
    yrs = {p: sum(x["yrs"][p] for x in res) for p in ("tune", "check")}
    gy = {g: {p: sum(x["yrs"][p] for x in res if KE.GRP.get(DG.EXPLORATION[x["sym"]].cls, "other") == g) for p in ("tune", "check")} for g in ("equities", "crypto")}
    opts = sorted(T["opt"].unique())
    S = {o: {p: {"all": summ(T, Cv, yrs[p], o, p), **{g: summ(T, Cv, gy[g][p], o, p, g) for g in ("equities", "crypto")}} for p in ("tune", "check")} for o in opts}
    sh = S["SHIPPED"]
    elig = [o for o in opts if o != "SHIPPED" and S[o]["tune"]["all"]["n"] >= 30
            and S[o]["tune"]["all"]["right"] >= sh["tune"]["all"]["right"] - 0.03 and S[o]["tune"]["all"]["excess"] >= sh["tune"]["all"]["excess"] - 0.02]
    chosen = max(elig, key=lambda o: S[o]["tune"]["all"]["rate"]) if elig else None
    ok = False
    if chosen:
        x, b = S[chosen]["check"], sh["check"]
        ok = (x["all"]["right"] >= b["all"]["right"] - 0.03 and x["all"]["excess"] >= b["all"]["excess"] - 0.02
              and x["all"]["coverage"] >= b["all"]["coverage"] and (x["crypto"]["coverage"] or 0) > (b["crypto"]["coverage"] or 0))
    out = {"options": S, "eligible": elig, "chosen": chosen, "adopted": chosen if ok else "SHIPPED",
           "reps": {x["sym"]: x["rep"] for x in res if x["rep"]},
           "meta": {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}}
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print("done", flush=True)


def render():
    out = json.loads(OUT.read_text())
    f = lambda v: f"{v['n']}, {v['rate']:.2f}/yr, right {v['right']:.2f}, excess {v['excess']:+.2f}, coverage {v['coverage']:.2f} of {v['swings']}" if v["n"] else f"0 (coverage of {v['swings']} swings: 0)"  # noqa: E731
    L = ["# KWB: weekly BUY for cycle bottoms (EXPLORATORY)", "", f"Chosen on <2018: {out['chosen']}; **adopted: {out['adopted']}**. 2018+ previously studied.", "",
         "| option | <2018 all | 2018+ all | 2018+ equities | 2018+ crypto |", "|---|---|---|---|---|"]
    for o, S in out["options"].items():
        L.append(f"| {o} | {f(S['tune']['all'])} | {f(S['check']['all'])} | {f(S['check']['equities'])} | {f(S['check']['crypto'])} |")
    L += ["", "## BTC / ETH / SOL weekly BUY dates (reported only)", ""]
    for sym, d in out["reps"].items():
        L.append(f"* **{sym}** shipped: {', '.join(d['SHIPPED']) or 'none'}; adopted ({out['adopted']}): {', '.join(d[out['adopted']]) or 'none'}")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"run": run, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
