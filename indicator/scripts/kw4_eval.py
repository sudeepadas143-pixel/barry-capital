"""KW-4 (reports/KW4_CONFIG.md, FROZEN): three Candidate A variants for the weekly SELL, scored with
the KW-3 evaluator and the unchanged KW-3 adoption rule. EXPLORATORY; tuning < 2018.

    python scripts/kw4_eval.py eval | render
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

from research import kenny_weekly_sell as WS, v5_data as DG, v5_gate as GT, v5_ledger as LG  # noqa: E402

_s = importlib.util.spec_from_file_location("kw3_eval", ROOT / "scripts" / "kw3_eval.py")
KE = importlib.util.module_from_spec(_s)
sys.modules["kw3_eval"] = KE
_s.loader.exec_module(KE)

OUT, MD = ROOT / "reports" / "kw4_results.json", ROOT / "reports" / "KW4_RESULTS.md"
GRID = {"A": [6.0], "A1": [2.0, 3.0], "A2": [2, 4], "A3": [1.5, 2.5]}
VARIANTS = ("A1", "A2", "A3")


def signals(f, st, low, cand, prm):
    if cand == "A":
        return WS.cand_A(f, prm)
    if cand == "A1":
        return WS.cand_A1(f, prm)
    if cand == "A2":
        return WS.cand_A2(f, int(prm), low)
    if cand == "A3":
        return WS.cand_A3(f, prm)
    raise ValueError(cand)


KE.signals = signals                       # the KW-3 evaluator dispatches through this name


def breadth(T, name, ref, period):
    """Share of instruments (>= 3 signals for both) where `name` has a higher useful rate than `ref`."""
    T = T[(T["t"] < KE.SPLIT) if period == "pre" else (T["t"] >= KE.SPLIT)]
    a = T[T["name"] == name].groupby("sym")["class"].agg(lambda x: ((x == "useful").mean(), len(x)))
    b = T[T["name"] == ref].groupby("sym")["class"].agg(lambda x: ((x == "useful").mean(), len(x)))
    common = [s for s in a.index if s in b.index and a[s][1] >= 3 and b[s][1] >= 3]
    if not common:
        return {"n_inst": 0, "share_better": None}
    return {"n_inst": len(common), "share_better": float(np.mean([a[s][0] > b[s][0] for s in common]))}


def evaluate():
    mode = GT.require_kw4_ready()
    LG.record("kw4-eval", "KW-4", ["exploration"], {"config": GT.KW4_CONFIG, "mode": mode}, list(GT.KW4_CODE),
              ["useful_rate", "premature_rate", "top_catch", "lag", "rate", "forward_return", "breadth"], True,
              GT.KW4_CONFIG, KE._data_files(), notes=f"exploration; review mode {mode}")
    KE._commit_ledger("kw4-eval")
    with ProcessPoolExecutor(4) as ex:
        res = [x for x in ex.map(KE.metrics_one, DG.EVAL_SYMBOLS, [GRID] * len(DG.EVAL_SYMBOLS)) if x]
    T = pd.DataFrame([row for x in res for row in x["rows"]])
    tops = pd.DataFrame([t for x in res for t in x["tops"]])
    chosen, wf = {}, []
    for cand, prms in GRID.items():
        for y in range(2012, 2027):
            hist = T[T["t"] < pd.Timestamp(f"{y}-01-01", tz="UTC") - pd.Timedelta(weeks=27)]
            best, bu = prms[0], -1.0
            for prm in prms:
                g = hist[hist["name"] == f"{cand}|{prm}"]
                if len(g) >= 25 and (u := (g["class"] == "useful").mean()) > bu:
                    best, bu = prm, u
            yr = T[(T["name"] == f"{cand}|{best}") & (T["t"] >= pd.Timestamp(f"{y}-01-01", tz="UTC")) & (T["t"] < pd.Timestamp(f"{y + 1}-01-01", tz="UTC"))]
            wf.append(yr.assign(name=f"{cand}|WF"))
        pre = T[(T["t"] < KE.SPLIT)]
        ok = {p: (pre[pre["name"] == f"{cand}|{p}"]["class"] == "useful").mean() for p in prms if (pre["name"] == f"{cand}|{p}").sum() >= 25}
        chosen[cand] = max(ok, key=ok.get) if ok else prms[0]
        tops[f"{cand}|WF"] = tops[f"{cand}|{chosen[cand]}"]
    T = pd.concat([T, *wf], ignore_index=True)
    R = {"T": T, "tops": tops, "res": res}
    names = ["W0", "RSI70", *[f"{c}|WF" for c in GRID]]
    out = {"chosen": chosen, "results": {}, "breadth": {}}
    for nm in names:
        out["results"][nm] = {p: {"all": KE.summary(R, nm, p), **{g: KE.summary(R, nm, p, g) for g in ("equities", "crypto", "other")}} for p in ("pre", "post")}
    for v in VARIANTS:
        out["breadth"][v] = {p: {"vs_W0": breadth(T, f"{v}|WF", "W0", p), "vs_A": breadth(T, f"{v}|WF", "A|WF", p)} for p in ("pre", "post")}
    out["adopt"] = KE.adopt(out, {v: GRID[v] for v in VARIANTS})              # the unchanged KW-3 rule, vs W0
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print("done", flush=True)


def render():
    out = json.loads(OUT.read_text())
    KE.OUT, KE.MD = OUT, MD
    KE.render()
    txt = MD.read_text().replace("# KW-3: weekly SELL recovery", "# KW-4: Candidate A variants for the weekly SELL")
    txt = txt.replace("Config `reports/KW3_CONFIG.md`", "Config `reports/KW4_CONFIG.md` (adoption rule of KW3_CONFIG.md, unchanged)")
    add = ["", "## Breadth (share of instruments with >= 3 signals each where the variant's useful rate is higher)", "",
           "| variant | period | vs W0 (n inst) | vs A (n inst) |", "|---|---|---|---|"]
    for v, d in out["breadth"].items():
        for p, x in d.items():
            f = lambda b: "–" if b["share_better"] is None else f"{b['share_better']:.2f} ({b['n_inst']})"  # noqa: E731
            add.append(f"| {v} | {'<2018' if p == 'pre' else '2018+'} | {f(x['vs_W0'])} | {f(x['vs_A'])} |")
    MD.write_text(txt + "\n".join(add) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"eval": evaluate, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
