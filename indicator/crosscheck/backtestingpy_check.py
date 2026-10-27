"""Independent trade-level backtest of the MAJOR signals with backtesting.py (AGPL-3.0).

Kept out of the hcmtf package on purpose (hcmtf does not import it; nothing here ships with the
indicator). It answers two questions:

1. Does an independent engine reproduce hcmtf's trade simulator on the same signals? Same rules:
   market entry at the next candle's open, initial stop 2 ATR from the fill (ATR of the signal
   candle), trailing stop 3 ATR from the best close, reversal on an opposite signal, commission
   = half the round-trip cost per side. One known convention difference: backtesting.py fills a
   time exit at the NEXT open, hcmtf at the time-exit candle's close; agreement is reported with
   and without time-exit trades.
2. Trade-level results per side (long = BULLISH, short = BEARISH): trades, win rate, mean and
   median trade return, worst trade, profit factor, and the per-symbol max drawdown and Sharpe
   that backtesting.py reports. Across crypto, equities and commodities, 1H/4H/1D/1W.

    python crosscheck/backtestingpy_check.py   → reports/BACKTESTINGPY.md, reports/backtestingpy.json
"""

import json
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

CASES = {
    "crypto": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "LINKUSDT", "XRPUSDT"],
    "equities": ["SPY", "QQQ", "AAPL", "MSFT", "JPM", "XOM"],
    "commodities": ["GLD", "SLV", "USO", "CPER", "DBA", "UNG"],
}
TFS = ["1H", "4H", "1D", "1W"]


def run_one(args):
    tf, sym, grp = args
    from backtesting import Backtest, Strategy

    from hcmtf import evaluate as E, study as St
    from hcmtf.report2 import active_params
    from hcmtf.universe import BY_SYMBOL

    s = St.prepare_one((BY_SYMBOL[sym], tf))
    if s is None:
        return None
    ev = St.signals_for(s, active_params(tf))
    ev = ev[ev["tier"] == "major"]
    if len(ev) < 2:
        return {"tf": tf, "symbol": sym, "group": grp, "trades": []}
    f = s.f
    n = len(f.c)
    max_hold = St.MAX_HOLD[tf]
    cost = s.cost / 1e4
    sig = np.zeros(n)
    sig[ev["i"].to_numpy(int)] = ev["dir"].to_numpy()
    # stop distance known at the fill: 2 x ATR of the signal candle
    stopdist = np.r_[np.nan, 2.0 * f.atr[:-1]]
    df = pd.DataFrame({"Open": f.o, "High": f.h, "Low": f.l, "Close": f.c, "Volume": 0.0},
                      index=s.index.tz_convert(None))

    class Major(Strategy):
        def init(self):
            self.sig = self.I(lambda: sig, name="sig", plot=False)
            self.atr = self.I(lambda: f.atr, name="atr", plot=False)
            self.best = None
            self.entry_i = None
            self.pending_stop = None
            self.late_sl = None
            self.n_late = 0

        def next(self):
            i = len(self.data) - 1
            # set the initial stop on the entry candle's first next(): it must be live on that
            # candle, so it is placed with the order (sl) using the stop distance array
            for t in self.trades:
                if self.entry_i is None:
                    self.entry_i = i
                d = 1 if t.is_long else -1
                if t.sl is None and self.late_sl is not None:
                    t.sl = self.late_sl
                    self.late_sl = None
                if i - self.entry_i + 1 >= max_hold:
                    t.close()
                    continue
                c = self.data.Close[-1]
                self.best = c if self.best is None else (max(self.best, c) if d > 0 else min(self.best, c))
                trail = self.best - d * 3.0 * self.atr[-1]
                t.sl = max(t.sl, trail) if d > 0 else min(t.sl, trail)
            d = int(self.sig[-1])
            cur = 0 if not self.trades else (1 if self.trades[0].is_long else -1)
            if d != 0 and i + 1 < n and d != cur:
                if self.trades:
                    self.position.close()
                nxt_open = f.o[i + 1]                      # the fill price of this market order
                sl = nxt_open - d * stopdist[i + 1]
                c = self.data.Close[-1]
                if (d > 0 and sl < c) or (d < 0 and sl > c):
                    (self.buy if d > 0 else self.sell)(size=0.99, sl=sl)
                    self.late_sl = None
                else:
                    # backtesting.py validates sl against the current close; after a gap of more
                    # than 2 ATR it would reject it, so the stop is attached one candle later
                    (self.buy if d > 0 else self.sell)(size=0.99)
                    self.late_sl = sl
                    self.n_late += 1
                self.best, self.entry_i = nxt_open, i + 1

    bt = Backtest(df, Major, cash=1e9, commission=cost / 2, trade_on_close=False, exclusive_orders=False,
                  finalize_trades=True)
    stats = bt.run()
    tr = stats["_trades"]
    trades = [{"dir": 1 if r.Size > 0 else -1, "entry_i": int(r.EntryBar), "exit_i": int(r.ExitBar),
               "entry": float(r.EntryPrice), "exit": float(r.ExitPrice), "ret": float(r.ReturnPct)}
              for r in tr.itertuples()]
    # hcmtf reference on the same signals
    ref = E.simulate(ev, f, s.cost, max_hold)
    refd = [{"dir": int(r.dir), "entry_i": int(r.entry_i), "exit_i": int(r.exit_i), "reason": r.reason,
             "ret": float(r.ret)} for r in ref.itertuples()]
    return {"tf": tf, "symbol": sym, "group": grp, "trades": trades, "ref": refd, "late_sl": int(stats._strategy.n_late),
            "max_dd": float(stats["Max. Drawdown [%]"]), "sharpe": float(stats["Sharpe Ratio"]) if stats["Sharpe Ratio"] == stats["Sharpe Ratio"] else None}


def main():
    jobs = [(tf, sym, grp) for tf in TFS for grp, syms in CASES.items() for sym in syms]
    with ProcessPoolExecutor(8) as ex:
        res = [r for r in ex.map(run_one, jobs) if r]
    (ROOT / "reports" / "backtestingpy.json").write_text(json.dumps(res))
    L = ["# backtesting.py: independent trade-level backtest of the MAJOR signals", "",
         "\n\n".join(__doc__.split("\n\n")[1:3]).strip(), "",
         "Position size: 99% of equity per trade (so per-symbol drawdowns are meaningful); returns per trade",
         "are backtesting.py's ReturnPct after commission.", "", "## Agreement with hcmtf's simulator", "",
         "| TF | trades (bt / hcmtf) | same entry candles | same exit candle (non-time exits) | sum of returns bt / hcmtf | entries with stop attached a candle late (gap > 2 ATR) |",
         "|---|---:|---:|---:|---:|---:|"]
    for tf in TFS:
        rs = [r for r in res if r["tf"] == tf and r.get("ref") is not None]
        nb = sum(len(r["trades"]) for r in rs)
        nr = sum(len(r["ref"]) for r in rs)
        same_e = same_x = nonttime = 0
        sb = sr = 0.0
        for r in rs:
            ref = {(x["entry_i"], x["dir"]): x for x in r["ref"]}
            for t in r["trades"]:
                sb += t["ret"]
                x = ref.get((t["entry_i"], t["dir"]))
                if x:
                    same_e += 1
                    if x["reason"] not in ("time", "open"):
                        nonttime += 1
                        same_x += x["exit_i"] == t["exit_i"]
            sr += sum(x["ret"] for x in r["ref"])
        late = sum(r.get("late_sl", 0) for r in rs)
        L.append(f"| {tf} | {nb} / {nr} | {same_e} | {same_x} / {nonttime} | {sb:+.2f} / {sr:+.2f} | {late} |")
    L += ["", "## Trade results by side (backtesting.py trades)", "",
          "| TF | group | side | trades | win rate | mean trade % | median % | worst % | profit factor | symbols | median per-symbol max DD % |",
          "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for tf in TFS:
        for grp in CASES:
            rs = [r for r in res if r["tf"] == tf and r["group"] == grp]
            for side, d in (("long (BULLISH)", 1), ("short (BEARISH)", -1)):
                x = np.array([t["ret"] for r in rs for t in r["trades"] if t["dir"] == d])
                if len(x) == 0:
                    L.append(f"| {tf} | {grp} | {side} | 0 | | | | | | | |")
                    continue
                pf = x[x > 0].sum() / -x[x < 0].sum() if (x < 0).any() else float("inf")
                dd = np.median([r["max_dd"] for r in rs if r["trades"]])
                L.append(f"| {tf} | {grp} | {side} | {len(x)} | {100 * (x > 0).mean():.0f}% | {100 * x.mean():+.2f} | "
                         f"{100 * np.median(x):+.2f} | {100 * x.min():+.1f} | {pf:.2f} | {len([r for r in rs if r['trades']])} | {dd:.1f} |")
    (ROOT / "reports" / "BACKTESTINGPY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
