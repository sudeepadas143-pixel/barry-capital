# Pre-registration: v3 validation (written before any v3 test was run)

Purpose: decide, with leakage-aware validation and an explicit correction for repeated
experimentation, whether the indicator's BULLISH and BEARISH signals have predictive value, per
timeframe, per side and per market group. Nothing in the signal engine is changed by this study;
it only measures. If a result is inconclusive it is reported as inconclusive.

## Configurations compared (all from the existing engine; nothing new is added)

| id | rule | role |
|---|---|---|
| C0 | every MTF structure break | simplest structural baseline |
| C1 | breaks with the HTFs (continuation + realignment) | = MAJOR + CONFIRMED |
| C2 | realignment with the HTFs | **= the shipped MAJOR signal** |
| C3 | continuation with the HTFs | = CONFIRMED |
| C4 | C2 + next-candle acceptance | shipped option |
| C5 | C1 + next-candle acceptance | |
| C6 | counter-HTF reversals (MTF change of character against the HTFs) | the reversals the HTF filter suppresses |
| B1 | EMA 20/50 cross | simple baseline |
| B2 | Supertrend(10, 3) flip | simple baseline |
| R | random entries, same symbols, dates, count and side | null baseline (p-values) |

Incremental-value questions, each answered by a paired comparison on identical data:
HTF gate = C1 vs C0; realignment restriction = C2 vs C1; acceptance = C4 vs C2 and C5 vs C1;
suppressed reversals = C6 vs C2 (and vs random).

## Outcome definition (unchanged from v1/v2, fixed)

Entry at the next candle's open after the signal candle closes. Horizon H: 1H 24, 4H 30, 1D 20,
1W 13 candles. Primary metric r_h = direction-adjusted move to the close of candle H, in ATR(14)
units, after round-trip costs (crypto 20 bp, commodities 8, equities 6, indices/bonds 4, FX 3).
Success (precision) = +2 ATR reached before −1 ATR; false positive = −1 ATR first (stop wins a tie,
gaps fill at the open). Also reported: forward return %, MFE/MAE, signals per symbol-year.

## Data

All 70 symbols (30 DEV + 40 FRESH incl. delisted coins), 1H/4H/1D/1W, from 2010 (1D/1W) or 2020
(1H/4H). Market groups: crypto; equities (stocks + index ETFs); commodities; rates & FX (bonds, FX)
reported separately. Regimes at entry (per asset, Regime Detector logic: ATR-percentile ≥ 80 =
volatile, ADX < 20 = range, else trend up/down by EMA(100) and its 20-bar slope).

## Leakage-aware validation

* **Combinatorial purged CV** (`purgedcv.CombinatorialPurgedCV`, 6 groups, 2 test groups → 15
  splits, 5 paths, embargo 1%, label end time t1 = entry + H candles). Rules are not fitted, so
  CPCV is used for the *selection* question: in every split the configuration with the best train
  mean r_h is "chosen" and its test result recorded. Reported: OOS mean r_h of the chosen
  configuration per path, and how often the shipped C2 is the chosen one.
* **Probability of backtest overfitting** (`finlab.pbo.probability_of_backtest_overfitting`, CSCV,
  16 partitions) on the matrix of monthly mean r_h of all candidate configurations C0–C6.
* **Deflated Sharpe ratio** (`finlab.stats.deflated_sharpe`) for each configuration's monthly
  series, with n_trials = **60**: an honest upper count of configurations tried across v1
  (threshold grids), v2 (14 screened components, tier designs) and v3 (this list).

## Success criteria (per timeframe × side × market group)

DEMONSTRATED requires all of:
1. mean r_h > 0 and beats random entries at Holm-adjusted p < 0.05 (Holm over every
   timeframe × side × group test of C2 in this study);
2. deflated Sharpe ratio > 0.95;
3. positive OOS mean in at least 4 of the 5 CPCV paths;
4. beats C0 (every structure break) on the same events' dates.

PROMISING: mean r_h > 0 and beats random at unadjusted p < 0.10. UNPROVEN: otherwise.
PBO ≥ 0.5 means picking among these configurations by past performance is not reliable; it is
reported for every timeframe and overrides any "best configuration" language.

## Independent tools and their roles

| repository | licence | role here |
|---|---|---|
| backtesting.py (kernc) | **AGPL-3.0** | Independent trade-level re-simulation, long and short separately, per symbol and timeframe; kept in `crosscheck/`, never imported by `hcmtf` or shipped. |
| purgedcv (landtml) | MIT | Combinatorial purged CV splits with label end times and embargo. |
| finlab-ml (landtml) | MIT | PBO (CSCV), deflated Sharpe, triple-barrier labelling cross-check. |
| pinescript-strategy-template (baronguyen001) | MIT | `pinewf pine-lint` on the Pine files; Monte Carlo on trade lists; reference for a `strategy()` twin of the indicator for TradingView's Strategy Tester. |

## Amendment 1 (before any v3 result was computed)

* `purgedcv` requires a unique time index, and pooled events share timestamps across symbols, so
  CPCV runs on time buckets of pooled events (weeks for 1H/4H, months for 1D/1W); a bucket's label
  end time t1 is the bucket end plus the horizon.
* A fixed rule such as C2 sees identical data in every CPCV path, so criterion 3 is applied to the
  6 chronological CPCV groups instead: **C2's mean r_h must be positive in at least 4 of the 6
  groups**. The CPCV paths are used, as stated, for the selection question.
