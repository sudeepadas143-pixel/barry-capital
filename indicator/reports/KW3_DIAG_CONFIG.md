# KW-3 stage 1: diagnosis of the weekly SELL (exploratory)

**Status: FROZEN** (2026-10-28), before any KW-3 code ran on market data.

**Scope and data.**
* Weekly SELL only. Weekly BUY and all other timeframes are untouched.
* Development data only: weekly candles **before 2018-01-01** of the EVAL universe, using the
  guarded loader with the usual protections. No 2018+ outcome is computed in this stage.

**Signals diagnosed.** The current weekly SELL (W0: Kenny Confirmed top, GBZ model, as shipped).

## Signal classes (`research/kenny_weekly_sell.classify`)

Moves are in weekly ATR14 at the signal; a meaningful move is MOVE = 3 ATR; the horizon is 26 weeks.

| class | definition |
|---|---|
| late | at the signal, price is already ≥ 3 ATR below its 26-week high |
| premature | price rises 3 ATR above the signal close before falling 3 ATR |
| useful | price falls 3 ATR first and does not regain the signal-week high within 26 weeks |
| false_reversal | price falls 3 ATR first, then regains the signal-week high within 26 weeks |
| flat | neither move happens within 26 weeks |

**Missed top.** A labelled major top (the frozen 1W top labels) with no W0 SELL within
[−13, +4] weeks of it.

## Characteristics compared per class

The median of each characteristic at the signal (or at the missed top), per class:
* ext26 and ext40: close vs EMA26 / SMA40, in ATR;
* dd52 and rally52: distance from the 52-week high / low, in ATR;
* TSMOM (52-week);
* roc13 and its 4-week change (momentum deceleration);
* RSI and its 8-week max;
* bearish RSI divergence in the last 8 weeks;
* log(ATR5/ATR26), volatility change;
* upper-wick share, shooting star, engulfing, failed new 52-week high in the last 4 weeks;
* SMA40 slope.

**Ledger trial:** `kw3-diag` (hypothesis KW-3D).
