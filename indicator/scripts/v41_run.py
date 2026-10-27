"""Run V4.1 (reports/V4_1_PREREGISTRATION.md) for one stage.

    python scripts/v41_run.py D          # 70 seen symbols, exploratory → reports/v41_D.json
    python scripts/v41_run.py H          # 38 holdout instruments, decisions → reports/v41_H.json
    python scripts/v41_run.py D 4H 1D    # some timeframes only (merged into the json)
"""

from __future__ import annotations

import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf.metrics import _perf, holm  # noqa: E402
from research import v41 as V  # noqa: E402
from research.universe41 import HOLDOUT, SEEN  # noqa: E402

CODE_FILES = ["research/v41.py", "research/universe41.py", "scripts/v41_run.py"]

# (family, set, value, bench kind, stratum, bench side rule)  — §4
SPECS = [
    ("H6", "state", "r", "U", None, "same"),        # primary
    ("H6", "state", "r", "V", "vt", "same"),
    ("H6", "state", "r", "Y", "yr", "same"),
    ("H6", "state", "rs", "U", None, "same"),
    ("H6", "state", "rl", "U", None, "same"),
    ("H6", "onset", "r", "U", None, "same"),
    ("H6", "state_lag", "r", "U", None, "same"),
    ("H7v", "h7", "rvr", "L", None, "zero"),        # primary (direction-free; side = all)
    ("H7v", "h7", "rvr", "U", None, "zero"),
    ("H7m", "h7", "mag", "L", None, "zero"),
    ("H7d", "h7", "r", "L", None, "same"),          # primary
    ("H7d", "h7", "r", "U", None, "same"),
    ("H1r", "B", "r", "S", None, "same"),           # primary
    ("H1r", "Bcont", "r", "S", None, "same"),
    ("H1r", "Breal", "r", "S", None, "same"),
    ("H1r", "M", "r", "S", None, "same"),
]
PRIMARY = {("H6", "state", "r", "U"), ("H7v", "h7", "rvr", "L"), ("H7d", "h7", "r", "L"), ("H1r", "B", "r", "S")}
TARGET = ("H1r", "Bcont", "r", "S", "4H", "crypto", 1)


def config_hash() -> dict:
    out = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in CODE_FILES}
    out["preregistration"] = hashlib.sha256((ROOT / "reports" / "V4_1_PREREGISTRATION.md").read_bytes()).hexdigest()
    return out


def evaluate_cell(units, bench, spec, side, clusters, W, window):
    fam, setname, val, kind, stratum, bside = spec
    u = units[(units["set"] == setname) & ((units["side"] == side) if side != 0 else True)]
    u = u[~u[val].isna()]
    b = bench[(bench["kind"] == kind) & (bench["val"] == val) & (bench["side"] == (0 if bside == "zero" else side))]
    if bside == "same" and side == 0:
        return None
    n, syms = len(u), u["sym"].nunique() if len(u) else 0
    ncl = u["cl"].nunique() if len(u) else 0
    out = {"n": int(n), "instruments": int(syms), "clusters": int(ncl)}
    if n == 0:
        return out
    reps, point, per_unit = V.boot_excess(u, b, val, stratum, W, clusters)
    ok = ~np.isnan(per_unit)
    pu = per_unit[ok]
    lo, hi = np.nanpercentile(reps, [2.5, 97.5])
    srt = np.sort(pu)
    k1 = max(int(round(0.01 * len(srt))), 1)
    out.update({
        "mean_excess": point, "lo": float(lo), "hi": float(hi),
        "p": float((1 + np.sum(reps <= 0)) / (len(reps) + 1)),
        "median_excess": float(np.median(pu)) if len(pu) else None,
        "mean_excess_ex_top1": float(srt[:-k1].mean()) if len(srt) > k1 else None,
        "mean_value": float(u[val].mean()), "median_value": float(u[val].median()),
        "bench_mean": float((u[val].to_numpy(float)[ok] - pu).mean()) if len(pu) else None,
        "evaluable": bool(n >= 100 and syms >= 3 and ncl >= 8),
        "_reps": reps,
    })
    if val == "r":
        out["mfe_med"], out["mae_med"] = float(u["mfe"].median()), float(u["mae"].median())
        out["share_pos"] = float((u["r"] > 0).mean())
    if setname == "h7":
        out["rinv_mean"], out["rinv_median"] = float(u["rinv"].mean()), float(u["rinv"].median())
    # purged chronological thirds (benchmark = full-window point benchmark)
    a, z = window
    edges = [a + (z - a) * j // 3 for j in range(4)]
    tt, te = u["t"].to_numpy()[ok], u["t_end"].to_numpy()[ok]
    spans = []
    for j in range(3):
        m = (tt >= edges[j]) & (tt < edges[j + 1]) & (te < edges[j + 1])
        spans.append({"n": int(m.sum()), "mean_excess": float(pu[m].mean()) if m.any() else None,
                      "from": str(pd.Timestamp(edges[j], tz="UTC").date()), "to": str(pd.Timestamp(edges[j + 1], tz="UTC").date())})
    out["spans"] = spans
    out["spans_positive"] = int(sum(1 for s in spans if s["mean_excess"] is not None and s["mean_excess"] > 0))
    vt = u["vt"].to_numpy()[ok]
    out["by_vol"] = {str(k): {"n": int((vt == k).sum()), "mean_excess": float(pu[vt == k].mean())}
                     for k in (0, 1, 2) if (vt == k).any()}
    return out


def run_tf(stage: str, tf: str, workers: int = 8) -> dict:
    assets = SEEN if stage == "D" else HOLDOUT
    with ProcessPoolExecutor(workers) as ex:
        res = list(ex.map(V.one, [(a, tf) for a in assets]))
    excluded = [r["excluded"] for r in res if "excluded" in r]
    res = [r for r in res if "excluded" not in r]
    out = {"tf": tf, "instruments": len(res), "excluded": excluded, "cells": {}, "trading": {},
           "coverage": {r["symbol"]: [str(pd.Timestamp(r["start"]).date()), str(pd.Timestamp(r["end"]).date()), r["n_elig"]] for r in res},
           "integrity_cuts": {r["symbol"]: r["integrity_cut"] for r in res if r.get("integrity_cut")}}
    for grp in list(V.GROUPS) + ["all"]:
        rs = [r for r in res if grp == "all" or r["group"] == grp]
        if not rs:
            continue
        units = pd.concat([r["units"].assign(sym=r["symbol"]) for r in rs if len(r["units"])], ignore_index=True)
        bench = pd.concat([r["bench"].assign(sym=r["symbol"]) for r in rs], ignore_index=True)
        clusters = np.array(sorted(bench["cl"].unique()))
        W = V.weights(clusters)
        window = (min(r["start"] for r in rs), max(r["end"] for r in rs))
        reps_keep = {}
        for spec in SPECS:
            fam, setname, val, kind, stratum, bside = spec
            for side in ((0,) if bside == "zero" else (1, -1)):
                c = evaluate_cell(units, bench, spec, side, clusters, W, window)
                if c is None:
                    continue
                key = f"{fam}|{tf}|{grp}|{side}|{setname}|{val}|{kind}"
                if "_reps" in c:
                    reps_keep[(setname, val, kind, side)] = c.pop("_reps")
                out["cells"][key] = c
            # H7d per side also needs the up/down split for direction-free outcomes: done via side loop
        # B − M difference (same clusters and replicates)
        for side in (1, -1):
            a, b = reps_keep.get(("B", "r", "S", side)), reps_keep.get(("M", "r", "S", side))
            if a is not None and b is not None:
                d = a - b
                ca = out["cells"][f"H1r|{tf}|{grp}|{side}|B|r|S"]
                cb = out["cells"][f"H1r|{tf}|{grp}|{side}|M|r|S"]
                lo, hi = np.nanpercentile(d, [2.5, 97.5])
                out["cells"][f"H1r|{tf}|{grp}|{side}|B-M|r|S"] = {
                    "mean_excess": ca["mean_excess"] - cb["mean_excess"], "lo": float(lo), "hi": float(hi),
                    "p": float((1 + np.sum(d <= 0)) / (len(d) + 1)), "n": ca["n"], "n_M": cb["n"]}
        # H6 trading view (§4)
        for side in (1, -1):
            for name in ("timed", "static"):
                daily = [r["daily"][(side, name)].rename(r["symbol"]) for r in rs]
                out["trading"][f"{grp}|{side}|{name}"] = _perf(daily, None)
    return out


def decide(R: dict) -> dict:
    """§6 decision rules on one stage's results (stage H for decisions)."""
    fams = {"H6": ("state", "r", "U"), "H7v": ("h7", "rvr", "L"), "H7d": ("h7", "r", "L"), "H1r": ("B", "r", "S")}
    tests = {}
    for tf, r in R.items():
        for key, c in r["cells"].items():
            fam, _, grp, side, setname, val, kind = key.split("|")
            if grp == "all" or fam not in fams or fams[fam] != (setname, val, kind) or not c.get("evaluable"):
                continue
            tests[key] = c["p"]
        tk = f"H1r|4H|crypto|1|Bcont|r|S"
        if tf == "4H" and tk in r["cells"] and r["cells"][tk].get("evaluable"):
            tests[tk] = r["cells"][tk]["p"]
    by_fam = {}
    for k, p in tests.items():
        by_fam.setdefault(k.split("|")[0], {})[k] = p
    adj = {}
    for f, t in by_fam.items():
        adj.update(holm(t))
    glob = holm(tests)

    def passing(key):
        tf = key.split("|")[1]
        c = R[tf]["cells"][key]
        mei = V.MEI["rvr" if key.split("|")[5] == "rvr" else "r"]
        return bool(adj.get(key, 1) < 0.05 and c["mean_excess"] >= mei and (c["median_excess"] or 0) > 0
                    and c["spans_positive"] >= 2)

    passed = {k: passing(k) for k in tests}
    D = {"holm_family": adj, "holm_global": glob, "passing": passed}

    def pooled_upper_below(fam, sides):
        setname, val, kind = fams[fam]
        mei = V.MEI["rvr" if val == "rvr" else "r"]
        ups = []
        for tf, r in R.items():
            for s in sides:
                c = r["cells"].get(f"{fam}|{tf}|all|{s}|{setname}|{val}|{kind}")
                if c and c.get("n"):
                    ups.append(c["hi"] < mei)
        return bool(ups) and all(ups)

    groups = [g for g in V.GROUPS]
    for fam, sides in (("H6", (1, -1)), ("H7d", (1, -1)), ("H7v", (0,)), ("H1r", (1, -1))):
        setname, val, kind = fams[fam]
        retain, one_sided, any_pass = False, False, False
        detail = []
        for tf in R:
            ok_groups = []
            for g in groups:
                ps = {s: passed.get(f"{fam}|{tf}|{g}|{s}|{setname}|{val}|{kind}", False) for s in sides}
                any_pass |= any(ps.values())
                if fam in ("H6", "H7d"):
                    if all(ps.values()):
                        ok_groups.append(g)
                    elif any(ps.values()):
                        one_sided = True
                        detail.append(f"{tf} {g}: one side only ({'bullish' if ps.get(1) else 'bearish'})")
                elif fam == "H7v":
                    if ps[0]:
                        ok_groups.append(g)
                else:
                    pass
            if fam == "H1r":
                for s in sides:
                    gs = []
                    for g in groups:
                        k = f"H1r|{tf}|{g}|{s}|B|r|S"
                        bm = R[tf]["cells"].get(f"H1r|{tf}|{g}|{s}|B-M|r|S", {})
                        if passed.get(k) and bm.get("mean_excess", -1) >= 0:
                            gs.append(g)
                    if len(gs) >= 2:
                        retain = True
                        detail.append(f"{tf} side {s}: {gs}")
            elif len(ok_groups) >= 2:
                retain = True
                detail.append(f"{tf}: {ok_groups}")
        if retain:
            dec = "RETAIN FOR FURTHER TESTING"
        elif not any_pass and pooled_upper_below(fam, sides):
            dec = "REJECT"
        else:
            dec = "INCONCLUSIVE"
        D[fam] = {"decision": dec, "any_passing_cell": any_pass, "one_sided_only": one_sided and not retain,
                  "pooled_upper_below_MEI_everywhere": pooled_upper_below(fam, sides), "detail": detail}
    tk = "H1r|4H|crypto|1|Bcont|r|S"
    c = R.get("4H", {}).get("cells", {}).get(tk)
    if c and c.get("n"):
        D["H1r_target"] = {"decision": "REJECT" if (c["lo"] <= 0 or (c["median_excess"] or 0) <= 0) else "RETAIN FOR FURTHER TESTING",
                           "mean_excess": c["mean_excess"], "ci": [c["lo"], c["hi"]], "median_excess": c["median_excess"],
                           "n": c["n"], "evaluable": c.get("evaluable")}
    else:
        D["H1r_target"] = {"decision": "INCONCLUSIVE", "why": "no events"}
    return D


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def main():
    stage = sys.argv[1]
    tfs = sys.argv[2:] or V.TFS
    path = ROOT / "reports" / f"v41_{stage}.json"
    R = json.loads(path.read_text()) if path.exists() else {}
    R.setdefault("results", {})
    R["config_hash"] = config_hash()
    R["stage"] = stage
    for tf in tfs:
        print(f"[{stage} {tf}] running", flush=True)
        R["results"][tf] = _clean(run_tf(stage, tf))
        path.write_text(json.dumps(R, indent=1))
    R["results"] = {k: R["results"][k] for k in V.TFS if k in R["results"]}
    R["decisions"] = _clean(decide(R["results"]))
    path.write_text(json.dumps(R, indent=1))
    print(json.dumps({k: v.get("decision") for k, v in R["decisions"].items() if isinstance(v, dict) and "decision" in v}, indent=1))


if __name__ == "__main__":
    main()
