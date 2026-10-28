# HC-MTF Universal Market Cycle Engine: research configuration (CY-1)

**Status: FROZEN** (2026-10-28). Committed before any cycle-engine code ran on real data. No
cycle outcome had been computed. A change after outcomes needs a new version (CY-2) and new trial
ids. Review mode: `self_audited_exploration_only`. All data used has been examined before, so
every result here is **exploratory, not independent confirmation**.

## 0. Reuse map (from V5/V6; nothing below is re-run)

| finding | source | applies to cycle detection? |
|---|---|---|
| Single-feature warnings (extension ≥ 3 ATR, RSI divergence, failed breakout, volatility jump) had **no lift** over warm candles in the same HTF state, crypto + cross-asset, 1H/4H, tops | family C x1 | **Yes, as evidence against those exact single-feature rules at 1H/4H.** Not tested: 1D/1W, bottoms, learned combinations, volume features. These are the new work here |
| Engine CHoCH (`counter_reversal`) clusters after tops (lift ≈ 1.25) but is not more precise than EMA20/50 cross / HTF flip at matched frequency | family C | Yes: CHoCH alone is not a better confirmation; baselines are reused as comparators |
| BTC trend/volatility gates: no measurable increment on crypto continuation or reversal alerts | workstream M | Partly: BTC gating is not re-tested; BTC context is display-only in Pine |
| RSI/MACD "momentum" confluence on structure breaks: dropped | v2 screening | Only for the old structure-break signals |
| Raw MTF structure breaks / MAJOR / counter-HTF trade entries: rejected | V3/V4 | Old continuation engine only |
| HTF trend state alone: inconclusive; forward test frozen | V4.1 H6 | Not re-tested (forward test protected) |
| Stage-1 EMA/RSI/MACD continuation (V6) | V6 config | Not run; continuation, not cycles. Left pending, unchanged |

**Do not repeat** without a materially different formulation:
* fixed-threshold extension, RSI-divergence pivots, failed-breakout-within-5 and ATR-percentile-jump
  warnings as standalone 1H/4H top detectors;
* BTC-regime gating;
* RSI/MACD as a confluence filter on structure breaks.

**Reused unchanged:**
* `v5_data` guarded loader (freeze cut, integrity cut, reserve refusal);
* `v5_labels` frozen major top/bottom labels (1H L168/F336/D8, 4H L126/F252/D8,
  1D L63/F126/D8, 1W L26/F52/D5);
* `v5_eval` (`frozen_labels`, `score_alerts`, `detection_report`, `lift_units`), `v5_baselines`
  (EMA cross, Supertrend flip, HTF flip, counter_reversal, `thin`);
* `v5_inference` (wild cluster bootstrap), `v41.cluster_id` (calendar blocks), `v5_ledger`,
  `v5_manifest`, `v5_gate`;
* `hcmtf.ta` (Pine-identical TA), `hcmtf.htf.align` (completed-HTF-candle alignment).

**Data status.** All 108 exploration instruments (crypto 36, equities/ETFs 41, commodities 11,
bonds 8, FX 12) up to the 2026-10-27 freeze are already examined, so they are exploratory only.
Never read: `V5_RESERVE` instruments and post-freeze candles. Neither is needed or touched here.
Dominance, TOTAL*, USDT.D and other external series are **not in the repository**, so they are
not tested here (Pine: optional, display-only).

## 1. Data and chronological splits

* Instruments: `v5_data.EVAL_SYMBOLS` (108; BTC-USD duplicate excluded), loaded only via
  `v5_data.load`.
* Timeframes: 1W, 1D, 4H, 1H.
* Splits by candle open time. Each split's candles must have complete label windows inside the
  data:

| TF | train | validation (model selection only) | test (evaluated once, after refit on train+val) |
|---|---|---|---|
| 1W | < 2010-01-01 | 2010 – 2015 | ≥ 2016-01-01 |
| 1D | < 2016-01-01 | 2016 – 2019 | ≥ 2020-01-01 |
| 4H, 1H | < 2021-01-01 | 2021 | ≥ 2022-01-01 |

* Non-crypto 1H/4H history starts 2023-11, so it appears in test only. Crypto 1W appears in test
  only. That is cross-asset, out-of-period generalisation, stated as such.

## 2. Targets

**Labels.** The frozen `v5_labels` tops and bottoms per TF (L, F, D), unchanged.

**Training target.** The zone target for tops, per candle s: y = 1 if a labelled top t lies in
[s − L/4, s + L/2] (integer division). Bottoms use their own labels. Candles whose window or
label region is censored are excluded.

**Scoring.** Unchanged frozen `score_alerts` windows:
* warning kind (zone and developing alerts): an event in [s − L, s + L/2];
* confirmation kind: an event in [s − L, s].

## 3. Features (per candle, causal, `hcmtf.ta`; L = the TF's label radius; q = max(2, L//4))

| group | features |
|---|---|
| price | `ext_c` = (c − EMA_L)/ATR14; `ext_f` = (c − EMA21)/ATR14; `rng` = (c − LL_L)/(HH_L − LL_L); `slope` = (EMA_L − EMA_L[q])/ATR14; `since_hh` = bars since the L-bar high / L; `since_ll` likewise; `atr_rank` = percentrank(ATR14/c, 100)/100 |
| momentum | `rsi` = RSI14/100; `rsi_slope` = (RSI14 − RSI14[3])/100; `rsi_gap_hi` = (highest(RSI14, L) − RSI14)/100; `rsi_gap_lo` = (RSI14 − lowest(RSI14, L))/100; `hist` = MACD(12,26,9) hist/ATR14; `hist_acc` = (hist − hist[3])/ATR14 |
| volume (only where volume exists) | `relvol` = clip(log(v/SMA20(v)), ±3); `vtrend` = clip(log(SMA5(v)/SMA_L(v)), ±3); `effort` = clip(log(\|c − o\|/ATR14 + 0.05) − relvol, ±5); `vpress` = Σ10 sign(Δc)·v / Σ10 v |
| interactions | `rng·rsi_gap_hi`, `(1 − rng)·rsi_gap_lo`, `ext_c·relvol` |
| context (tested increments) | `htf_rng`: `rng` of the next-higher TF (`engine.LADDER`; 1W uses 1M), previous completed HTF candle via `hcmtf.htf.align`. `breadth` (1D/1W): share of same-class instruments with `rng` > 0.8 (tops) / < 0.2 (bottoms) on the **previous** candle date; undefined if fewer than 5 instruments report |

* Features are z-scored with train(+val) means and standard deviations, then clipped to ±5.
* A row with any undefined feature of a model is excluded for that model. **Missing is never
  0.**

## 4. Candidate models and the selection rule (bounded; fixed now)

Per TF × direction (tops and bottoms are separate models).

| id | score |
|---|---|
| B_ext | `ext_c` (tops) / −`ext_c` (bottoms) |
| B_rsi | `rsi` / −`rsi` |
| B_rng | `rng` / −`rng` |
| L_price | L2 logistic regression on price |
| L_mom | price + momentum |
| L_vol | price + momentum + volume (volume assets only) |
| L_int | L_vol + interactions |
| G_ref | HistGradientBoosting (depth 3, 200 iterations, learning rate 0.05) on L_vol features. Reference only; never shipped (not Pine-portable) |

* **Regularisation.** C ∈ {0.01, 0.1, 1} per logistic model, chosen by validation average
  precision (AP). Class weight balanced.
* **Volume.** Models that need volume are fitted and scored only on volume assets. The no-volume
  ship model (FX, and any feed without volume) is the best of B_* / L_price / L_mom under the
  same rule.
* **Selection on validation AP.** Among shippable models, take the highest AP. If a simpler model
  (order B_* < L_price < L_mom < L_vol < L_int) is within 3% (relative) of it, take the simplest
  such.
* **Context.** `htf_rng`, then `breadth` (1D/1W), are added to the selected model one at a time.
  Each is kept only if validation AP rises by ≥ 3% relative.
* The selected spec is refit on train+val. The test set is never used to choose anything.

## 5. Alert mechanics (identical for every model; Pine-portable)

c = max(2, L//4), m = L//2, D = the label size.

* **Zone onset (potential reversal):** p ≥ θ and max(p[i−c … i−1]) < θ. θ is set on train+val so
  that onsets per asset-year = 2 × labelled events per asset-year, per TF × direction ×
  volume group.
* **Developing:** the first candle within c candles after an onset with:
  * top: RSI falling, MACD histogram falling, and close < open;
  * bottom: the mirror.
* **Confirmed:** within m candles after an onset, let X be the extreme since the onset (top:
  highest high). The first candle with close < EMA21 **and** X − close ≥ (D/4)·ATR14 confirms
  (bottom mirrored). At most one per onset.

## 6. Evaluation (test split), per TF × direction

**Detection metrics** (`score_alerts` / `detection_report`), for zone onsets, developing and
confirmed alerts:
* events, recall, precision excluding duplicates;
* false alarms per asset-year;
* lead (median, IQR).

**After-signal movement.** MFE/MAE in ATR over m candles. For confirmed 1H/4H/1D alerts, the net
return at m after `COST_BPS` per class, plus a 2× cost sensitivity.

**Primary test** (8 cells):
* the lift excess of the shipped model's zone onsets (`lift_units`, warning kind, single
  stratum), using `cluster_mean_test` with calendar clusters (`cluster_id`: 1W 12 months, 1D 3,
  4H 2, 1H 1);
* Holm across the 8 cells;
* a cell is **SUPPORTED (exploratory)** if Holm p < 0.05, lift > 1, and zone precision excluding
  duplicates ≥ that of B_ext at matched rate;
* otherwise **NOT SUPPORTED**. An evaluable cell needs ≥ 30 test events, ≥ 3 instruments, and
  G ≥ 10.

**Reported, not decisive:**
* every candidate on test (transparency);
* the shipped model vs B_ext at matched rate (`cluster_diff_test` on alert-level `near`);
* confirmations vs EMA cross / Supertrend flip / HTF flip / counter_reversal thinned to the same
  frequency;
* splits by asset class, by test era halves and by `atr_rank` tercile.

## 7. Pine export

* Shipped coefficients, means, standard deviations and θ per (TF, direction, volume group) are
  generated into the new indicator `pine/HC_CycleEngine.pine` by `scripts/cycle_export_pine.py`.
* Parameter sets by chart TF: ≥ 1W uses 1W; ≥ 1D uses 1D; ≥ 4H uses 4H; otherwise 1H. Charts
  below 1H use the 1H set and are labelled **unvalidated**.
* The production `pine/HighConvictionMTF*.pine` stays unchanged.

## 8. Ledger

Trials `cy1-1W`, `cy1-1D`, `cy1-4H`, `cy1-1H` (hypothesis ids `CY-1W` … `CY-1H`), each recorded
and committed before its computation. Gate: `v5_gate.cy_blockers()`.
