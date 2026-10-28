# KB: benchmark library for Kenny's Divergence Indicator (exploratory)

**Status: FROZEN** (2026-10-28), before any KB code ran on market data.

**Question.** Which existing ideas materially improve Kenny's final BUY/SELL signals?

**Data and timing:**
* Same as CY-2 (`reports/CYCLE2_CONFIG.md`): 108-instrument universe, guarded loader, no
  reserved instruments, no post-freeze candles.
* All data was examined before, so every KB result is **exploratory**.
* Signals are indexed on the first closed candle on which they are knowable. Pivots are reported
  on their confirming candle. There is no lookahead.
* Test span = the CY-2 walk-forward years per TF. Learned components are refit per test year on
  earlier data, purged.

## 1. References inspected (ideas only; no code copied)

| # | reference | used for | not used because |
|---|---|---|---|
| 1 | Divergence for Many Indicators v4 (TradingView) | DIV: many oscillators, minimum count | source not on page; TradingView House Rules |
| 2 | LunqFX divergence (TradingView) | HID (hidden = continuation), engine count | no source on page |
| 3 | RSI and MACD Divergence (TradingView) | pivot 5, RSI14, MACD 12/26/9 defaults | – |
| 10 | divergence-signal-alerts-pine (GitHub) | pivots on the confirming bar; previous pivot 5..60 back, nearest first | PolyForm Noncommercial licence: logic re-implemented, no code reused |
| 4 | Alorse pinescript-strategies | PA: pin bar, engulfing / failed breakout; RSI 30/70 | no licence file: ideas only |
| 5 | QuantConnect trend-following | TREND: EMA50/200 regime + RSI pullback | portfolio and execution parts not relevant |
| 7 | futures-signal-metamodel | META: meta-labelling filter over primary signals | no validation or leakage detail; claims ignored |
| 8 | triple-barrier how-to | the barrier label | the project already has one (CY-2 §2) |
| 6 | time-series-trading-model | – | its own notes report degenerate models and test-set thresholds |
| 9 | QuantConnect LEAN | – | an engine, not a model; nothing to add |

Published performance figures are **not** evidence here.

## 2. Candidates

Per TF × direction. BUY = bottom, SELL = top. Fixed reference defaults; no tuning.

**Reference families (`research/kb_signals.py`):**
* **RSIX**: RSI14 re-crosses 30 up (BUY) or 70 down (SELL). Simple baseline.
* **B_ext**: ATR extension, CY-2 standard tier. Simple baseline.
* **DIV1 / DIV2**: regular divergence against the nearest previous confirmed pivot 5–60 candles
  back.
  * Pivots: left 5, right 5.
  * Oscillators: RSI14, MACD line and histogram, Stoch %K(14,3), CCI20, MOM10, and OBV for volume
    feeds.
  * DIV1 needs ≥ 1 oscillator; DIV2 needs ≥ 2.
* **HID**: hidden divergence in ≥ 2 oscillators (continuation).
* **PA**: any of the following:
  * failed breakout of the prior L-candle high or low (close back inside);
  * engulfing after a candle in the top/bottom 10% of the L range;
  * pin bar (wick ≥ 60% of the range) at a new L extreme.
* **TREND**: EMA50 > EMA200 and close > EMA200, with RSI re-crossing 40 up (BUY). Mirrored for
  SELL with 60.
* Every family has a cooldown: a signal is dropped if the same family fired in the previous
  c = max(2, L/4) candles.

**Kenny states.** Walk-forward onsets of the shipped CY-2 model per cell (`cycle2_model_spec.json`:
GBZ where promoted, else B_ext):
* **K_W**: warning tier;
* **K_S**: standard tier;
* **K_H**: high tier;
* **K_CONF**: the CY-1 confirmation rule after K_S.

**Kenny + idea:**
* **K_DIV / K_PA**: the first DIV1 / PA signal within m = L/2 candles after a K_S onset.
* **META**: a gradient-boosted signal-quality filter (meta-labelling).
  * Events: the union of K_S, DIV1, PA and TREND.
  * Features: CY-2 features plus family flags.
  * Label: the CY-2 barrier.
  * Model: depth 3, 60 trees, learning rate 0.1, min leaf 50, L2 1.0.
  * Refit per test year on events whose barrier window ended before that year; skipped with
    fewer than 300 training events.
  * An event is kept when p ≥ the median p of its training events.
* **K_META**: K_S events kept by the META model.

**As-shipped deduplication.** Every candidate is also scored after this step: drop candles where
BUY and SELL fire together, then drop same-direction repeats within c candles.

## 3. Metrics (identical for all candidates)

Scored on test-span alerts, in cycle2 `evaluate`, using the frozen **warning** window for every
candidate:
* events, recall, precision excluding duplicates, false alarms per asset-year, lead;
* alerts per asset-year;
* lift (calendar-cluster wild bootstrap);
* barrier win rate (target before adverse);
* MFE/MAE in ATR;
* net return after `COST_BPS` (and 2×).

Differences against **K_CONF** (the working default) use the calendar-cluster wild bootstrap, for:
* near rate;
* net return;
* barrier win rate.

## 4. Decision rules (reported with uncertainty, no significance gate)

**Material improvement** of a candidate over K_CONF in a cell requires all of:
* Δnet > 0 in both halves of the test years;
* Δwin > 0;
* the lower bound of the Δnear CI > −0.01;
* ≥ 0.05 alerts per asset-year.

**Adoption.** A Kenny + idea candidate is adopted into the final signal if it materially improves
on K_CONF in ≥ 5 of the 8 TF × direction cells.

**Default state.** One global default for the visible signal is chosen among K_W, K_S, K_H, K_CONF
and the adopted candidates:
* score: the best mean rank across the 8 cells of win rate, net mean and precision;
* constraint: ≥ 0.05 alerts per asset-year in every cell.

**Ledger trials:** `kb-1W`, `kb-1D`, `kb-4H`, `kb-1H`.
