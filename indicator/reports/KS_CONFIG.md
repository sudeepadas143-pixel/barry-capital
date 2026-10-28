# KS: strong arrows only (exploratory)

**Status: FROZEN** (2026-10-28), before any KS code ran on market data.

**User's choices:**
* **Strong arrows only.** Weaker setups stay internal.
* **Quality is judged by "right in retrospect"** (the KR rule: in the lowest/highest 25% of the
  ±L/2 range, and price moved the right way after L/4 candles).

**Arrows.** The current Optimized profile (KR adopted choices) per timeframe and side.

## Strength (`research/kenny_strength.py`): S = M + E + H, from 0 to 5

* **M (margin):** the setup is ≥ 10% beyond its threshold. For the weekly SELL: a rally from the
  52-week low ≥ 9 ATR.
* **E (evidence):** independent witnesses, one per role, 0 to 3:
  * RSI/MACD divergence within 8 candles;
  * a price-action reversal within 3 candles;
  * a volatility/volume burst with a reversal wick within 3 candles.
* **H (higher timeframe):** the completed higher-timeframe trend agrees (up for BUY, down for
  SELL).

## Selection (per timeframe × side)

Splits are as in KR: tuning before 2018 (1W, 1D) or before 2024 (4H, 1H); the check period has
been studied before.

**Tuning period.** For each cut-off k ∈ {1, 2, 3} (draw only arrows with S ≥ k), compute the
right-rate. A cut-off is eligible if it keeps:
* ≥ 30 arrows;
* ≥ 20% of the arrows.

Choose the eligible k with the highest right-rate.

**Check period.** Adopt "strong only" for the cell only if the strong arrows' right-rate is ≥ the
right-rate of all arrows + 0.03. Otherwise that cell keeps all its arrows; nothing is filtered
without evidence.

**Reported per cell:** right-rate, zone and follow-through, arrows per instrument-year, coverage,
each component's effect on the tuning period, and equities vs crypto.

**Ledger trial:** `ks-all` (hypothesis KS-1).
