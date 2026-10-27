# V5 family C (major tops): first exploration configuration, 1H/4H

**Status: FROZEN** (2026-10-27).

* **Frozen in a commit of its own**, after the self-audit (`V5_SELF_AUDIT.md`) and before any
  detector code was written or any detector outcome computed.
* **Review status.** External review is UNAVAILABLE (`V5_REVIEW_WAIVER.md`). This configuration
  therefore runs in mode `self_audited_exploration_only`, and its results can support no G2/G3
  step until an independent review exists.
* **No changes after freezing.** Nothing in this file may change once any outcome is computed.
  A defect found afterwards needs a logged amendment and a re-run of every trial under new ids.

* **Drafted from** the register, the protocol, the audit and first principles. No detector output
  has been computed. The only data-derived information seen is:
  * the label base rates in `V5_DATA_AUDIT.md` §5 (counts of targets, not of detectors);
  * the earlier V3–V4.1 results for related ideas (H3 counter-HTF reversals rejected as trade
    entries; liquidity sweeps failed as a confluence filter).
* **Kind of study**: exploration on already-examined data. Nothing here can demonstrate an edge.
  A variant that survives goes to G2 and then to the reserved data.

## 1. Data and universe

| item | value |
|---|---|
| instruments | `research.v5_data.EVAL_SYMBOLS` **minus FX**: 96 instruments. Crypto 36; equities 41 (stocks, index/sector/country ETFs); commodities 11 (ETFs); rates 8 (bond ETFs: EMB, HYG, IEF, LQD, MUB, SHY, TIP, TLT) |
| excluded | BTC-USD (duplicates BTCUSDT); all 12 FX pairs (§1.1) |
| timeframes | 1H and 4H charts. HTFs from `engine.LADDER`: 1H → 4H/1D, 4H → 1D/1W |
| loading | `research.v5_data.load` only: cache only, closed-candle freeze cut, integrity cut, incomplete RTH 4H edge dropped |
| window | crypto from 2020-01-01 (or listing) to the last candle closing by the freeze. Non-crypto intraday starts 2023-11-28 (Yahoo limit) |
| data identity | `reports/V5_EXPLORATION_DATA_MANIFEST.json`, combined sha256 `57e107b08c6912a08042639c633604b90e612a60e06fe024b88b84a20e40530d`. `research.v5_manifest.verify()` must return no missing, changed or extra file at the start of every trial |

### 1.1 Why FX is excluded

FX higher-timeframe states on 1H/4H read Yahoo daily candles. Their session boundary cannot be
reproduced exactly from Yahoo hourly bars. The best fit is the 00:00–24:00 UTC day, but with a
median high/low error of 2–7·10⁻⁴ (audit U2). A few hours of overlap with the next day, and so
of look-ahead, cannot be ruled out. Causal alignment is therefore **not demonstrably safe**, and
FX stays out until either:

* FX daily candles are rebuilt from the hourly feed (a declared state-source change, in a new
  configuration version); or
* a vendor with documented session boundaries is used.

## 2. Market state and targets

| item | value |
|---|---|
| state | `research.v5_state.classify` with the default `StateConfig` (direction, ADX strength, ATR% tercile, extension) |
| labels | frozen `research.v5_labels.TOP_PARAMS` (1H: L 168, F 336, D 8 ATR14; 4H: L 126, F 252, D 8). Unchanged since commit `7fc7e68` (test P2) |
| alert windows | warning: an event t may be claimed if t ∈ [s−K, s+W]; confirmation: t ∈ [s−K, s]; K = L, W = L/2 (`v5_eval.windows`) |
| censoring | `v5_eval.score_instrument`: events outside [L, n−1−max(L, F)] and alerts whose window leaves that region are excluded and counted |
| matching | one-to-one, earliest unclaimed event (`v5_eval.match_alerts`); duplicates counted apart from false alarms |
| eligibility | an alert counts only on a candle where `state.warm` is True. Lift benchmark candles: warm and scorable candles of the same instrument |

## 3. Detectors (side = bearish; all causal, closed candle; one alert per candle; no cooldown)

Every parameter below was fixed before any detector existed. The rationale is given; none were
chosen from data. Variants are labelled; **no other variant may be evaluated under this
configuration version.**

| id | register | role | definition (at chart candle i) | parameters and rationale |
|---|---|---|---|---|
| C1a | C1 | W | `extension_atr[i] ≥ 3` and `extension_atr[i−1] < 3` and `direction_label[i] == "bull"` | 3 ATR = the `far_above` cut already fixed in `v5_state` |
| C1b | C1 | W | `direction_label[i] == "bull"` and `extension_atr[i]` ≥ the 95th percentile of the previous 500 defined `extension_atr` values (strictly before i), and not so at i−1 | 95th percentile and 500 candles are conventional; needs 500 prior values |
| C2 | C2 | W | when a pivot high at p = i−3 is confirmed at i (`ta.pivots`, left 5, right 3), compare with the latest earlier confirmed pivot high p₀ with p − p₀ ≤ 100: fire if `high[p] > high[p0]`, `RSI14[p] < RSI14[p0]` and `direction_label[i]` ∈ {bull, neutral} | pivots = the engine defaults for 1H/4H; RSI14 standard; 100-candle limit keeps the two pivots in one swing |
| C3 | C3 | W **and** C (two trials) | track the latest confirmed swing high level S (`ta.pivots` 5/3). After a close above S at b, fire at the first i ∈ (b, b+5] with `close[i] < S`; at most once per breakout | k = 5 candles: a breakout that fails within a few candles |
| C4 | C4 | W | `extension_atr[i−1] ≥ 1`, `close[i] < open[i]` and `vol_pct[i] − vol_pct[i−5] ≥ 33.3` | one volatility tercile of increase within 5 candles, on a down candle, after an extended advance |
| C5a | C5 | C | a warm bearish change of character at i (`hcmtf.engine.breaks`, shipped DEFAULTS, `dir == −1`, `choch`), with `direction_label[i]` ∈ {bull, neutral} and at least one of C1a, C1b, C2, C3, C4 fired in [i−50, i−1] | 50 candles ≈ 2 days (1H) / 8 days (4H) |
| C5b | C5 | C | the same change of character **without** the warning precondition (ablation of C5a) | isolates what the warning adds |

**Code.** The detectors are to be implemented in `research/v5_detect_c.py` after this
configuration is frozen, with truncation (causality) tests on synthetic data. They must import
nothing from `research/v5_labels.py` (test P1).

## 4. Baselines (confirmations only)

`research.v5_baselines.generate(..., side = −1)`:

* **htf_flip** — bearish HTF-state onset;
* **ema_cross** — EMA20 crosses below EMA50;
* **supertrend_flip** — Supertrend(10, 3) flips down;
* **counter_reversal** — engine counter-HTF bearish change of character.

Each baseline is reported twice:

* **unthinned**;
* **at matched frequency**: `v5_baselines.thin` per (instrument, calendar block), 50 seeded
  replicates. Metrics are averaged over replicates, with the replicate 2.5–97.5% range. The
  shortfall (blocks where a baseline fired less often than the detector) is reported; the method
  never pads.

## 5. Metrics

**Detection** (`v5_eval.detection_report`, per TF × group and pooled):

* events, alerts and the censored counts;
* recall, strict precision, precision excluding duplicates;
* duplicates and false alarms, with false alarms per 100 candles and per instrument-year;
* lead time: median, IQR and cluster CI;
* move remaining: median and share > 0.5.

**Lift** (`v5_eval.lift_report`): stratum = `direction_label`. Lift and the excess "event in
window" rate over warm, scorable candles of the same instrument and state.

**Trading** (secondary, confirmations only; `v5_eval.trade`):

* short entry at the next open;
* stop = the highest high of candles i−19 … i;
* time exit after 2H (1H 48 candles, 4H 60);
* costs per `v5_costs` (no FX, so no unavailable costs);
* r_h excess over the **causal** benchmark (`v5_eval.causal_benchmark`, stratum
  `direction_label`, `min_history` 200) as primary, with the whole-window benchmark secondary.

Detection and trading metrics are reported in separate tables.

## 6. Uncertainty

| item | value |
|---|---|
| clusters | calendar blocks shared by all instruments: 1H 1 month, 4H 2 months |
| primary test | `research.v5_inference.cluster_mean_test` (wild cluster bootstrap with the null imposed; Rademacher if G ≥ 12, Webb otherwise; 9,999 replicates; seed 20261027). Applied to the per-unit lift excess (alerts) and r_h excess (trades); one-sided H1: excess > 0 |
| interval | t(G−1) CI from the same function |
| secondary | the percentile cluster bootstrap of `v5_eval` (5,000 replicates), reported for continuity with V4.1 |
| deciding | cells with G < 10 clusters are reported and never used for a decision. Evaluability minimums as in `v5_eval`: ≥ 30 events, ≥ 3 instruments, ≥ 8 event clusters; the G ≥ 10 rule applies on top |

This section uses the method of **proposed** protocol Amendment 1
([`V5_PROTOCOL_AMENDMENT_1.md`](V5_PROTOCOL_AMENDMENT_1.md)) for an *exploration* decision rule
only. It does not adopt the amendment for confirmatory use.

## 7. Multiple testing and trial accounting

* **Exploration makes no confirmatory claim.** Every cell is reported. A Holm adjustment over
  all family-C lift tests in this configuration (detector × kind × TF × group) is reported as
  information. It is not used for selection, which follows §8.
* **Trials** (18, all with `outcomes_accessed = True`), recorded through
  `research.v5_ledger.record` with `config_file = reports/V5_C_EXPLORATION_CONFIG.md` and
  `data_files` from `research.v5_manifest.files_for`:

  | group | trial ids | hypothesis id |
  |---|---|---|
  | warnings | `c-x1-C1a-W-1H`, `c-x1-C1a-W-4H` | C1 |
  | | `c-x1-C1b-W-1H`, `c-x1-C1b-W-4H` | C1 |
  | | `c-x1-C2-W-1H`, `c-x1-C2-W-4H` | C2 |
  | | `c-x1-C3-W-1H`, `c-x1-C3-W-4H` | C3 |
  | | `c-x1-C4-W-1H`, `c-x1-C4-W-4H` | C4 |
  | confirmations | `c-x1-C3-C-1H`, `c-x1-C3-C-4H` | C3 |
  | | `c-x1-C5a-C-1H`, `c-x1-C5a-C-4H` | C5 |
  | | `c-x1-C5b-C-1H`, `c-x1-C5b-C-4H` | C5 |
  | unthinned baselines | `c-x1-baselines-1H`, `c-x1-baselines-4H` | C5 (comparators) |

* **Commits.** The ledger is committed after every trial (`verify_against_git` must pass before
  the next).

## 8. Variant-selection rule for G2 (fixed now)

1. **Eligible.** A detector × kind with at least one TF in which ≥ 2 groups have evaluable cells
   with G ≥ 10.
2. **Score.** The lower bound of the pooled t(G−1) 95% CI of the lift excess in its best eligible
   TF.
3. **Requirements**, all needed:
   * pooled wild-bootstrap one-sided p < 0.05;
   * for warnings, pooled median lead time > 0;
   * for confirmations, pooled median move remaining ≥ 0.5, and precision excluding duplicates ≥
     the best matched-frequency baseline's (replicate mean) in the same TF.
4. **Choice.** The ≤ 3 highest scores among those meeting all requirements, ties broken by
   higher precision excluding duplicates. Selected variants go to G2 **exactly as specified in
   §3**, with no parameter changes.
5. **If none qualifies**, family C at this configuration version is recorded as **REJECTED at
   exploration** or **REDESIGN**. A redesign is a new configuration version with new trial ids;
   the trial count carries over and is disclosed.

## 9. Rejection criteria at exploration (per detector × kind)

A detector × kind is **dropped** if, in every evaluable cell, either:

* the t(G−1) 95% CI of the lift excess lies entirely below 0 (lift < 1); or
* (warnings) the median lead time is ≤ 0.

All other non-selected variants are **inconclusive**, and are not re-tested under a new name
without a new version.

## 10. Integrity checklist (each trial)

1. `research.v5_gate.require_c_ready()` passes. That requires:
   * the external review approved;
   * this file frozen;
   * the manifest committed and matching the cache;
   * baselines and detectors committed and unmodified.
2. The full test suite passes on the commit being run; the commit is recorded in the ledger.
3. `research.v5_manifest.verify()` reports no differences.
4. Ledger: append, then commit; `verify_against_git` passes.
5. Disclosures stay as written: exploratory data, prior related results seen, label counts seen.

## 11. Freezing clarifications

These were resolved before freezing (self-audit SA2) and are binding. Every detail the draft left
implicit is fixed here.

* **F1 (C1b percentile).**
  * pct_i = 100 · #{j ∈ [i−500, i−1] : ext[j] ≤ ext[i]} / 500, where ext = `extension_atr`. This
    is `hcmtf.engine.percentrank`, defined only when all 500 previous values are defined.
  * Fire when (bull and pct_i ≥ 95) holds at i and does not hold at i−1.
* **F2 (C2 divergence).**
  * Pivots: `hcmtf.ta.pivots(high, low, 5, 3)`. A pivot high at p is known at i = p + 3.
  * p₀ is the latest earlier pivot high (p₀ < p). If p − p₀ > 100 there is no comparison and no
    alert.
  * RSI is `hcmtf.ta.rsi(close, 14)`, read at p and p₀.
  * Fire at i when high[p] > high[p₀], RSI[p] < RSI[p₀] and `direction_label[i]` ∈ {bull, neutral}.
* **F3 (C3 failed breakout).**
  * S is the price of each confirmed pivot high (`ta.pivots` 5/3). A level can be broken once:
    the first candle b after S is known with close[b] > S is its breakout.
  * Fire at the first i ∈ [b+1, b+5] with close[i] < S.
  * Several pending breakouts are tracked independently; one alert per candle.
  * No state condition.
  * The same alert set is scored as warning (trial `…-W-…`) and as confirmation (trial `…-C-…`).
* **F4 (C4).** `vol_pct` is the `v5_state` ATR%-percentile against the previous 200 candles.
  Fire when ext[i−1] ≥ 1, close[i] < open[i] and vol_pct[i] − vol_pct[i−5] ≥ 33.3. NaN gives no
  alert.
* **F5 (C5a / C5b).**
  * Change of character: `hcmtf.engine.breaks(engine.features(Ctx(df, htf1, htf2, None,
    asset.volume, is_crypto)), DEFAULTS[tf])` rows with dir = −1, choch = True, warm = True;
    `direction_label[i]` ∈ {bull, neutral}.
  * C5a additionally needs an eligible C1a, C1b, C2, C3 or C4 alert at some j ∈ [i−50, i−1].
* **F6 (eligibility and window).**
  * Every detector **and every baseline** alert is kept only on candles with `state.warm` True,
    and only with candle open time ≥ 2020-01-01.
  * Labels and scoring use `v5_eval.score_alerts(…, start_i)` with start_i = the first candle at
    or after 2020-01-01 (non-crypto data begins 2023-11-28 anyway).
* **F7 (groups).** crypto; equities; commodities; rates (the 8 bond ETFs); pooled = all 96.
* **F8 (evaluable).** A cell decides only if all three hold:
  * `detection_report.evaluable` (≥ 30 scorable events, ≥ 3 instruments, ≥ 8 event clusters);
  * ≥ 30 lift units;
  * G ≥ 10 lift-unit clusters.

  Other cells are reported only.
* **F9 (lift test).**
  * Units: `v5_eval.lift_units(…, state = direction_label, warm = state.warm, start_i)`.
  * Per-unit excess goes to `v5_inference.cluster_mean_test` (one-sided greater; clusters =
    calendar blocks of the alert candle; 9,999 replicates; seed 20261027).
  * lift = mean(near) / mean(bench).
  * Secondary: percentile cluster bootstrap of the mean excess (`v5_eval._ratio_ci`, 5,000
    replicates).
* **F10 (trading, confirmations only).**
  * `v5_eval.trade(o, h, l, c, index, i, side=−1, hold=2H, stop=max(high[i−19..i]), asset_cls,
    funding=v5_data.load_funding(sym))`; mean and median net with cost sources.
  * r_h = the register outcome at H (short; `hcmtf.evaluate.bar_outcomes`, round-trip costs
    only).
  * Excess over `v5_eval.causal_benchmark` (warm candles, stratum `direction_label`, horizon H,
    `min_history` 200) through `cluster_mean_test` is primary. The whole-window benchmark
    (`v5_eval.excess`) is secondary.
* **F11 (baselines).**
  * For each confirmation trial and TF, each baseline (after F6 eligibility) is thinned to that
    detector's eligible alerts per (instrument, calendar block). 50 replicates, seed 20261027.
  * Replicate means of recall, strict precision, precision excluding duplicates, false alarms
    per 100 candles, median lead and median move remaining, each with its 2.5–97.5% range.
  * Unthinned baselines are scored as confirmations in trials `c-x1-baselines-<TF>`.
* **F12 (selection).** §8 applied per TF; "best eligible TF" = the TF with the highest score.
* **F13 (Holm).** `hcmtf.metrics.holm` over the `p_wild` of all evaluable non-pooled cells.
  Reported, not used for selection.
* **F14 (ledger).**
  * The 18 trials of §7, each recorded **before** its computation (`outcomes_accessed = True`).
    The ledger is committed after each trial.
  * `data_files` = the 1h and 1d cache files of the 96 instruments.
  * `code_files` = `research/v5_detect_c.py`, `v5_eval.py`, `v5_baselines.py`, `v5_state.py`,
    `v5_data.py`, `v5_inference.py`, `v5_costs.py` and the runner script.
* **F15 (outputs).** `reports/v5_c_x1_results.json` and `reports/V5_C_EXPLORATION_RESULTS.md`,
  reporting every variant and every baseline, whatever the outcome.
