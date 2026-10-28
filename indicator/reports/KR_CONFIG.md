# KR: optimise Kenny's BUY/SELL to be "right enough in retrospect" (exploratory)

**Status: FROZEN** (2026-10-28), before any KR code ran on market data. The user chose the
definition (balanced) and asked for weekly SELL to be included.

## Success rule (`research/kenny_retro.py`)

A signal at candle s, on a chart with cycle length L, is **right** when both hold:
* **Zone:** its close is in the lowest 25% (BUY) or highest 25% (SELL) of the high-low range of
  candles s − L/2 … s + L/2.
* **Follow-through:** close[s + L/4] is above (BUY) or below (SELL) close[s].

It need not be the exact top or bottom.

**Coverage.** The share of meaningful swing lows (BUY) or highs (SELL) that get a right signal of
that side within ±L/4 candles. A meaningful swing is the extreme of its ±L/2 window, with that
window's range ≥ 4 ATR.

## Options per timeframe × side

Kenny's internal states:
* Early Warning (W), High Conviction (H), Confirmed (CONF);
* the shipped thresholds scaled by 0.9, 1.0 or 1.1;
* the shipped same-side cooldown.

**Weekly SELL only:** also KW-3 Candidate A (R = 6) and the KW-6 engine warning.

**Current production:** BUY = H|1.0, SELL = CONF|1.0.

## Data and split

**Data.** EVAL instruments via the guarded loader, with the shipped CY-2 spec. The spec was fitted
on all years, so every option, the current one included, shares that in-sample component.

**Split:**

| timeframes | tuning | check | note |
|---|---|---|---|
| 1W, 1D | < 2018 | ≥ 2018 | – |
| 4H, 1H | < 2024 | ≥ 2024 | non-crypto intraday data starts 2023-11 |

The check period has been studied before, so it is not unseen.

## Selection (per timeframe × side, frozen)

**Eligible on the tuning period:**
* ≥ 30 signals;
* signal rate ≥ 0.5× the current option's;
* coverage ≥ the current option's − 0.05.

**Chosen:** the eligible option with the highest right-rate on the tuning period.

**Adopted** only if, on the check period:
* its right-rate is ≥ the current option's;
* its coverage is ≥ the current option's − 0.05.

Otherwise the current option stays. Results are reported per side, for equities and crypto.

**Ledger trial:** `kr-all` (hypothesis KR-1).
