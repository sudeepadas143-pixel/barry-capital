# backtrader cross-check

Same candles, same MAJOR/CONFIRMED signal list, exits re-implemented as backtrader orders
(next-open market entries, Stop orders, Close order for the time exit). Trades are read from
backtrader's own executions. `python crosscheck/backtrader_check.py`

| TF | symbol | trades (hcmtf) | trades (backtrader) | same entries | identical exits | sum of returns hcmtf | sum backtrader |
|---|---|---:|---:|---:|---:|---:|---:|
| 1D | SPY | 169 | 169 | 169 | 169 | +1.304042 | +1.304042 |
| 1D | BTCUSDT | 52 | 52 | 52 | 52 | +2.046608 | +2.046608 |
| 1D | EURUSD=X | 112 | 112 | 112 | 112 | -0.391457 | -0.391457 |
| 4H | ETHUSDT | 268 | 268 | 268 | 268 | +2.562892 | +2.562892 |
| 4H | GLD | 33 | 33 | 33 | 33 | +0.453417 | +0.453417 |
| 1W | TLT | 27 | 27 | 27 | 27 | +0.331636 | +0.331636 |
| 1W | XRPUSDT | 7 | 7 | 7 | 7 | -1.731259 | -1.731259 |
| 1H | LINKUSDT | 946 | 946 | 946 | 946 | +0.907904 | +0.907904 |
| 1H | AAPL | 104 | 104 | 104 | 104 | -0.224566 | -0.224566 |
