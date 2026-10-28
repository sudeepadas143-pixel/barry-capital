"""KB benchmark (reports/KB_CONFIG.md, FROZEN): reference model families vs Kenny's states, on the
CY-2 data, timing rules and outcome definitions. EXPLORATORY (all data examined before).

    python scripts/kb_bench.py run [TF ...]
    python scripts/kb_bench.py render
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research import cycle_features as CF, kb_signals as KS, v5_data as DG, v5_gate as GT  # noqa: E402
from research import v5_inference as INF, v5_ledger as LG, v5_manifest as MF  # noqa: E402

_s = importlib.util.spec_from_file_location("cycle2_research", ROOT / "scripts" / "cycle2_research.py")
C = importlib.util.module_from_spec(_s)
sys.modules["cycle2_research"] = C                     # picklable for worker processes
_s.loader.exec_module(C)

CONFIG = GT.KB_CONFIG
OUT = ROOT / "reports" / "kb_results.json"
MD = ROOT / "reports" / "KB_RESULTS.md"
SPEC = ROOT / "reports" / "cycle2_model_spec.json"
TFS = ("1W", "1D", "4H", "1H")
DIRS = ("top", "bot")
REF = "K_CONF"
META_GB = dict(max_depth=3, max_iter=60, learning_rate=0.1, min_samples_leaf=50, l2_regularization=1.0)
META_FAMS = ("K_S", "DIV1", "PA", "TREND")
META_MIN = 300
MIN_RATE = 0.05
REPS = 999
CODE_FILES = list(GT.KB_CODE)
KENNY = ("K_W", "K_S", "K_H", "K_CONF")
COMBOS = ("K_DIV", "K_PA", "K_META")
REFS = ("RSIX", "B_ext", "DIV1", "DIV2", "HID", "PA", "TREND", "META")


def build(args):
    r = C.build(args)
    if r is None:
        return None
    o, h, l, c = r["ohlc"]
    tf = args[1]
    L = C.CR.LABEL[tf][0]
    v = None
    if r["vol"]:                                       # build() does not keep volume: reload through the guarded loader
        df = DG.load(args[0], tf)
        assert df.index.equals(r["idx"])
        v = df["volume"].to_numpy(float)
    r["fam"] = KS.families(o, h, l, c, v, L, CF.q_of(L))
    return r


# ----------------------------------------------------------------------------- META

def meta(results, tf, d, events):
    """Meta-label filter: GB on primary events (CY-2 features + family flags), barrier label,
    refit per test year on events whose barrier window ended before it; keep p >= train median."""
    feats = C.ALLF
    rows = []
    for r in results:
        ev = events[r["sym"]]
        idx = np.unique(np.concatenate([ev[f] for f in META_FAMS])) if any(len(ev[f]) for f in META_FAMS) else np.array([], int)
        if not len(idx):
            continue
        X = r["F"][feats].to_numpy(float)[idx]
        fl = np.column_stack([np.isin(idx, ev[f]).astype(float) for f in META_FAMS])
        rows.append(pd.DataFrame({"sym": r["sym"], "i": idx, "t": r["idx"][idx], "end": r["end_bar"][idx], "y": r["bar"][d][idx],
                                  "ks": np.isin(idx, ev["K_S"])}).join(pd.DataFrame(np.hstack([X, fl]))))
    kept = {r["sym"]: [] for r in results}
    kept_ks = {r["sym"]: [] for r in results}
    if not rows:
        return {s: np.array([], int) for s in kept}, {s: np.array([], int) for s in kept}
    E = pd.concat(rows, ignore_index=True)
    XC = [c for c in E.columns if isinstance(c, int)]
    ys = C.YEARS[tf]
    for k, y0 in enumerate(ys):
        a = pd.Timestamp(f"{y0}-01-01", tz="UTC")
        b = pd.Timestamp(f"{ys[k + 1]}-01-01", tz="UTC") if k + 1 < len(ys) else pd.Timestamp("2100-01-01", tz="UTC")
        tr = E[(E["end"] < a) & np.isfinite(E["y"])]
        if len(tr) < META_MIN or tr["y"].sum() < 20 or (1 - tr["y"]).sum() < 20:
            continue
        m = HistGradientBoostingClassifier(random_state=C.SEED, **META_GB).fit(tr[XC].to_numpy(float), tr["y"].to_numpy(int))
        thr = float(np.median(m.predict_proba(tr[XC].to_numpy(float))[:, 1]))
        te = E[(E["t"] >= a) & (E["t"] < b)]
        if not len(te):
            continue
        keep = te[m.predict_proba(te[XC].to_numpy(float))[:, 1] >= thr]
        for s, g in keep.groupby("sym"):
            kept[s] += g["i"].tolist()
            kept_ks[s] += g.loc[g["ks"], "i"].tolist()
    f = lambda D: {s: np.array(sorted(v), int) for s, v in D.items()}  # noqa: E731
    return f(kept), f(kept_ks)


# ----------------------------------------------------------------------------- candidates

def candidates(results, tf, spec):
    """All candidate alert sets per direction: {d: {name: {sym: idx}}}."""
    L = C.CR.LABEL[tf][0]
    m = L // 2
    out = {}
    for d in DIRS:
        model = spec["tfs"][tf]["models"][d]["model"]
        kw = C.walk_forward(results, tf, d, model)
        be = kw if model == "B_ext" else C.walk_forward(results, tf, d, "B_ext")
        cand = {n: {} for n in KENNY + COMBOS + REFS}
        ev = {}
        for r in results:
            s = r["sym"]
            ks = kw[s]["standard"]
            cand["K_W"][s], cand["K_S"][s], cand["K_H"][s] = kw[s]["warning"], ks, kw[s]["high"]
            cand["K_CONF"][s] = C.confirmations(r, ks, d, tf)[0]
            cand["K_DIV"][s] = KS.after_zone(ks, r["fam"]["DIV1"][d], m)
            cand["K_PA"][s] = KS.after_zone(ks, r["fam"]["PA"][d], m)
            cand["B_ext"][s] = be[s]["standard"]
            for f in ("RSIX", "DIV1", "DIV2", "HID", "PA", "TREND"):
                cand[f][s] = r["fam"][f][d]
            ev[s] = {"K_S": ks, **{f: r["fam"][f][d] for f in ("DIV1", "PA", "TREND")}}
        cand["META"], cand["K_META"] = meta(results, tf, d, ev)
        out[d] = cand
    return out


def shipped(cands, tf):
    """As-shipped deduplication (both directions jointly)."""
    c = CF.q_of(C.CR.LABEL[tf][0])
    out = {d: {} for d in DIRS}
    for n in cands["top"]:
        out["top"][n], out["bot"][n] = {}, {}
        for s in cands["top"][n]:
            b, t = KS.dedupe_final(cands["bot"][n][s], cands["top"][n][s], c)
            out["bot"][n][s], out["top"][n][s] = b, t
    return out


def asset_years(results, tf):
    start = pd.Timestamp(f"{C.YEARS[tf][0]}-01-01", tz="UTC")
    yrs = {}
    for r in results:
        t = r["idx"][r["idx"] >= start]
        yrs[r["sym"]] = (t[-1] - t[0]).total_seconds() / (365.25 * 86400) if len(t) > 1 else 0.0
    return yrs


def compare3(a, b):
    out = C.compare(a, b, reps=REPS)
    A, B_ = a.get("_T"), b.get("_T")
    if A is not None and B_ is not None and len(A) and len(B_):
        both = pd.concat([A[["win", "cl", "half"]].assign(k=True), B_[["win", "cl", "half"]].assign(k=False)], ignore_index=True)
        both = both[np.isfinite(both["win"])]
        t = INF.cluster_diff_test(both["win"].to_numpy(float), both["k"].to_numpy(bool), both["cl"].to_numpy(), reps=REPS, seed=C.SEED)
        out["win"] = {"delta": t.get("delta"), "ci95": t.get("ci95"), "p": t.get("p_wild")}
    return out


def material(cmp_, rate):
    n, t, w = cmp_.get("near"), cmp_.get("net"), cmp_.get("win")
    if not (n and t and w) or None in (n["delta"], t["delta"], w["delta"]) or n.get("ci95") is None:
        return False
    return bool(t["delta"] > 0 and t["by_half"] and all(v > 0 for v in t["by_half"].values()) and w["delta"] > 0
                and n["ci95"][0] > -0.01 and rate >= MIN_RATE)


def run_tf(tf, data_files, mode, spec):
    tid = f"kb-{tf}"
    LG.record(tid, f"KB-{tf}", ["exploration"], {"config": CONFIG, "tf": tf, "mode": mode}, CODE_FILES,
              ["recall", "precision", "false_alarms", "lead", "lift", "net_return", "win_rate", "mfe", "mae", "rate"], True, CONFIG,
              data_files, notes=f"exploration; review mode {mode}")
    _commit_ledger(tid)
    with ProcessPoolExecutor(4) as ex:
        results = [r for r in ex.map(build, [(s, tf) for s in DG.EVAL_SYMBOLS]) if r is not None]
    raw = candidates(results, tf, spec)
    shp = shipped(raw, tf)
    yrs = sum(asset_years(results, tf).values())
    start = pd.Timestamp(f"{C.YEARS[tf][0]}-01-01", tz="UTC")
    st = {r["sym"]: int(r["idx"].searchsorted(start)) for r in results}
    res = {"instruments": len(results), "asset_years": yrs, "models": {d: spec["tfs"][tf]["models"][d]["model"] for d in DIRS}}
    for d in DIRS:
        cell = {}
        evs = {}
        for n in shp[d]:
            n_al = sum(int((v >= st[s]).sum()) for s, v in shp[d][n].items())
            evs[n] = C.evaluate(results, tf, d, shp[d][n], "warning", reps=REPS)
            er = C.evaluate(results, tf, d, raw[d][n], "warning", reps=REPS)
            cell[n] = {"shipped": C._strip(evs[n]), "raw": C._strip(er), "rate": n_al / yrs if yrs else None}
        for n in cell:
            if n != REF:
                cell[n]["vs_ref"] = compare3(evs[n], evs[REF])
                cell[n]["material"] = material(cell[n]["vs_ref"], cell[n]["rate"] or 0.0)
        res[d] = cell
    return res


def _commit_ledger(tid):
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"KB ledger: record trial {tid} (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    LG.verify_against_git(LG.LEDGER)


def run(tfs=TFS):
    mode = GT.require_kb_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    spec = json.loads(SPEC.read_text())
    R = json.loads(OUT.read_text()) if OUT.exists() else {"tfs": {}}
    for tf in tfs:
        R["tfs"][tf] = run_tf(tf, data_files, mode, spec)
        R["meta"] = {"mode": mode, "config": CONFIG, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
        OUT.write_text(json.dumps(C.CR._clean(R), indent=1, default=str))
        print(f"[{tf}] done", flush=True)


# ----------------------------------------------------------------------------- decisions and render

def decide(R):
    """§4: adoption of Kenny+idea combos and the global default state."""
    cells = [(tf, d) for tf in R["tfs"] for d in DIRS]
    adopted = [n for n in COMBOS if sum(R["tfs"][tf][d][n].get("material", False) for tf, d in cells) >= 5]
    pool = list(KENNY) + adopted
    ok = [n for n in pool if all((R["tfs"][tf][d][n]["rate"] or 0) >= MIN_RATE for tf, d in cells)]
    ranks = {n: [] for n in ok}
    for tf, d in cells:
        for key in ("win_rate", "net_mean", "precision"):
            vals = {}
            for n in ok:
                s = R["tfs"][tf][d][n]["shipped"]
                v = s.get("trade", {}).get(key) if key != "precision" else (s.get("det") or {}).get("precision")
                v = v[0] if isinstance(v, (list, tuple)) else v
                vals[n] = -np.inf if v is None else v
            order = sorted(ok, key=lambda n: -vals[n])
            for k, n in enumerate(order):
                ranks[n].append(k + 1)
    mean_rank = {n: float(np.mean(v)) for n, v in ranks.items()}
    default = min(mean_rank, key=mean_rank.get) if mean_rank else REF
    material = {n: {f"{tf}-{d}": R["tfs"][tf][d][n].get("material", False) for tf, d in cells} for n in COMBOS + REFS + tuple(k for k in KENNY if k != REF)}
    return {"adopted": adopted, "eligible": ok, "mean_rank": mean_rank, "default": default, "material": material}


def _g(x, n=2, s=False):
    if isinstance(x, (list, tuple)):
        x = x[0]
    return "–" if x is None else (f"{x:+.{n}f}" if s else f"{x:.{n}f}")


def render():
    R = json.loads(OUT.read_text())
    D = decide(R)
    L = ["# KB: benchmark library vs Kenny's states (EXPLORATORY: all data examined before)", "",
         "Config: `reports/KB_CONFIG.md`. As-shipped alerts (BUY/SELL clash and same-direction repeats within c candles removed). "
         "Warning window for every candidate. Win = barrier target (+D/2 ATR before −D/4 ATR within L/2). Net = entry next open, exit after L/2, "
         "after COST_BPS. Δ columns are against K_CONF (calendar-cluster wild bootstrap, 95% CI).", ""]
    for tf, T in R["tfs"].items():
        L += [f"## {tf} ({T['instruments']} instruments, {T['asset_years']:.0f} asset-years; shipped model top {T['models']['top']}, bottom {T['models']['bot']})", "",
              "| dir · candidate | alerts/asset-yr | recall | precision* | lift | win | MFE/MAE | net mean | net 2× | lead | Δwin [CI] | Δnet [CI] (halves) | Δnear [CI] | material |",
              "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|---|---|---|"]
        for d in DIRS:
            for n, v in T[d].items():
                s = v["shipped"]
                det, tr, lf = s.get("det") or {}, s.get("trade") or {}, s.get("lift") or {}
                c = v.get("vs_ref", {})
                w, t, nr = c.get("win", {}), c.get("net", {}), c.get("near", {})
                ci = lambda x: f"[{_g(x['ci95'][0], 3, True)}, {_g(x['ci95'][1], 3, True)}]" if x.get("ci95") else ""  # noqa: E731
                halves = "/".join(_g(h, 3, True) for h in t.get("by_half", {}).values())
                L.append(f"| {'SELL' if d == 'top' else 'BUY'} · {n} | {_g(v['rate'])} | {_g(det.get('recall'))} | {_g(det.get('precision'))} | {_g(lf.get('lift'))} | "
                         f"{_g(tr.get('win_rate'))} | {_g(tr.get('mfe_med'))}/{_g(tr.get('mae_med'))} | {_g(tr.get('net_mean'), 4, True)} | {_g(tr.get('net2_mean'), 4, True)} | "
                         f"{_g(det.get('lead'), 0)} | {_g(w.get('delta'), 3, True)} {ci(w)} | {_g(t.get('delta'), 4, True)} {ci(t)} ({halves}) | "
                         f"{_g(nr.get('delta'), 3, True)} {ci(nr)} | {'**yes**' if v.get('material') else ('ref' if n == REF else 'no')} |")
        L.append("")
    L += ["## Decisions (KB_CONFIG.md §4)", "",
          f"* Adopted Kenny + idea candidates (material in ≥ 5 of 8 cells): {', '.join(D['adopted']) or 'none'}.",
          f"* Eligible default states (≥ {MIN_RATE} alerts/asset-yr in every cell): {', '.join(D['eligible'])}.",
          "* Mean rank (win rate, net mean, precision; lower is better): " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(D["mean_rank"].items(), key=lambda kv: kv[1])) + ".",
          f"* **Default visible signal: {D['default']}.**", "",
          "Cells with a material improvement over K_CONF:", ""]
    for n, cells in D["material"].items():
        hit = [k for k, v in cells.items() if v]
        L.append(f"* {n}: {len(hit)}/8 {('(' + ', '.join(hit) + ')') if hit else ''}")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run(tuple(sys.argv[2:]) or TFS)
    elif len(sys.argv) > 1 and sys.argv[1] == "render":
        render()
    else:
        print(__doc__)
