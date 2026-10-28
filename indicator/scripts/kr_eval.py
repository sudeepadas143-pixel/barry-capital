"""KR (reports/KR_CONFIG.md, FROZEN): choose, per timeframe x side, the Kenny signal option that is
'right enough in retrospect'. EXPLORATORY.

    python scripts/kr_eval.py run | render
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research import kenny_retro as KR, kenny_sim as KSIM, kenny_weekly_sell as WS, v5_data as DG, v5_gate as GT  # noqa: E402
from research import v5_ledger as LG, v5_manifest as MF, weekly_cycle as WC  # noqa: E402

SPEC = ROOT / "reports" / "cycle2_model_spec.json"
OUT, MD = ROOT / "reports" / "kr_results.json", ROOT / "reports" / "KR_RESULTS.md"
TFS = ("1W", "1D", "4H", "1H")
SPLIT = {"1W": "2018-01-01", "1D": "2018-01-01", "4H": "2024-01-01", "1H": "2024-01-01"}
CURRENT = {"bot": "H|1.0", "top": "CONF|1.0"}
GRP = {"equity": "equities", "equity_index": "equities", "crypto": "crypto"}


def one(args):
    sym, tf = args
    try:
        df = DG.load(sym, tf)
    except Exception:
        return None
    if len(df) < 400:
        return None
    spec = json.loads(SPEC.read_text())
    st = KSIM.states(df, tf, spec)
    split = pd.Timestamp(SPLIT[tf], tz="UTC")
    idx = df.index
    grp = GRP.get(DG.EXPLORATION[sym].cls, "other")
    rows, cov = [], []
    for d, side in (("bot", 1), ("top", -1)):
        opts = KR.options(df, st, tf, side)
        if tf == "1W" and d == "top":
            opts["A"] = WS.cand_A(WS.features(df), 6.0)
            opts["WCE"] = WC.signals(WC.features(df), "top")["warn"]
        sw = KR.swings(df, tf, side)
        L = KSIM.CF.SCALE[tf]["L"]
        for name, sig in opts.items():
            sig = np.asarray(sig, int)
            sc = KR.score(df, tf, sig, side)
            for s, (z, f, ok) in zip(sig, sc):
                if np.isfinite(ok):
                    rows.append({"side": d, "opt": name, "per": "tune" if idx[s] < split else "check", "grp": grp, "sym": sym,
                                 "zone": z, "follow": f, "right": ok})
            right_idx = sig[np.nan_to_num(sc[:, 2]) > 0] if len(sig) else sig
            for k in sw:
                cov.append({"side": d, "opt": name, "per": "tune" if idx[k] < split else "check", "grp": grp,
                            "hit": bool(((right_idx >= k - L // 4) & (right_idx <= k + L // 4)).any())})
    yrs = {"tune": max(0.0, (min(split, idx[-1]) - idx[0]).total_seconds() / 3.15576e7),
           "check": max(0.0, (idx[-1] - max(split, idx[0])).total_seconds() / 3.15576e7)}
    return {"sym": sym, "grp": grp, "rows": rows, "cov": cov, "yrs": yrs}


def summ(T, Cv, yrs, side, opt, per, grp=None):
    t = T[(T["side"] == side) & (T["opt"] == opt) & (T["per"] == per)]
    c = Cv[(Cv["side"] == side) & (Cv["opt"] == opt) & (Cv["per"] == per)]
    if grp:
        t, c = t[t["grp"] == grp], c[c["grp"] == grp]
    return {"n": int(len(t)), "rate": len(t) / yrs if yrs else 0.0, "right": float(t["right"].mean()) if len(t) else np.nan,
            "zone": float(t["zone"].mean()) if len(t) else np.nan, "follow": float(t["follow"].mean()) if len(t) else np.nan,
            "coverage": float(c["hit"].mean()) if len(c) else np.nan, "n_swings": int(len(c))}


def run():
    mode = GT.require_kr_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    LG.record("kr-all", "KR-1", ["exploration"], {"config": GT.KR_CONFIG, "mode": mode}, list(GT.KR_CODE),
              ["right_rate", "zone", "follow", "coverage", "rate"], True, GT.KR_CONFIG, data_files, notes=f"exploration; review mode {mode}")
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "KR ledger: record trial kr-all (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    out = {"tfs": {}}
    for tf in TFS:
        with ProcessPoolExecutor(4) as ex:
            res = [x for x in ex.map(one, [(s, tf) for s in DG.EVAL_SYMBOLS]) if x]
        T = pd.DataFrame([r for x in res for r in x["rows"]])
        Cv = pd.DataFrame([r for x in res for r in x["cov"]])
        yrs = {p: sum(x["yrs"][p] for x in res) for p in ("tune", "check")}
        gy = {g: {p: sum(x["yrs"][p] for x in res if x["grp"] == g) for p in ("tune", "check")} for g in ("equities", "crypto")}
        cell = {}
        for d in ("bot", "top"):
            opts = sorted(T[T["side"] == d]["opt"].unique())
            S = {o: {p: {"all": summ(T, Cv, yrs[p], d, o, p), **{g: summ(T, Cv, gy[g][p], d, o, p, g) for g in ("equities", "crypto")}}
                     for p in ("tune", "check")} for o in opts}
            cur = S[CURRENT[d]]
            elig = [o for o in opts if S[o]["tune"]["all"]["n"] >= 30 and S[o]["tune"]["all"]["rate"] >= 0.5 * cur["tune"]["all"]["rate"]
                    and S[o]["tune"]["all"]["coverage"] >= cur["tune"]["all"]["coverage"] - 0.05]
            chosen = max(elig, key=lambda o: S[o]["tune"]["all"]["right"]) if elig else CURRENT[d]
            ch, cu = S[chosen]["check"]["all"], cur["check"]["all"]
            adopt = chosen != CURRENT[d] and ch["right"] >= cu["right"] and ch["coverage"] >= cu["coverage"] - 0.05
            cell[d] = {"options": S, "eligible": elig, "chosen": chosen, "adopted": chosen if adopt else CURRENT[d], "changed": bool(adopt)}
        out["tfs"][tf] = {"instruments": len(res), "asset_years": yrs, "cells": cell}
        print(f"[{tf}] done", flush=True)
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))


def render():
    out = json.loads(OUT.read_text())
    L = ["# KR: 'right enough in retrospect' (EXPLORATORY)", "",
         "Right = close in the lowest/highest 25% of the +-L/2 range AND price moved the signal's way after L/4 candles. "
         "Coverage = share of meaningful swings (range >= 4 ATR) with a right signal within +-L/4. Tuning <2018 (1W/1D) or <2024 (4H/1H); "
         "check period previously studied.", ""]
    for tf, T in out["tfs"].items():
        L += [f"## {tf} ({T['instruments']} instruments)", ""]
        for d in ("bot", "top"):
            c = T["cells"][d]
            L += [f"**{'BUY' if d == 'bot' else 'SELL'}** — current {CURRENT[d]}, chosen on tuning {c['chosen']}, **adopted {c['adopted']}**", "",
                  "| option | tune: n, /yr, right, zone, follow, coverage | check: n, /yr, right, zone, follow, coverage | check equities right (n) | check crypto right (n) |",
                  "|---|---|---|---|---|"]
            for o, S in sorted(c["options"].items(), key=lambda kv: -(kv[1]["tune"]["all"]["right"] or 0)):
                f = lambda v: f"{v['n']}, {v['rate']:.2f}, {v['right']:.2f}, {v['zone']:.2f}, {v['follow']:.2f}, {v['coverage']:.2f}" if v["n"] else "0"  # noqa: E731
                g = lambda v: f"{v['right']:.2f} ({v['n']})" if v["n"] else "– (0)"  # noqa: E731
                mark = " ←current" if o == CURRENT[d] else (" ←adopted" if o == c["adopted"] else "")
                L.append(f"| {o}{mark} | {f(S['tune']['all'])} | {f(S['check']['all'])} | {g(S['check']['equities'])} | {g(S['check']['crypto'])} |")
            L.append("")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"run": run, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
