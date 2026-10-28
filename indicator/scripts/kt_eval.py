"""KT (reports/KT_CONFIG.md, FROZEN): four extra signal types vs their baselines. EXPLORATORY.

    python scripts/kt_eval.py run | render
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

from research import kenny_sim as KSIM, kenny_types as KT, v5_data as DG, v5_gate as GT, v5_ledger as LG, v5_manifest as MF  # noqa: E402

_s = importlib.util.spec_from_file_location("kr_eval", ROOT / "scripts" / "kr_eval.py")
KE = importlib.util.module_from_spec(_s)
_s.loader.exec_module(KE)

OUT, MD = ROOT / "reports" / "kt_results.json", ROOT / "reports" / "KT_RESULTS.md"
TYPES = ("CAU", "CONT", "BRK", "EARLY")
EARLY_SCALES = (0.9, 1.0, 1.1)


def one(args):
    sym, tf = args
    try:
        df = DG.load(sym, tf)
    except Exception:
        return None
    if len(df) < 400:
        return None
    b = KT.base(df, tf)
    spec = json.loads(KE.SPEC.read_text())
    st = KSIM.states(df, tf, spec)
    split = pd.Timestamp(KE.SPLIT[tf], tz="UTC")
    grp = KE.GRP.get(DG.EXPLORATION[sym].cls, "other")
    sets = {"CONT": KT.continuation(b), "BRK": KT.breakdown(b), **{f"EARLY|{sc}": KT.early(st, tf, sc) for sc in EARLY_SCALES}}
    if tf != "1W":
        sets["CAU"] = KT.caution(b)
    rows = []
    for name, idx in sets.items():
        kind = name.split("|")[0]
        for s in idx:
            v = KT.test(kind, b, int(s))
            if np.isfinite(v):
                rows.append({"name": name, "per": "tune" if df.index[s] < split else "check", "grp": grp, "hit": v})
    base = []
    for kind in TYPES:
        if kind == "CAU" and tf == "1W":
            continue
        m = np.flatnonzero(KT.baseline_mask(kind, b))
        for s in m[::3]:                                              # every 3rd qualifying candle (rate estimate)
            v = KT.test(kind, b, int(s))
            if np.isfinite(v):
                base.append({"kind": kind, "per": "tune" if df.index[s] < split else "check", "grp": grp, "hit": v})
    idx = df.index
    yrs = {"tune": max(0.0, (min(split, idx[-1]) - idx[0]).total_seconds() / 3.15576e7),
           "check": max(0.0, (idx[-1] - max(split, idx[0])).total_seconds() / 3.15576e7)}
    return {"rows": rows, "base": base, "yrs": yrs}


def run():
    mode = GT.require_kt_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    LG.record("kt-all", "KT-1", ["exploration"], {"config": GT.KT_CONFIG, "mode": mode}, list(GT.KT_CODE),
              ["hit_rate", "baseline_hit_rate", "rate"], True, GT.KT_CONFIG, data_files, notes=f"exploration; review mode {mode}")
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "KT ledger: record trial kt-all (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    out = {"tfs": {}}
    for tf in ("1W", "1D", "4H", "1H"):
        with ProcessPoolExecutor(4) as ex:
            res = [x for x in ex.map(one, [(s, tf) for s in DG.EVAL_SYMBOLS]) if x]
        T = pd.DataFrame([r for x in res for r in x["rows"]])
        B = pd.DataFrame([r for x in res for r in x["base"]])
        yrs = {p: sum(x["yrs"][p] for x in res) for p in ("tune", "check")}
        cell = {}
        for kind in TYPES:
            if kind == "CAU" and tf == "1W":
                continue
            names = [f"EARLY|{sc}" for sc in EARLY_SCALES] if kind == "EARLY" else [kind]
            bs = {p: float(B[(B["kind"] == kind) & (B["per"] == p)]["hit"].mean()) for p in ("tune", "check")}
            stats = {}
            for nm in names:
                stats[nm] = {}
                for p in ("tune", "check"):
                    t = T[(T["name"] == nm) & (T["per"] == p)]
                    stats[nm][p] = {"n": int(len(t)), "rate": len(t) / yrs[p] if yrs[p] else 0.0, "hit": float(t["hit"].mean()) if len(t) else None,
                                    **{g: (float(t[t["grp"] == g]["hit"].mean()) if (t["grp"] == g).any() else None, int((t["grp"] == g).sum()))
                                       for g in ("equities", "crypto")}}
            chosen = max(names, key=lambda nm: (stats[nm]["tune"]["hit"] or -1)) if len(names) > 1 else names[0]
            x = stats[chosen]
            ok = all(x[p]["n"] >= 30 and x[p]["hit"] is not None and x[p]["hit"] >= bs[p] + 0.05 for p in ("tune", "check"))
            cell[kind] = {"baseline": bs, "stats": stats, "chosen": chosen, "adopted": bool(ok)}
        out["tfs"][tf] = cell
        print(f"[{tf}] done", flush=True)
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))


def render():
    out = json.loads(OUT.read_text())
    f2 = lambda x: "–" if x is None else f"{x:.2f}"  # noqa: E731
    L = ["# KT: extra signal types vs baselines (EXPLORATORY)", "", "Hit = the type's own success test (reports/KT_CONFIG.md). "
         "Tuning <2018 (1W/1D) or <2024 (4H/1H); check period previously studied.", "",
         "| TF · type | chosen | tune: n, /yr, hit vs baseline | check: n, /yr, hit vs baseline | check equities hit (n) | check crypto hit (n) | shown |",
         "|---|---|---|---|---|---|---|"]
    for tf, cell in out["tfs"].items():
        for kind, v in cell.items():
            x = v["stats"][v["chosen"]]
            t, c = x["tune"], x["check"]
            L.append(f"| {tf} · {kind} | {v['chosen']} | {t['n']}, {t['rate']:.2f}, {f2(t['hit'])} vs {f2(v['baseline']['tune'])} | "
                     f"{c['n']}, {c['rate']:.2f}, {f2(c['hit'])} vs {f2(v['baseline']['check'])} | {f2(c['equities'][0])} ({c['equities'][1]}) | "
                     f"{f2(c['crypto'][0])} ({c['crypto'][1]}) | {'**yes**' if v['adopted'] else 'no'} |")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"run": run, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
