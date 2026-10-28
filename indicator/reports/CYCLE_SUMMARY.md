# HC-MTF Universal Market Cycle Engine (CY-1): summary

> **EXPLORATORY ONLY.**
> * Every candle used had been examined in earlier studies. Review mode is
>   `self_audited_exploration_only`.
> * There is no independent confirmation, and **no timeframe/direction passed the pre-registered,
>   multiple-testing-corrected test.**
> * Configuration: [`CYCLE_CONFIG.md`](CYCLE_CONFIG.md), frozen in `fa13907` before any cycle code
>   ran. Ledger trials `cy1-1W`, `cy1-1D`, `cy1-4H`, `cy1-1H`.
> * Full tables: [`CYCLE_RESULTS.md`](CYCLE_RESULTS.md). Raw output:
>   [`cycle_results.json`](cycle_results.json).

## What was tested

* **Labels.** The frozen major top/bottom labels, scaled per timeframe:
  * 1W: radius 26 candles, size 5 ATR;
  * 1D: 63 candles, 8 ATR;
  * 4H: 126 candles, 8 ATR;
  * 1H: 168 candles, 8 ATR.
* **Universe.** 108 instruments: crypto, equities/ETFs, commodities, bonds, FX.
* **Chronological splits.** Train, then validation (model selection only), then a single test:

  | TF | test period |
  |---|---|
  | 1W | ≥ 2016 |
  | 1D | ≥ 2020 |
  | 4H, 1H | ≥ 2022 |

* **Candidates.** Bounded set, tops and bottoms separately:
  * single-feature baselines: ATR extension from the cycle EMA, RSI, range position;
  * L2-logistic models on price structure, + momentum (RSI level/slope/fade, MACD
    histogram/acceleration), + volume (relative volume, volume trend, effort-vs-result, signed
    volume pressure), + interactions;
  * a gradient-boosting reference.
* **Context increments:** the higher-timeframe cycle position, and cross-sectional breadth
  (1D/1W).
* **Not tested:** dominance, TOTAL* and stablecoin series. They are not in the repository.

## Results (test period; zone = potential-reversal onset)

| TF · dir | shipped model (vol / no-vol) | test events | zone recall | zone precision* | FA / asset-yr | lead (candles, median) | lift [raw p] | Holm p | B_ext lift | confirmed precision* (EMA-cross matched) | confirmed: MFE / MAE (ATR, median) | confirmed net return mean (2× cost) |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|---|---|
| 1W · top | L_mom / L_mom | 245 | 0.38 | 0.21 | 0.43 | 2 | 0.94 [0.653] | 1.00 | 0.98 | 0.41 (0.53) | 1.31 / 2.30 | -4.83% (-4.89%) |
| 1W · bot | L_mom / L_price | 253 | 0.68 | 0.43 | 0.28 | 3 | 1.78 [0.042] | 0.29 | 1.86 | 0.50 (0.64) | 1.78 / 1.07 | 2.50% (2.44%) |
| 1D · top | L_mom / L_price | 424 | 0.41 | 0.25 | 0.78 | 9 | 1.10 [0.235] | 1.00 | 1.14 | 0.24 (0.46) | 2.47 / 2.62 | -1.00% (-1.09%) |
| 1D · bot | L_price / L_price | 451 | 0.59 | 0.29 | 0.99 | 7 | 1.31 [0.091] | 0.55 | 1.45 | 0.26 (0.44) | 2.47 / 2.35 | 0.83% (0.72%) |
| 4H · top | B_ext / B_ext | 864 | 0.56 | 0.41 | 2.16 | 13 | 1.17 [0.036] | 0.29 | 1.17 | 0.33 (0.36) | 3.00 / 3.52 | -2.32% (-2.46%) |
| 4H · bot | L_price+htf / L_price+htf | 916 | 0.63 | 0.35 | 3.37 | 21 | 0.96 [0.666] | 1.00 | 1.12 | 0.22 (0.33) | 3.03 / 3.15 | -0.62% (-0.78%) |
| 1H · top | L_price / L_price | 3189 | 0.71 | 0.43 | 8.65 | 20 | 1.01 [0.407] | 1.00 | 0.89 | 0.25 (0.33) | 3.93 / 3.99 | -0.32% (-0.48%) |
| 1H · bot | L_price / L_price | 3134 | 0.50 | 0.30 | 10.34 | 30 | 0.77 [1.000] | 1.00 | 0.79 | 0.16 (0.32) | 3.66 / 3.90 | -0.42% (-0.58%) |

* precision* = precision excluding duplicates.
* lift = how often a zone alert lands near a labelled turn, relative to random candles of the
  same instrument.
* Holm is over the 8 cells.
* "confirmed" compares the confirmation rule with an EMA20/50 cross thinned to the same
  frequency.

## What the evidence says

1. **Bottoms are more detectable than tops, mainly on the weekly and daily charts.**
   * Weekly bottom zones landed near a labelled major bottom 1.8x as often as random candles.
     That is 68% of bottoms caught, with 0.28 false alerts per asset-year, typically about 3
     weeks early.
   * With only 10 yearly clusters in the test it does not survive correction (Holm p 0.29).
2. **Tops were barely or not at all detectable** on 1W, 1D and 1H. 4H tops showed 1.17x
   (Holm p 0.29).
3. **Learning did not beat the simplest feature out of sample.**
   * The ATR extension from the cycle EMA (B_ext) matched or beat the learned models on 1W/1D
     bottoms and 4H.
   * The validation-chosen higher-timeframe context **hurt** 4H bottoms on test: hit rate -0.066
     vs B_ext, CI below 0.
   * Only at 1H tops did the learned model beat B_ext at matched rate (+0.055, p 0.001), and even
     there it was only at random level (lift 1.01).
   * Volume features, interactions, breadth and gradient boosting raised **validation** AP
     slightly but showed no consistent test advantage.
4. **The confirmation rule** (EMA21 cross after a D/4 ATR retreat) **was less precise than a
   plain EMA20/50 cross** at matched frequency in every cell.
5. **Trading view** (net of the per-class `COST_BPS`, 2x cost in brackets):
   * shorting confirmed tops lost money on every timeframe;
   * buying confirmed weekly/daily bottoms averaged +2.5% / +0.8%, with negative medians on daily;
   * 1H/4H were negative after costs.

   Turning-point detection and profitable trading are different questions; neither is
   established here.

## What ships

* **Model choice.** `pine/HC_CycleEngine.pine` implements the **pre-registered,
  validation-selected** models (config section 4), refit on train+validation, with their
  matched-rate thresholds. The test results were **not** used to switch models. Switching to the
  test winner would be test-set selection.
* **Mechanics.** The indicator computes exactly the research features and scores (coefficients
  generated from `cycle_model_spec.json` by `scripts/cycle_export_pine.py`; tested equal to the
  Python score). Zone, developing and confirmed stages follow the frozen mechanics.
* **Lower timeframes.** Charts below 1H use the 1H set and are **unvalidated**.
* **Context.** Context symbols (BTC.D, TOTAL2, USDT.D, SPY by default; configurable) are
  **display-only**. A missing symbol shows "n/a" and never feeds a signal.

## Limitations

* **Already-examined data and short tests.**
  * The weekly test has only about 10 yearly clusters, so power is low.
  * Crypto appears only from 2017 onwards, in validation and test only, at 1W/1D.
  * Non-crypto intraday data starts 2023-11, so it is test-only at 1H/4H.
* **Survivorship.** Equities are today's large caps; crypto pairs were chosen with hindsight.
* **Pine vs research.**
  * The volume model switches on a rolling 50-candle check, vs whole-history per instrument in
    research.
  * `ta.highestbars` tie-breaking is assumed to be most-recent.
  * Partial 4H candles are as in the V6 audit.
  * Neither difference was measured.
* **The Python mirror** proves score equality from features, not TradingView execution. The
  indicator has passed `pinewf pine-lint` (only known false positives), but has not been run on
  TradingView in this environment.

## Using the indicator

1. In TradingView: Pine Editor > paste `pine/HC_CycleEngine.pine` > Add to chart. The production
   HC-MTF indicator is unchanged.
2. The timeframe sets the scale automatically: 1W = major cycles, 1D = intermediate, 4H/1H =
   swings. Below 1H, the 1H set is used (unvalidated).
3. **Markers:**
   * small dot = potential zone;
   * triangle = developing;
   * TOP/BOT label = confirmed.

   All appear only on closed candles and do not repaint.
4. **Alerts:** add an alert with "Once per bar close" on any of the six conditions (potential,
   developing or confirmed top/bottom).
5. **Inputs:**
   * Sensitivity (Standard = researched threshold);
   * volume model (Auto/Off);
   * diagnostics table;
   * optional context panel (display-only).
