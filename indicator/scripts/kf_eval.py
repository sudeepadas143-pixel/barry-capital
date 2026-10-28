"""KF (reports/KF_CONFIG.md, FROZEN): most frequent arrows that still beat a random entry by 5 points.
EXPLORATORY.

    python scripts/kf_eval.py run | render
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

from research import kenny_freq as KF, kenny_sim as KSIM, kenny_weekly_sell as WS, v5_data as DG, v5_gate as GT  # noqa: E402
from research import v5_ledger as LG, v5_manifest as MF  # noqa: E402

_s = importlib.util.spec_from_file_location("kr_eval", ROOT / "scripts" / "kr_eval.py")
KE = importlib.util.module_from_spec(_s)
_s.loader.exec_module(KE)
_g = importlib.util.spec_from_file_location("kenny_export_pine", ROOT / "scripts" / "kenny_export_pine.py")
KG = importlib.util.module_from_spec(_g)
_g.loader.exec_module(KG)

OUT, MD = ROOT / "reports" / "kf_results.json", ROOT / "reports" / "KF_RESULTS.md"
BUCKET = {"1W": 3, "1D": 2, "4H": 1, "1H": 0}


def current(tf, d):
    b = BUCKET[tf]
    if d == "bot":
        return f"H|{KG.KR_BUY_SCALE[b]}"
    if d == "brk":
        return "BRK"
    return "A" if b == 3 else f"{KG.KR_SELL[b][0]}|{KG.KR_SELL[b][1]}"


def one(args):
    sym, tf = args
    try:
        df = DG.load(sym, tf)
    except Exception:
        return None
    if len(df) < 400:
        return None
    spec = json.loads(KE.SPEC.read_text())
    st = KSIM.states(df, tf, spec)
    c = df["close"].to_numpy(float)
    H = KSIM.CF.SCALE[tf]["L"] // 2
    split = pd.Timestamp(KE.SPLIT[tf], tz="UTC")
    pre = np.asarray(df.index < split)
    grp = KE.GRP.get(DG.EXPLORATION[sym].cls, "other")
    sets = {"bot": KF.options(df, st, tf, 1), "top": KF.options(df, st, tf, -1)}
    if tf == "1W":
        sets["top"]["A"] = WS.cand_A(WS.features(df), 6.0)
    else:
        sets["brk"] = KF.breakdown_options(df, tf)
    rows = []
    for d, opts in sets.items():
        side = 1 if d == "bot" else -1
        base = {"tune": KF.base_rate(c, H, side, pre), "check": KF.base_rate(c, H, side, ~pre)}
        for name, idx in opts.items():
            idx = np.asarray(idx, int)
            if not len(idx):
                continue
            out = KF.outcome(c, idx, H, side)
            for s, v in zip(idx, out):
                if np.isfinite(v):
                    per = "tune" if pre[s] else "check"
                    rows.append({"side": d, "opt": name, "per": per, "grp": grp, "hit": v, "excess": v - base[per],
                                 "ret": side * (c[s + H] / c[s] - 1), "base": base[per]})
    idx = df.index
    yrs = {"tune": max(0.0, (min(split, idx[-1]) - idx[0]).total_seconds() / 3.15576e7),
           "check": max(0.0, (idx[-1] - max(split, idx[0])).total_seconds() / 3.15576e7)}
    return {"rows": rows, "yrs": yrs}


def st_(t, yrs):
    return {"n": int(len(t)), "rate": len(t) / yrs if yrs else 0.0, "excess": float(t["excess"].mean()) if len(t) else None,
            "hit": float(t["hit"].mean()) if len(t) else None, "base": float(t["base"].mean()) if len(t) else None,
            "ret_med": float(t["ret"].median()) if len(t) else None}


def run():
    mode = GT.require_kf_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    LG.record("kf-all", "KF-1", ["exploration"], {"config": GT.KF_CONFIG, "mode": mode}, list(GT.KF_CODE),
              ["rate", "excess", "hit", "base_rate"], True, GT.KF_CONFIG, data_files, notes=f"exploration; review mode {mode}")
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "KF ledger: record trial kf-all (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    out = {"tfs": {}}
    for tf in ("1W", "1D", "4H", "1H"):
        with ProcessPoolExecutor(4) as ex:
            res = [x for x in ex.map(one, [(s, tf) for s in DG.EVAL_SYMBOLS]) if x]
        T = pd.DataFrame([r for x in res for r in x["rows"]])
        yrs = {p: sum(x["yrs"][p] for x in res) for p in ("tune", "check")}
        cell = {}
        for d in sorted(T["side"].unique()):
            Td = T[T["side"] == d]
            S = {o: {p: {"all": st_(Td[(Td["opt"] == o) & (Td["per"] == p)], yrs[p]),
                         **{g: st_(Td[(Td["opt"] == o) & (Td["per"] == p) & (Td["grp"] == g)], yrs[p]) for g in ("equities", "crypto")}}
                     for p in ("tune", "check")} for o in Td["opt"].unique()}
            elig = [o for o, v in S.items() if v["tune"]["all"]["n"] >= 30 and (v["tune"]["all"]["excess"] or -1) >= 0.05]
            chosen = max(elig, key=lambda o: S[o]["tune"]["all"]["rate"]) if elig else None
            cur = current(tf, d)
            ok = bool(chosen and S[chosen]["check"]["all"]["n"] >= 30 and (S[chosen]["check"]["all"]["excess"] or -1) >= 0.03)
            cell[d] = {"options": S, "eligible": elig, "chosen": chosen, "current": cur, "adopted": chosen if ok else cur, "changed": bool(ok and chosen != cur)}
        out["tfs"][tf] = cell
        print(f"[{tf}] done", flush=True)
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))


def render():
    out = json.loads(OUT.read_text())
    f = lambda v: f"{v['n']}, {v['rate']:.2f}/yr, hit {v['hit']:.2f} vs base {v['base']:.2f} (excess {v['excess']:+.2f}), med {v['ret_med'] * 100:+.1f}%" if v["n"] else "0"  # noqa: E731
    L = ["# KF: frequency vs accuracy (EXPLORATORY)", "", "Works out = price higher (BUY) / lower (SELL, ✕) L/2 candles later. Excess = hit − the instrument's own base rate. "
         "Most frequent option with tuning excess >= +0.05, kept if check excess >= +0.03. Check period previously studied.", ""]
    names = {"bot": "BUY", "top": "SELL", "brk": "Breakdown ✕"}
    for tf, cell in out["tfs"].items():
        for d, c in cell.items():
            L += [f"## {tf} {names[d]} — current {c['current']}, chosen {c['chosen']}, **adopted {c['adopted']}**", "",
                  "| option | tune | check | check equities | check crypto |", "|---|---|---|---|---|"]
            for o in [c["adopted"], c["current"]] + [o for o in sorted(c["options"], key=lambda o: -c["options"][o]["tune"]["all"]["rate"]) if o not in (c["adopted"], c["current"])][:6]:
                if o not in c["options"]:
                    continue
                v = c["options"][o]
                tag = " ←adopted" if o == c["adopted"] else (" ←current" if o == c["current"] else "")
                L.append(f"| {o}{tag} | {f(v['tune']['all'])} | {f(v['check']['all'])} | {f(v['check']['equities'])} | {f(v['check']['crypto'])} |")
            L.append("")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"run": run, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
