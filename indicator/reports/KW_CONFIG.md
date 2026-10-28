# KW: weekly-only improvement of Kenny's Divergence Indicator (exploratory)

**Status: FROZEN** (2026-10-28), before any KW code ran on market data.

**Scope.** The weekly chart only (bucket ≥ 1W). The daily and lower-timeframe engines are
unchanged. Data, guards and the universe are as in CY-2, KB and KC (EVAL instruments, weekly
candles, no reserved instruments, no post-freeze candles). All data was examined before.

**Tuning vs hold-out.**
* Thresholds are tuned on signals **before 2018** only. Results from 2018 onwards are reported
  separately as a hold-out period.
* The hold-out was examined in earlier research, so it is **not** genuinely unseen.
* Kenny's weekly scores (`cycle2_model_spec.json`) were fitted on all years and are shared by every
  variant, including the current one.

## Variants (`research/kenny_weekly.py`)

| id | BUY (major bottom) | SELL (major top) |
|---|---|---|
| W0 | current: High Conviction onset (B_ext), cooldown | current: Confirmed (GBZ), cooldown |
| W1 | KC cluster families on weekly (ext tiers, cnf, RSI/MACD divergence 5/5, price action, vol burst) | same families, mirrored |
| W2 | weekly families: ext tiers, drawdown-from-52w-high crossings (8 / 14 ATR), divergence 5/2, hammer at the 26-week low, RSI re-cross 35, capitulation; zone = Kenny zone **or** drawdown ≥ 8 ATR, and 52-week TSMOM ≤ 1 | ext tiers, cnf, rally-from-52w-low crossings (12 / 20 ATR), divergence 5/2, shooting star at the 26-week high, RSI re-cross 65 down; zone = Kenny zone **and** TSMOM ≥ 0.5 |

**Shared cluster mechanics** (no cooldown):
* novelty-limited family traces;
* opposite-evidence shrink κ = 0.5;
* minimum new evidence δ = 0.15;
* decay half-life h weeks;
* thresholds θ_BUY and θ_SELL tuned **separately**.

**Tuning grid**, per variant (W1, W2) and side, on pre-2018 signals:
* h ∈ {4, 8} weeks;
* θ ∈ {1.0, 1.5, 2.0, 2.5}.

**Objective**, per side:
* BUY: the median 26-week forward return;
* SELL: minus the median 26-week forward return (a top is good when price falls afterwards).

**Constraints:**
* ≥ 0.05 signals per asset-year;
* ≥ 25 signals before 2018.

The best (h, θ) per variant and side is then frozen and scored on 2018+ signals.

## Metrics

Per side, variant and period:
* signals and episodes per asset-year;
* forward returns at 13, 26 and 52 weeks (median and mean);
* 26-week MFE and MAE (%);
* distance from the eventual extreme: % above the lowest low (BUY) or below the highest high (SELL)
  within ±26 weeks;
* timing: weeks from that extreme to the signal (negative = before it);
* major-turn hit rate: the share of signals within the frozen 1W label warning window of a
  labelled major turn (CY-2 precision);
* barrier win rate;
* net return at 13 weeks after costs.

**Representative instruments** (listed before any run): BTCUSDT, ETHUSDT, SOLUSDT, SPY, QQQ, AAPL,
GLD. These are shown for chart review only and are never used for tuning.

## Adoption rule

A variant replaces W0 for a side if, in the **2018+ hold-out**:
* its median 26-week forward return is better than W0's;
* its major-turn hit rate is ≥ W0's − 0.05;
* it has ≥ 0.05 signals per asset-year.

If several variants qualify, the one with the better pre-2018 objective wins. BUY and SELL are
decided independently. Otherwise W0 stays.

**Ledger trial:** `kw-1W` (hypothesis KW-1).
