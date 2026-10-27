"""Family C (major tops) 1H/4H EXPLORATION, exactly as frozen in reports/V5_C_EXPLORATION_CONFIG.md.

    python scripts/v5_c_explore.py run      # gate, manifest check, ledger trials, compute, results json
    python scripts/v5_c_explore.py render   # reports/V5_C_EXPLORATION_RESULTS.md from the json

Exploratory only: every candle used was examined before; results are labelled with the review mode
returned by research.v5_gate.require_c_ready() (self_audited_exploration_only when no independent
review exists). Nothing here changes a parameter, a label, a detector or a decision rule.
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

from hcmtf import engine as G, ta  # noqa: E402
from hcmtf.evaluate import bar_outcomes  # noqa: E402
from hcmtf.metrics import holm  # noqa: E402
from research import v5_baselines as B, v5_data as DG, v5_detect_c as DC, v5_eval as EV  # noqa: E402
from research import v5_gate as GT, v5_inference as INF, v5_ledger as LG, v5_manifest as MF, v5_state as ST  # noqa: E402
from research.v41 import cluster_id, group_of  # noqa: E402
from research.v5_costs import round_trip  # noqa: E402

CONFIG = "reports/V5_C_EXPLORATION_CONFIG.md"
OUT = ROOT / "reports" / "v5_c_x1_results.json"
MD = ROOT / "reports" / "V5_C_EXPLORATION_RESULTS.md"
START = pd.Timestamp("2020-01-01", tz="UTC")
TFS = {"1H": {"H": 24, "hold": 48}, "4H": {"H": 30, "hold": 60}}
GROUPS = ("crypto", "equities", "commodities", "rates")
REPS_THIN, SEED = 50, 20261027
UNIVERSE = [s for s in DG.EVAL_SYMBOLS if DG.EXPLORATION[s].cls != "fx"]
CODE_FILES = ["research/v5_detect_c.py", "research/v5_eval.py", "research/v5_baselines.py", "research/v5_state.py",
              "research/v5_data.py", "research/v5_inference.py", "research/v5_costs.py", "scripts/v5_c_explore.py"]
WARN_TRIALS = [(d, "warning") for d in DC.WARNINGS]
CONF_TRIALS = [(d, "confirmation") for d in DC.CONFIRMATIONS]
HYP = {"C1a": "C1", "C1b": "C1", "C2": "C2", "C3": "C3", "C4": "C4", "C5a": "C5", "C5b": "C5"}


def grp(sym: str) -> str:
    g = group_of(DG.EXPLORATION[sym].cls)
    return "rates" if g == "rates_fx" else g


def trial_id(det, kind, tf):
    return f"c-x1-{det}-{'W' if kind == 'warning' else 'C'}-{tf}"


class _F:
    pass


def worker(args):
    sym, tf = args
    asset = DG.EXPLORATION[sym]
    _, h1n, h2n = G.LADDER[tf]
    df, htf1, htf2 = DG.load(sym, tf), DG.load(sym, h1n), DG.load(sym, h2n)
    st = ST.classify(df, htf1, htf2)
    idx = df.index
    start_i = int(idx.searchsorted(START))
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    det = DC.detect_all(df, htf1, htf2, st, tf, asset, START)
    base = {k: DC.eligible(v, st, START) for k, v in B.generate(df, htf1, htf2, st, tf, -1).items()}
    lab = EV.frozen_labels(sym, h, l, c, "top", tf, idx)
    cl = cluster_id(idx, tf)
    dl = st["direction_label"].to_numpy(object)
    warm = st["warm"].to_numpy(bool)
    res = {"sym": sym, "group": grp(sym), "tf": tf, "n": len(c), "start_i": start_i, "index": idx,
           "scores": {}, "lift": {}, "trading": {}, "matched": {}, "baseline_scores": {}}
    for d, kind in WARN_TRIALS + CONF_TRIALS:
        sc = EV.score_alerts(lab, det[d], kind, start_i)
        res["scores"][(d, kind)] = sc
        u = EV.lift_units(lab, sc, kind, dl, warm, start_i)
        u["cl"] = cl[u["i"].to_numpy(int)] if len(u) else []
        res["lift"][(d, kind)] = u
    # trading outcomes (confirmations)
    H, hold = TFS[tf]["H"], TFS[tf]["hold"]
    f = _F(); f.o, f.h, f.l, f.c = o, h, l, c; f.atr = ta.atr(h, l, c, 14)
    r_short = bar_outcomes(f, H, round_trip(asset.cls) * 1e4)[-1]["r_h"]
    r_eval = np.where(warm, r_short, np.nan)
    ct = EV.candle_table(sym, idx, tf, H, {"direction_label": dl}, {"r_h": r_eval})
    cb = EV.causal_benchmark(ct, "r_h", ["direction_label"], H, 200)
    funding = DG.load_funding(sym) if asset.cls == "crypto" else None
    cts = ct.iloc[start_i:]
    cts.attrs.update(ct.attrs)
    wbench = EV.bench_table(cts, "r_h", ["direction_label"])
    for d in DC.CONFIRMATIONS:
        a = det[d]
        rows = []
        for i in a:
            t = EV.trade(o, h, l, c, idx, int(i), -1, hold, float(np.max(h[max(0, i - 19):i + 1])), asset.cls, funding)
            rows.append({"i": int(i), "cl": int(cl[i]), "r_h": float(r_short[i]) if np.isfinite(r_short[i]) else np.nan,
                         "cb": float(cb[i]) if np.isfinite(cb[i]) else np.nan, "dl": dl[i],
                         "net": t["net"] if t else np.nan, "gross": t["gross"] if t else np.nan,
                         "src": t["holding_cost_source"] if t else "no_exit_in_data"})
        res["trading"][d] = {"rows": pd.DataFrame(rows), "wbench": wbench,
                             "units": EV.units_from(ct, pd.DataFrame({"sym": sym, "i": a}), ["direction_label"])}
    # baselines: unthinned (confirmation kind) and matched-frequency per confirmation detector
    for b in B.BASELINES:
        res["baseline_scores"][b] = EV.score_alerts(lab, base[b], "confirmation", start_i)
    for d in DC.CONFIRMATIONS:
        for b in B.BASELINES:
            th = B.thin(base[b], det[d], idx, tf, reps=REPS_THIN, seed=SEED)
            reps = []
            for r in th["replicates"]:
                sc = EV.score_alerts(lab, r, "confirmation", start_i)
                stt = list(sc["status"].values())
                reps.append({"events": len(sc["events"]), "matched": len(sc["pairs"]), "alerts": len(sc["alerts"]),
                             "dup": stt.count("duplicate"), "fa": stt.count("false_alarm"),
                             "cand": sc["scorable_candles"], "leads": sc["leads"], "remaining": sc["remaining"]})
            res["matched"][(d, b)] = {"reps": reps, "target": th["target"], "available": th["available"],
                                      "shortfall_blocks": len(th["shortfall_blocks"])}
    return res


# ----------------------------------------------------------------------------- aggregation

def _cells(results, tf):
    rs = [r for r in results if r["tf"] == tf]
    cells = {g: [r for r in rs if r["group"] == g] for g in GROUPS}
    cells["pooled"] = rs
    return cells


def lift_stats(rs, key):
    u = pd.concat([r["lift"][key] for r in rs if len(r["lift"][key])], ignore_index=True) if rs else pd.DataFrame()
    if len(u) == 0:
        return {"units": 0, "clusters": 0}
    w = INF.cluster_mean_test(u["excess"].to_numpy(float), u["cl"].to_numpy(), reps=9999, seed=SEED)
    sec = EV._ratio_ci(u["excess"].to_numpy(float), np.ones(len(u)), u["cl"].to_numpy(), 5000, SEED)
    return {"units": int(len(u)), "clusters": int(u["cl"].nunique()), "alert_near_rate": float(u["near"].mean()),
            "bench_rate": float(u["bench"].mean()), "lift": float(u["near"].mean() / u["bench"].mean()) if u["bench"].mean() > 0 else None,
            "excess": w.get("mean"), "ci95_t": w.get("ci95"), "p_wild": w.get("p_wild"), "p_t": w.get("p_t"),
            "wild_weights": w.get("wild_weights"), "percentile_ci": [sec[1], sec[2]], "cluster_sizes": w.get("cluster_sizes")}


def matched_stats(rs, key):
    agg = []
    for k in range(REPS_THIN):
        m = [r["matched"][key]["reps"][k] for r in rs]
        ev, mt, al, du, fa, ca = (sum(x[f] for x in m) for f in ("events", "matched", "alerts", "dup", "fa", "cand"))
        leads = np.concatenate([x["leads"] for x in m]) if m else np.array([])
        rem = np.concatenate([x["remaining"] for x in m]) if m else np.array([])
        agg.append({"recall": mt / ev if ev else np.nan, "precision": mt / al if al else np.nan,
                    "precision_excl_dup": mt / (mt + fa) if (mt + fa) else np.nan,
                    "fa_per_100": 100 * fa / ca if ca else np.nan, "lead_median": float(np.median(leads)) if len(leads) else np.nan,
                    "remaining_median": float(np.median(rem)) if len(rem) else np.nan, "alerts": al})
    out = {}
    for f in agg[0]:
        v = np.array([a[f] for a in agg], float)
        out[f] = [float(np.nanmean(v)), float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))] if np.isfinite(v).any() else None
    out["target_alerts"] = int(sum(r["matched"][key]["target"] for r in rs))
    out["available_alerts"] = int(sum(r["matched"][key]["available"] for r in rs))
    out["shortfall_blocks"] = int(sum(r["matched"][key]["shortfall_blocks"] for r in rs))
    return out


def trading_stats(rs, d, tf):
    rows = pd.concat([r["trading"][d]["rows"].assign(sym=r["sym"]) for r in rs if len(r["trading"][d]["rows"])], ignore_index=True) \
        if any(len(r["trading"][d]["rows"]) for r in rs) else pd.DataFrame()
    if len(rows) == 0:
        return {"trades": 0}
    ok = rows[rows["net"].notna()]
    out = {"trades": int(len(rows)), "net_mean": float(ok["net"].mean()) if len(ok) else None,
           "net_median": float(ok["net"].median()) if len(ok) else None,
           "cost_sources": rows["src"].value_counts().to_dict()}
    cc = rows[rows["r_h"].notna() & rows["cb"].notna()]
    out["r_h_mean"] = float(rows["r_h"].mean()) if rows["r_h"].notna().any() else None
    out["r_h_median"] = float(rows["r_h"].median()) if rows["r_h"].notna().any() else None
    if len(cc):
        w = INF.cluster_mean_test((cc["r_h"] - cc["cb"]).to_numpy(float), cc["cl"].to_numpy(), reps=9999, seed=SEED)
        out["causal_excess"] = {k: w.get(k) for k in ("n", "clusters", "mean", "ci95", "p_wild", "valid")}
    units = pd.concat([r["trading"][d]["units"] for r in rs], ignore_index=True)
    units.attrs.update(rs[0]["trading"][d]["units"].attrs)
    wb = pd.concat([r["trading"][d]["wbench"] for r in rs], ignore_index=True)
    if len(units):
        e = EV.excess(units, wb, "r_h", TFS[tf]["H"], (int(units["t"].min()), int(units["t"].max()) + 1), reps=2000, seed=SEED)
        e.pop("_reps", None)
        out["whole_window_excess"] = {k: e.get(k) for k in ("n", "mean_excess", "lo", "hi", "median_excess")}
    return out


def evaluate(results):
    out = {"cells": {}, "baselines_unthinned": {}}
    for tf in TFS:
        cells = _cells(results, tf)
        times = {r["sym"]: r["index"] for r in cells["pooled"]}
        for d, kind in WARN_TRIALS + CONF_TRIALS:
            for g, rs in cells.items():
                if not rs:
                    continue
                det = EV.detection_report({r["sym"]: r["scores"][(d, kind)] for r in rs}, times, tf, kind, reps=2000)
                lf = lift_stats(rs, (d, kind))
                ev_ok = bool(det["evaluable"] and lf["units"] >= 30 and lf["clusters"] >= 10)
                cell = {"trial": trial_id(d, kind, tf), "detector": d, "kind": kind, "tf": tf, "group": g,
                        "detection": det, "lift": lf, "evaluable": ev_ok}
                if kind == "confirmation":
                    cell["matched_baselines"] = {b: matched_stats(rs, (d, b)) for b in B.BASELINES}
                    cell["trading"] = trading_stats(rs, d, tf)
                out["cells"][f"{tf}|{g}|{d}|{kind}"] = cell
        for b in B.BASELINES:
            for g, rs in cells.items():
                if rs:
                    out["baselines_unthinned"][f"{tf}|{g}|{b}"] = EV.detection_report(
                        {r["sym"]: r["baseline_scores"][b] for r in rs}, times, tf, "confirmation", reps=2000)
    # Holm over evaluable non-pooled cells (information only)
    ps = {k: c["lift"]["p_wild"] for k, c in out["cells"].items() if c["evaluable"] and c["group"] != "pooled"}
    out["holm"] = holm(ps) if ps else {}
    out["selection"], out["rejection"] = select(out["cells"])
    return out


def select(cells):
    """Frozen §8 (selection) and §9 (rejection)."""
    cand = []
    for d, kind in WARN_TRIALS + CONF_TRIALS:
        best = None
        for tf in TFS:
            groups_ok = [g for g in GROUPS if cells.get(f"{tf}|{g}|{d}|{kind}", {}).get("evaluable")]
            pooled = cells.get(f"{tf}|pooled|{d}|{kind}")
            if len(groups_ok) < 2 or not pooled or pooled["lift"].get("clusters", 0) < 10:
                continue
            lf, det = pooled["lift"], pooled["detection"]
            score = lf["ci95_t"][0]
            req = lf["p_wild"] is not None and lf["p_wild"] < 0.05
            if kind == "warning":
                req &= det["lead_median"][0] is not None and det["lead_median"][0] > 0
            else:
                req &= det["remaining_median"] is not None and det["remaining_median"] >= 0.5
                bl = [m["precision_excl_dup"][0] for m in pooled["matched_baselines"].values() if m.get("precision_excl_dup")]
                req &= det["precision_excluding_duplicates"] is not None and det["precision_excluding_duplicates"] >= (max(bl) if bl else 0)
            row = {"detector": d, "kind": kind, "tf": tf, "score": score, "meets_requirements": bool(req),
                   "groups_evaluable": groups_ok, "precision_excl_dup": det["precision_excluding_duplicates"]}
            if best is None or score > best["score"]:
                best = row
        if best:
            cand.append(best)
    ok = sorted([c for c in cand if c["meets_requirements"]], key=lambda c: (-c["score"], -(c["precision_excl_dup"] or 0)))
    selection = {"eligible": cand, "selected": ok[:3],
                 "family_outcome": "variants retained for G2 (requires independent review)" if ok else
                 "no variant qualifies: family C at configuration x1 is REJECTED at exploration or needs REDESIGN"}
    rejection = {}
    for d, kind in WARN_TRIALS + CONF_TRIALS:
        ev = [c for k, c in cells.items() if c["detector"] == d and c["kind"] == kind and c["evaluable"] and c["group"] != "pooled"]
        if not ev:
            rejection[f"{d}|{kind}"] = "no evaluable cell (inconclusive)"
            continue
        below = all(c["lift"]["ci95_t"][1] < 0 for c in ev)
        lead_bad = kind == "warning" and all((c["detection"]["lead_median"][0] or 0) <= 0 for c in ev)
        rejection[f"{d}|{kind}"] = "DROPPED" if (below or lead_bad) else "not dropped"
    return selection, rejection


# ----------------------------------------------------------------------------- run

def _commit_ledger(tid):
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    msg = (f"V5 ledger: record trial {tid} (before its computation)\n\n"
           "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
           "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25")
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=ROOT, check=True)
    LG.verify_against_git(LG.LEDGER)


def run():
    mode = GT.require_c_ready()
    v = MF.verify(ROOT / GT.MANIFEST)
    if any(v.values()):
        raise SystemExit(f"cache differs from the manifest: {v}")
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    data_files = sorted(str(Path(p)) for s in UNIVERSE for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m))
    LG.verify_against_git(LG.LEDGER)
    results = []
    for tf in TFS:
        trials = [(d, k) for d, k in WARN_TRIALS + CONF_TRIALS]
        for d, kind in trials:
            tid = trial_id(d, kind, tf)
            LG.record(tid, HYP[d], ["exploration"], {"config": CONFIG, "detector": d, "kind": kind, "tf": tf, "mode": mode},
                      CODE_FILES, ["recall", "precision", "precision_excl_dup", "false_alarms", "lead", "remaining", "lift"]
                      + (["matched_baselines", "trading"] if kind == "confirmation" else []), True, CONFIG, data_files,
                      notes=f"exploration; review mode {mode}")
            _commit_ledger(tid)
        tid = f"c-x1-baselines-{tf}"
        LG.record(tid, "C5", ["exploration"], {"config": CONFIG, "baselines": list(B.BASELINES), "tf": tf, "mode": mode},
                  CODE_FILES, ["recall", "precision", "false_alarms", "lead", "remaining"], True, CONFIG, data_files,
                  notes=f"unthinned baselines; review mode {mode}")
        _commit_ledger(tid)
        with ProcessPoolExecutor(8) as ex:
            results += list(ex.map(worker, [(s, tf) for s in UNIVERSE]))
        print(f"[{tf}] computed {len(UNIVERSE)} instruments", flush=True)
    ev = evaluate(results)
    ev["meta"] = {"mode": mode, "config": CONFIG, "universe": UNIVERSE, "manifest_combined_sha256": m["combined_sha256"],
                  "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                  "instruments_per_group": {g: sum(1 for s in UNIVERSE if grp(s) == g) for g in GROUPS}}
    OUT.write_text(json.dumps(_clean(ev), indent=1))
    print("selection:", json.dumps(_clean(ev["selection"]["selected"])), ev["selection"]["family_outcome"])


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return [_clean(v) for v in o.tolist()]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


# ----------------------------------------------------------------------------- render

def _f(x, nd=3, sign=False):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "–"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def _ci(t, nd=3):
    return "–" if not t or t[0] is None else f"{_f(t[0], nd)} [{_f(t[1], nd)}, {_f(t[2], nd)}]"


def render():
    R = json.loads(OUT.read_text())
    meta, C = R["meta"], R["cells"]
    L = ["# V5 family C (major tops) 1H/4H exploration: results", "",
         f"**EXPLORATORY ONLY. Review mode: `{meta['mode']}`.** Every candle used was examined in earlier studies; nothing here is",
         "independent confirmation, and no result may be used for G2/G3 without an independent review.",
         f"Configuration `{meta['config']}` (frozen, commit 74d5ae5); run at commit `{meta['git_head'][:7]}`; data manifest",
         f"`{meta['manifest_combined_sha256'][:16]}…`; universe {len(meta['universe'])} instruments {meta['instruments_per_group']}.",
         "Generated by `python scripts/v5_c_explore.py run` then `render`; raw numbers in `reports/v5_c_x1_results.json`.", "",
         "Columns: events = labelled major tops scorable in the cell; recall / precision with 95% calendar-block cluster CI;",
         "precision* = excluding duplicates; dup = alerts whose window held only already-claimed tops; FA = false alarms",
         "(per 100 candles / per instrument-year); lead = candles from alert to top (median [CI]; > 0 = before the top);",
         "remain = share of the subsequent decline still ahead at the alert (median); lift = event-in-window rate of alerts",
         "over warm scorable candles of the same instrument and HTF state; excess [t(G−1) 95% CI], one-sided wild-bootstrap",
         "p, Holm (information only); eval = cell meets the frozen evaluability rule (F8).", ""]
    for tf in TFS:
        for kind in ("warning", "confirmation"):
            dets = DC.WARNINGS if kind == "warning" else DC.CONFIRMATIONS
            L += [f"## {tf} · {kind}s", "",
                  "| detector | group | events | alerts | recall | precision | precision* | dup | FA /100c | FA /inst-yr | lead | remain | lift | excess [CI] | p wild | Holm | G | eval |",
                  "|---|---|---:|---:|---|---|---:|---:|---:|---:|---|---:|---:|---|---:|---:|---:|---|"]
            for d in dets:
                for g in list(GROUPS) + ["pooled"]:
                    c = C.get(f"{tf}|{g}|{d}|{kind}")
                    if not c:
                        continue
                    dt, lf = c["detection"], c["lift"]
                    hp = R["holm"].get(f"{tf}|{g}|{d}|{kind}")
                    exc = "–" if lf.get("excess") is None else f"{_f(lf['excess'], 4, True)} [{_f(lf['ci95_t'][0], 4, True)}, {_f(lf['ci95_t'][1], 4, True)}]"
                    L.append(f"| {d} | {g} | {dt['events']} | {dt['alerts']} | {_ci(dt['recall'])} | {_ci(dt['precision'])} | "
                             f"{_f(dt['precision_excluding_duplicates'])} | {dt['duplicates']} | {_f(dt['false_alarms_per_100_candles'], 2)} | "
                             f"{_f(dt['false_alarms_per_instrument_year'], 1)} | {_ci(dt['lead_median'], 0)} | {_f(dt['remaining_median'], 2)} | "
                             f"{_f(lf.get('lift'), 2)} | {exc} | {_f(lf.get('p_wild'), 4)} | {_f(hp, 3)} | {lf.get('clusters', 0)} | "
                             f"{'yes' if c['evaluable'] else 'no'} |")
            L.append("")
            if kind == "confirmation":
                L += [f"### {tf} · confirmations vs matched-frequency baselines (replicate mean [2.5%, 97.5%], 50 replicates)", "",
                      "| detector | group | baseline | recall | precision | precision* | FA /100c | lead | remain | alerts kept / detector alerts (available) | shortfall blocks |",
                      "|---|---|---|---|---|---|---|---|---|---|---:|"]
                for d in dets:
                    for g in list(GROUPS) + ["pooled"]:
                        c = C.get(f"{tf}|{g}|{d}|{kind}")
                        if not c:
                            continue
                        for b, m in c["matched_baselines"].items():
                            L.append(f"| {d} | {g} | {b} | {_ci(m.get('recall'))} | {_ci(m.get('precision'))} | {_ci(m.get('precision_excl_dup'))} | "
                                     f"{_ci(m.get('fa_per_100'), 2)} | {_ci(m.get('lead_median'), 0)} | {_ci(m.get('remaining_median'), 2)} | "
                                     f"{_f((m.get('alerts') or [None])[0], 0)} / {m['target_alerts']} ({m['available_alerts']}) | {m['shortfall_blocks']} |")
                L += ["", f"### {tf} · confirmations, trading view (secondary; short at next open, stop = 20-candle high, 2H exit)", "",
                      "| detector | group | trades | net mean | net median | r_h mean | r_h median | r_h − causal benchmark [CI] (p wild, G) | r_h − whole-window benchmark [CI] | holding-cost sources |",
                      "|---|---|---:|---:|---:|---:|---:|---|---|---|"]
                for d in dets:
                    for g in list(GROUPS) + ["pooled"]:
                        c = C.get(f"{tf}|{g}|{d}|{kind}")
                        if not c:
                            continue
                        t = c["trading"]
                        if not t.get("trades"):
                            L.append(f"| {d} | {g} | 0 | | | | | | | |")
                            continue
                        ce, ww = t.get("causal_excess") or {}, t.get("whole_window_excess") or {}
                        cs = "–" if ce.get("mean") is None else f"{_f(ce['mean'], 3, True)} [{_f(ce['ci95'][0], 3, True)}, {_f(ce['ci95'][1], 3, True)}] ({_f(ce.get('p_wild'), 4)}, {ce.get('clusters')})"
                        ws = "–" if ww.get("mean_excess") is None else f"{_f(ww['mean_excess'], 3, True)} [{_f(ww['lo'], 3, True)}, {_f(ww['hi'], 3, True)}]"
                        L.append(f"| {d} | {g} | {t['trades']} | {_f(t['net_mean'], 4, True)} | {_f(t['net_median'], 4, True)} | "
                                 f"{_f(t['r_h_mean'], 3, True)} | {_f(t['r_h_median'], 3, True)} | {cs} | {ws} | {t['cost_sources']} |")
                L.append("")
        L += [f"### {tf} · baselines, unthinned (scored as confirmations)", "",
              "| baseline | group | events | alerts | recall | precision | precision* | FA /100c | lead | remain |", "|---|---|---:|---:|---|---|---:|---:|---|---:|"]
        for b in B.BASELINES:
            for g in list(GROUPS) + ["pooled"]:
                dt = R["baselines_unthinned"].get(f"{tf}|{g}|{b}")
                if dt:
                    L.append(f"| {b} | {g} | {dt['events']} | {dt['alerts']} | {_ci(dt['recall'])} | {_ci(dt['precision'])} | "
                             f"{_f(dt['precision_excluding_duplicates'])} | {_f(dt['false_alarms_per_100_candles'], 2)} | {_ci(dt['lead_median'], 0)} | "
                             f"{_f(dt['remaining_median'], 2)} |")
        L.append("")
    sel = R["selection"]
    L += ["## Frozen selection rule (§8) and rejection rule (§9), applied mechanically", "",
          "| detector | kind | best TF | score (pooled lift-excess t-CI lower bound) | groups evaluable | meets all requirements |",
          "|---|---|---|---:|---|---|"]
    for c in sel["eligible"]:
        L.append(f"| {c['detector']} | {c['kind']} | {c['tf']} | {_f(c['score'], 4, True)} | {', '.join(c['groups_evaluable'])} | {'yes' if c['meets_requirements'] else 'no'} |")
    L += ["", f"Selected for G2 (≤ 3): {[(c['detector'], c['kind'], c['tf']) for c in sel['selected']] or 'none'}.",
          f"**Family outcome: {sel['family_outcome']}.**", "", "| detector · kind | §9 rejection |", "|---|---|"]
    for k, v in R["rejection"].items():
        L.append(f"| {k} | {v} |")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"run": run, "render": render}[sys.argv[1]]()
