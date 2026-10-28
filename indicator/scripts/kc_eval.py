"""KC (reports/KC_CONFIG.md, FROZEN): cumulative signal clusters vs the current Kenny behaviour.
EXPLORATORY (all data examined before; shipped spec fitted on the same data).

    python scripts/kc_eval.py run
    python scripts/kc_eval.py render
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

from hcmtf.universe import COST_BPS  # noqa: E402
from research import cycle2_features as C2, cycle_features as CF, kenny_cluster as KC, kenny_sim as KSIM  # noqa: E402
from research import v5_data as DG, v5_gate as GT, v5_ledger as LG, v5_manifest as MF  # noqa: E402

CONFIG = GT.KC_CONFIG
OUT = ROOT / "reports" / "kc_results.json"
MD = ROOT / "reports" / "KC_RESULTS.md"
SPEC = ROOT / "reports" / "cycle2_model_spec.json"
TFS = ("1W", "1D", "4H", "1H")
MID = {"1W": 2018, "1D": 2018, "4H": 2024, "1H": 2024}       # CY-2 test-year midpoints
SETTINGS = {"S1": (1 / 8, 1.5, True), "S2": (1 / 8, 2.0, True), "S3": (1 / 4, 1.5, True), "S4": (1 / 4, 2.0, True),
            "S5": (1 / 8, 1.5, False)}
CANDS = ("S1", "S2", "S3", "S4")
CODE_FILES = list(GT.KC_CODE)


def outcomes(df, tf, idx, side, cls):
    L, D = CF.SCALE[tf]["L"], CF.SCALE[tf]["D"]
    H = L // 2
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    from hcmtf import ta
    atr = ta.atr(h, l, c, 14)
    idx = np.asarray(idx, int)
    idx = idx[idx + H < len(c)]
    win = C2.barrier_target(o, h, l, c, atr, side, H, D / 2, D / 4)[idx]
    px, ex = o[idx + 1], c[idx + H]
    net = side * (ex / px - 1) - COST_BPS[cls] / 1e4
    mfe = np.array([(h[s + 1:s + H + 1].max() - o[s + 1]) if side > 0 else (o[s + 1] - l[s + 1:s + H + 1].min()) for s in idx]) / atr[idx]
    mae = np.array([(o[s + 1] - l[s + 1:s + H + 1].min()) if side > 0 else (h[s + 1:s + H + 1].max() - o[s + 1]) for s in idx]) / atr[idx]
    return pd.DataFrame({"i": idx, "t": df.index[idx], "win": win, "net": net, "mfe": mfe, "mae": mae})


def one(args):
    sym, tf = args
    spec = json.loads(SPEC.read_text())
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
    cls = DG.EXPLORATION[sym].cls
    b0, s0, st = KSIM.shipped_signals(df, tf, spec)
    ev = KC.evidence(df, tf, st, htf)
    sig = {"S0": (b0, s0)}
    for k, (hl, th, nov) in SETTINGS.items():
        b, s, _ = KC.run_clusters(ev, tf, hl, th, nov)
        sig[k] = (b, s)
    yrs = (df.index[-1] - df.index[0]).total_seconds() / (365.25 * 86400)
    c = CF.q_of(CF.SCALE[tf]["L"])
    out = {"sym": sym, "yrs": yrs, "res": {}}
    for k, (b, s) in sig.items():
        for d, idx, side in (("bot", b, 1), ("top", s, -1)):
            t = outcomes(df, tf, idx, side, cls)
            t["sym"] = sym
            ep = int(1 + np.sum(np.diff(np.sort(idx)) > c)) if len(idx) else 0
            out["res"][(k, d)] = (t, ep)
    return out


def summarise(rows, tf):
    yrs = sum(r["yrs"] for r in rows)
    mid = pd.Timestamp(f"{MID[tf]}-01-01", tz="UTC")
    res = {}
    for k in ["S0", *SETTINGS]:
        for d in ("bot", "top"):
            T = pd.concat([r["res"][(k, d)][0] for r in rows], ignore_index=True)
            ep = sum(r["res"][(k, d)][1] for r in rows)
            if not len(T):
                res[f"{k}|{d}"] = {"n": 0, "rate": 0.0, "episodes": ep}
                continue
            res[f"{k}|{d}"] = {
                "n": int(len(T)), "rate": len(T) / yrs, "episodes": ep, "episode_rate": ep / yrs,
                "win": float(np.nanmean(T["win"])), "mfe_med": float(np.nanmedian(T["mfe"])), "mae_med": float(np.nanmedian(T["mae"])),
                "net_mean": float(T["net"].mean()), "net_median": float(T["net"].median()),
                "pair_median": float(T.groupby("sym")["net"].median().median()),
                "halves": {h: {"n": int(len(g)), "win": float(np.nanmean(g["win"])), "net_median": float(g["net"].median())}
                           for h, g in T.groupby(np.where(T["t"] < mid, "early", "late"))}}
    return {"asset_years": yrs, "instruments": len(rows), "cells": res}


def decide(R):
    cells = [(tf, d) for tf in R["tfs"] for d in ("bot", "top")]
    ok = []
    for k in CANDS:
        rate_ok = all(R["tfs"][tf]["cells"][f"{k}|{d}"]["rate"] <= 4 * max(R["tfs"][tf]["cells"][f"S0|{d}"]["rate"], 1e-9) for tf, d in cells)
        mae_ok = sum(R["tfs"][tf]["cells"][f"{k}|{d}"].get("mae_med", np.inf) <= 1.10 * R["tfs"][tf]["cells"][f"S0|{d}"].get("mae_med", np.inf)
                     for tf, d in cells) >= 6
        if rate_ok and mae_ok:
            ok.append(k)
    ranks = {k: [] for k in ok}
    for tf, d in cells:
        for key in ("win", "net_median", "pair_median"):
            order = sorted(ok, key=lambda k: -R["tfs"][tf]["cells"][f"{k}|{d}"].get(key, -np.inf))
            for j, k in enumerate(order):
                ranks[k].append(j + 1)
    mean_rank = {k: float(np.mean(v)) for k, v in ranks.items()}
    return {"qualifying": ok, "mean_rank": mean_rank, "chosen": min(mean_rank, key=mean_rank.get) if mean_rank else None}


def _commit_ledger(tid):
    subprocess.run(["git", "add", str(LG.LEDGER)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"KC ledger: record trial {tid} (before its computation)\n\n"
                    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                    "Claude-Session: https://claude.ai/code/session_01PE4opNBuW3L5a8HGngHZ25"], cwd=ROOT, check=True)
    LG.verify_against_git(LG.LEDGER)


def run():
    mode = GT.require_kc_ready()
    m = json.loads((ROOT / GT.MANIFEST).read_text())
    if any(MF.verify(m).values()):
        raise SystemExit("cache differs from the manifest")
    data_files = sorted({str(Path(p)) for s in DG.EVAL_SYMBOLS for p in MF.files_for(s, "1H", m) + MF.files_for(s, "1D", m)})
    LG.verify_against_git(LG.LEDGER)
    LG.record("kc-all", "KC-1", ["exploration"], {"config": CONFIG, "mode": mode}, CODE_FILES,
              ["rate", "episodes", "win_rate", "mfe", "mae", "net_return"], True, CONFIG, data_files, notes=f"exploration; review mode {mode}")
    _commit_ledger("kc-all")
    R = {"tfs": {}}
    for tf in TFS:
        with ProcessPoolExecutor(4) as ex:
            rows = [r for r in ex.map(one, [(s, tf) for s in DG.EVAL_SYMBOLS]) if r is not None]
        R["tfs"][tf] = summarise(rows, tf)
        print(f"[{tf}] done", flush=True)
    R["decision"] = decide(R)
    R["meta"] = {"mode": mode, "config": CONFIG, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(R, indent=1, default=str))


def render():
    R = json.loads(OUT.read_text())
    L = ["# KC: cumulative signal clusters vs current Kenny signals (EXPLORATORY)", "",
         "Config `reports/KC_CONFIG.md`. All instruments in the EVAL universe, full history; the shipped CY-2 spec was fitted on these data "
         "for every setting (like-for-like, in-sample levels). Win = +D/2 ATR before −D/4 ATR within L/2; net = next open to close at L/2 after costs.", ""]
    for tf, T in R["tfs"].items():
        L += [f"## {tf} ({T['instruments']} instruments, {T['asset_years']:.0f} asset-years)", "",
              "| side · setting | signals/asset-yr | episodes/asset-yr | n | win | MFE/MAE (ATR) | net mean | net median | per-instrument median | early/late win | early/late net median |",
              "|---|---:|---:|---:|---:|---|---:|---:|---:|---|---|"]
        for d in ("bot", "top"):
            for k in ["S0", *SETTINGS]:
                v = T["cells"][f"{k}|{d}"]
                if not v.get("n"):
                    L.append(f"| {'BUY' if d == 'bot' else 'SELL'} · {k} | 0 | 0 | 0 | | | | | | | |")
                    continue
                hv = v["halves"]
                L.append(f"| {'BUY' if d == 'bot' else 'SELL'} · {k} | {v['rate']:.2f} | {v['episode_rate']:.2f} | {v['n']} | {v['win']:.3f} | "
                         f"{v['mfe_med']:.2f}/{v['mae_med']:.2f} | {v['net_mean'] * 100:+.2f}% | {v['net_median'] * 100:+.2f}% | {v['pair_median'] * 100:+.2f}% | "
                         + "/".join(f"{hv[h]['win']:.3f}" if h in hv else "–" for h in ("early", "late")) + " | "
                         + "/".join(f"{hv[h]['net_median'] * 100:+.2f}%" if h in hv else "–" for h in ("early", "late")) + " |")
        L.append("")
    D = R["decision"]
    L += ["## Decision (KC_CONFIG.md)", "", f"* Candidates meeting the usability constraints: {', '.join(D['qualifying']) or 'none'}.",
          "* Mean rank (win, median net, per-instrument median; lower is better): " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(D["mean_rank"].items(), key=lambda kv: kv[1])) + ".",
          f"* **Chosen: {D['chosen']}.**"]
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run()
    elif len(sys.argv) > 1 and sys.argv[1] == "render":
        render()
    else:
        print(__doc__)
