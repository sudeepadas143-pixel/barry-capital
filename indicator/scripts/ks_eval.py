"""KS (reports/KS_CONFIG.md, FROZEN): strength tiers for the Optimized arrows. EXPLORATORY.

    python scripts/ks_eval.py run | render
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

from research import kenny_retro as KR, kenny_sim as KSIM, kenny_strength as KST, kenny_weekly_sell as WS  # noqa: E402
from research import kenny_cluster as KC, v5_data as DG, v5_gate as GT, v5_ledger as LG, v5_manifest as MF  # noqa: E402

_s = importlib.util.spec_from_file_location("kr_eval", ROOT / "scripts" / "kr_eval.py")
KE = importlib.util.module_from_spec(_s)
_s.loader.exec_module(KE)
_g = importlib.util.spec_from_file_location("kenny_export_pine", ROOT / "scripts" / "kenny_export_pine.py")
KG = importlib.util.module_from_spec(_g)
_g.loader.exec_module(KG)

OUT, MD = ROOT / "reports" / "ks_results.json", ROOT / "reports" / "KS_RESULTS.md"
BUCKET = {"1W": 3, "1D": 2, "4H": 1, "1H": 0}


def arrows(df, tf, st):
    """The Optimized-profile arrows (as in Pine) with their threshold for the margin component."""
    b = BUCKET[tf]
    L = KSIM.CF.SCALE[tf]["L"]
    c = KSIM.CF.q_of(L)
    from research.kb_signals import cooldown
    thb = st["bot"]["theta"]["high"] * KG.KR_BUY_SCALE[b]
    buy = cooldown(KSIM.CF.zone_onsets(st["bot"]["p"], thb, c), c)
    if b == 3:
        wsf = WS.features(df)
        return {"bot": (buy, "score", thb, None), "top": (WS.cand_A(wsf, 6.0), "A", None, wsf)}
    state, sc = KG.KR_SELL[b]
    tht = st["top"]["theta"]["high" if state == "H" else "warning"] * sc
    sell = cooldown(KSIM.CF.zone_onsets(st["top"]["p"], tht, c), c)
    return {"bot": (buy, "score", thb, None), "top": (sell, "score", tht, None)}


def one(args):
    sym, tf = args
    try:
        df = DG.load(sym, tf)
    except Exception:
        return None
    if len(df) < 400:
        return None
    try:
        htf = DG.load(sym, KC.HTF_OF[tf])
    except Exception:
        htf = None
    spec = json.loads(KE.SPEC.read_text())
    st = KSIM.states(df, tf, spec)
    split = pd.Timestamp(KE.SPLIT[tf], tz="UTC")
    grp = KE.GRP.get(DG.EXPLORATION[sym].cls, "other")
    rows = []
    for d, side in (("bot", 1), ("top", -1)):
        idx, kind, thr, wsf = arrows(df, tf, st)[d]
        if not len(idx):
            continue
        comp = KST.components(df, tf, st, htf, side, idx, kind, thr, wsf)
        sc = KR.score(df, tf, idx, side)
        for j, s in enumerate(idx):
            if np.isfinite(sc[j, 2]):
                rows.append({"side": d, "per": "tune" if df.index[s] < split else "check", "grp": grp, "sym": sym,
                             "right": sc[j, 2], "zone": sc[j, 0], "follow": sc[j, 1],
                             **{k: int(v[j]) for k, v in comp.items()}})
    idx = df.index
    yrs = {"tune": max(0.0, (min(split, idx[-1]) - idx[0]).total_seconds() / 3.15576e7),
           "check": max(0.0, (idx[-1] - max(split, idx[0])).total_seconds() / 3.15576e7)}
    return {"rows": rows, "yrs": yrs, "grp": grp}


def run():
    mode = GT.require_ks_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    LG.record("ks-all", "KS-1", ["exploration"], {"config": GT.KS_CONFIG, "mode": mode}, list(GT.KS_CODE),
              ["right_rate", "rate", "component_effects"], True, GT.KS_CONFIG, data_files, notes=f"exploration; review mode {mode}")
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "KS ledger: record trial ks-all (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    out = {"tfs": {}}
    for tf in ("1W", "1D", "4H", "1H"):
        with ProcessPoolExecutor(4) as ex:
            res = [x for x in ex.map(one, [(s, tf) for s in DG.EVAL_SYMBOLS]) if x]
        T = pd.DataFrame([r for x in res for r in x["rows"]])
        yrs = {p: sum(x["yrs"][p] for x in res) for p in ("tune", "check")}
        cell = {}
        for d in ("bot", "top"):
            Td = T[T["side"] == d]
            tune, chk = Td[Td["per"] == "tune"], Td[Td["per"] == "check"]
            info = {"all": {"tune": {"n": len(tune), "right": float(tune["right"].mean()), "rate": len(tune) / yrs["tune"]},
                            "check": {"n": len(chk), "right": float(chk["right"].mean()), "rate": len(chk) / yrs["check"]}},
                    "components": {k: {"with": float(tune[tune[k] > 0]["right"].mean()) if (tune[k] > 0).any() else None,
                                       "without": float(tune[tune[k] == 0]["right"].mean()) if (tune[k] == 0).any() else None,
                                       "share": float((tune[k] > 0).mean())} for k in ("M", "E", "H")}, "tiers": {}}
            best, bval = 0, -1.0
            for k in (1, 2, 3):
                t, c = tune[tune["S"] >= k], chk[chk["S"] >= k]
                info["tiers"][k] = {"tune": {"n": len(t), "right": float(t["right"].mean()) if len(t) else None, "share": len(t) / max(1, len(tune)),
                                             "rate": len(t) / yrs["tune"]},
                                    "check": {"n": len(c), "right": float(c["right"].mean()) if len(c) else None, "share": len(c) / max(1, len(chk)),
                                              "rate": len(c) / yrs["check"],
                                              **{g: (float(c[c["grp"] == g]["right"].mean()) if (c["grp"] == g).any() else None, int((c["grp"] == g).sum()))
                                                 for g in ("equities", "crypto")}}}
                if len(t) >= 30 and len(t) >= 0.2 * len(tune) and t["right"].mean() > bval:
                    best, bval = k, t["right"].mean()
            adopt = bool(best and info["tiers"][best]["check"]["n"] and info["tiers"][best]["check"]["right"] >= info["all"]["check"]["right"] + 0.03)
            info.update({"chosen_k": best, "adopted_k": best if adopt else 0})
            cell[d] = info
        out["tfs"][tf] = cell
        print(f"[{tf}] done", flush=True)
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))


def render():
    out = json.loads(OUT.read_text())
    f2 = lambda x: "–" if x is None else f"{x:.2f}"  # noqa: E731
    L = ["# KS: strong arrows only (EXPLORATORY)", "", "Strength S = M (margin) + E (independent evidence, 0-3) + H (higher-timeframe agrees). "
         "Right = KR rule. Tuning <2018 (1W/1D) or <2024 (4H/1H); check period previously studied.", ""]
    for tf, cell in out["tfs"].items():
        for d in ("bot", "top"):
            x = cell[d]
            L += [f"## {tf} {'BUY' if d == 'bot' else 'SELL'} — strong cut-off chosen S >= {x['chosen_k']}, **adopted: "
                  f"{'S >= ' + str(x['adopted_k']) if x['adopted_k'] else 'all arrows (no filter)'}**", "",
                  f"All arrows: tune right {f2(x['all']['tune']['right'])} (n {x['all']['tune']['n']}, {x['all']['tune']['rate']:.2f}/yr); "
                  f"check right {f2(x['all']['check']['right'])} (n {x['all']['check']['n']}, {x['all']['check']['rate']:.2f}/yr).", "",
                  "Component effects on tuning (right-rate with / without; share of arrows with it): " +
                  "; ".join(f"{k} {f2(v['with'])}/{f2(v['without'])} ({v['share']:.2f})" for k, v in x["components"].items()), "",
                  "| S >= | tune: n, share, right | check: n, share, /yr, right | check equities right (n) | check crypto right (n) |", "|---|---|---|---|---|"]
            for k, v in x["tiers"].items():
                t, c = v["tune"], v["check"]
                L.append(f"| {k} | {t['n']}, {t['share']:.2f}, {f2(t['right'])} | {c['n']}, {c['share']:.2f}, {c['rate']:.2f}, {f2(c['right'])} | "
                         f"{f2(c['equities'][0])} ({c['equities'][1]}) | {f2(c['crypto'][0])} ({c['crypto'][1]}) |")
            L.append("")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"run": run, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
