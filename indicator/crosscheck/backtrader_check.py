"""Independent re-simulation of the signal trades in backtrader (GPL-3.0).

Kept out of the hcmtf package on purpose: hcmtf does not import backtrader, so the
research code carries no GPL dependency; this script only reads hcmtf's output.

What it checks: given the same bars and the same signal list, does backtrader's broker
(next-open market fills, stop orders that fill at the stop or at a gapped open) produce
the same trades as hcmtf.evaluate.simulate? It re-implements the exit rules in a
backtrader Strategy using cheat-on-open so the initial stop can be set from the actual
fill price before that candle trades, exactly as the hcmtf simulator assumes.

    python crosscheck/backtrader_check.py 4H BTCUSDT ETHUSDT SPY
"""

import sys
from pathlib import Path

import backtrader as bt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf import evaluate as E, study as St  # noqa: E402
from hcmtf.report2 import active_params  # noqa: E402
from hcmtf.universe import BY_SYMBOL  # noqa: E402


DEBUG = False


class SignalStrategy(bt.Strategy):
    """Exit rules as backtrader orders; trades are read back from backtrader's notify_trade.

    Broker: cheat-on-open + cheat-on-close.
    * next_open(i): a pending signal is executed with market orders flagged coc=False, which
      cheat-on-open fills at candle i's open (close the old position if any, open the new
      one), plus the initial Stop priced from that open, so it is live on candle i.
    * next(i): if the position has been held max_hold candles, a market order closes it at
      candle i's close (cheat-on-close). Otherwise the trailing stop is moved (cancel and
      replace). Then the signal on candle i, if any and different from the position left
      after this candle, becomes pending for i + 1.
    """
    params = dict(signals=None, atr=None, max_hold=60, stop_atr=2.0, trail_atr=3.0, n=0)

    def __init__(self):
        self.pending = None
        self.stop_order = None
        self.dir = 0            # direction of the open position (0 = flat)
        self.entry_i = None
        self.best = self.stop_px = None
        self.closed = []
        self.fill_pos = 0
        self.lot = None

    def _i(self):
        return len(self.data) - 1

    def notify_order(self, order):
        """Record trades from fills alone: a fill from flat opens a lot, an opposite fill closes it."""
        if order.status != order.Completed:
            return
        size, px, i = order.executed.size, order.executed.price, self._i()
        if DEBUG:
            print("fill", i, size, round(px, 4), "pos", self.fill_pos, order.exectype)
        if self.fill_pos == 0:
            self.lot = dict(entry_i=i, dir=1 if size > 0 else -1, entry=px)
        else:
            self.closed.append(dict(self.lot, exit_i=i, exit=px))
            self.lot = None
        self.fill_pos += 1 if size > 0 else -1
        # notify_order receives clones: compare by ref, not identity
        if self.stop_order is not None and order.ref == self.stop_order.ref:
            self.stop_order = None
            self.dir = 0

    def _new_stop(self):
        if self.stop_order is not None and self.stop_order.alive():
            self.cancel(self.stop_order)
        self.stop_order = (self.sell if self.dir > 0 else self.buy)(exectype=bt.Order.Stop, price=self.stop_px, size=1)

    def next_open(self):
        if self.pending is None:
            return
        d, self.pending = self.pending, None
        i, px = self._i(), self.data.open[0]
        if self.dir != 0:
            if self.stop_order is not None and self.stop_order.alive():
                self.cancel(self.stop_order)
            self.stop_order = None
            (self.sell if self.dir > 0 else self.buy)(size=1).addinfo(coc=False)   # fills at this open
        (self.buy if d > 0 else self.sell)(size=1).addinfo(coc=False)
        self.dir, self.entry_i, self.best = d, i, px
        self.stop_px = px - d * self.p.stop_atr * self.p.atr[i - 1]
        self._new_stop()

    def next(self):
        i = self._i()
        if self.dir != 0:
            if i - self.entry_i + 1 >= self.p.max_hold:
                if self.stop_order is not None and self.stop_order.alive():
                    self.cancel(self.stop_order)
                self.stop_order = None
                (self.sell if self.dir > 0 else self.buy)(size=1)   # fills at this close
                self.dir = 0
            else:
                c = self.data.close[0]
                self.best = max(self.best, c) if self.dir > 0 else min(self.best, c)
                trail = self.best - self.dir * self.p.trail_atr * self.p.atr[i]
                new = max(self.stop_px, trail) if self.dir > 0 else min(self.stop_px, trail)
                if new != self.stop_px:
                    self.stop_px = new
                    self._new_stop()
        d = self.p.signals.get(i)
        if d is not None and i + 1 < self.p.n and d != self.dir:
            self.pending = d

    def trades(self) -> pd.DataFrame:
        return pd.DataFrame(self.closed, columns=["entry_i", "dir", "entry", "exit_i", "exit"])


def run(tf: str, symbol: str):
    s = St.prepare_one((BY_SYMBOL[symbol], tf))
    p = active_params(tf)
    ev = St.signals_for(s, p)
    ev = ev[ev["tier"].isin(["major", "confirmed"])]
    ref = E.simulate(ev, s.f, 0.0, St.MAX_HOLD[tf])
    df = pd.DataFrame({"open": s.f.o, "high": s.f.h, "low": s.f.l, "close": s.f.c, "volume": 0.0},
                      index=s.index.tz_convert(None))
    cer = bt.Cerebro(stdstats=False, cheat_on_open=True, tradehistory=False)
    cer.broker.set_coo(True)
    cer.broker.set_coc(True)
    cer.adddata(bt.feeds.PandasData(dataname=df))
    cer.addstrategy(SignalStrategy, signals=dict(zip(ev["i"].astype(int), ev["dir"].astype(int))),
                    atr=s.f.atr, max_hold=St.MAX_HOLD[tf], n=len(df))
    cer.broker.setcash(1e12)
    strat = cer.run()[0]
    got = strat.trades()
    if strat.lot is not None:   # still open at the end: mark at the last close, like hcmtf
        got = pd.concat([got, pd.DataFrame([dict(strat.lot, exit_i=len(df) - 1, exit=df["close"].iloc[-1])])],
                        ignore_index=True)
    ref = ref[["entry_i", "exit_i", "dir", "entry", "exit"]].reset_index(drop=True)
    got = got[["entry_i", "exit_i", "dir", "entry", "exit"]].reset_index(drop=True)
    m = ref.merge(got, on=["entry_i", "dir"], how="outer", suffixes=("_ref", "_bt"), indicator=True)
    both = m[m["_merge"] == "both"]
    same_exit = np.isclose(both["exit_ref"], both["exit_bt"], rtol=1e-9) & (np.abs(both["exit_i_ref"] - both["exit_i_bt"]) <= 1)
    r_ref = (ref["dir"] * (ref["exit"] / ref["entry"] - 1)).sum()
    r_bt = (got["dir"] * (got["exit"] / got["entry"] - 1)).sum()
    return {"tf": tf, "symbol": symbol, "trades_ref": len(ref), "trades_bt": len(got),
            "matched_entries": int(len(both)), "identical_exits": int(same_exit.sum()),
            "sum_ret_ref": float(r_ref), "sum_ret_bt": float(r_bt)}, m[~m.index.isin(both[same_exit].index)]


DEFAULT_CASES = [("1D", "SPY"), ("1D", "BTCUSDT"), ("1D", "EURUSD=X"), ("4H", "ETHUSDT"), ("4H", "GLD"),
                 ("1W", "TLT"), ("1W", "XRPUSDT"), ("1H", "LINKUSDT"), ("1H", "AAPL")]

if __name__ == "__main__":
    cases = [(sys.argv[1], s) for s in sys.argv[2:]] if len(sys.argv) > 2 else DEFAULT_CASES
    rows = []
    for tf, sym in cases:
        res, diff = run(tf, sym)
        rows.append(res)
        print(res, flush=True)
        if len(diff):
            print(diff.head(5).to_string())
    if len(sys.argv) <= 2:
        out = Path(__file__).resolve().parent.parent / "reports" / "BACKTRADER_CROSSCHECK.md"
        L = ["# backtrader cross-check", "",
             "Same candles, same MAJOR/CONFIRMED signal list, exits re-implemented as backtrader orders",
             "(next-open market entries, Stop orders, Close order for the time exit). Trades are read from",
             "backtrader's own executions. `python crosscheck/backtrader_check.py`", "",
             "| TF | symbol | trades (hcmtf) | trades (backtrader) | same entries | identical exits | sum of returns hcmtf | sum backtrader |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
        for r in rows:
            L.append(f"| {r['tf']} | {r['symbol']} | {r['trades_ref']} | {r['trades_bt']} | {r['matched_entries']} | "
                     f"{r['identical_exits']} | {r['sum_ret_ref']:+.6f} | {r['sum_ret_bt']:+.6f} |")
        out.write_text("\n".join(L) + "\n")
