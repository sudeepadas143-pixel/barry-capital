"""Cycle engine CY-1: bounded formula research exactly as frozen in reports/CYCLE_CONFIG.md.

    python scripts/cycle_research.py run [TF ...]   # gate, ledger trial per TF, build, fit, select, test
    python scripts/cycle_research.py render         # reports/CYCLE_RESULTS.md from reports/cycle_results.json

Exploratory only (all data examined before). Writes the shipped model spec to
reports/cycle_model_spec.json for scripts/cycle_export_pine.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf import engine as G  # noqa: E402
from hcmtf.evaluate import bar_outcomes  # noqa: E402
from hcmtf.htf import align  # noqa: E402
from hcmtf.metrics import holm  # noqa: E402
from hcmtf.universe import COST_BPS  # noqa: E402
from research import cycle_features as CF, v5_baselines as B, v5_data as DG, v5_eval as EV  # noqa: E402
from research import v5_gate as GT, v5_inference as INF, v5_ledger as LG, v5_manifest as MF, v5_state as ST  # noqa: E402
from research.v41 import cluster_id  # noqa: E402

CONFIG = "reports/CYCLE_CONFIG.md"
OUT = ROOT / "reports" / "cycle_results.json"
SPEC = ROOT / "reports" / "cycle_model_spec.json"
MD = ROOT / "reports" / "CYCLE_RESULTS.md"
TFS = ("1W", "1D", "4H", "1H")
SPLIT = {"1W": ("2010-01-01", "2016-01-01"), "1D": ("2016-01-01", "2020-01-01"),
         "4H": ("2021-01-01", "2022-01-01"), "1H": ("2021-01-01", "2022-01-01")}          # (validation start, test start)
LABEL = {"1H": (168, 336, 8.0), "4H": (126, 252, 8.0), "1D": (63, 126, 8.0), "1W": (26, 52, 5.0)}   # = frozen label table (tested equal)
MODELS = {"L_price": CF.PRICE, "L_mom": CF.PRICE + CF.MOM, "L_vol": CF.PRICE + CF.MOM + CF.VOL,
          "L_int": CF.PRICE + CF.MOM + CF.VOL + CF.INTER}
BASE = {"B_ext": "ext_c", "B_rsi": "rsi", "B_rng": "rng"}
ORDER = ["B_ext", "B_rsi", "B_rng", "L_price", "L_mom", "L_vol", "L_int"]       # simplest first
CS = (0.01, 0.1, 1.0)
SEED = 20261027
CODE_FILES = ["research/cycle_features.py", "scripts/cycle_research.py", "research/v5_eval.py", "research/v5_baselines.py",
              "research/v5_data.py", "research/v5_inference.py", "research/v5_state.py", "research/v5_gate.py"]
DIRS = {"top": -1, "bot": 1}


def kind_of(sym):
    return DG.EXPLORATION[sym].cls


# ----------------------------------------------------------------------------- per-instrument build

def build(args):
    sym, tf = args
    asset = DG.EXPLORATION[sym]
    df = DG.load(sym, tf)
    if len(df) < 400:
        return None
    L, Fw, D = LABEL[tf]
    vol_ok = bool(asset.volume) and "volume" in df and float((df["volume"].fillna(0) > 0).mean()) > 0.9
    F = CF.features(df, tf, vol_ok)
    htf = DG.load(sym, CF.HTF_OF[tf])
    rh = CF.range_position(*(htf[k].to_numpy(float) for k in ("high", "low", "close")), CF.SCALE[CF.HTF_OF[tf]]["L"])
    F["htf_rng"] = align(df.index, htf.index, rh)
    idx = df.index
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    a, b = L // 4, L // 2
    res = {"sym": sym, "cls": asset.cls, "tf": tf, "vol": vol_ok, "idx": idx, "F": F.astype("float32"),
           "ohlc": (o, h, l, c), "labs": {}, "y": {}, "valid": {}}
    for d, fam in (("top", "top"), ("bot", "bottom")):
        lab = EV.frozen_labels(sym, h, l, c, fam, tf, idx)
        lo, hi = EV.scorable_region(lab)
        ev = np.sort(lab.events)
        s = np.arange(len(c))
        y = (np.searchsorted(ev, s + b, "right") > np.searchsorted(ev, s - a, "left"))
        res["labs"][d], res["y"][d], res["valid"][d] = lab, y, (s - a >= lo) & (s + b <= hi)
    # baselines for the confirmation comparison (completed-HTF state as in V5)
    _, h1n, h2n = G.LADDER[tf]
    try:
        h1, h2 = DG.load(sym, h1n), DG.load(sym, h2n)
        st = ST.classify(df, h1, h2)
        res["base"] = {d: B.generate(df, h1, h2, st, tf, side) for d, side in DIRS.items()}
    except Exception as e:                       # reported, never silently empty
        res["base"] = None
        res["base_error"] = repr(e)
    return res


# ----------------------------------------------------------------------------- fitting

def _split(idx, tf):
    v, t = (pd.Timestamp(x, tz="UTC") for x in SPLIT[tf])
    return np.where(idx < v, "train", np.where(idx < t, "val", "test"))


def table(results, d, feats, group):
    """Stacked rows (features, y, split, sym) for direction d and a feature list."""
    parts = []
    for r in results:
        if group == "vol" and not r["vol"]:
            continue
        X = r["F"][feats].to_numpy(float)
        ok = r["valid"][d] & ~np.isnan(X).any(axis=1)
        parts.append(pd.DataFrame(X[ok], columns=feats).assign(_y=r["y"][d][ok].astype(int), _sp=_split(r["idx"], r["tf"])[ok],
                                                               _sym=r["sym"]))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def fit_logit(T, feats, C):
    mu, sd = T[feats].mean().to_numpy(dtype=float, copy=True), T[feats].std().to_numpy(dtype=float, copy=True)
    sd[sd == 0] = 1.0
    Z = np.clip((T[feats].to_numpy() - mu) / sd, -5, 5)
    m = LogisticRegression(C=C, class_weight="balanced", max_iter=2000).fit(Z, T["_y"].to_numpy())
    return {"kind": "logit", "features": list(feats), "mu": mu.tolist(), "sd": sd.tolist(), "coef": m.coef_[0].tolist(),
            "intercept": float(m.intercept_[0]), "C": C}


def score(spec, X: pd.DataFrame) -> np.ndarray:
    if spec["kind"] == "base":
        return spec["sign"] * X[spec["feature"]].to_numpy(float)
    Z = np.clip((X[spec["features"]].to_numpy(float) - np.array(spec["mu"])) / np.array(spec["sd"]), -5, 5)
    return 1.0 / (1.0 + np.exp(-(spec["intercept"] + Z @ np.array(spec["coef"]))))


def select(results, d, group, log):
    """§4: validation AP, C grid, simplest-within-3% rule, then context increments. Returns the
    spec refit on train+val, and the validation table of every candidate."""
    sign = 1.0 if d == "top" else -1.0
    allf = CF.PRICE + CF.MOM + (CF.VOL + CF.INTER if group == "vol" else [])
    Tall = table(results, d, allf, group)
    tr, va = Tall[Tall["_sp"] == "train"], Tall[Tall["_sp"] == "val"]
    cand = {}
    for name in ORDER:
        if name in BASE:
            spec = {"kind": "base", "feature": BASE[name], "sign": sign}
            cand[name] = (average_precision_score(va["_y"], score(spec, va)), spec)
        elif group == "vol" or name in ("L_price", "L_mom"):
            best = None
            for C in CS:
                spec = fit_logit(tr, MODELS[name], C)
                ap = average_precision_score(va["_y"], score(spec, va))
                if best is None or ap > best[0]:
                    best = (ap, spec)
            cand[name] = best
    if group == "vol":
        g = HistGradientBoostingClassifier(max_depth=3, max_iter=200, learning_rate=0.05, random_state=SEED)
        g.fit(tr[MODELS["L_vol"]], tr["_y"])
        log["G_ref_val_ap"] = float(average_precision_score(va["_y"], g.predict_proba(va[MODELS["L_vol"]])[:, 1]))
    top = max(v[0] for v in cand.values())
    chosen = next(n for n in ORDER if n in cand and cand[n][0] >= 0.97 * top)
    log["val_ap"] = {k: float(v[0]) for k, v in cand.items()}
    log["val_base_rate"] = float(va["_y"].mean())
    log["selected_core"] = chosen
    spec = dict(cand[chosen][1])
    feats = list(spec.get("features", [])) if spec["kind"] == "logit" else []
    ap_core = cand[chosen][0]
    log["context"] = {}
    if spec["kind"] == "logit":
        for ctx in ("htf_rng",) + (("breadth",) if results[0]["tf"] in ("1D", "1W") else ()):
            fx = feats + [ctx]
            T2 = table(results, d, fx, group)
            tr2, va2 = (T2[T2["_sp"] == "train"], T2[T2["_sp"] == "val"]) if len(T2) else (T2, T2)
            if len(tr2) == 0 or len(va2) == 0 or tr2["_y"].nunique() < 2 or va2["_y"].sum() == 0:
                log["context"][ctx] = {"kept": False, "not_evaluable": True, "rows": int(len(va2))}
                continue
            core_on_same = fit_logit(tr2, feats, spec["C"])
            ap0 = average_precision_score(va2["_y"], score(core_on_same, va2))
            s2 = fit_logit(tr2, fx, spec["C"])
            ap1 = average_precision_score(va2["_y"], score(s2, va2))
            keep = ap1 >= 1.03 * ap0
            log["context"][ctx] = {"ap_without": float(ap0), "ap_with": float(ap1), "kept": bool(keep),
                                   "rows": int(len(va2))}
            if keep:
                feats = fx
    # refit on train+val
    if spec["kind"] == "logit":
        T3 = table(results, d, feats, group)
        spec = fit_logit(T3[T3["_sp"] != "test"], feats, spec["C"])
    spec["model"] = chosen
    return spec, cand


def p_series(r, spec) -> np.ndarray:
    feats = spec["features"] if spec["kind"] == "logit" else [spec["feature"]]
    X = r["F"][feats]
    p = np.array(score(spec, X), dtype=float, copy=True)
    p[np.isnan(X.to_numpy(float)).any(axis=1)] = np.nan
    return p


def calibrate_theta(results, spec, d, tf):
    """θ such that zone onsets per asset-year on train+val = 2 x labelled events per asset-year (§5)."""
    L = LABEL[tf][0]
    c = CF.q_of(L)
    P, M = [], []
    events, years = 0, 0.0
    for r in results:
        sp = _split(r["idx"], tf)
        p = p_series(r, spec)
        prev = pd.Series(p).shift(1).rolling(c, min_periods=1).max().to_numpy()
        w = (sp != "test") & r["valid"][d]
        if not w.any():
            continue
        P.append(p[w]); M.append(prev[w])
        ev = r["labs"][d].events
        events += int(w[ev[ev < len(w)]].sum()) if len(ev) else 0
        t = r["idx"][w]
        years += (t[-1] - t[0]).total_seconds() / (365.25 * 86400)
    P, M = np.concatenate(P), np.concatenate(M)
    target = 2.0 * events / years
    fin = P[np.isfinite(P)]
    grid = np.unique(np.quantile(fin, np.linspace(0.5, 0.9995, 300)))
    with np.errstate(invalid="ignore"):
        rates = np.array([np.sum((P >= t) & ~(M >= t)) / years for t in grid])
    k = int(np.argmin(np.abs(rates - target)))
    return float(grid[k]), {"target_onsets_per_asset_year": target, "achieved": float(rates[k]),
                            "events_per_asset_year": events / years}


# ----------------------------------------------------------------------------- evaluation

def alerts_for(r, spec, theta, d, tf):
    L, _, D = LABEL[tf]
    o, h, l, c = r["ohlc"]
    p = p_series(r, spec)
    on = CF.zone_onsets(p, theta, CF.q_of(L))
    F = r["F"]
    dev, conf = CF.developing_and_confirmed(on, DIRS[d], o, h, l, c, F["_rsi"].to_numpy(float), F["_hist"].to_numpy(float),
                                             F["_ema_f"].to_numpy(float), F["_atr"].to_numpy(float), L, D)
    return {"zone": on, "developing": dev, "confirmed": conf}


def movement(r, alerts, d, tf, cost_mult=1.0):
    L = LABEL[tf][0]
    o, h, l, c = r["ohlc"]

    class _F:
        pass
    f = _F(); f.o, f.h, f.l, f.c, f.atr = o, h, l, c, r["F"]["_atr"].to_numpy(float)
    bo = bar_outcomes(f, L // 2, COST_BPS[DG.EXPLORATION[r["sym"]].cls] * cost_mult)[DIRS[d]]
    a = np.asarray(alerts, int)
    return {k: bo[k][a] for k in ("mfe", "mae", "r_h", "ret_h")}


def evaluate_tf(results, specs, thetas, tf, reps_wild=9999):
    out = {}
    vstart = pd.Timestamp(SPLIT[tf][1], tz="UTC")
    for d in DIRS:
        with_breadth(results, d)
        cell = {"models": {}}
        per = {}
        for r in results:
            start_i = int(r["idx"].searchsorted(vstart))
            if start_i >= len(r["idx"]) - LABEL[tf][0]:
                continue
            g = "vol" if r["vol"] else "novol"
            per[r["sym"]] = (r, start_i, g)
        times = {s: v[0]["idx"] for s, v in per.items()}
        # shipped model and every candidate (each at its own matched-rate θ)
        names = ["SHIPPED"] + [n for n in ORDER if (d, n) in specs["candidates"]]
        for name in names:
            sc_z, sc_d, sc_c, units, units_cl, mv = {}, {}, {}, [], [], {"zone": [], "confirmed": []}
            mv2 = []
            for s, (r, start_i, g) in per.items():
                if name == "SHIPPED":
                    spec, th = specs["shipped"][(d, g)], thetas[(d, g)]
                else:
                    if (d, name) not in specs["candidates"] or (name in ("L_vol", "L_int") and not r["vol"]):
                        continue
                    spec, th = specs["candidates"][(d, name)]
                al = alerts_for(r, spec, th, d, tf)
                lab = r["labs"][d]
                sc_z[s] = EV.score_alerts(lab, al["zone"][al["zone"] >= start_i], "warning", start_i)
                if name == "SHIPPED":
                    sc_d[s] = EV.score_alerts(lab, al["developing"][al["developing"] >= start_i], "warning", start_i)
                    sc_c[s] = EV.score_alerts(lab, al["confirmed"][al["confirmed"] >= start_i], "confirmation", start_i)
                    for k in ("zone", "confirmed"):
                        a = al[k][al[k] >= start_i]
                        if len(a):
                            m = movement(r, a, d, tf)
                            mv[k].append(pd.DataFrame(m).assign(sym=s, cls=r["cls"]))
                            if k == "confirmed":
                                mv2.append(pd.DataFrame(movement(r, a, d, tf, 2.0)).assign(sym=s))
                warm = ~np.isnan(p_series(r, spec))
                u = EV.lift_units(lab, sc_z[s], "warning", np.full(len(warm), "all", object), warm, start_i)
                if len(u):
                    u["cl"] = cluster_id(r["idx"], tf)[u["i"].to_numpy(int)]
                    u["sym"], u["cls"] = s, r["cls"]
                    u["era"] = np.where(r["idx"][u["i"].to_numpy(int)] < vstart + (pd.Timestamp("2026-10-27", tz="UTC") - vstart) / 2, "early", "late")
                    u["atr_t"] = pd.cut(r["F"]["atr_rank"].to_numpy(float)[u["i"].to_numpy(int)], [-1, 1 / 3, 2 / 3, 2], labels=["low", "mid", "high"]).astype(str)
                    units.append(u)
            det = EV.detection_report(sc_z, {k: times[k] for k in sc_z}, tf, "warning", reps=1000) if sc_z else None
            U = pd.concat(units, ignore_index=True) if units else pd.DataFrame()
            lift = None
            if len(U):
                t = INF.cluster_mean_test(U["excess"].to_numpy(float), U["cl"].to_numpy(), reps=reps_wild, seed=SEED)
                lift = {"units": int(len(U)), "near": float(U["near"].mean()), "bench": float(U["bench"].mean()),
                        "lift": float(U["near"].mean() / U["bench"].mean()) if U["bench"].mean() > 0 else None,
                        "excess": t.get("mean"), "ci95": t.get("ci95"), "p_wild": t.get("p_wild"), "G": t.get("clusters"),
                        "valid": t.get("valid")}
            m = {"zone": det, "lift": lift}
            if name == "SHIPPED":
                m["developing"] = EV.detection_report(sc_d, {k: times[k] for k in sc_d}, tf, "warning", reps=1000) if sc_d else None
                m["confirmed"] = EV.detection_report(sc_c, {k: times[k] for k in sc_c}, tf, "confirmation", reps=1000) if sc_c else None
                for k in ("zone", "confirmed"):
                    X = pd.concat(mv[k], ignore_index=True) if mv[k] else pd.DataFrame()
                    m[f"move_{k}"] = {"n": int(len(X)), "mfe_med": _med(X, "mfe"), "mae_med": _med(X, "mae"),
                                      "r_h_mean_net": _mean(X, "r_h"), "r_h_med_net": _med(X, "r_h"),
                                      "ret_mean_net": _mean(X, "ret_h"), "ret_med_net": _med(X, "ret_h")}
                X2 = pd.concat(mv2, ignore_index=True) if mv2 else pd.DataFrame()
                m["move_confirmed"]["ret_mean_net_2x_cost"] = _mean(X2, "ret_h")
                if len(U):
                    m["by_class"] = U.groupby("cls").agg(n=("near", "size"), near=("near", "mean"), bench=("bench", "mean")).reset_index().to_dict("records")
                    m["by_era"] = U.groupby("era").agg(n=("near", "size"), near=("near", "mean"), bench=("bench", "mean")).reset_index().to_dict("records")
                    m["by_vol"] = U.groupby("atr_t").agg(n=("near", "size"), near=("near", "mean"), bench=("bench", "mean")).reset_index().to_dict("records")
                    m["_units"] = U[["near", "cl"]]
                m["confirmed_vs_baselines"] = confirm_baselines(per, sc_c, d, tf)
            cell["models"][name] = m
        # shipped vs B_ext at matched rate (information) and the primary verdict inputs
        sh, be = cell["models"]["SHIPPED"], cell["models"].get("B_ext")
        if be is not None and sh.get("_units") is not None and be["lift"]:
            Ub = []
            for s, (r, start_i, g) in per.items():
                spec, th = specs["candidates"][(d, "B_ext")]
                al = alerts_for(r, spec, th, d, tf)
                scb = EV.score_alerts(r["labs"][d], al["zone"][al["zone"] >= start_i], "warning", start_i)
                warm = ~np.isnan(p_series(r, spec))
                u = EV.lift_units(r["labs"][d], scb, "warning", np.full(len(warm), "all", object), warm, start_i)
                if len(u):
                    Ub.append(pd.DataFrame({"near": u["near"], "cl": cluster_id(r["idx"], tf)[u["i"].to_numpy(int)]}))
            Ub = pd.concat(Ub, ignore_index=True)
            both = pd.concat([sh["_units"].assign(k=True), Ub.assign(k=False)], ignore_index=True)
            cell["shipped_minus_B_ext_near"] = {k: v for k, v in INF.cluster_diff_test(both["near"], both["k"], both["cl"], reps=reps_wild, seed=SEED).items()
                                                if k in ("delta", "ci95", "p_wild", "clusters")}
        sh.pop("_units", None)
        out[d] = cell
    return out


def confirm_baselines(per, sc_c, d, tf, reps=20):
    res = {}
    for b in B.BASELINES:
        agg = {"matched": 0, "fa": 0, "events": 0, "alerts": 0, "available": 0, "target": 0}
        for s, (r, start_i, g) in per.items():
            if r.get("base") is None or s not in sc_c:
                continue
            target = sc_c[s]["alerts"]
            base = np.asarray(r["base"][d][b], int)
            base = base[base >= start_i]
            th = B.thin(base, target, r["idx"], tf, reps=reps, seed=SEED)
            agg["available"] += th["available"]; agg["target"] += th["target"]
            for rep in th["replicates"]:
                x = EV.score_alerts(r["labs"][d], rep, "confirmation", start_i)
                stt = list(x["status"].values())
                agg["matched"] += len(x["pairs"]) / reps; agg["fa"] += stt.count("false_alarm") / reps
                agg["events"] += len(x["events"]) / reps; agg["alerts"] += len(x["alerts"]) / reps
        res[b] = {"precision_excl_dup": agg["matched"] / (agg["matched"] + agg["fa"]) if (agg["matched"] + agg["fa"]) else None,
                  "recall": agg["matched"] / agg["events"] if agg["events"] else None, "alerts": agg["alerts"],
                  "target": agg["target"], "available": agg["available"]}
    return res


def _med(X, k):
    return float(np.nanmedian(X[k])) if len(X) and np.isfinite(X[k]).any() else None


def _mean(X, k):
    return float(np.nanmean(X[k])) if len(X) and np.isfinite(X[k]).any() else None


# ----------------------------------------------------------------------------- breadth (1D/1W)

def add_breadth(results):
    """§3 breadth: share of same-class instruments with rng > 0.8 (tops) / < 0.2 (bottoms) on the
    PREVIOUS candle date; NaN with fewer than 5 reporting instruments. Stored as breadth_top/bot and
    exposed per direction as 'breadth'."""
    for cls in {r["cls"] for r in results}:
        rs = [r for r in results if r["cls"] == cls]
        panel = pd.DataFrame({r["sym"]: pd.Series(r["F"]["rng"].to_numpy(float), index=r["idx"]) for r in rs})
        n = panel.notna().sum(axis=1)
        for key, fn in (("breadth_top", lambda x: x > 0.8), ("breadth_bot", lambda x: x < 0.2)):
            share = (fn(panel) & panel.notna()).sum(axis=1).astype(float) / n.where(n > 0).astype(float)
            share[n < 5] = np.nan
            share = share.shift(1)                                     # previous candle date only
            for r in rs:
                r["F"][key] = share.reindex(r["idx"]).to_numpy(float).astype("float32")


def with_breadth(results, d):
    for r in results:
        if "breadth_top" in r["F"]:
            r["F"]["breadth"] = r["F"]["breadth_top" if d == "top" else "breadth_bot"]


# ----------------------------------------------------------------------------- run

def _commit_ledger(tid):
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"CY ledger: record trial {tid} (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    LG.verify_against_git(LG.LEDGER)


def run_tf(tf, data_files, mode):
    tid = f"cy1-{tf}"
    LG.record(tid, f"CY-{tf}", ["exploration"], {"config": CONFIG, "tf": tf, "mode": mode}, CODE_FILES,
              ["val_ap", "recall", "precision", "false_alarms", "lead", "lift", "movement"], True, CONFIG, data_files,
              notes=f"exploration; review mode {mode}")
    _commit_ledger(tid)
    with ProcessPoolExecutor(8) as ex:
        results = [r for r in ex.map(build, [(s, tf) for s in DG.EVAL_SYMBOLS]) if r is not None]
    if tf in ("1D", "1W"):
        add_breadth(results)
    log, shipped, cands, thetas = {}, {}, {}, {}
    for d in DIRS:
        with_breadth(results, d)
        cand_g = {}
        for g in ("vol", "novol"):
            lg = {}
            spec, cand_g[g] = select(results, d, g, lg)
            th, cal = calibrate_theta(results if g == "novol" else [r for r in results if r["vol"]], spec, d, tf)
            spec["theta"] = th
            shipped[(d, g)] = spec
            thetas[(d, g)] = th
            lg["calibration"] = cal
            log[f"{d}|{g}"] = lg
        # candidates at their own matched-rate θ (all assets; volume models on volume assets)
        for name in ORDER:
            if name in BASE:
                spec = {"kind": "base", "feature": BASE[name], "sign": 1.0 if d == "top" else -1.0}
            else:                                   # refit on train+val with the C chosen on validation
                g = "vol" if name in ("L_vol", "L_int") else "novol"
                C = cand_g[g][name][1]["C"]
                T = table(results, d, MODELS[name], g)
                spec = fit_logit(T[T["_sp"] != "test"], MODELS[name], C)
            pool = [r for r in results if (r["vol"] or name not in ("L_vol", "L_int"))]
            th, _ = calibrate_theta(pool, spec, d, tf)
            cands[(d, name)] = (spec, th)
    ev = evaluate_tf(results, {"shipped": shipped, "candidates": cands}, thetas, tf)
    base_err = sorted({r["sym"] for r in results if r.get("base") is None})
    return {"selection": log, "evaluation": ev, "instruments": len(results), "baseline_errors": base_err,
            "n_vol_instruments": sum(r["vol"] for r in results)}, shipped


def run(tfs=TFS):
    mode = GT.require_cy_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    R = json.loads(OUT.read_text()) if OUT.exists() else {"tfs": {}}
    S = json.loads(SPEC.read_text()) if SPEC.exists() else {"tfs": {}}
    for tf in tfs:
        res, shipped = run_tf(tf, data_files, mode)
        R["tfs"][tf] = res
        L, Fw, D = LABEL[tf]
        S["tfs"][tf] = {"L": L, "D": D, "c": CF.q_of(L), "m": L // 2, "htf": CF.HTF_OF[tf], "L_htf": CF.SCALE[CF.HTF_OF[tf]]["L"],
                        "models": {f"{d}|{g}": v for (d, g), v in shipped.items()}}
        R["meta"] = {"mode": mode, "config": CONFIG, "manifest": m["combined_sha256"],
                     "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
        OUT.write_text(json.dumps(_clean(R), indent=1, default=str))
        SPEC.write_text(json.dumps(_clean(S), indent=1))
        print(f"[{tf}] done", flush=True)
    decide(R)
    OUT.write_text(json.dumps(_clean(R), indent=1, default=str))


def decide(R):
    """§6 primary test: Holm over the 8 TF x direction lift tests of the shipped zone onsets."""
    ps, info = {}, {}
    for tf, res in R["tfs"].items():
        for d, cell in res["evaluation"].items():
            sh = cell["models"]["SHIPPED"]
            lf, det = sh.get("lift"), sh.get("zone")
            ok = bool(lf and det and lf.get("valid") and det.get("events", 0) >= 30 and det.get("instruments", 0) >= 3 and (lf.get("G") or 0) >= 10)
            ps[f"{tf}|{d}"] = lf["p_wild"] if ok else 1.0
            info[f"{tf}|{d}"] = (ok, sh, cell)
    adj = holm(ps)
    out = {}
    for k, p in adj.items():
        ok, sh, cell = info[k]
        be = cell["models"].get("B_ext", {}).get("zone") or {}
        prec, bprec = (sh["zone"] or {}).get("precision_excluding_duplicates"), be.get("precision_excluding_duplicates")
        lift = (sh.get("lift") or {}).get("lift")
        sup = ok and p < 0.05 and lift is not None and lift > 1 and prec is not None and bprec is not None and prec >= bprec
        out[k] = {"evaluable": ok, "p_holm": p, "lift": lift, "precision": prec, "B_ext_precision": bprec,
                  "verdict": "SUPPORTED (exploratory)" if sup else ("NOT SUPPORTED" if ok else "NOT EVALUABLE")}
    R["primary"] = out


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items() if not str(k).startswith("_")}
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
    if isinstance(o, pd.DataFrame):
        return None
    return o


# ----------------------------------------------------------------------------- render

def _f(x, nd=3, sign=False):
    if x is None:
        return "–"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def render():
    R = json.loads(OUT.read_text())
    L = ["# Cycle engine CY-1: results (EXPLORATORY)", "",
         f"Review mode `{R['meta']['mode']}`; config `{R['meta']['config']}` (frozen); run at `{R['meta']['git_head'][:7]}`. "
         "All data was examined in earlier studies: nothing here is independent confirmation. Test periods: 1W ≥ 2016, 1D ≥ 2020, 4H/1H ≥ 2022.", "",
         "## Primary verdicts (Holm over 8 TF × direction lift tests of the shipped model's zone onsets)", "",
         "| TF · dir | verdict | lift | Holm p | zone precision* | B_ext precision* (matched rate) |", "|---|---|---:|---:|---:|---:|"]
    for k, v in R.get("primary", {}).items():
        L.append(f"| {k} | **{v['verdict']}** | {_f(v['lift'], 2)} | {_f(v['p_holm'], 4)} | {_f(v['precision'])} | {_f(v['B_ext_precision'])} |")
    for tf, res in R["tfs"].items():
        L += ["", f"## {tf} ({res['instruments']} instruments, {res['n_vol_instruments']} with volume)", ""]
        for key, lg in res["selection"].items():
            L.append(f"* selection {key}: core **{lg['selected_core']}**; val AP {json.dumps({k: round(v, 4) for k, v in lg['val_ap'].items()})} "
                     f"(base rate {lg['val_base_rate']:.4f}); G_ref {lg.get('G_ref_val_ap')}; context {json.dumps(lg['context'])}; "
                     f"θ calibration {json.dumps({k: round(v, 3) for k, v in lg['calibration'].items()})}")
        L += ["", "| dir · model | events | alerts | recall | precision* | FA/asset-yr | lead med | lift | excess [CI] (p, G) |", "|---|---:|---:|---|---:|---:|---:|---:|---|"]
        for d, cell in res["evaluation"].items():
            for name, m in cell["models"].items():
                z, lf = m.get("zone") or {}, m.get("lift") or {}
                L.append(f"| {d} · {name} | {z.get('events', '–')} | {z.get('alerts', '–')} | {_f((z.get('recall') or [None])[0])} | "
                         f"{_f(z.get('precision_excluding_duplicates'))} | {_f(z.get('false_alarms_per_instrument_year'), 2)} | "
                         f"{_f((z.get('lead_median') or [None])[0], 0)} | {_f(lf.get('lift'), 2)} | {_f(lf.get('excess'), 4, True)} "
                         f"[{_f((lf.get('ci95') or [None, None])[0], 4, True)}, {_f((lf.get('ci95') or [None, None])[1], 4, True)}] ({_f(lf.get('p_wild'), 4)}, {lf.get('G')}) |")
        L += ["", "| dir | alert | events | alerts | recall | precision* | FA/asset-yr | lead med (candles) | MFE / MAE med (ATR) | net ret mean / med (2× cost mean) |", "|---|---|---:|---:|---|---:|---:|---:|---|---|"]
        for d, cell in res["evaluation"].items():
            sh = cell["models"]["SHIPPED"]
            for a in ("zone", "developing", "confirmed"):
                z = sh.get(a) or {}
                mv = sh.get(f"move_{a}") or {}
                L.append(f"| {d} | {a} | {z.get('events', '–')} | {z.get('alerts', '–')} | {_f((z.get('recall') or [None])[0])} | "
                         f"{_f(z.get('precision_excluding_duplicates'))} | {_f(z.get('false_alarms_per_instrument_year'), 2)} | "
                         f"{_f((z.get('lead_median') or [None])[0], 0)} | {_f(mv.get('mfe_med'), 2)} / {_f(mv.get('mae_med'), 2)} | "
                         f"{_f(mv.get('ret_mean_net'), 4, True)} / {_f(mv.get('ret_med_net'), 4, True)} ({_f(mv.get('ret_mean_net_2x_cost'), 4, True)}) |")
            cb = sh.get("confirmed_vs_baselines") or {}
            L.append(f"| {d} | confirmed vs matched baselines (precision* / recall) | | | | | | | | "
                     + "; ".join(f"{b}: {_f(v['precision_excl_dup'])} / {_f(v['recall'])}" for b, v in cb.items()) + " |")
            L.append(f"| {d} | shipped − B_ext near-rate (matched rate) | | | | | | | | {json.dumps(cell.get('shipped_minus_B_ext_near'))} |")
            for g in ("by_class", "by_era", "by_vol"):
                if sh.get(g):
                    L.append(f"| {d} | {g} (near vs bench) | | | | | | | | " + "; ".join(
                        f"{x.get('cls', x.get('era', x.get('atr_t')))}: {x['near']:.3f} vs {x['bench']:.3f} (n {x['n']})" for x in sh[g]) + " |")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(tuple(sys.argv[2:]) or TFS)
    else:
        render()
