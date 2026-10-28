"""Cycle engine CY-2 (reports/CYCLE2_CONFIG.md, FROZEN): walk-forward nonlinear and trade-aware
turning-point models vs the extension baseline. EXPLORATORY (all data examined before).

    python scripts/cycle2_research.py run [TF ...]
    python scripts/cycle2_research.py render
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
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf import ta  # noqa: E402
from hcmtf.universe import COST_BPS  # noqa: E402
from research import cycle2_features as C2, cycle_features as CF, v5_data as DG, v5_eval as EV  # noqa: E402
from research import v5_gate as GT, v5_inference as INF, v5_ledger as LG, v5_manifest as MF  # noqa: E402
from research.v41 import cluster_id  # noqa: E402

_s = importlib.util.spec_from_file_location("cycle_research", ROOT / "scripts" / "cycle_research.py")
CR = importlib.util.module_from_spec(_s)
_s.loader.exec_module(CR)

CONFIG = "reports/CYCLE2_CONFIG.md"
OUT = ROOT / "reports" / "cycle2_results.json"
SPEC = ROOT / "reports" / "cycle2_model_spec.json"
MD = ROOT / "reports" / "CYCLE2_RESULTS.md"
TFS = ("1W", "1D", "4H", "1H")
YEARS = {"1W": list(range(2008, 2027, 2)), "1D": list(range(2010, 2027)), "4H": list(range(2021, 2027)), "1H": list(range(2021, 2027))}
ALLF = CF.PRICE + CF.MOM + CF.VOL + CF.INTER + C2.NEW
LRF = CF.PRICE + CF.MOM
PRIMARY = dict(max_depth=3, max_iter=60, learning_rate=0.1, min_samples_leaf=200, l2_regularization=1.0)
VARIANTS = {"d2": dict(PRIMARY, max_depth=2), "d4": dict(PRIMARY, max_depth=4), "t30": dict(PRIMARY, max_iter=30),
            "t120": dict(PRIMARY, max_iter=120)}
TIERS = {"warning": 3.0, "standard": 2.0, "high": 0.75}
MAX_ROWS = 300_000
SEED = 20261027
DIRS = {"top": -1, "bot": 1}
CODE_FILES = ["research/cycle2_features.py", "scripts/cycle2_research.py", "research/cycle_features.py", "scripts/cycle_research.py",
              "research/v5_eval.py", "research/v5_inference.py", "research/v5_data.py"]


# ----------------------------------------------------------------------------- data

def build(args):
    sym, tf = args
    CR.ST.classify = lambda *a, **k: None          # CY-1 confirmation baselines are not used by CY-2: skip them
    CR.B.generate = lambda *a, **k: {}
    r = CR.build((sym, tf))
    if r is None:
        return None
    o, h, l, c = r["ohlc"]
    F2 = C2.features(pd.DataFrame({"open": o, "high": h, "low": l, "close": c}, index=r["idx"]), tf,
                     r["F"]["relvol"].to_numpy(float) if r["vol"] else None)
    r["F"] = pd.concat([r["F"], F2.astype("float32")], axis=1)
    L, Fw, D = CR.LABEL[tf]
    atr = r["F"]["_atr"].to_numpy(float)
    r["bar"] = {d: C2.barrier_target(o, h, l, c, atr, side, L // 2, D / 2, D / 4) for d, side in DIRS.items()}
    n = len(c)
    s = np.arange(n)
    r["end_zone"] = r["idx"][np.minimum(s + L // 2 + max(L, Fw), n - 1)]     # last candle the zone label can depend on
    r["end_bar"] = r["idx"][np.minimum(s + L // 2 + 1, n - 1)]
    r.pop("base", None)
    return r


def stack(results, d, feats, target, year_start=None, train=True):
    """Rows for training (purged before year_start) with target 'zone' or 'barrier'."""
    parts = []
    for r in results:
        X = r["F"][feats].to_numpy(float)
        y = r["y"][d].astype(float) if target == "zone" else r["bar"][d]
        ok = (r["valid"][d] if target == "zone" else np.isfinite(y))
        end = r["end_zone"] if target == "zone" else r["end_bar"]
        ok = ok & (end < year_start)
        if feats == LRF:
            ok &= ~np.isnan(X).any(axis=1)
        else:
            ok &= ~np.isnan(X[:, :len(CF.PRICE)]).any(axis=1)          # core price features required; others may be NaN
        parts.append((X[ok], y[ok]))
    X = np.concatenate([p[0] for p in parts])
    y = np.concatenate([p[1] for p in parts])
    if len(y) > MAX_ROWS:
        stride = int(np.ceil(len(y) / MAX_ROWS))
        X, y = X[::stride], y[::stride]
    return X, y


def fit(kind, X, y, params=None):
    if kind == "LR":
        mu, sd = np.nanmean(X, axis=0), np.nanstd(X, axis=0)
        sd[sd == 0] = 1
        m = LogisticRegression(C=0.1, class_weight="balanced", max_iter=2000).fit(np.clip((X - mu) / sd, -5, 5), y)
        return ("LR", m, mu, sd)
    m = HistGradientBoostingClassifier(random_state=SEED, **(params or PRIMARY)).fit(X, y)
    return ("GB", m, None, None)


def predict(model, r, feats):
    kind, m, mu, sd = model
    X = r["F"][feats].to_numpy(float)
    if kind == "LR":
        p = m.predict_proba(np.clip((X - mu) / sd, -5, 5))[:, 1]
        p[np.isnan(X).any(axis=1)] = np.nan
    else:
        p = m.predict_proba(X)[:, 1]
        p[np.isnan(X[:, :len(CF.PRICE)]).any(axis=1)] = np.nan
    return p


def base_score(r, d):
    x = r["F"]["ext_c"].to_numpy(float)
    return x if d == "top" else -x


# ----------------------------------------------------------------------------- walk-forward

def theta_for(scores_train, prevmax_train, years, target_rate):
    P, M = np.concatenate(scores_train), np.concatenate(prevmax_train)
    fin = P[np.isfinite(P)]
    grid = np.unique(np.quantile(fin, np.linspace(0.5, 0.9995, 300)))
    with np.errstate(invalid="ignore"):
        rates = np.array([np.sum((P >= t) & ~(M >= t)) / years for t in grid])
    return float(grid[int(np.argmin(np.abs(rates - target_rate)))])


def walk_forward(results, tf, d, model_name, params=None):
    """Out-of-time onsets per instrument per tier, each year scored by a model trained on earlier data."""
    L = CR.LABEL[tf][0]
    c = CF.q_of(L)
    ys = YEARS[tf]
    alerts = {r["sym"]: {t: [] for t in TIERS} for r in results}
    for k, y0 in enumerate(ys):
        a = pd.Timestamp(f"{y0}-01-01", tz="UTC")
        b = pd.Timestamp(f"{ys[k + 1]}-01-01", tz="UTC") if k + 1 < len(ys) else pd.Timestamp("2100-01-01", tz="UTC")
        if model_name == "B_ext":
            model, feats = None, None
        else:
            feats = LRF if model_name == "LR" else ALLF
            target = "barrier" if model_name.startswith("GBB") else "zone"
            X, yv = stack(results, d, feats, target, a)
            if len(yv) < 1000 or yv.sum() < 50:
                continue
            model = fit("LR" if model_name == "LR" else "GB", X, yv, params)
        # thresholds from training-period candles only (events and asset-years before the year)
        Ptr, Mtr, ev, yrs = [], [], 0, 0.0
        P_all = {}
        for r in results:
            p = base_score(r, d) if model is None else predict(model, r, feats)
            P_all[r["sym"]] = p
            prev = pd.Series(p).shift(1).rolling(c, min_periods=1).max().to_numpy()
            w = (r["end_zone"] < a) & r["valid"][d]
            if w.sum() < 10:
                continue
            Ptr.append(p[w]); Mtr.append(prev[w])
            e = r["labs"][d].events
            ev += int(w[e].sum()) if len(e) else 0
            t = r["idx"][w]
            yrs += (t[-1] - t[0]).total_seconds() / (365.25 * 86400)
        if not Ptr or yrs <= 0:
            continue
        for tier, mult in TIERS.items():
            th = theta_for(Ptr, Mtr, yrs, mult * ev / yrs)
            for r in results:
                on = CF.zone_onsets(P_all[r["sym"]], th, c)
                sel = on[(r["idx"][on] >= a) & (r["idx"][on] < b)]
                alerts[r["sym"]][tier].extend(sel.tolist())
    return {s: {t: np.array(sorted(v), int) for t, v in tv.items()} for s, tv in alerts.items()}


# ----------------------------------------------------------------------------- evaluation

def trade_stats(r, a, d, tf, cost_mult=1.0):
    L, _, D = CR.LABEL[tf]
    H = L // 2
    o, h, l, c = r["ohlc"]
    atr = r["F"]["_atr"].to_numpy(float)
    side = DIRS[d]
    a = a[a + H < len(c)]
    cost = COST_BPS[r["cls"]] / 1e4 * cost_mult
    px = o[a + 1]
    ex = c[a + H]
    net = side * (ex / px - 1) - cost
    mfe = np.array([(np.max(h[s + 1:s + H + 1]) - o[s + 1]) if side > 0 else (o[s + 1] - np.min(l[s + 1:s + H + 1])) for s in a]) / atr[a]
    mae = np.array([(o[s + 1] - np.min(l[s + 1:s + H + 1])) if side > 0 else (np.max(h[s + 1:s + H + 1]) - o[s + 1]) for s in a]) / atr[a]
    return pd.DataFrame({"i": a, "net": net, "mfe": mfe, "mae": mae, "win": r["bar"][d][a]})


def confirmations(r, on, d, tf):
    """(a) CY-1 rule; (b) first EMA20/50 cross against the prior move within m candles after an onset."""
    L, _, D = CR.LABEL[tf]
    o, h, l, c = r["ohlc"]
    F = r["F"]
    _, conf_a = CF.developing_and_confirmed(on, DIRS[d], o, h, l, c, F["_rsi"].to_numpy(float), F["_hist"].to_numpy(float),
                                            F["_ema_f"].to_numpy(float), F["_atr"].to_numpy(float), L, D)
    e20, e50 = ta.ema(c, 20), ta.ema(c, 50)
    diff = np.sign(e20 - e50)
    want = -1 if d == "top" else 1
    cross = np.flatnonzero((diff == want) & (np.r_[np.nan, diff[:-1]] == -want))
    m = L // 2
    conf_b = []
    for s in on:
        k = cross[(cross > s) & (cross <= s + m)]
        if len(k):
            conf_b.append(int(k[0]))
    return conf_a, np.unique(np.array(conf_b, int))


def evaluate(results, tf, d, alerts_by_sym, kind="warning", reps=2999):
    start = pd.Timestamp(f"{YEARS[tf][0]}-01-01", tz="UTC")
    mid = pd.Timestamp(f"{YEARS[tf][len(YEARS[tf]) // 2]}-01-01", tz="UTC")
    sc, times, U, T = {}, {}, [], []
    for r in results:
        a = alerts_by_sym.get(r["sym"], np.array([], int))
        st = int(r["idx"].searchsorted(start))
        if st >= len(r["idx"]) - CR.LABEL[tf][0]:
            continue
        a = a[a >= st]
        sc[r["sym"]] = EV.score_alerts(r["labs"][d], a, kind, st)
        times[r["sym"]] = r["idx"]
        warm = ~np.isnan(r["F"]["ext_c"].to_numpy(float))
        u = EV.lift_units(r["labs"][d], sc[r["sym"]], kind, np.full(len(warm), "all", object), warm, st)
        cl = cluster_id(r["idx"], tf)
        if len(u):
            u["cl"] = cl[u["i"].to_numpy(int)]
            u["half"] = np.where(r["idx"][u["i"].to_numpy(int)] < mid, "early", "late")
            U.append(u)
        if len(a):
            t = trade_stats(r, a, d, tf)
            t2 = trade_stats(r, a, d, tf, 2.0)
            t["net2"] = t2["net"].to_numpy()
            t["cl"] = cl[t["i"].to_numpy(int)]
            t["half"] = np.where(r["idx"][t["i"].to_numpy(int)] < mid, "early", "late")
            t["sym"] = r["sym"]
            T.append(t)
    det = EV.detection_report(sc, times, tf, kind, reps=500) if sc else None
    U = pd.concat(U, ignore_index=True) if U else pd.DataFrame()
    T = pd.concat(T, ignore_index=True) if T else pd.DataFrame()
    out = {"det": det}
    if len(U):
        tt = INF.cluster_mean_test(U["excess"].to_numpy(float), U["cl"].to_numpy(), reps=reps, seed=SEED)
        out["lift"] = {"lift": float(U["near"].mean() / U["bench"].mean()), "ci95_excess": tt.get("ci95"), "p": tt.get("p_wild"),
                       "G": tt.get("clusters"), "by_half": {h: float(g["near"].mean() / g["bench"].mean()) for h, g in U.groupby("half")}}
    if len(T):
        tt = INF.cluster_mean_test(T["net"].to_numpy(float), T["cl"].to_numpy(), reps=reps, seed=SEED, alternative="two-sided")
        out["trade"] = {"n": int(len(T)), "net_mean": float(T["net"].mean()), "net_ci95": tt.get("ci95"), "net_median": float(T["net"].median()),
                        "net2_mean": float(T["net2"].mean()), "win_rate": float(np.nanmean(T["win"])), "mfe_med": float(np.nanmedian(T["mfe"])),
                        "mae_med": float(np.nanmedian(T["mae"])), "by_half": {h: float(g["net"].mean()) for h, g in T.groupby("half")},
                        "pair_median_of_mean_net": float(T.groupby("sym")["net"].mean().median())}
    out["_U"], out["_T"] = U, T
    return out


def compare(a, b, reps=2999):
    """a minus b: near rate (lift units) and net return, calendar-cluster wild bootstrap."""
    out = {}
    for key, col in (("near", "_U"), ("net", "_T")):
        A, B_ = a.get(col), b.get(col)
        if A is None or B_ is None or not len(A) or not len(B_):
            continue
        v = "near" if key == "near" else "net"
        both = pd.concat([A[[v, "cl", "half"]].assign(k=True), B_[[v, "cl", "half"]].assign(k=False)], ignore_index=True)
        t = INF.cluster_diff_test(both[v].to_numpy(float), both["k"].to_numpy(bool), both["cl"].to_numpy(), reps=reps, seed=SEED)
        halves = {h: float(g[g["k"]][v].mean() - g[~g["k"]][v].mean()) for h, g in both.groupby("half") if g["k"].any() and (~g["k"]).any()}
        out[key] = {"delta": t.get("delta"), "ci95": t.get("ci95"), "p": t.get("p_wild"), "by_half": halves}
    return out


def promote(c, rob):
    """§7 promotion of a GB model over B_ext (standard tier)."""
    n, t = c.get("near"), c.get("net")
    if not n or not t or n["delta"] is None or t["delta"] is None:
        return False, "not comparable"
    ok = n["delta"] > 0 and t["delta"] > 0 and n["ci95"][0] > -0.01
    ok &= all(v > 0 for v in n["by_half"].values()) and all(v > 0 for v in t["by_half"].values())
    agree = sum(1 for v in rob.values() if v.get("near", {}).get("delta", -1) > 0 and v.get("net", {}).get("delta", -1) > 0)
    ok &= agree >= 3
    return bool(ok), f"robust variants agreeing: {agree}/4"


# ----------------------------------------------------------------------------- run

def _commit_ledger(tid):
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"CY2 ledger: record trial {tid} (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    LG.verify_against_git(LG.LEDGER)


def run_tf(tf, data_files, mode):
    tid = f"cy2-{tf}"
    LG.record(tid, f"CY2-{tf}", ["exploration"], {"config": CONFIG, "tf": tf, "mode": mode}, CODE_FILES,
              ["recall", "precision", "false_alarms", "lead", "lift", "net_return", "win_rate"], True, CONFIG, data_files,
              notes=f"exploration; review mode {mode}")
    _commit_ledger(tid)
    with ProcessPoolExecutor(8) as ex:
        results = [r for r in ex.map(build, [(s, tf) for s in DG.EVAL_SYMBOLS]) if r is not None]
    res = {"instruments": len(results)}
    for d in DIRS:
        cell = {"models": {}, "confirm": {}}
        evs = {}
        for name in ("B_ext", "LR", "GBZ", "GBB"):
            al = walk_forward(results, tf, d, name)
            evs[name] = {tier: evaluate(results, tf, d, {s: v[tier] for s, v in al.items()}) for tier in TIERS}
            cell["models"][name] = {tier: {k: v for k, v in e.items() if not k.startswith("_")} for tier, e in evs[name].items()}
            if name in ("B_ext", "GBZ", "GBB"):
                ca, cb = {}, {}
                for r in results:
                    a, b = confirmations(r, al[r["sym"]]["standard"], d, tf)
                    ca[r["sym"]], cb[r["sym"]] = a, b
                cell["confirm"][name] = {"cy1_rule": _strip(evaluate(results, tf, d, ca, "confirmation")),
                                         "ema_cross_after_zone": _strip(evaluate(results, tf, d, cb, "confirmation"))}
        cell["vs_B_ext"] = {}
        for name in ("LR", "GBZ", "GBB"):
            cmp_ = compare(evs[name]["standard"], evs["B_ext"]["standard"])
            rob = {}
            if name.startswith("GB") and cmp_.get("near", {}).get("delta", -1) > 0 and cmp_.get("net", {}).get("delta", -1) > 0:
                for vn, vp in VARIANTS.items():
                    alv = walk_forward(results, tf, d, name, vp)
                    rob[vn] = compare(evaluate(results, tf, d, {s: v["standard"] for s, v in alv.items()}), evs["B_ext"]["standard"])
            prom = promote(cmp_, rob) if name.startswith("GB") else (False, "reference")
            cell["vs_B_ext"][name] = {"standard": cmp_, "robustness": {k: {kk: {"delta": vv.get("delta")} for kk, vv in v.items()} for k, v in rob.items()},
                                      "promoted": prom[0], "note": prom[1]}
        res[d] = cell
    return res, results


def _strip(e):
    return {k: v for k, v in e.items() if not k.startswith("_")}


def final_models(results, tf, R):
    """Promoted GB models refit on ALL eligible data (for Pine); others ship B_ext."""
    spec = {}
    for d in DIRS:
        best = None
        for name in ("GBZ", "GBB"):
            v = R[d]["vs_B_ext"][name]
            if v["promoted"] and (best is None or v["standard"]["net"]["delta"] > R[d]["vs_B_ext"][best]["standard"]["net"]["delta"]):
                best = name
        if best is None:
            spec[d] = {"kind": "base", "feature": "ext_c", "sign": 1.0 if d == "top" else -1.0, "model": "B_ext"}
            sc = [base_score(r, d) for r in results]
        else:
            X, y = stack(results, d, ALLF, "barrier" if best == "GBB" else "zone", pd.Timestamp("2100-01-01", tz="UTC"))
            m = HistGradientBoostingClassifier(random_state=SEED, **PRIMARY).fit(X, y)
            spec[d] = {"kind": "gb", "model": best, "features": ALLF, **export_gb(m)}
            sc = [predict(("GB", m, None, None), r, ALLF) for r in results]
        c = CF.q_of(CR.LABEL[tf][0])
        P, Mx, ev, yrs = [], [], 0, 0.0
        for r, p in zip(results, sc):
            w = r["valid"][d]
            if w.sum() < 10:
                continue
            P.append(p[w]); Mx.append(pd.Series(p).shift(1).rolling(c, min_periods=1).max().to_numpy()[w])
            e = r["labs"][d].events
            ev += int(w[e].sum()) if len(e) else 0
            t = r["idx"][w]
            yrs += (t[-1] - t[0]).total_seconds() / (365.25 * 86400)
        spec[d]["theta"] = {tier: theta_for(P, Mx, yrs, mult * ev / yrs) for tier, mult in TIERS.items()}
    return spec


def export_gb(m) -> dict:
    """Trees of a fitted HistGradientBoostingClassifier as plain lists (feature, threshold,
    missing-left, children, leaf value), plus the baseline log-odds."""
    trees = []
    for pred in m._predictors:
        nodes = pred[0].nodes
        trees.append([{"f": int(nd["feature_idx"]), "t": float(nd["num_threshold"]), "ml": bool(nd["missing_go_to_left"]),
                       "l": int(nd["left"]), "r": int(nd["right"]), "leaf": bool(nd["is_leaf"]), "v": float(nd["value"])} for nd in nodes])
    return {"baseline": float(np.ravel(m._baseline_prediction)[0]), "trees": trees}


def gb_logodds(spec, X: np.ndarray) -> np.ndarray:
    """Evaluate exported trees (the same logic the Pine code runs)."""
    out = np.full(len(X), spec["baseline"])
    for tr in spec["trees"]:
        for i in range(len(X)):
            k = 0
            while not tr[k]["leaf"]:
                x = X[i, tr[k]["f"]]
                go_left = tr[k]["ml"] if np.isnan(x) else x <= tr[k]["t"]
                k = tr[k]["l"] if go_left else tr[k]["r"]
            out[i] += tr[k]["v"]
    return out


def run(tfs=TFS):
    mode = GT.require_cy2_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    R = json.loads(OUT.read_text()) if OUT.exists() else {"tfs": {}}
    S = json.loads(SPEC.read_text()) if SPEC.exists() else {"tfs": {}}
    for tf in tfs:
        res, results = run_tf(tf, data_files, mode)
        R["tfs"][tf] = res
        L, Fw, D = CR.LABEL[tf]
        S["tfs"][tf] = {"L": L, "D": D, "c": CF.q_of(L), "m": L // 2, "models": final_models(results, tf, res)}
        R["meta"] = {"mode": mode, "config": CONFIG, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
        OUT.write_text(json.dumps(CR._clean(R), indent=1, default=str))
        SPEC.write_text(json.dumps(CR._clean(S)))
        print(f"[{tf}] done", flush=True)


# ----------------------------------------------------------------------------- render

def _f(x, n=3, s=False):
    return "–" if x is None else (f"{x:+.{n}f}" if s else f"{x:.{n}f}")


def render():
    R = json.loads(OUT.read_text())
    L = ["# Cycle engine CY-2: walk-forward results (EXPLORATORY: all data examined before)", "",
         "Out-of-time = each year scored by models trained only on earlier years. Zone alerts scored with the frozen warning window; "
         "trade = entry next open, exit after L/2 candles, net of COST_BPS.", ""]
    for tf, res in R["tfs"].items():
        L += [f"## {tf} ({res['instruments']} instruments)", "",
              "| dir · model · tier | events | alerts | recall | precision* | FA/asset-yr | lead | lift (early/late) | win rate | net mean [CI] | net median | pair-median net | 2× cost | MFE/MAE |",
              "|---|---:|---:|---:|---:|---:|---:|---|---:|---|---:|---:|---:|---|"]
        for d in ("top", "bot"):
            for name, tiers in res[d]["models"].items():
                for tier, e in tiers.items():
                    z, lf, t = e.get("det") or {}, e.get("lift") or {}, e.get("trade") or {}
                    bh = lf.get("by_half") or {}
                    L.append(f"| {d} · {name} · {tier} | {z.get('events', '–')} | {z.get('alerts', '–')} | {_f((z.get('recall') or [None])[0], 2)} | "
                             f"{_f(z.get('precision_excluding_duplicates'), 2)} | {_f(z.get('false_alarms_per_instrument_year'), 2)} | {_f((z.get('lead_median') or [None])[0], 0)} | "
                             f"{_f(lf.get('lift'), 2)} ({_f(bh.get('early'), 2)}/{_f(bh.get('late'), 2)}) | {_f(t.get('win_rate'), 2)} | "
                             f"{_f(t.get('net_mean'), 4, True)} [{_f((t.get('net_ci95') or [None])[0], 4, True)}, {_f((t.get('net_ci95') or [None, None])[1], 4, True)}] | "
                             f"{_f(t.get('net_median'), 4, True)} | {_f(t.get('pair_median_of_mean_net'), 4, True)} | {_f(t.get('net2_mean'), 4, True)} | {_f(t.get('mfe_med'), 2)}/{_f(t.get('mae_med'), 2)} |")
            for name, cf in res[d]["confirm"].items():
                for rule, e in cf.items():
                    z, t = e.get("det") or {}, e.get("trade") or {}
                    L.append(f"| {d} · {name} · confirm:{rule} | {z.get('events', '–')} | {z.get('alerts', '–')} | {_f((z.get('recall') or [None])[0], 2)} | "
                             f"{_f(z.get('precision_excluding_duplicates'), 2)} | {_f(z.get('false_alarms_per_instrument_year'), 2)} | {_f((z.get('lead_median') or [None])[0], 0)} | | "
                             f"{_f(t.get('win_rate'), 2)} | {_f(t.get('net_mean'), 4, True)} | {_f(t.get('net_median'), 4, True)} | {_f(t.get('pair_median_of_mean_net'), 4, True)} | {_f(t.get('net2_mean'), 4, True)} | {_f(t.get('mfe_med'), 2)}/{_f(t.get('mae_med'), 2)} |")
        L += ["", "| dir · model | Δ near vs B_ext [CI] (halves) | Δ net vs B_ext [CI] (halves) | robustness | promoted |", "|---|---|---|---|---|"]
        for d in ("top", "bot"):
            for name, v in res[d]["vs_B_ext"].items():
                n, t = v["standard"].get("near", {}), v["standard"].get("net", {})
                L.append(f"| {d} · {name} | {_f(n.get('delta'), 4, True)} {n.get('ci95')} {n.get('by_half')} | {_f(t.get('delta'), 4, True)} {t.get('ci95')} {t.get('by_half')} | "
                         f"{v['note']} {v.get('robustness')} | **{v['promoted']}** |")
        L.append("")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(tuple(sys.argv[2:]) or TFS)
    else:
        render()
