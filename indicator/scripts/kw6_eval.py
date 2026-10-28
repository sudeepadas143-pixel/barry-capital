"""KW-6 (reports/KW6_SPEC.md, FROZEN): Weekly Cycle Engine vs baselines, both sides, with ablations.
EXPLORATORY; no tuning; 2018+ previously studied.

    python scripts/kw6_eval.py eval | render
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

from hcmtf.universe import COST_BPS  # noqa: E402
from research import kenny_sim as KSIM, kenny_weekly_sell as WS, v5_data as DG, v5_gate as GT, v5_ledger as LG  # noqa: E402
from research import weekly_cycle as WC  # noqa: E402

_s = importlib.util.spec_from_file_location("kw3_eval", ROOT / "scripts" / "kw3_eval.py")
KE = importlib.util.module_from_spec(_s)
sys.modules["kw3_eval"] = KE
_s.loader.exec_module(KE)
C = KE.C

OUT, MD = ROOT / "reports" / "kw6_results.json", ROOT / "reports" / "KW6_RESULTS.md"
SPLIT, START = KE.SPLIT, KE.START
ALL = ("stretch", "decel", "trigger")
ABL = {"no_location": dict(use=("decel", "trigger")), "no_momentum": dict(use=("stretch", "trigger")),
       "no_trigger": dict(use=("stretch", "decel")), "no_exhaustion_link": dict(need_exhaustion=False),
       "no_structure": dict(need_structure=False)}


def _mirror(h, l, c):
    return -l, -h, -c


def one(sym):
    r = C.build((sym, "1W"))
    if r is None:
        return None
    df = DG.load(sym, "1W")
    assert df.index.equals(r["idx"])
    spec = json.loads(KE.SPEC.read_text())
    b0, s0, _ = KSIM.shipped_signals(df, "1W", spec)
    f = WC.features(df)
    wsf = WS.features(df)
    o, h, l, c = r["ohlc"]
    idx = r["idx"]
    grp = KE.CLASS_OF.get(r["cls"], "other")
    sets = {"top": {"W0": np.asarray(s0, int), "A": WS.cand_A(wsf, 6.0), "RSI": WC.rsi_recross(f, "top"),
                    "SMA40": WC.ma_cross(f, "top"), "REGIME": WC.regime_transition(f, "top")},
            "bot": {"W0": np.asarray(b0, int), "RSI": WC.rsi_recross(f, "bot"), "SMA40": WC.ma_cross(f, "bot"),
                    "REGIME": WC.regime_transition(f, "bot")}}
    for d in ("top", "bot"):
        full = WC.signals(f, d)
        sets[d]["WCE_warn"], sets[d]["WCE_conf"] = full["warn"], full["conf"]
        for name, kw in ABL.items():
            a = WC.signals(f, d, **kw)
            sets[d][f"WCE_warn|{name}"], sets[d][f"WCE_conf|{name}"] = a["warn"], a["conf"]
    atr = f["atr"]
    cost = COST_BPS[r["cls"]] / 1e4
    rows, turns = [], []
    for d, side in (("top", -1), ("bot", 1)):
        hh, ll, cc = (h, l, c) if d == "top" else _mirror(h, l, c)              # mirrored prices: a BUY is a SELL on -price
        prior = (WS.highest(hh, 26) - cc) / atr
        for name, sig in sets[d].items():
            for s in sig:
                if idx[s] < START or s + 1 >= len(c):
                    continue
                px = o[s + 1]
                row = {"side": d, "name": name, "sym": sym, "grp": grp, "t": idx[s], "class": WS.classify(hh, ll, cc, atr, s, prior[s])}
                for H in (4, 13, 26):
                    row[f"dec{H}"] = WS.decline_within(hh, ll, cc, atr, s, H)
                    row[f"f{H}"] = side * (c[s + H] / px - 1) if s + H < len(c) else np.nan
                end = min(len(c), s + 27)
                row["mfe"] = (h[s + 1:end].max() / px - 1) if side > 0 else (1 - l[s + 1:end].min() / px)
                row["mae"] = (1 - l[s + 1:end].min() / px) if side > 0 else (h[s + 1:end].max() / px - 1)
                row["net13"] = row["f13"] - cost if row["f13"] == row["f13"] else np.nan
                a, b = max(0, s - 26), min(len(c), s + 27)
                row["lag"] = float(s - (a + int(np.argmax(hh[a:b])))) if b - s >= 27 else np.nan
                rows.append(row)
        for e in r["labs"][d].events:
            if idx[e] < START or e + 4 >= len(c):
                continue
            turns.append({"side": d, "sym": sym, "grp": grp, "t": idx[e],
                          **{name: bool(((sig >= e - 13) & (sig <= e + 2)).any()) for name, sig in sets[d].items()}})
    yrs = {"pre": max(0.0, (min(SPLIT, idx[-1]) - max(idx[0], START)).total_seconds() / 3.15576e7),
           "post": max(0.0, (idx[-1] - max(SPLIT, idx[0])).total_seconds() / 3.15576e7)}
    return {"sym": sym, "grp": grp, "rows": rows, "turns": turns, "yrs": yrs}


def summ(T, turns, res, side, name, period, grp=None):
    T = T[(T["side"] == side) & (T["name"] == name) & ((T["t"] < SPLIT) if period == "pre" else (T["t"] >= SPLIT))]
    tu = turns[(turns["side"] == side) & ((turns["t"] < SPLIT) if period == "pre" else (turns["t"] >= SPLIT))]
    yrs = sum(x["yrs"][period] for x in res if grp is None or x["grp"] == grp)
    if grp:
        T, tu = T[T["grp"] == grp], tu[tu["grp"] == grp]
    out = {"n": int(len(T)), "rate": len(T) / yrs if yrs else 0.0, "top_catch": float(tu[name].mean()) if len(tu) and name in tu else np.nan, "n_turns": int(len(tu))}
    if len(T):
        cls = T["class"].value_counts(normalize=True)
        out.update({k: float(cls.get(k, 0)) for k in ("useful", "premature", "late", "false_reversal", "flat")})
        out.update({**{f"dec{h}": float(np.nanmean(T[f"dec{h}"])) for h in (4, 13, 26)}, **{f"f{h}_med": float(np.nanmedian(T[f"f{h}"])) for h in (4, 13, 26)},
                    "mfe_med": float(np.nanmedian(T["mfe"])), "mae_med": float(np.nanmedian(T["mae"])), "lag_med": float(np.nanmedian(T["lag"])),
                    "net13_mean": float(np.nanmean(T["net13"])), "net13_median": float(np.nanmedian(T["net13"]))})
    return out


def rule(x, b):
    """KW-3 adoption rule (mirrored for BUY by construction of the metrics)."""
    why = []
    for p in ("pre", "post"):
        xa, ba = x[p]["all"], b[p]["all"]
        if not xa["n"]:
            why.append(f"{p}: no signals")
            continue
        if xa["useful"] < ba["useful"] + 0.05:
            why.append(f"{p}: useful {xa['useful']:.2f} < W0 {ba['useful']:.2f} + 0.05")
        if xa["f26_med"] < ba["f26_med"] + 0.01:
            why.append(f"{p}: 26w median {xa['f26_med']:+.3f} < W0 {ba['f26_med']:+.3f} + 0.01")
    xp, bp = x["post"]["all"], b["post"]["all"]
    if xp["n"]:
        if xp["top_catch"] < bp["top_catch"] - 0.05:
            why.append(f"post: turn capture {xp['top_catch']:.2f} < W0 {bp['top_catch']:.2f} - 0.05")
        if xp["rate"] > 2 * bp["rate"]:
            why.append(f"post: rate {xp['rate']:.2f} > 2x W0 {bp['rate']:.2f}")
        if xp["lag_med"] > bp["lag_med"] + 2:
            why.append(f"post: lag {xp['lag_med']:+.0f} > W0 {bp['lag_med']:+.0f} + 2")
        for g in ("equities", "crypto"):
            xg, bg = x["post"][g], b["post"][g]
            if xg["n"] >= 20 and bg["n"] >= 20 and xg["useful"] <= bg["useful"]:
                why.append(f"post {g}: useful {xg['useful']:.2f} <= W0 {bg['useful']:.2f}")
    return {"pass": not why, "why": why}


def breadth(T, side, name, ref, period):
    T = T[(T["side"] == side) & ((T["t"] < SPLIT) if period == "pre" else (T["t"] >= SPLIT))]
    a = T[T["name"] == name].groupby("sym")["class"].agg(lambda x: ((x == "useful").mean(), len(x)))
    b = T[T["name"] == ref].groupby("sym")["class"].agg(lambda x: ((x == "useful").mean(), len(x)))
    common = [s for s in a.index if s in b.index and a[s][1] >= 3 and b[s][1] >= 3]
    return {"n_inst": len(common), "share_better": float(np.mean([a[s][0] > b[s][0] for s in common])) if common else None}


def evaluate():
    mode = GT.require_kw6_ready()
    LG.record("kw6-eval", "KW-6", ["exploration"], {"config": GT.KW6_CONFIG, "mode": mode}, list(GT.KW6_CODE),
              ["useful_rate", "premature", "late", "turn_capture", "lag", "forward_return", "mfe", "mae", "rate", "net_return", "ablation"], True,
              GT.KW6_CONFIG, KE._data_files(), notes=f"exploration; review mode {mode}")
    KE._commit_ledger("kw6-eval")
    with ProcessPoolExecutor(4) as ex:
        res = [x for x in ex.map(one, DG.EVAL_SYMBOLS) if x]
    T = pd.DataFrame([row for x in res for row in x["rows"]])
    turns = pd.DataFrame([t for x in res for t in x["turns"]])
    names = {d: sorted(T[T["side"] == d]["name"].unique()) for d in ("top", "bot")}
    out = {"results": {}, "rule": {}, "ablation": {}, "breadth": {}}
    for d in ("top", "bot"):
        for nm in names[d]:
            out["results"][f"{d}|{nm}"] = {p: {"all": summ(T, turns, res, d, nm, p), **{g: summ(T, turns, res, d, nm, p, g) for g in ("equities", "crypto", "other")}}
                                           for p in ("pre", "post")}
        base = out["results"][f"{d}|W0"]
        for nm in ("WCE_warn", "WCE_conf"):
            out["rule"][f"{d}|{nm}"] = rule(out["results"][f"{d}|{nm}"], base)
            out["breadth"][f"{d}|{nm}"] = {p: breadth(T, d, nm, "W0", p) for p in ("pre", "post")}
            full = out["results"][f"{d}|{nm}"]
            for ab in ABL:
                x = out["results"].get(f"{d}|{nm}|{ab}")
                if not x:
                    continue
                dl = {p: {"useful": full[p]["all"].get("useful", np.nan) - x[p]["all"].get("useful", np.nan),
                          "f26": full[p]["all"].get("f26_med", np.nan) - x[p]["all"].get("f26_med", np.nan),
                          "n_full": full[p]["all"]["n"], "n_ablated": x[p]["all"]["n"]} for p in ("pre", "post")}
                adds = all(v["useful"] >= 0.03 or v["f26"] >= 0.01 for v in dl.values())
                out["ablation"][f"{d}|{nm}|{ab}"] = {"delta": dl, "adds_value": bool(adds)}
    out["merits_further_testing"] = any(v["pass"] for v in out["rule"].values())
    out["meta"] = {"mode": mode, "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print("done", flush=True)


def render():
    out = json.loads(OUT.read_text())
    pc = lambda x: "–" if x is None or x != x else f"{x * 100:+.1f}%"  # noqa: E731
    L = ["# KW-6: Weekly Cycle Engine vs baselines (EXPLORATORY)", "",
         "Spec `reports/KW6_SPEC.md` (no tuning). Weekly EVAL instruments from 2008; <2018 development, 2018+ previously studied. "
         "Classes/declines per KW-3 (MOVE = 3 ATR); BUY metrics mirror SELL. Forward returns in the signal direction.", ""]
    order = {"top": ["W0", "A", "RSI", "SMA40", "REGIME", "WCE_warn", "WCE_conf"], "bot": ["W0", "RSI", "SMA40", "REGIME", "WCE_warn", "WCE_conf"]}
    for d in ("top", "bot"):
        L += [f"## {'SELL (tops)' if d == 'top' else 'BUY (bottoms)'}", "",
              "| signal · period · group | n | /inst-yr | useful | premature | late | false rev. | move 4/13/26w | fwd 4/13/26w (median) | MFE/MAE 26w | turns caught | lag (w) | net 13w (mean / median) |",
              "|---|---:|---:|---:|---:|---:|---:|---|---|---|---:|---:|---|"]
        for nm in order[d]:
            x = out["results"].get(f"{d}|{nm}")
            if not x:
                continue
            for p in ("pre", "post"):
                for g in ("all", "equities", "crypto"):
                    v = x[p][g]
                    if not v["n"]:
                        continue
                    L.append(f"| {nm} · {'<2018' if p == 'pre' else '2018+'} · {g} | {v['n']} | {v['rate']:.2f} | {v['useful']:.2f} | {v['premature']:.2f} | {v['late']:.2f} | "
                             f"{v['false_reversal']:.2f} | {v['dec4']:.2f}/{v['dec13']:.2f}/{v['dec26']:.2f} | {pc(v['f4_med'])}/{pc(v['f13_med'])}/{pc(v['f26_med'])} | "
                             f"{v['mfe_med'] * 100:.1f}/{v['mae_med'] * 100:.1f}% | {v['top_catch']:.2f} of {v['n_turns']} | {v['lag_med']:+.0f} | {pc(v['net13_mean'])} / {pc(v['net13_median'])} |")
        L.append("")
    L += ["## Decision rule (KW-3 rule; mirrored for BUY)", ""]
    for k, v in out["rule"].items():
        L.append(f"* {k}: {'PASS' if v['pass'] else 'fail'}" + ("" if v["pass"] else " — " + "; ".join(v["why"])))
    L += ["", "Breadth (share of instruments with >= 3 signals each where WCE's useful rate beats W0):", ""]
    for k, v in out["breadth"].items():
        L.append(f"* {k}: <2018 {v['pre']['share_better']} ({v['pre']['n_inst']} inst), 2018+ {v['post']['share_better']} ({v['post']['n_inst']} inst)")
    L += ["", "## Ablation (full minus ablated; a group adds value if useful drops >= 0.03 or 26w median >= 1 pp in both periods)", "",
          "| signal · removed group | <2018 Δuseful / Δ26w (n full→ablated) | 2018+ Δuseful / Δ26w (n) | adds value |", "|---|---|---|---|"]
    for k, v in out["ablation"].items():
        dpre, dpost = v["delta"]["pre"], v["delta"]["post"]
        L.append(f"| {k} | {dpre['useful']:+.2f} / {dpre['f26'] * 100:+.1f} pp ({dpre['n_full']}→{dpre['n_ablated']}) | "
                 f"{dpost['useful']:+.2f} / {dpost['f26'] * 100:+.1f} pp ({dpost['n_full']}→{dpost['n_ablated']}) | {'yes' if v['adds_value'] else 'no'} |")
    L.append(f"\n**Merits further testing: {'yes' if out['merits_further_testing'] else 'no'}.**")
    MD.write_text("\n".join(L) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    {"eval": evaluate, "render": render}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
