"""KLB (reports/KLB_CONFIG.md, FROZEN). EXPLORATORY.

    python scripts/klb_eval.py run | render
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

from research import kenny_freq as KF, kenny_ltfbuy as LB, kenny_retro as KR, kenny_sim as KSIM, v5_data as DG, v5_gate as GT  # noqa: E402
from research import v5_ledger as LG, v5_manifest as MF  # noqa: E402

_s = importlib.util.spec_from_file_location("kr_eval", ROOT / "scripts" / "kr_eval.py")
KE = importlib.util.module_from_spec(_s)
_s.loader.exec_module(KE)

OUT, MD = ROOT / "reports" / "klb_results.json", ROOT / "reports" / "KLB_RESULTS.md"
CUR = "H|0.8"


def one(args):
    sym, tf = args
    try:
        df = DG.load(sym, tf)
    except Exception:
        return None
    if len(df) < 400:
        return None
    st = KSIM.states(df, tf, json.loads(KE.SPEC.read_text()))
    L = KSIM.CF.SCALE[tf]["L"]
    Q = KSIM.CF.q_of(L)
    c = df["close"].to_numpy(float)
    split = pd.Timestamp(KE.SPLIT[tf], tz="UTC")
    pre = np.asarray(df.index < split)
    base = {True: KF.base_rate(c, L // 2, 1, pre), False: KF.base_rate(c, L // 2, 1, ~pre)}
    grp = KE.GRP.get(DG.EXPLORATION[sym].cls, "other")
    sw = KR.swings(df, tf, 1)
    rows, cov = [], []
    for name, idx in LB.options(df, st, tf).items():
        idx = np.asarray(idx, int)
        sc = KR.score(df, tf, idx, 1) if len(idx) else np.zeros((0, 3))
        out = KF.outcome(c, idx, L // 2, 1) if len(idx) else np.zeros(0)
        inv, dd = LB.follow_up(df, idx, Q)
        for j, s in enumerate(idx):
            if np.isfinite(sc[j, 2]):
                rows.append({"opt": name, "per": "tune" if pre[s] else "check", "grp": grp, "right": sc[j, 2], "zone": sc[j, 0], "follow": sc[j, 1],
                             "excess": out[j] - base[bool(pre[s])] if np.isfinite(out[j]) else np.nan, "inv": inv[j], "dd": dd[j]})
        ok = idx[np.nan_to_num(sc[:, 2]) > 0] if len(idx) else idx
        for k in sw:
            cov.append({"opt": name, "per": "tune" if pre[k] else "check", "grp": grp, "hit": bool(((ok >= k - Q) & (ok <= k + Q)).any())})
    ix = df.index
    yrs = {"tune": max(0.0, (min(split, ix[-1]) - ix[0]).total_seconds() / 3.15576e7),
           "check": max(0.0, (ix[-1] - max(split, ix[0])).total_seconds() / 3.15576e7)}
    return {"rows": rows, "cov": cov, "yrs": yrs}


def summ(T, C, yrs, o, p, g=None):
    t, c = T[(T["opt"] == o) & (T["per"] == p)], C[(C["opt"] == o) & (C["per"] == p)]
    if g:
        t, c = t[t["grp"] == g], c[c["grp"] == g]
    m = lambda k: float(np.nanmean(t[k])) if len(t) else None  # noqa: E731
    return {"n": int(len(t)), "rate": len(t) / yrs if yrs else 0.0, "right": m("right"), "zone": m("zone"), "follow": m("follow"),
            "excess": m("excess"), "invalidated": m("inv"), "dd_med": float(np.nanmedian(t["dd"])) if len(t) else None,
            "coverage": float(c["hit"].mean()) if len(c) else None}


def run():
    mode = GT.require_klb_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    LG.record("klb-all", "KLB-1", ["exploration"], {"config": GT.KLB_CONFIG, "mode": mode}, list(GT.KLB_CODE),
              ["right_rate", "coverage", "excess", "invalidation", "rate"], True, GT.KLB_CONFIG, data_files, notes=f"exploration; review mode {mode}")
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "KLB ledger: record trial klb-all (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    out = {"tfs": {}}
    for tf in ("4H", "1H"):
        with ProcessPoolExecutor(4) as ex:
            res = [x for x in ex.map(one, [(s, tf) for s in DG.EVAL_SYMBOLS]) if x]
        T = pd.DataFrame([r for x in res for r in x["rows"]])
        C = pd.DataFrame([r for x in res for r in x["cov"]])
        yrs = {p: sum(x["yrs"][p] for x in res) for p in ("tune", "check")}
        S = {o: {p: {"all": summ(T, C, yrs[p], o, p), **{g: summ(T, C, yrs[p], o, p, g) for g in ("equities", "crypto")}} for p in ("tune", "check")}
             for o in sorted(T["opt"].unique())}
        cu = S[CUR]
        elig = [o for o in S if S[o]["tune"]["all"]["n"] >= 30 and S[o]["tune"]["all"]["rate"] >= 0.6 * cu["tune"]["all"]["rate"]
                and S[o]["tune"]["all"]["coverage"] >= cu["tune"]["all"]["coverage"] - 0.03 and (S[o]["tune"]["all"]["excess"] or -1) >= 0.02]
        chosen = max(elig, key=lambda o: S[o]["tune"]["all"]["right"]) if elig else CUR
        ch, cc = S[chosen]["check"]["all"], cu["check"]["all"]
        adopt = chosen != CUR and ch["right"] >= cc["right"] + 0.03 and ch["coverage"] >= cc["coverage"] - 0.03 and (ch["excess"] or -1) >= 0.02
        out["tfs"][tf] = {"options": S, "eligible": elig, "chosen": chosen, "adopted": chosen if adopt else CUR, "changed": bool(adopt)}
        print(f"[{tf}] done", flush=True)
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))


def render():
    out = json.loads(OUT.read_text())
    f = lambda v: (f"{v['n']}, {v['rate']:.2f}, {v['right']:.2f}, {v['zone']:.2f}, {v['coverage']:.2f}, {v['excess']:+.2f}, {v['invalidated']:.2f}, "  # noqa: E731
                   f"{v['dd_med']:.1f}") if v["n"] else "0"
    L = ["# KLB: better-placed 4H/1H BUY arrows (EXPLORATORY)", "",
         "Columns: n, per instrument-year, right (KR), zone, coverage of swing lows, excess at L/2, invalidated within L/4, median further drop "
         "(ATR). Tuning < 2024, check >= 2024 (previously studied).", ""]
    for tf, x in out["tfs"].items():
        L += [f"## {tf}: current {CUR}, chosen on tuning {x['chosen']}, **adopted {x['adopted']}**", "",
              "| option | tuning | check | check crypto | check equities |", "|---|---|---|---|---|"]
        for o, S in sorted(x["options"].items(), key=lambda kv: -(kv[1]["tune"]["all"]["right"] or 0)):
            mark = " ←current" if o == CUR else (" ←adopted" if o == x["adopted"] else "")
            L.append(f"| {o}{mark} | {f(S['tune']['all'])} | {f(S['check']['all'])} | {f(S['check']['crypto'])} | {f(S['check']['equities'])} |")
        L.append("")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"run": run, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
