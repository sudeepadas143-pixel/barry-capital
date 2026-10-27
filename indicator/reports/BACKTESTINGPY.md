# backtesting.py: independent trade-level backtest of the MAJOR signals

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

Position size: 99% of equity per trade (so per-symbol drawdowns are meaningful); returns per trade
are backtesting.py's ReturnPct after commission.

## Agreement with hcmtf's simulator

| TF | trades (bt / hcmtf) | same entry candles | same exit candle (non-time exits) | sum of returns bt / hcmtf | entries with stop attached a candle late (gap > 2 ATR) |
|---|---:|---:|---:|---:|---:|
| 1H | 3146 / 3146 | 3146 | 3093 / 3093 | +3.64 / +3.63 | 0 |
| 4H | 877 / 877 | 877 | 827 / 827 | +6.94 / +6.95 | 0 |
| 1D | 1046 / 1046 | 1046 | 1001 / 1001 | +9.41 / +9.45 | 3 |
| 1W | 210 / 211 | 210 | 130 / 130 | +8.79 / +8.68 | 0 |

## Trade results by side (backtesting.py trades)

| TF | group | side | trades | win rate | mean trade % | median % | worst % | profit factor | symbols | median per-symbol max DD % |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1H | crypto | long (BULLISH) | 1237 | 31% | +0.26 | -1.31 | -8.3 | 1.18 | 6 | -62.2 |
| 1H | crypto | short (BEARISH) | 1425 | 31% | +0.01 | -1.20 | -12.7 | 1.01 | 6 | -62.2 |
| 1H | equities | long (BULLISH) | 170 | 39% | +0.34 | -0.33 | -6.4 | 1.61 | 6 | -8.8 |
| 1H | equities | short (BEARISH) | 77 | 31% | -0.39 | -0.93 | -4.7 | 0.58 | 6 | -8.8 |
| 1H | commodities | long (BULLISH) | 139 | 42% | +0.43 | -0.46 | -8.4 | 1.53 | 6 | -16.2 |
| 1H | commodities | short (BEARISH) | 98 | 21% | -0.66 | -1.02 | -5.6 | 0.44 | 6 | -16.2 |
| 4H | crypto | long (BULLISH) | 311 | 29% | +1.69 | -2.79 | -19.7 | 1.56 | 6 | -71.1 |
| 4H | crypto | short (BEARISH) | 424 | 34% | +0.27 | -2.36 | -20.2 | 1.10 | 6 | -71.1 |
| 4H | equities | long (BULLISH) | 63 | 49% | +1.05 | -0.00 | -4.6 | 2.23 | 6 | -12.2 |
| 4H | equities | short (BEARISH) | 14 | 36% | -0.61 | -2.29 | -4.2 | 0.65 | 6 | -12.2 |
| 4H | commodities | long (BULLISH) | 47 | 45% | +0.35 | -0.91 | -6.7 | 1.23 | 6 | -15.0 |
| 4H | commodities | short (BEARISH) | 18 | 22% | -1.10 | -2.14 | -10.2 | 0.55 | 6 | -15.0 |
| 1D | crypto | long (BULLISH) | 57 | 37% | +3.42 | -7.81 | -27.4 | 1.48 | 6 | -69.2 |
| 1D | crypto | short (BEARISH) | 76 | 33% | -0.86 | -6.03 | -26.0 | 0.88 | 6 | -69.2 |
| 1D | equities | long (BULLISH) | 519 | 44% | +1.69 | -0.95 | -13.1 | 1.96 | 6 | -48.8 |
| 1D | equities | short (BEARISH) | 121 | 30% | -1.29 | -3.04 | -13.9 | 0.63 | 6 | -48.8 |
| 1D | commodities | long (BULLISH) | 135 | 39% | +1.31 | -1.84 | -12.0 | 1.64 | 6 | -42.7 |
| 1D | commodities | short (BEARISH) | 138 | 31% | -0.63 | -2.59 | -13.3 | 0.80 | 6 | -42.7 |
| 1W | crypto | long (BULLISH) | 7 | 43% | +33.39 | -15.15 | -29.0 | 3.53 | 3 | -51.6 |
| 1W | crypto | short (BEARISH) | 4 | 50% | +1.70 | -1.63 | -37.6 | 1.09 | 3 | -51.6 |
| 1W | equities | long (BULLISH) | 121 | 53% | +5.16 | +1.35 | -25.2 | 2.41 | 6 | -43.0 |
| 1W | equities | short (BEARISH) | 13 | 38% | -1.19 | -9.97 | -23.6 | 0.87 | 6 | -43.0 |
| 1W | commodities | long (BULLISH) | 24 | 46% | +0.72 | -1.08 | -12.7 | 1.20 | 6 | -34.9 |
| 1W | commodities | short (BEARISH) | 41 | 41% | +0.30 | -4.67 | -38.0 | 1.04 | 6 | -34.9 |
