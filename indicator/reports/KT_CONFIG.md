# KT: four additional signal types (exploratory)

**Status: FROZEN** (2026-10-28), before any KT code ran on market data. The user chose all four
types.

**Definitions, tests and baselines:** `research/kenny_types.py`. Each type has one job, its own
success test and a plain baseline population.

| type | job | success test (Q = L/4 candles) | baseline (every candle that…) |
|---|---|---|---|
| CAU, caution / take profit | rally stretched and exhausted near its high | a pullback ≥ 1.5 ATR below the signal close within Q | is within 2 ATR of the 2L high |
| CONT, trend-continuation BUY | a pullback inside an uptrend is ending | close higher after Q, and no low below the pullback low within Q | is in an EMA50 > EMA200 uptrend above EMA200 |
| BRK, breakdown / exit | a mature uptrend is breaking down | close lower after Q, and no close above the signal candle's high within Q | closes below SMA(1.5L) after a recent 2L high |
| EARLY, bottom forming | heads-up that a low may be forming | the swing low of ±L/2 lies within ±Q of the signal (window range ≥ 2 ATR) | closes ≥ 1 ATR below EMA_L |

**Tuning.** Definitions are fixed except EARLY's threshold scale, chosen from {0.9, 1.0, 1.1} on
the tuning period. CAU is not tested on 1W, where the weekly SELL already is this signal.

**Split.** As in KR: tuning before 2018 (1W, 1D) or before 2024 (4H, 1H). The check period has
been studied before.

## Adoption (per type × timeframe)

The type is shown on that timeframe only if all hold:
* ≥ 30 signals in each period;
* in **both** periods, its hit rate is ≥ the baseline's hit rate + 0.05.

Otherwise it is not shown on that timeframe. Results are reported for equities and crypto.

**Display.** Each adopted type gets its own small marker and its own on/off input. The
BUY/SELL triangles are unchanged.

**Ledger trial:** `kt-all` (hypothesis KT-1).
