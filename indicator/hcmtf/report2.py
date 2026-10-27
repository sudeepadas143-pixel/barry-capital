"""v2 validation. Writes reports/RESULTS.md, results.json, verdicts.json.

    python -m hcmtf.report2            # all timeframes
    python -m hcmtf.report2 --render   # markdown from results.json only

Evidence tiers, in order of how much they can be trusted:

1. FRESH symbols (never used for any v2 decision), from the first walk-forward window
   to the end of the data. PRIMARY.
2. DEV symbols, 2010 (daily/weekly) or 2020 (intraday) to the holdout: the screening and
   the design check used these periods, so this is in-sample for the design. SECONDARY.
3. DEV symbols, holdout window: was looked at once in v1. Reported, flagged.

VERDICT RULE (fixed before the first v2 run). Per timeframe, separately for crypto and
for non-crypto FRESH symbols, MAJOR signals are:

  DEMONSTRATED  mean r_h 95% month-cluster CI above 0, AND beat random entries (same
                symbols, windows, count and long/short mix) at Holm-adjusted p < 0.05
                (Holm over the 8 timeframe x market tests), AND beat every structure break
                taken unfiltered, AND the dev-window record also beat random (p < 0.10).
  PROMISING     mean r_h > 0, beat random at unadjusted p < 0.10, beat unfiltered breaks.
  UNPROVEN      otherwise, including n < 30.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import engine as G, evaluate as E, metrics as M, study as St
from .universe import FRESH, UNIVERSE

OUT = Path(__file__).resolve().parent.parent / "reports"
TFS = ["1H", "4H", "1D", "1W"]
ACTIVE_PATH = OUT / "active_config.json"


def active_params(tf: str) -> G.Params:
    """Engine configuration for a timeframe after screening (reports/active_config.json)."""
    cfg = json.loads(ACTIVE_PATH.read_text())
    return G.with_(G.DEFAULTS[tf], evidence=tuple(cfg["evidence"]), filters=tuple(cfg["filters"]),
                   crypto_only=tuple(cfg["crypto_only"]), counter_major=cfg["counter_major"])


def _sets(sig: pd.DataFrame) -> dict:
    trade = sig[sig["tier"].isin(["major", "confirmed"])]
    return {
        "MAJOR (realignment)": sig[sig["tier"] == "major"],
        "CONFIRMED (continuation)": sig[sig["tier"] == "confirmed"],
        "all signals": trade,
        "WATCH (counter-HTF reversal)": sig[sig["tier"] == "watch"],
    }


def _collect(series, params_by_window: list, windows: list) -> dict:
    """Signals/warnings/baselines inside windows, each window with its own params."""
    store: dict[str, list] = {}
    sig_sym: dict[str, list] = {}
    for s in series:
        for (a, b), p in zip(windows, params_by_window):
            sig = St.in_window(s, St.signals_for(s, p), a, b)
            sig_sym.setdefault(s.symbol, []).append(sig)
            store.setdefault("signals", []).append(St.tag(s, sig))
            store.setdefault("warnings", []).append(St.tag(s, St.in_window(s, s.warn, a, b)))
            for k, ev in s.base.items():
                store.setdefault(k, []).append(St.tag(s, St.in_window(s, ev, a, b)))
    out = {k: pd.concat(v, ignore_index=True) for k, v in store.items()}
    out["_by_symbol"] = {k: pd.concat(v) for k, v in sig_sym.items()}
    return out


def _evaluate(series, coll: dict, windows: list, tf: str, sims: bool = True) -> dict:
    by_sym = {s.symbol: s for s in series}
    sy = M.symbol_years(series, windows)
    sets = _sets(coll["signals"])
    sets["early warnings"] = coll["warnings"]
    sets["baseline: every structure break"] = coll["raw_breaks"]
    sets["baseline: EMA 20/50 cross"] = coll["ema_cross"]
    sets["baseline: Supertrend(10,3) flip"] = coll["supertrend"]
    ev = {}
    for name, e in sets.items():
        row = M.summary(e, sy)
        if row["n"]:
            row.update(M.random_baseline(e, by_sym, windows, reps=300))
        ev[name] = row
    res = {"events": ev, "symbol_years": sy, "n_symbols": len(series)}
    if sims:
        mh = St.MAX_HOLD[tf]
        per = lambda e: {k: g for k, g in e.groupby("symbol")}
        sig = coll["signals"][coll["signals"]["tier"].isin(["major", "confirmed"])]
        res["sim"] = {
            "MAJOR": M.portfolio(series, per(sig[sig["tier"] == "major"]), windows, mh),
            "all signals": M.portfolio(series, per(sig), windows, mh),
            "baseline: every structure break": M.portfolio(series, per(coll["raw_breaks"]), windows, mh),
            "baseline: Supertrend(10,3) flip": M.portfolio(series, per(coll["supertrend"]), windows, mh),
            "buy & hold": M.buy_hold(series, windows),
        }
        tl = {}
        for name, e in [("MAJOR", sig[sig["tier"] == "major"]), ("all signals", sig),
                        ("early warnings", coll["warnings"]), ("baseline: Supertrend(10,3) flip", coll["supertrend"])]:
            rows = []
            for s in series:
                t = E.timeliness(e[e["symbol"] == s.symbol], s.f, k=4.0)
                if len(t):
                    tt = s.index[t["turn_i"].to_numpy(int)]
                    m = np.zeros(len(t), bool)
                    for a, b in windows:
                        m |= (tt >= a) & (tt < b)
                    rows.append(t[m])
            t = pd.concat(rows) if rows else pd.DataFrame()
            if len(t):
                d = t[t["detected"]]
                tl[name] = {"turns": len(t), "detected": float(t["detected"].mean()),
                            "lag_median": float(d["lag_bars"].median()) if len(d) else None,
                            "captured_median": float(d["captured"].median()) if len(d) else None}
        res["timeliness"] = tl
        # breakdowns for MAJOR and all signals
        br = {}
        for name, e in [("MAJOR", sig[sig["tier"] == "major"]), ("all signals", sig),
                        ("WATCH", coll["signals"][coll["signals"]["tier"] == "watch"])]:
            for col in ("cls_asset", "tier_cls"):
                for k, g in e.groupby(col):
                    if len(g) == 0:
                        continue
                    m, lo, hi = M.cluster_ci(g, "r_h")
                    rb = M.random_baseline(g, by_sym, windows, reps=200)
                    br.setdefault(name, {}).setdefault(col, {})[k] = {
                        "n": len(g), "mean_r": m, "lo": lo, "hi": hi,
                        "precision": float((g["barrier"] == 1).mean()),
                        "rand_mean_r": rb.get("rand_mean_r"), "p_value": rb.get("p_value")}
        res["breakdown"] = br
    return res


def run_tf(tf: str) -> dict:
    print(f"[{tf}] preparing dev", flush=True)
    dev = St.prepare(tf, UNIVERSE)
    print(f"[{tf}] preparing fresh", flush=True)
    fresh = St.prepare(tf, FRESH)
    base = active_params(tf)
    UTC = lambda x: pd.Timestamp(x, tz="UTC")
    windows = [(UTC(a), UTC(b)) for a, b in St.WINDOWS[tf]]
    hstart = UTC(St.HOLDOUT[tf])
    end = max(s.index[-1] for s in dev + fresh) + pd.Timedelta(days=1)
    final = base
    out = {"tf": tf, "evidence": list(base.evidence), "filters": list(base.filters),
           "major_classes": list(base.major_classes), "confirm_classes": list(base.confirm_classes),
           "dev_symbols": [s.symbol for s in dev], "fresh_symbols": [s.symbol for s in fresh]}

    print(f"[{tf}] evaluating", flush=True)
    fw = [(windows[0][0], end)]
    fresh_coll = _collect(fresh, [final], fw)
    out["fresh"] = _evaluate(fresh, fresh_coll, fw, tf)
    for grp, keep in (("fresh_crypto", lambda s: s.cls == "crypto"), ("fresh_other", lambda s: s.cls != "crypto")):
        ss = [s for s in fresh if keep(s)]
        out[grp] = _evaluate(ss, _collect(ss, [final], fw), fw, tf, sims=grp == "fresh_crypto") if ss else {}
    out["fresh_holdout_window"] = _evaluate(fresh, _collect(fresh, [final], [(hstart, end)]), [(hstart, end)], tf, sims=False)
    out["dev_windows"] = _evaluate(dev, _collect(dev, [final] * len(windows), windows), windows, tf, sims=True)
    out["dev_holdout_seen_in_v1"] = _evaluate(dev, _collect(dev, [final], [(hstart, end)]), [(hstart, end)], tf, sims=False)
    return out


def verdicts(R: dict) -> dict:
    tests, rows = {}, {}
    for tf, r in R.items():
        for grp in ("fresh_crypto", "fresh_other"):
            o = (r.get(grp) or {}).get("events", {}).get("MAJOR (realignment)", {})
            if o.get("n", 0) >= 30 and o.get("p_value") is not None:
                tests[f"{tf} {grp}"] = o["p_value"]
    adj = M.holm(tests)
    for tf, r in R.items():
        dev = r["dev_windows"]["events"].get("MAJOR (realignment)", {})
        for grp in ("fresh_crypto", "fresh_other"):
            g = r.get(grp) or {}
            o = g.get("events", {}).get("MAJOR (realignment)", {})
            base = g.get("events", {}).get("baseline: every structure break", {})
            key = f"{tf} {grp.replace('fresh_', '')}"
            if o.get("n", 0) < 30:
                rows[key] = ("UNPROVEN", f"only {o.get('n', 0)} MAJOR signals on fresh symbols")
                continue
            nz = lambda x, d=np.nan: d if x is None else x
            beats = nz(o["mean_r"]) > nz(base.get("mean_r"), np.inf)
            strict = (nz(o["mean_r_lo"], -1) > 0 and adj.get(f"{tf} {grp}", 1) < 0.05 and beats
                      and nz(dev.get("p_value"), 1) < 0.10)
            loose = nz(o["mean_r"], -1) > 0 and nz(o["p_value"], 1) < 0.10 and beats
            why = (f"fresh n={o['n']}: mean r {o['mean_r']:+.3f} [{nz(o['mean_r_lo']):+.2f}, {nz(o['mean_r_hi']):+.2f}] vs random "
                   f"{nz(o.get('rand_mean_r')):+.3f}, p {nz(o.get('p_value')):.3f} (Holm {adj.get(f'{tf} {grp}', 1):.3f}); "
                   f"unfiltered breaks {nz(base.get('mean_r')):+.3f}; dev windows p {nz(dev.get('p_value')):.3f}")
            rows[key] = ("DEMONSTRATED" if strict else "PROMISING" if loose else "UNPROVEN", why)
    return rows


# ------------------------------------------------------------------------ markdown

EV_COLS = [("n", "n", "int"), ("per_sym_yr", "per sym-yr", "f"), ("precision", "precision", "pct"),
           ("false_pos", "false pos.", "pct"), ("mean_r", "mean r_h [95% CI]", "ci"),
           ("mfe_med", "MFE", "f"), ("mae_med", "MAE", "f"),
           ("rand_mean_r", "random r_h", "f"), ("p_value", "p vs random", "p")]
SIM_COLS = [("trades", "trades", "int"), ("win", "win", "pct"), ("avg_trade_pct", "avg trade %", "f"),
            ("profit_factor", "PF", "f"), ("cagr", "CAGR", "pct"), ("sharpe", "Sharpe [95% CI]", "ci"),
            ("max_dd", "max DD", "pct")]


def _md_table(rows: dict, cols) -> str:
    from .report import _table
    return _table(rows, cols)


def markdown(R: dict, V: dict) -> str:
    L = ["# Validation results (v2)", "",
         "Generated by `python -m hcmtf.report2`. r_h = direction-adjusted move from the next candle's open",
         "to the close H candles later (1H 24, 4H 30, 1D 20, 1W 13), in ATR(14) units, after costs.",
         "Precision = share reaching +2 ATR before −1 ATR; false positives = share hitting −1 ATR first.",
         "\"Random\" = 300 draws of entries at random candles of the same symbols and windows with the same",
         "count and long/short mix. Intervals: 95% month-cluster bootstrap.", "",
         "**Which numbers to trust:** *Fresh symbols* were never used for any v2 decision (primary).",
         "*Dev windows* are the periods the screening and design check used (in-sample for the design;",
         "the verdicts' dev criterion pools all dev markets). *Dev holdout* was already looked at in v1.", "",
         "## Verdicts (MAJOR signals, fresh symbols)", "", "| timeframe / market | verdict | evidence |", "|---|---|---|"]
    for k, (v, why) in V.items():
        L.append(f"| {k} | **{v}** | {why} |")
    for tf in [t for t in TFS if t in R]:
        r = R[tf]
        L += ["", f"## {tf}", "",
              f"MAJOR = {', '.join(r['major_classes'])} with the HTFs; CONFIRMED = {', '.join(r['confirm_classes'])} with the HTFs; "
              f"evidence gating: {', '.join(r['evidence']) or 'none'}; filters: {', '.join(r['filters']) or 'none'}. Nothing fitted."]
        for key, title in [("fresh_crypto", "Fresh crypto symbols (primary)"), ("fresh_other", "Fresh non-crypto symbols (primary)"),
                           ("fresh_holdout_window", "Fresh symbols, holdout window only"),
                           ("dev_windows", "Dev symbols, 2010/2020 → holdout, design decisions made here (secondary)"),
                           ("dev_holdout_seen_in_v1", "Dev symbols, holdout window (seen in v1)")]:
            g = r.get(key) or {}
            if not g:
                continue
            L += ["", f"### {title}", "", f"{g['n_symbols']} symbols, {g['symbol_years']:.0f} symbol-years.", "",
                  _md_table(g["events"], EV_COLS)]
            if g.get("sim"):
                L += ["", "Trade simulation (equal weight, next-open fills, ATR trailing stop, costs):", "",
                      _md_table(g["sim"], SIM_COLS)]
            if g.get("timeliness"):
                L += ["", "Timeliness vs ex-post 4-ATR swings:", "", "| set | turns | detected | median lag | share of leg left |",
                      "|---|---:|---:|---:|---:|"]
                for k, v in g["timeliness"].items():
                    lag = "–" if v["lag_median"] is None else f"{v['lag_median']:.0f}"
                    cap = "–" if v["captured_median"] is None else f"{100 * v['captured_median']:.0f}%"
                    L.append(f"| {k} | {v['turns']} | {100 * v['detected']:.0f}% | {lag} | {cap} |")
            if g.get("breakdown"):
                L += ["", "Breakdown:", "", "| set | group | n | mean r_h [CI] | random | p | precision |", "|---|---|---:|---:|---:|---:|---:|"]
                for name, d in g["breakdown"].items():
                    for col, dd in d.items():
                        for k, v in dd.items():
                            rr = "–" if v["rand_mean_r"] is None else f"{v['rand_mean_r']:+.3f}"
                            pp = "–" if v["p_value"] is None else f"{v['p_value']:.3f}"
                            L.append(f"| {name} | {k} | {v['n']} | {v['mean_r']:+.3f} [{v['lo']:+.2f}, {v['hi']:+.2f}] | {rr} | {pp} | {100 * v['precision']:.1f}% |")
    return "\n".join(L) + "\n"


def main(tfs, render_only=False):
    from .report import _clean
    path = OUT / "results.json"
    R = json.loads(path.read_text()) if path.exists() else {}
    for tf in ([] if render_only else tfs):
        R[tf] = _clean(run_tf(tf))
        path.write_text(json.dumps(R, indent=1))
    R = {k: R[k] for k in TFS if k in R}
    V = verdicts(R)
    (OUT / "RESULTS.md").write_text(markdown(R, V))
    (OUT / "verdicts.json").write_text(json.dumps(V, indent=1))
    for k, (v, why) in V.items():
        print(f"{k}: {v} — {why}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args or TFS, render_only="--render" in sys.argv)
