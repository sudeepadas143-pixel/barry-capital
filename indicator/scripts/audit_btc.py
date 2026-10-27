"""BTC audit: bullish and bearish signals separately, 1H/4H/1D/1W, default vs acceptance.

    python scripts/audit_btc.py      → reports/BTC_AUDIT.md, reports/btc_audit.json

Data: BTCUSDT (Binance, from 2017-08) for every timeframe, plus BTC-USD (Yahoo, from
2014-09) for 1D/1W, closer to the long BTC history TradingView loads for BTCUSD charts.
Periods: "design" = before each timeframe's holdout start (the v2 design used these
dates); "recent" = holdout start to the end of the data (not used for any v2 design
decision; BTC is a development symbol, so this is the out-of-sample check for BTC).

Per row: signals, signals per year, precision (+2 ATR before -1 ATR), false positives
(-1 ATR first), invalidated (a close back through the broken level within 3 candles),
mean r_h in ATR with 95% month-cluster CI, mean forward return % over H candles after
costs, median MFE/MAE, and the same-count random-entry baseline (same direction).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_fixes import invalidated  # noqa: E402
from hcmtf import engine as G, evaluate as E, study as St  # noqa: E402
from hcmtf.metrics import cluster_ci, random_baseline  # noqa: E402
from hcmtf.report2 import active_params  # noqa: E402
from hcmtf.universe import BY_SYMBOL  # noqa: E402

CASES = [("BTCUSDT", "1H"), ("BTCUSDT", "4H"), ("BTCUSDT", "1D"), ("BTC-USD", "1D"),
         ("BTCUSDT", "1W"), ("BTC-USD", "1W")]


def row(s, ev, a, b):
    if len(ev) == 0:
        return {"n": 0}
    ev = St.tag(s, ev.assign(invalid3=invalidated(s, ev)))
    m, lo, hi = cluster_ci(ev, "r_h")
    yrs = max((b - a).days / 365.25, 1e-9)
    rb = random_baseline(ev, {s.symbol: s}, [(a, b)], reps=300)
    return {"n": int(len(ev)), "per_yr": len(ev) / yrs, "precision": float((ev["barrier"] == 1).mean()),
            "false_pos": float((ev["barrier"] == -1).mean()), "invalid3": float(ev["invalid3"].mean()),
            "mean_r": m, "lo": lo, "hi": hi, "ret_pct": 100 * float(ev["ret_h"].mean()),
            "mfe": float(ev["mfe"].median()), "mae": float(ev["mae"].median()),
            "rand_r": rb.get("rand_mean_r"), "p": rb.get("p_value")}


def main():
    out = {}
    L = ["# BTC audit", "", __doc__.split("\n\n", 1)[1].strip(), ""]
    for sym, tf in CASES:
        s = St.prepare_one((BY_SYMBOL[sym], tf))
        hold = pd.Timestamp(St.HOLDOUT[tf], tz="UTC")
        start, end = s.index[0], s.index[-1] + pd.Timedelta(days=1)
        L += [f"## {sym} {tf}  ({start.date()} → {s.index[-1].date()})", "",
              "| variant | tier | side | period | n | per yr | precision | false pos | invalidated ≤3 | mean r_h [95% CI] | fwd ret % | MFE / MAE | random r_h | p |",
              "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for vname, p in (("default", active_params(tf)), ("acceptance", G.with_(active_params(tf), accept=True))):
            sig = St.signals_for(s, p)
            sig = sig[sig["tier"].isin(["major", "confirmed"])]
            for tier, sub in (("MAJOR (shown)", sig[sig["tier"] == "major"]), ("MAJOR+CONFIRMED", sig)):
                for side, d in (("bullish", 1), ("bearish", -1)):
                    e = sub[sub["dir"] == d]
                    t = s.index[e["i"].to_numpy(int)]
                    for pname, a, b in (("design", start, hold), ("recent", hold, end)):
                        r = row(s, e[(t >= a) & (t < b)], a, b)
                        out[f"{sym} {tf} {vname} {tier} {side} {pname}"] = r
                        if not r["n"]:
                            L.append(f"| {vname} | {tier} | {side} | {pname} | 0 | | | | | | | | | |")
                            continue
                        rr = "–" if r["rand_r"] is None else f"{r['rand_r']:+.2f}"
                        pp = "–" if r["p"] is None else f"{r['p']:.2f}"
                        L.append(f"| {vname} | {tier} | {side} | {pname} | {r['n']} | {r['per_yr']:.1f} | "
                                 f"{100 * r['precision']:.0f}% | {100 * r['false_pos']:.0f}% | {100 * r['invalid3']:.0f}% | "
                                 f"{r['mean_r']:+.2f} [{r['lo']:+.2f}, {r['hi']:+.2f}] | {r['ret_pct']:+.2f} | "
                                 f"{r['mfe']:.2f} / {r['mae']:.2f} | {rr} | {pp} |")
        L.append("")
        print(sym, tf, "done", flush=True)
    (ROOT / "reports" / "BTC_AUDIT.md").write_text("\n".join(L) + "\n")
    (ROOT / "reports" / "btc_audit.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
