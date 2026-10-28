"""KW-5 (reports/KW5_CONFIG.md, FROZEN): two-state weekly SELL (early warning -> confirmation).
No tuning; KW-3 evaluator and adoption rule unchanged. EXPLORATORY.

    python scripts/kw5_eval.py eval | render
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

OUT, MD = ROOT / "reports" / "kw5_results.json", ROOT / "reports" / "KW5_RESULTS.md"
GRID = {"A": [WS.EW_R], "CF": [WS.CF_WINDOW], "EWCF": [WS.CF_WINDOW]}


def signals(f, st, low, cand, prm):
    ew, _, cf = WS.two_state(f, low)
    return {"A": ew, "CF": cf, "EWCF": np.union1d(ew, cf)}[cand]


KE.signals = signals


def outcome(h, l, c, atr, s, prior_dd):
    o = {"class": WS.classify(h, l, c, atr, s, prior_dd[s])}
    for H in (4, 13, 26):
        o[f"dec{H}"] = WS.decline_within(h, l, c, atr, s, H)
        o[f"f{H}"] = -(c[s + H] / c[s] - 1) if s + H < len(c) else np.nan
    return o


def conditional_one(sym):
    p = KE.prep(sym)
    if p is None:
        return []
    r, df, st, s0, f, (o, h, l, c), prior_dd = p
    idx = r["idx"]
    grp = KE.CLASS_OF.get(r["cls"], "other")
    ew, per, _ = WS.two_state(f, l)
    rows = []
    for w, k in zip(ew, per):
        if idx[w] < KE.START:
            continue
        row = {"sym": sym, "grp": grp, "t": idx[w], "confirmed": k >= 0, **{f"ew_{a}": b for a, b in outcome(h, l, c, f["atr"], w, prior_dd).items()}}
        if k >= 0:
            row.update({"delay": int(k - w), "cost_wait": float(-(c[k] / c[w] - 1)), "dd_at_cf": float(f["dd52"][k]),
                        **{f"cf_{a}": b for a, b in outcome(h, l, c, f["atr"], k, prior_dd).items()}})
        rows.append(row)
    return rows


def _cond_summary(T, prefix):
    if not len(T):
        return {"n": 0}
    cls = T[f"{prefix}_class"].value_counts(normalize=True)
    return {"n": int(len(T)), **{k: float(cls.get(k, 0)) for k in ("useful", "premature", "late", "false_reversal", "flat")},
            **{f"dec{h}": float(np.nanmean(T[f"{prefix}_dec{h}"])) for h in (4, 13, 26)},
            **{f"f{h}_med": float(np.nanmedian(T[f"{prefix}_f{h}"])) for h in (4, 13, 26)}}


def evaluate():
    mode = GT.require_kw5_ready()
    LG.record("kw5-eval", "KW-5", ["exploration"], {"config": GT.KW5_CONFIG, "mode": mode}, list(GT.KW5_CODE),
              ["conditional_outcomes", "delay", "cost_of_waiting", "useful_rate", "top_catch", "lag"], True,
              GT.KW5_CONFIG, KE._data_files(), notes=f"exploration; review mode {mode}")
    KE._commit_ledger("kw5-eval")
    with ProcessPoolExecutor(4) as ex:
        res = [x for x in ex.map(KE.metrics_one, DG.EVAL_SYMBOLS, [GRID] * len(DG.EVAL_SYMBOLS)) if x]
        cond = [row for rs in ex.map(conditional_one, DG.EVAL_SYMBOLS) for row in rs]
    T = pd.DataFrame([row for x in res for row in x["rows"]])
    tops = pd.DataFrame([t for x in res for t in x["tops"]])
    for cand, prms in GRID.items():                                  # no tuning: the single setting is the |WF series
        T = pd.concat([T, T[T["name"] == f"{cand}|{prms[0]}"].assign(name=f"{cand}|WF")], ignore_index=True)
        tops[f"{cand}|WF"] = tops[f"{cand}|{prms[0]}"]
    R = {"T": T, "tops": tops, "res": res}
    out = {"results": {}, "conditional": {}}
    for nm in ("W0", "RSI70", "A|WF", "CF|WF", "EWCF|WF"):
        out["results"][nm] = {p: {"all": KE.summary(R, nm, p), **{g: KE.summary(R, nm, p, g) for g in ("equities", "crypto", "other")}} for p in ("pre", "post")}
    D = pd.DataFrame(cond)
    for p in ("pre", "post"):
        Dp = D[(D["t"] < KE.SPLIT) if p == "pre" else (D["t"] >= KE.SPLIT)]
        for g in ("all", "equities", "crypto"):
            Dg = Dp if g == "all" else Dp[Dp["grp"] == g]
            C1, C0 = Dg[Dg["confirmed"]], Dg[~Dg["confirmed"]]
            out["conditional"][f"{p}|{g}"] = {
                "ew_all": _cond_summary(Dg, "ew"), "ew_confirmed": _cond_summary(C1, "ew"), "ew_unconfirmed": _cond_summary(C0, "ew"),
                "cf": _cond_summary(C1, "cf"), "confirm_rate": float(Dg["confirmed"].mean()) if len(Dg) else None,
                "delay_med": float(C1["delay"].median()) if len(C1) else None, "cost_wait_med": float(C1["cost_wait"].median()) if len(C1) else None,
                "dd_at_cf_med": float(C1["dd_at_cf"].median()) if len(C1) else None}
    # incremental value of confirmation (KW5_CONFIG.md, reported)
    inc = {}
    for p in ("pre", "post"):
        ew, cf = out["results"]["A|WF"][p]["all"], out["results"]["CF|WF"][p]["all"]
        w0 = out["results"]["W0"][p]["all"]
        inc[p] = {"useful_gain": cf["useful"] - ew["useful"], "f26_gain": cf["f26_med"] - ew["f26_med"], "late_cf": cf["late"], "late_w0": w0["late"],
                  "pass": bool(cf["useful"] >= ew["useful"] + 0.05 and cf["f26_med"] >= ew["f26_med"] and cf["late"] <= w0["late"])}
    out["incremental"] = {"by_period": inc, "adds_value": all(v["pass"] for v in inc.values())}
    out["adopt"] = KE.adopt(out, {"CF": GRID["CF"], "EWCF": GRID["EWCF"]})       # unchanged KW-3 rule vs W0
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print("done", flush=True)


def render():
    out = json.loads(OUT.read_text())
    KE.OUT, KE.MD = OUT, MD
    out.setdefault("chosen", {"A": WS.EW_R, "CF": WS.CF_WINDOW, "EWCF": WS.CF_WINDOW})
    OUT.write_text(json.dumps(out, indent=1, default=str))
    KE.render()
    txt = MD.read_text().replace("# KW-3: weekly SELL recovery", "# KW-5: two-state weekly SELL (early warning -> confirmation)")
    txt = txt.replace("Config `reports/KW3_CONFIG.md`", "Config `reports/KW5_CONFIG.md` (no tuning; adoption rule of KW3_CONFIG.md unchanged)")
    pct = lambda x: "–" if x is None or x != x else f"{x * 100:+.1f}%"  # noqa: E731
    L = ["", "## Conditional outcomes (forward returns in the SELL direction: positive = price fell)", "",
         "| period · group | slice | n | useful | premature | late | false rev. | decline 4/13/26w | fwd 4/13/26w (median) |", "|---|---|---:|---:|---:|---:|---:|---|---|"]
    for k, v in out["conditional"].items():
        p, g = k.split("|")
        for sl in ("ew_all", "ew_confirmed", "ew_unconfirmed", "cf"):
            x = v[sl]
            if not x["n"]:
                continue
            L.append(f"| {'<2018' if p == 'pre' else '2018+'} · {g} | {sl.replace('_', ' ')} | {x['n']} | {x['useful']:.2f} | {x['premature']:.2f} | {x['late']:.2f} | "
                     f"{x['false_reversal']:.2f} | {x['dec4']:.2f}/{x['dec13']:.2f}/{x['dec26']:.2f} | {pct(x['f4_med'])}/{pct(x['f13_med'])}/{pct(x['f26_med'])} |")
        if v["confirm_rate"] is not None:
            L.append(f"| | confirmation rate {v['confirm_rate']:.2f}; median delay {v['delay_med']} w; price change EW→CF {pct(v['cost_wait_med'])} (SELL direction); "
                     f"drawdown from 52w high at CF {v['dd_at_cf_med']:.1f} ATR | | | | | | | |" if v["delay_med"] is not None else f"| | confirmation rate {v['confirm_rate']:.2f} | | | | | | | |")
    L += ["", "## Incremental value of confirmation (KW5_CONFIG.md)", ""]
    for p, v in out["incremental"]["by_period"].items():
        L.append(f"* {'<2018' if p == 'pre' else '2018+'}: useful CF − EW {v['useful_gain']:+.2f}; 26w median CF − EW {v['f26_gain'] * 100:+.1f} pp; "
                 f"late CF {v['late_cf']:.2f} vs W0 {v['late_w0']:.2f} → {'pass' if v['pass'] else 'fail'}")
    L.append(f"* **Confirmation adds value: {'yes' if out['incremental']['adds_value'] else 'no'}.**")
    MD.write_text(txt + "\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"eval": evaluate, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
