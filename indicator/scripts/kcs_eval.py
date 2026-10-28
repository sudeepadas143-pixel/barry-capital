"""KCS (reports/KCS_CONFIG.md, FROZEN). EXPLORATORY.

    python scripts/kcs_eval.py run | render
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

from research import kenny_closeshort as CS, kenny_freq as KF, kenny_retro as KR, kenny_sim as KSIM, v5_data as DG, v5_gate as GT  # noqa: E402
from research import v5_ledger as LG, v5_manifest as MF  # noqa: E402
from research.kb_signals import cooldown  # noqa: E402

_s = importlib.util.spec_from_file_location("kr_eval", ROOT / "scripts" / "kr_eval.py")
KE = importlib.util.module_from_spec(_s)
_s.loader.exec_module(KE)
_g = importlib.util.spec_from_file_location("kenny_export_pine", ROOT / "scripts" / "kenny_export_pine.py")
KG = importlib.util.module_from_spec(_g)
_g.loader.exec_module(KG)

OUT, MD = ROOT / "reports" / "kcs_results.json", ROOT / "reports" / "KCS_RESULTS.md"
BUCKET = {"1W": 3, "1D": 2, "4H": 1, "1H": 0}


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
    L = KSIM.CF.SCALE[tf]["L"]
    c = KSIM.CF.q_of(L)
    b = BUCKET[tf]
    buy = cooldown(KSIM.CF.zone_onsets(st["bot"]["p"], st["bot"]["theta"]["high"] * KG.KR_BUY_SCALE[b], c), c)
    cs = CS.close_short(df)
    conf = CS.confluence(buy, cs, L // 4)
    cl = df["close"].to_numpy(float)
    H = L // 2
    split = pd.Timestamp(KE.SPLIT[tf], tz="UTC")
    pre = np.asarray(df.index < split)
    base = {True: KF.base_rate(cl, H, 1, pre), False: KF.base_rate(cl, H, 1, ~pre)}
    grp = KE.GRP.get(DG.EXPLORATION[sym].cls, "other")
    rows = []
    for name, idx in (("BUY", buy), ("CS", cs), ("BUY+CS", conf)):
        idx = np.asarray(idx, int)
        if not len(idx):
            continue
        out = KF.outcome(cl, idx, H, 1)
        sc = KR.score(df, tf, idx, 1)
        inv = CS.invalidated(df, idx, L // 4)
        for j, s in enumerate(idx):
            rows.append({"name": name, "per": "tune" if pre[s] else "check", "grp": grp,
                         "excess": out[j] - base[bool(pre[s])] if np.isfinite(out[j]) else np.nan, "right": sc[j, 2], "inv": inv[j]})
    idx = df.index
    yrs = {"tune": max(0.0, (min(split, idx[-1]) - idx[0]).total_seconds() / 3.15576e7),
           "check": max(0.0, (idx[-1] - max(split, idx[0])).total_seconds() / 3.15576e7)}
    return {"rows": rows, "yrs": yrs}


def st_(t, yrs):
    return {"n": int(len(t)), "rate": len(t) / yrs if yrs else 0.0, "excess": float(np.nanmean(t["excess"])) if len(t) else None,
            "right": float(np.nanmean(t["right"])) if len(t) else None, "invalidated": float(np.nanmean(t["inv"])) if len(t) else None}


def run():
    mode = GT.require_kcs_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    LG.record("kcs-all", "KCS-1", ["exploration"], {"config": GT.KCS_CONFIG, "mode": mode}, list(GT.KCS_CODE),
              ["excess", "right_rate", "invalidation", "rate"], True, GT.KCS_CONFIG, data_files, notes=f"exploration; review mode {mode}")
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "KCS ledger: record trial kcs-all (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    out = {"tfs": {}}
    for tf in ("1W", "1D", "4H", "1H"):
        with ProcessPoolExecutor(4) as ex:
            res = [x for x in ex.map(one, [(s, tf) for s in DG.EVAL_SYMBOLS]) if x]
        T = pd.DataFrame([r for x in res for r in x["rows"]])
        yrs = {p: sum(x["yrs"][p] for x in res) for p in ("tune", "check")}
        S = {nm: {p: {"all": st_(T[(T["name"] == nm) & (T["per"] == p)], yrs[p]),
                      **{g: st_(T[(T["name"] == nm) & (T["per"] == p) & (T["grp"] == g)], yrs[p]) for g in ("equities", "crypto")}}
                  for p in ("tune", "check")} for nm in ("BUY", "CS", "BUY+CS")}
        cs_ok = all(S["CS"][p]["all"]["n"] >= 30 and (S["CS"][p]["all"]["excess"] or -1) >= 0.03 for p in ("tune", "check"))
        cf_ok = all(S["BUY+CS"][p]["all"]["n"] >= 20 and S["BUY+CS"][p]["all"]["excess"] is not None
                    and S["BUY+CS"][p]["all"]["excess"] >= S["BUY"][p]["all"]["excess"] + 0.03
                    and S["BUY+CS"][p]["all"]["right"] >= S["BUY"][p]["all"]["right"] - 0.05 for p in ("tune", "check"))
        out["tfs"][tf] = {"stats": S, "show_cs": bool(cs_ok), "show_confluence": bool(cf_ok)}
        print(f"[{tf}] done", flush=True)
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))


def render():
    out = json.loads(OUT.read_text())
    f = lambda v: f"n {v['n']} ({v['rate']:.2f}/yr), excess {v['excess']:+.2f}, right {v['right']:.2f}, invalidated {v['invalidated']:.2f}" if v["n"] else "n 0"  # noqa: E731
    L = ["# KCS: Close Short and BUY + Close Short confluence (EXPLORATORY)", "", "Excess = price higher L/2 later vs the instrument's base rate; right = KR rule; "
         "invalidated = new low below the signal candle within L/4. Check period previously studied.", "",
         "| TF · signal | tuning | check | check equities | check crypto |", "|---|---|---|---|---|"]
    for tf, x in out["tfs"].items():
        for nm in ("BUY", "CS", "BUY+CS"):
            v = x["stats"][nm]
            L.append(f"| {tf} · {nm} | {f(v['tune']['all'])} | {f(v['check']['all'])} | {f(v['check']['equities'])} | {f(v['check']['crypto'])} |")
        L.append(f"| {tf} · **shown** | Close Short marker: {'**yes**' if x['show_cs'] else 'no'} | BUY+CS emphasis: {'**yes**' if x['show_confluence'] else 'no'} | | |")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"run": run, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
