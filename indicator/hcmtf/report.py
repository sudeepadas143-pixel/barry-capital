"""Run the full study and write reports/RESULTS.md and reports/results.json.

    python -m hcmtf.report            # all four timeframes
    python -m hcmtf.report 1D 1W      # a subset
    python -m hcmtf.report --render   # rebuild the markdown from reports/results.json

The verdict rules are fixed here, in code, and were written before the first full run:

DEMONSTRATED  walk-forward OOS mean r_h has a 95% month-cluster CI above zero, AND beats
              same-count random entries with Holm-adjusted p < 0.05 (adjusted across every
              timeframe x tier tested), AND beats the unfiltered structure-break baseline,
              AND the untouched holdout mean r_h is above zero.
PROMISING     OOS mean r_h > 0, beats random at unadjusted p < 0.10 and beats the
              unfiltered baseline, but misses one of the stricter tests.
UNPROVEN      anything else, including too few events to tell (n < 30).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import evaluate as E, metrics as M, signals as S, walkforward as W

OUT = Path(__file__).resolve().parent.parent / "reports"
TFS = ["1H", "4H", "1D", "1W"]


def _fmt(x, nd=2, pct=False):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "–"
    if pct:
        return f"{100 * x:.{nd - 1 if nd > 1 else 0}f}%"
    return f"{x:+.{nd}f}" if isinstance(x, float) else str(x)


def analyse(res: W.Result) -> dict:
    tf = res.tf
    by_sym = {s.symbol: s for s in res.series}
    sy_oos = M.symbol_years(res.series, res.windows_oos)
    sy_hold = M.symbol_years(res.series, [res.window_hold])
    sig = res.oos["signals"]
    sets = {
        "all signals": sig,
        "major": sig[sig["tier"] == "major"],
        "confirmed (not major)": sig[sig["tier"] == "confirmed"],
        "major reversal": sig[(sig["tier"] == "major") & (sig["kind"] == "reversal")],
        "major continuation": sig[(sig["tier"] == "major") & (sig["kind"] == "continuation")],
        "confirmed reversal": sig[(sig["tier"] == "confirmed") & (sig["kind"] == "reversal")],
        "confirmed continuation": sig[(sig["tier"] == "confirmed") & (sig["kind"] == "continuation")],
        "early warnings": res.oos["warnings"],
        "baseline: every structure break": res.oos["raw_breaks"],
        "baseline: EMA 20/50 cross": res.oos["ema_cross"],
        "baseline: Supertrend(10,3) flip": res.oos["supertrend"],
    }
    oos = {}
    for name, ev in sets.items():
        row = M.summary(ev, sy_oos)
        if row["n"]:
            row.update(M.random_baseline(ev, by_sym, res.windows_oos))
        oos[name] = row

    hsig = res.hold["signals"]
    hsets = {
        "all signals": hsig,
        "major": hsig[hsig["tier"] == "major"],
        "confirmed (not major)": hsig[hsig["tier"] == "confirmed"],
        "early warnings": res.hold["warnings"],
        "baseline: every structure break": res.hold["raw_breaks"],
        "baseline: EMA 20/50 cross": res.hold["ema_cross"],
        "baseline: Supertrend(10,3) flip": res.hold["supertrend"],
    }
    hold = {}
    for name, ev in hsets.items():
        row = M.summary(ev, sy_hold)
        if row["n"]:
            row.update(M.random_baseline(ev, by_sym, [res.window_hold]))
        hold[name] = row

    # trade simulation
    mh = W.MAX_HOLD[tf]
    def per_sym(ev):
        return {k: g for k, g in ev.groupby("symbol")}
    sim_oos = {
        "major": M.portfolio(res.series, per_sym(sig[sig["tier"] == "major"]), res.windows_oos, mh),
        "all signals": M.portfolio(res.series, per_sym(sig), res.windows_oos, mh),
        "baseline: every structure break": M.portfolio(res.series, per_sym(res.oos["raw_breaks"]), res.windows_oos, mh),
        "baseline: EMA 20/50 cross": M.portfolio(res.series, per_sym(res.oos["ema_cross"]), res.windows_oos, mh),
        "baseline: Supertrend(10,3) flip": M.portfolio(res.series, per_sym(res.oos["supertrend"]), res.windows_oos, mh),
        "buy & hold": M.buy_hold(res.series, res.windows_oos),
    }
    sim_hold = {
        "major": M.portfolio(res.series, per_sym(hsig[hsig["tier"] == "major"]), [res.window_hold], mh),
        "all signals": M.portfolio(res.series, per_sym(hsig), [res.window_hold], mh),
        "baseline: every structure break": M.portfolio(res.series, per_sym(res.hold["raw_breaks"]), [res.window_hold], mh),
        "buy & hold": M.buy_hold(res.series, [res.window_hold]),
    }

    # timeliness against ex-post turns (k = 4 ATR legs), OOS windows
    tl = {}
    for name, ev in [("major", sig[sig["tier"] == "major"]), ("all signals", sig),
                     ("early warnings", res.oos["warnings"]),
                     ("baseline: EMA 20/50 cross", res.oos["ema_cross"]),
                     ("baseline: Supertrend(10,3) flip", res.oos["supertrend"])]:
        rows = []
        for s in res.series:
            e = ev[ev["symbol"] == s.symbol]
            t = E.timeliness(e, s.f, k=4.0)
            if len(t) == 0:
                continue
            tt = s.index[t["turn_i"].to_numpy(int)]
            m = np.zeros(len(t), bool)
            for a, b in res.windows_oos:
                m |= (tt >= a) & (tt < b)
            rows.append(t[m])
        t = pd.concat(rows) if rows else pd.DataFrame()
        if len(t):
            d = t[t["detected"]]
            tl[name] = {"turns": len(t), "detected": float(t["detected"].mean()),
                        "lag_median": float(d["lag_bars"].median()) if len(d) else np.nan,
                        "captured_median": float(d["captured"].median()) if len(d) else np.nan}

    cls = {}
    for name, ev in [("all signals", sig), ("major", sig[sig["tier"] == "major"])]:
        for c, g in ev.groupby("cls"):
            m, lo, hi = M.cluster_ci(g, "r_h")
            cls.setdefault(name, {})[c] = {"n": len(g), "mean_r": m, "lo": lo, "hi": hi,
                                           "precision": float((g["barrier"] == 1).mean())}

    return {
        "tf": tf,
        "symbols": [s.symbol for s in res.series],
        "folds": [{"start": str(a.date()), "end": str(b.date()), "confirm": c, "major": m,
                   "selection": {k: list(v) for k, v in log.items()}} for a, b, c, m, log in res.folds],
        "holdout": {"start": str(res.holdout[0].date()), "confirm": res.holdout[1], "major": res.holdout[2],
                    "selection": {k: list(v) for k, v in res.holdout[3].items()}},
        "oos": oos, "hold": hold, "sim_oos": sim_oos, "sim_hold": sim_hold,
        "timeliness": tl, "by_class": cls,
        "score_curve": M.score_curve(res.trig_oos).to_dict("records"),
        "component_lift": M.component_lift(res.trig_oos, S.COMPONENTS).to_dict("records"),
        "symbol_years_oos": sy_oos, "symbol_years_hold": sy_hold,
        "spans": {s.symbol: [str(s.index[0].date()), str(s.index[-1].date())] for s in res.series},
    }


def _nan(d: dict) -> dict:
    return {k: (np.nan if v is None else v) for k, v in (d or {}).items()}


def verdicts(all_res: dict) -> dict:
    tests = {}
    for tf, r in all_res.items():
        for tier in ("major", "all signals"):
            o = r["oos"].get(tier, {})
            if o.get("n", 0) >= 30:
                tests[f"{tf} {tier}"] = o["p_value"]
    adj = M.holm(tests)
    out = {}
    for tf, r in all_res.items():
        for tier in ("major", "all signals"):
            key = f"{tf} {tier}"
            o, h = _nan(r["oos"].get(tier)), _nan(r["hold"].get(tier))
            base = _nan(r["oos"].get("baseline: every structure break"))
            if o.get("n", 0) < 30:
                out[key] = ("UNPROVEN", "too few out-of-sample events")
                continue
            beats_base = o["mean_r"] > base.get("mean_r", np.inf)
            strict = (o["mean_r_lo"] > 0 and adj.get(key, 1) < 0.05 and beats_base
                      and h.get("n", 0) > 0 and h.get("mean_r", -1) > 0)
            loose = o["mean_r"] > 0 and o["p_value"] < 0.10 and beats_base
            why = (f"OOS mean r {o['mean_r']:+.3f} [{o['mean_r_lo']:+.3f}, {o['mean_r_hi']:+.3f}], "
                   f"p vs random {o['p_value']:.3f} (Holm {adj.get(key, 1):.3f}), "
                   f"unfiltered breaks {base.get('mean_r', np.nan):+.3f}, "
                   f"holdout {h.get('mean_r', np.nan):+.3f} vs random {h.get('rand_mean_r', np.nan):+.3f}, "
                   f"p {h.get('p_value', np.nan):.3f} (n={h.get('n', 0)})")
            out[key] = ("DEMONSTRATED" if strict else "PROMISING" if loose else "UNPROVEN", why)
    return out


# ------------------------------------------------------------------------- markdown


def _table(rows: dict, cols: list[tuple[str, str, str]]) -> str:
    head = "| set | " + " | ".join(c[1] for c in cols) + " |"
    sep = "|---|" + "|".join("---:" for _ in cols) + "|"
    lines = [head, sep]
    for name, r in rows.items():
        r = _nan(r)
        cells = []
        for key, _, kind in cols:
            v = r.get(key, np.nan) if r else np.nan
            if kind == "int":
                cells.append(str(int(v)) if v == v else "–")
            elif kind == "pct":
                cells.append(_fmt(v, 2, pct=True))
            elif kind == "ci":
                lo, hi = r.get(key + "_lo"), r.get(key + "_hi")
                cells.append(f"{_fmt(r.get(key), 3)} [{_fmt(lo, 2)}, {_fmt(hi, 2)}]" if r.get("n") else "–")
            elif kind == "p":
                cells.append(f"{v:.3f}" if v == v else "–")
            else:
                cells.append(_fmt(v, 2) if isinstance(v, float) else str(v))
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


EV_COLS = [("n", "n", "int"), ("per_sym_yr", "per sym-yr", "f"), ("precision", "precision", "pct"),
           ("false_pos", "false pos.", "pct"), ("mean_r", "mean r_h (ATR) [95% CI]", "ci"),
           ("mean_ret_pct", "mean ret_h %", "f"), ("mfe_med", "MFE med", "f"), ("mae_med", "MAE med", "f"),
           ("rand_mean_r", "random r_h", "f"), ("rand_precision", "random prec.", "pct"),
           ("p_value", "p vs random", "p")]
SIM_COLS = [("trades", "trades", "int"), ("win", "win", "pct"), ("avg_trade_pct", "avg trade %", "f"),
            ("profit_factor", "PF", "f"), ("cagr", "CAGR", "pct"), ("vol", "vol", "pct"),
            ("sharpe", "Sharpe [95% CI]", "ci"), ("max_dd", "max DD", "pct")]


def markdown(all_res: dict, verdict: dict) -> str:
    L = ["# Validation results", "",
         "Generated by `python -m hcmtf.report`. Every number below is out of sample unless the",
         "heading says otherwise. Units: r_h is the direction-adjusted move from the next bar's open",
         f"to the close H bars later, in ATR(14) units, after costs (H: " + ", ".join(f"{k} {v}" for k, v in E.HORIZON.items()) + " bars). Precision is the",
         f"share of signals that reached +{E.TARGET_ATR:g} ATR before -{E.STOP_ATR:g} ATR within H bars;",
         "false positives are the share that hit -1 ATR first. MFE/MAE are medians in ATR units.",
         "\"Random\" is the mean over 500 draws of entries at random bars of the same symbols and",
         "windows, with the same count and long/short mix. CIs are 95% month-cluster bootstraps.", "",
         "## Verdicts", "", "| timeframe / set | verdict | evidence |", "|---|---|---|"]
    for k, (v, why) in verdict.items():
        L.append(f"| {k} | **{v}** | {why} |")
    L.append("")
    for tf in [t for t in TFS if t in all_res]:
        r = all_res[tf]
        L += [f"## {tf}", "",
              f"Symbols: {len(r['symbols'])}. Out-of-sample symbol-years: {r['symbol_years_oos']:.0f}; "
              f"holdout symbol-years: {r['symbol_years_hold']:.0f} (from {r['holdout']['start']}).", "",
              "Thresholds picked on data before each test window (score fraction needed):", "",
              "| test window | confirm ≥ | major ≥ |", "|---|---:|---:|"]
        for fo in r["folds"]:
            L.append(f"| {fo['start']} → {fo['end']} | {fo['confirm']} | {fo['major']} |")
        L.append(f"| holdout {r['holdout']['start']} → end (shipped in Pine) | {r['holdout']['confirm']} | {r['holdout']['major']} |")
        L += ["", "### Walk-forward out-of-sample events", "", _table(r["oos"], EV_COLS), "",
              "### Holdout (evaluated once)", "", _table(r["hold"], EV_COLS), "",
              "### Does a higher score mean a better outcome? (all OOS structure breaks)", "",
              "| score | n | mean r_h [95% CI] | precision |", "|---|---:|---:|---:|"]
        for row in r["score_curve"]:
            L.append(f"| {row['score']} | {row['n']} | {row['mean_r']:+.3f} [{row['lo']:+.2f}, {row['hi']:+.2f}] | {100 * row['precision']:.1f}% |")
        L += ["", "### Each condition on its own (all OOS structure breaks, with vs without)", "",
              "| condition | n with | mean r_h with [CI] | n without | mean r_h without | difference |",
              "|---|---:|---:|---:|---:|---:|"]
        for row in r["component_lift"]:
            L.append(f"| {row['condition']} | {row['n_with']} | {row['mean_r_with']:+.3f} {row['ci_with']} | "
                     f"{row['n_without']} | {row['mean_r_without']:+.3f} | {row['diff']:+.3f} |")
        L += ["", "### Trade simulation, walk-forward OOS (equal-weight across symbols, net of costs)", "",
              _table(r["sim_oos"], SIM_COLS), "", "### Trade simulation, holdout", "",
              _table(r["sim_hold"], SIM_COLS), "",
              "### Timeliness against ex-post 4-ATR swings (OOS)", "",
              "| set | turns | detected | median lag (bars) | median share of leg left |",
              "|---|---:|---:|---:|---:|"]
        for k, v in r["timeliness"].items():
            L.append(f"| {k} | {v['turns']} | {100 * v['detected']:.0f}% | {v['lag_median']:.0f} | {100 * v['captured_median']:.0f}% |")
        L += ["", "### By asset class (OOS)", "", "| set | class | n | mean r_h [95% CI] | precision |",
              "|---|---|---:|---:|---:|"]
        for name, d in r["by_class"].items():
            for c, v in d.items():
                L.append(f"| {name} | {c} | {v['n']} | {v['mean_r']:+.3f} [{v['lo']:+.2f}, {v['hi']:+.2f}] | {100 * v['precision']:.1f}% |")
        L.append("")
    return "\n".join(L)


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if (np.isnan(o) or np.isinf(o)) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


def main(tfs: list[str], render_only: bool = False) -> None:
    OUT.mkdir(exist_ok=True)
    path = OUT / "results.json"
    all_res = json.loads(path.read_text()) if path.exists() else {}
    for tf in ([] if render_only else tfs):
        print(f"[{tf}] preparing", flush=True)
        res = W.run(tf)
        print(f"[{tf}] analysing", flush=True)
        all_res[tf] = _clean(analyse(res))
        path.write_text(json.dumps(all_res, indent=1))
    all_res = {k: all_res[k] for k in TFS if k in all_res}
    v = verdicts(all_res)
    (OUT / "RESULTS.md").write_text(markdown(all_res, v))
    (OUT / "verdicts.json").write_text(json.dumps(v, indent=1))
    print("\n".join(f"{k}: {a} — {b}" for k, (a, b) in v.items()))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args or TFS, render_only="--render" in sys.argv)
