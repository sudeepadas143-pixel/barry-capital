"""Analyse a TradingView Strategy Tester "List of Trades" export of HC-MTF ST, by side.

    python scripts/analyze_tv_trades.py trades.csv [--iters 2000]

Pairs each entry with its exit by trade number and reads the direction from the entry row
("Entry Long" / "Entry Short"). The template's own parser (pinewf.pine_csv) falls back to
exit/entry - 1 for every trade, which is the wrong sign for shorts, so it is not used for that.
Reports per side: trades, win rate, mean / median trade %, profit factor, a bootstrap 95%
interval of the mean, and pinewf's Monte Carlo bands (trade-order bootstrap) for the equity
curve of each side.
"""
import argparse
import re

import numpy as np
import pandas as pd


def parse(path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    cols = {c.lower(): c for c in raw.columns}
    num = next(c for k, c in cols.items() if k.startswith("trade"))
    typ = cols["type"]
    price = next(c for k, c in cols.items() if k.startswith("price"))
    pct = next((c for k, c in cols.items() if re.search(r"(net )?(p&l|profit) ?%", k)), None)
    rows = []
    for tid, g in raw.groupby(num):
        ent = g[g[typ].str.lower().str.startswith("entry")]
        ex = g[g[typ].str.lower().str.startswith("exit")]
        if len(ent) == 0 or len(ex) == 0:
            continue
        d = 1 if "long" in ent[typ].iloc[0].lower() else -1
        pe, px = float(ent[price].iloc[0]), float(ex[price].iloc[0])
        r = float(ex[pct].iloc[0]) / 100 if pct and pd.notna(ex[pct].iloc[0]) else d * (px / pe - 1)
        rows.append({"trade": tid, "side": "BULLISH" if d > 0 else "BEARISH", "ret": r})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--iters", type=int, default=2000)
    a = ap.parse_args()
    t = parse(a.csv)
    rng = np.random.default_rng(7)
    for side, g in t.groupby("side"):
        x = g["ret"].to_numpy()
        boot = [rng.choice(x, len(x)).mean() for _ in range(a.iters)]
        pf = x[x > 0].sum() / -x[x < 0].sum() if (x < 0).any() else float("inf")
        print(f"{side}: trades {len(x)}, win {100 * (x > 0).mean():.0f}%, mean {100 * x.mean():+.2f}% "
              f"[{100 * np.percentile(boot, 2.5):+.2f}, {100 * np.percentile(boot, 97.5):+.2f}], "
              f"median {100 * np.median(x):+.2f}%, profit factor {pf:.2f}")
        try:
            from pinewf.montecarlo import MonteCarloConfig, equity_path_bands
            bands = equity_path_bands(x * 100, MonteCarloConfig(iters=a.iters, seed=7))
            last = bands.iloc[-1]
            print(f"  Monte Carlo final equity from 10,000 (5/50/95%): {last['p05']:.0f} / {last['p50']:.0f} / {last['p95']:.0f}")
        except Exception as e:  # pinewf optional
            print("  (pinewf Monte Carlo unavailable:", e, ")")


if __name__ == "__main__":
    main()
