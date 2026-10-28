# V5 validation protocol

How every V5 signal family moves from idea to release. It applies to each family on its own:

* A, bullish continuation;
* B, bearish continuation;
* C, major tops and bearish reversals;
* D, major bottoms and bullish reversals.

Only after that is the combined system (E) evaluated. **Any family may be rejected or redesigned
at any gate. The product goal is four useful signal types if the evidence allows, not four
outputs regardless of evidence.**

Inherited methods are kept where V3/V4/V4.1 showed they work: next-open entry, ATR-normalised
outcomes after costs, calendar-block cluster bootstrap with benchmarks re-estimated per replicate
(`research/v41.py: boot_excess`), Holm, purged chronological spans, and medians as co-primary.
Methods V4 showed to be flawed are dropped: iid random-entry p-values, the ±2H local control, and
deflated Sharpe on bucket means read as a multiple-testing correction.

## 1. Gates

| gate | name | entry condition | what happens | exit |
|---|---|---|---|---|
| G0 | registered | hypothesis in `V5_HYPOTHESIS_REGISTER.md` with role, benchmark and falsifier | none | — |
| G1 | exploration | G0 | detectors built and iterated **on exploration data only** (`research.v5_reserve.exploration_only`); every evaluated variant logged in `V5_TRIAL_LEDGER.md` | the family proposes ≤ 3 variants, or is **dropped** (allowed; recorded) |
| G2 | frozen | G1 variants | per-family confirmatory pre-registration committed: variants, parameters, cells, benchmarks, costs, horizons, sample minimums, decision rule, code sha256 | — |
| G3a | cross-sectional check | G2 | **one** run on the V5 reserve instruments' history (same calendar period; not confirmation) | pass → G3b; fail → reject, or redesign starting again at G1 with a new family version |
| G3b | forward confirmation | G3a pass, forward data at the minimum size (§5) | one run on forward candles of all 154 instruments | pass → G4; fail → reject. **No re-tuning on forward data** |
| G4 | combined system | ≥ 1 family passed G3b | state machine (E) evaluated as a whole, conflicts and duplicates measured | pass → G5 |
| G5 | Pine port | G4 | port only the passed logic; parity and execution checks (§7) | release |

Before G3b exists (that is, until enough forward data accumulates), the strongest possible status
is "G3a passed: retained for forward testing". Documents must use that wording and must not claim
an edge.

## 2. Data roles

As in [`V5_DATA_AUDIT.md`](V5_DATA_AUDIT.md):

* **Exploration**: the 108 instruments plus BTC-USD, candles opening at or before
  2026-10-27 23:59:59 UTC.
* **Reserved cross-sectional**: the 46 V5 reserve instruments, all dates.
* **Reserved forward**: every instrument, candles after the freeze.

The frozen V4.1 H6/H7v forward test is evaluated only by its own pre-registration; V5 never
modifies or pre-empts it.

## 3. Statistics per family

### Continuation, families A and B

* **Unit**: a signal.
* **Outcome**: r_h at H (1H 24, 4H 30, 1D 20, 1W 13), with secondary H/4 and 2H.
* **Primary statistic**: mean excess over the **matched benchmark** for the same instrument, side
  and state, and the same pullback-depth band (A) or rally/range state (B); see the register.
* **Also reported**:
  * excess over S (all state candles) and over M (ROC20 trigger);
  * median excess;
  * mean without the top 1%;
  * MFE/MAE;
  * +2/−1 barrier rates;
  * signals per instrument-year;
  * trade-level results with a structural stop and a 2H time exit (CAGR, Sharpe with a
    block-bootstrap CI, max drawdown, worst 1% of trades).
* **Family B also reports**: the squeeze tail (share of MAE ≥ 3 ATR, gap-through-stop rate,
  worst 1%), after the short costs of §4.

### Tops and bottoms, families C and D

Scored against the frozen labels of register §2.2.

* **Warnings (W)** report:
  * recall;
  * lead time (median and IQR);
  * false-alarm rate per 100 candles and as a share of warnings;
  * **lift**: P(labelled event in window | warning) divided by the same probability for random
    warnings at matched frequency in the same HTF state.
* **Confirmations (C)** report:
  * precision, recall and lift (as for W);
  * **move remaining after confirmation**: median and the share with > 0.5;
  * the trade outcome r_h (short for C, long for D) after costs.

  Every confirmation statistic is compared with the baselines: HTF state-flip onset, EMA20/50
  cross, Supertrend(10, 3) flip and engine `counter_reversal`, **at matched signal frequency**.

### Every family

Results are reported per TF × group × side:

* n signals, instruments, clusters, signal frequency;
* the regime split: causal volatility tercile × HTF state × the three purged chronological spans;
* asset dependence: the leave-one-instrument-out range of the primary statistic, and the share of
  the total contributed by the single largest instrument.

## 4. Costs

| item | value |
|---|---|
| round trip, all families | unchanged: crypto 20 bp, equities 6, index/sector ETFs 4, commodities 8, bonds 4, FX 3 |
| equity / ETF short borrow (family B, C trades) | 1.0% a year on general collateral, applied per candle held. Hard-to-borrow fees are not modelled (stated as a limitation) |
| crypto short | perp funding where cached (9 coins: the actual funding paid or received); otherwise a conservative 10% a year charge |
| FX | carry not modelled (stated) |
| gap risk | stops fill at the open when gapped (unchanged) |

## 5. Sample minimums and dependence

* **Cluster length**: calendar blocks shared by all instruments in a cell (1H 1 month, 4H 2
  months, 1D 3 months, 1W 12 months). Residual overlap across block edges is disclosed.
* **A cell is evaluable** with ≥ 100 signals (C/D: ≥ 30 labelled events in the cell),
  ≥ 3 instruments and ≥ 8 clusters with signals.
* **G3b minimum forward size**: the first date at which at least two groups have evaluable cells
  for the family. Rough expectation from `V5_DATA_AUDIT.md` §5: 1H ≈ 8–12 months, 4H ≈ 2 years,
  1D ≥ 3 years, 1W not within this decade.
* **No interim peeks.** The forward test runs once, at the registered date.

## 6. Acceptance criteria (fixed now; restated and frozen per family at G2)

* **Minimum effect of interest (MEI)**: 0.10 ATR per H-horizon after costs, for r_h-based
  statistics.
* **"Passing cell" for A and B**:
  * Holm-adjusted p < 0.05 within the family;
  * mean excess over matched ≥ MEI;
  * median excess > 0;
  * mean excess > 0 in ≥ 2 of 3 purged spans;
  * excess over M ≥ 0;
  * B only: the squeeze tail does not turn the mean negative without its worst 1%.
* **"Passing cell" for C and D confirmations**:
  * lift over matched-frequency random confirmations with a Holm-adjusted CI above 1;
  * median move remaining ≥ 0.5;
  * precision ≥ the best baseline's precision at the same signal frequency;
  * trade r_h after costs: mean ≥ MEI and median > 0.
* **"Passing cell" for C and D warnings**:
  * lift CI above 1 (Holm);
  * median lead time > 0;
  * a false-alarm share reported, with no threshold, but published with the marker.
* **A family passes a gate** when, in at least one TF, at least two asset groups have passing
  cells. Fewer than that is reported as narrow (e.g. crypto-only) and may be released only with
  that scope stated on the chart.
* **Rejection.** A family is **rejected** when no cell passes and the pooled CIs exclude effects
  ≥ MEI. Otherwise it is "inconclusive" and stays unreleased.

## 7. Pine implementation and release checks (G5)

1. **Python mirror.** A Pine-transliteration test for every ported detector, as
   `tests/pine_mirror_v2.py` does today.
2. **Closed-candle and truncation tests.** Every signal is final on the candle it prints.
   * HTF values come from `request.security(..., f()[1], lookahead = barmerge.lookahead_on)` only.
   * The LTF comes from `request.security_lower_tf` candles inside the closed chart candle.
3. **TradingView export parity.** Parity plots, an "Export chart data", and
   `scripts/compare_tv_export.py` on at least one instrument per group and timeframe. Every
   disagreement is explained before release.
4. **Strategy twin.** The V4 F5a stop/clock reset on same-direction signals is fixed first. Then
   a TradingView List-of-Trades export is compared with `evaluate.simulate`.
5. **Duplicates and state.** For each family:
   * at most one marker per signal;
   * the cooldown and conflict rules of the state machine are proven by tests (no simultaneous
     opposite markers on one candle, no repeated marker within its cooldown);
   * early warnings and confirmations use distinct markers **only if** register E2 passed.
6. **Production stays as is until G5 passes.** `pine/HighConvictionMTF.pine` and
   `HC-MTF_TradingView.txt` stay byte-identical until then; `git diff` against the last release
   commit is recorded in each report.

## 8. Reporting

Every result document states:

* which data role it used;
* exploratory or confirmatory;
* the trial count;
* commands and code sha256;
* failures and inconclusive cells, with the same prominence as passes.

A passing software test is never presented as evidence of predictive value.

## Amendments

| no. | subject | status | document |
|---|---|---|---|
| 1 | small-cluster inference: wild cluster bootstrap and t(G−1) as the decision statistics; G ≥ 10 for exploratory decisions and G ≥ 20 for confirmatory cells | **exploration scope ADOPTED 2026-10-27 (v1.1-exploration); confirmatory scope NOT ADOPTED** (needs independent review before any G3) | [`V5_PROTOCOL_AMENDMENT_1.md`](V5_PROTOCOL_AMENDMENT_1.md) |
| M1 | workstream M (crypto-only, stages A/B): universe of 35 non-BTC cached crypto pairs with point-in-time eligibility; per-pair reporting; Δ test with time clusters (calendar blocks and BTC episodes, larger p decides); Holm within each hypothesis, with all-cell Holm as a sensitivity | **exploration scope, 2026-10-27**; no confirmatory scope | [`V5_M_B_CONFIG.md`](V5_M_B_CONFIG.md) |
| V6-1 | HC-MTF 6.0 stage 1 (crypto continuation, models A–D): E1–E6 eligibility, slippage 10/20 bp by liquidity rank, Holm within four families that include every predefined alternative (20/28/36/28 cells) with all-112-cell Holm as a sensitivity, robustness to trimming the top 5% of moves and dropping the best pair | **exploration scope, 2026-10-28**; no confirmatory scope | [`V6_CONT_CONFIG.md`](V6_CONT_CONFIG.md) |
| V6-A1 | HC-MTF 6.0 stage 1: four implementation clarifications (trading-median test; gap at the touch candle; name-keyed seeding; shared trades), recorded 2026-10-28 before any V6 outcome; text below and in the hypothesis register | **in force for V6 stage 1** (exploration scope); thresholds unchanged | [`V5_HYPOTHESIS_REGISTER.md`](V5_HYPOTHESIS_REGISTER.md) |

### Amendment V6-A1 (2026-10-28): four implementation clarifications of `V6_CONT_CONFIG.md`, recorded before any V6 outcome

**Scope.** These clarifications do **not** edit the frozen configuration file. They record how
four points that the frozen text left implicit are implemented. They were written, tested and
committed before any V6 trial was recorded or any V6 outcome computed.

None of the four changes a threshold, a parameter, a family size, a decision rule or a selection.
None reads an outcome, and none can select or favour a configuration. Regression tests:
`tests/test_v6_amendment.py`.

The pre-amendment review found two places where the code did not yet match the frozen text: item 2
(gap at the touch candle) and item 3 (an order-fragile seed). Both were corrected in this
amendment's commit.

**1. Trading-median test** (§9, stage success: "the model's `P` net trading median per pair ≥ 0").

* **Implemented:**
  * Per eligible pair, the mean net return per completed trade of the model, at primary costs:
    fees 20 bp, slippage 10/20 bp by liquidity rank, and short funding (observed or the
    estimated 10%/yr).
  * Then the median of those per-pair means across pairs (`pair_median_of_mean_net`).
  * Eligible pairs are the target pairs with at least one completed trade in the model's unit set
    (signals passing E1–E6 with a full outcome window). Pairs whose trades all ended
    `no_exit_in_data` / `trade_gap` are not counted. BTCUSDT is excluded.
  * The ×0 and ×2 slippage sensitivities never enter this test.
* **Consistent with the protocol because:**
  * "median per pair" names a cross-pair median of a per-pair quantity;
  * the per-trade mean is a pair's expectancy, the quantity the trading test is about;
  * it is computed only for the TF at which the feature's own cell passes, as §9 states.
* **Kept separate** from:
  * the pooled per-trade mean and median, which are reported in their own columns and never
    decide;
  * the signal-quality criteria of §9.
* **Thresholds and outcomes:** the threshold stays ≥ 0, and no configuration is selected by it.
* **Tests:** a case where the pooled mean is positive while the median of per-pair means is
  negative; the median differs from the pooled per-trade median; slippage sensitivities do not
  change it; pairs without a completed trade are not counted.

**2. Gap at the touch candle** (§2 gap definition; §3.2 steps 1 and 4).

* **Implemented:**
  * **Gap.** A gap before candle k means open time[k] − open time[k−1] > 1.5 × the nominal
    duration: 1.5 h for 1H, 6 h for 4H. For 4H candles, built from 1H data in UTC buckets, a gap
    therefore means at least one whole bucket is missing.
  * **Behaviour.** When a pullback would start at candle j (trend `up`, low[j] ≤ EMA_f[j], pair
    armed) and there is a gap before j, the pullback **starts and is immediately ended** by the
    gap rule. So:
    * it never triggers, not even at j itself;
    * starting it **disarms** the pair, so a new pullback needs the pair to re-arm first.

    Shorts mirror this.
* **Consistent with the protocol because:**
  * §3.2 step 1 starts the pullback and disarms the pair on exactly these conditions.
  * Step 4 ends a pullback at the first candle i with a gap before i. Pullback candles run from
    j, so i = j qualifies, and the end check precedes the trigger.
  * The pre-amendment code did not start such a pullback and left the pair armed. That let the
    next touching candle start one, which the frozen text does not allow. It is corrected here.
* **Why a gap disqualifies the touch.** A trigger at j would compare close[j] with high[j−1],
  which lies on the far side of missing data, and the pullback itself would begin across that
  missing data. The frozen gap rule exists to stop either.
* **Thresholds and outcomes:** the 1.5× threshold is the frozen §2 value. Prices are read only
  as frozen; outcomes are not read.
* **Tests:** the gap threshold at 1H and 4H; a touch after a gap starts nothing tradable and
  disarms; the next touch without re-arming is ignored; after re-arming a new pullback triggers;
  a gapped touch candle never triggers itself.

**3. Matched-random-entry seeding** (§7 C0: "200 seeded replicates, `default_rng(20261027)`").

* **Implemented:**
  * One stream per (pair, configuration, side, TF):
    `np.random.default_rng(np.random.SeedSequence(20261027, spawn_key=(crc32(pair),
    crc32(config id), side + 1, crc32(TF))))`.
  * Within a stream, calendar blocks are drawn in ascending block order. In each block, the 200
    replicates are drawn in sequence, uniformly without replacement.
  * The pre-amendment code keyed the stream by list positions, and drew blocks in
    `value_counts` order (count-descending, ties unspecified). Both are replaced here.
* **Consistent with the protocol because:**
  * every stream derives from seed 20261027, so it is seeded and reproducible as frozen;
  * the draw rule (same pair, same calendar block, same trend state, same count, no replacement)
    is unchanged;
  * keying by names makes the result independent of execution order, worker scheduling and
    list order.
* **Thresholds and outcomes:** it does not depend on outcomes, and it selects nothing.
* **Tests:**
  * identical draws for identical keys, and different draws when any key differs;
  * the worker uses the named stream and sorted blocks;
  * one pair's replicate sums are identical when the universe order is reversed and another pair
    is processed first.

**4. Shared trades** (§5: entry, exit and costs identical for every model).

* **Implemented:**
  * Within a pair and TF, every unit with the same (signal candle i, pullback start j, side) uses
    one trade from `shared_trade`, whose inputs are only pair data and (i, j, side):
    * entry at open[i+1];
    * stop = min low[j..i] − 0.5 × ATR14[i] (short: max high[j..i] + 0.5 × ATR14[i]);
    * fills and the time exit by `v5_eval.trade`;
    * slippage by the liquidity rank at i;
    * funding for shorts.
  * The trade is computed once, by the first configuration under which the unit is eligible
    (E1–E6, full outcome window, defined `rh_x`). It is reused by every configuration and model
    (A, B, C, D) with the same key.
* **Consistent with the protocol because:**
  * §5 requires identical entry, exit and costs across compared models;
  * the trade depends on nothing configuration-specific. EMA periods, RSI, MACD and extension
    settings and the B/C/D flags are not inputs. j is part of the key, so different pullback
    starts give different stops, as the frozen stop rule requires.
* **Thresholds and outcomes:** it does not depend on outcomes, and it selects nothing.
* **Tests:**
  * the helper's signature has no configuration argument;
  * on a synthetic run, every unit sharing a key has identical net, gross, MAE and cost source
    across configurations, even where the B/C/D flags differ;
  * recomputing from (i, j, side) reproduces every stored trade;
  * the trade equals `v5_eval.trade` with the same stop.

### Pre-run audit note to V6-A1 (2026-10-28, before any V6 outcome)

Append-only. It records findings of the pre-run audit. It changes no threshold, decision rule,
family or configuration, and `V6_CONT_CONFIG.md` is untouched.

1. **Trading-median test: eligibility and pair accounting.**
   * The test is computed only on the model's units that pass the frozen §1 eligibility (E1–E6)
     and the §5 full-window rules.
   * A pair enters it with **≥ 1 completed trade**. A pair whose units all ended
     `no_exit_in_data` / `trade_gap` (data end or a timestamp gap) is excluded, and listed in the
     results as `pairs_without_completed_trade`.
   * That exclusion depends only on trade status, never on returns, so it cannot favour the
     result (tested by flipping returns).
   * The frozen §8 per-pair minimum (≥ 20) is defined for the signal-quality contrasts, not for
     the trading test, so it is **not** applied to the decisive median. The trading test is only
     consulted at a TF where the feature's own cell has passed, which already requires ≥ 8 pairs
     with ≥ 20 kept units each.
   * A median over pairs with ≥ 20 completed trades, and the count of such pairs, are reported
     as a **reporting-only sensitivity** that never decides.
2. **Random entry.** The draw is now `random_entry_draws(pool, cl, signal_i, rng, reps)`. Its
   inputs are masks, block ids and signal positions only.
   * **Pool:** E1–E6-eligible, in-window candles with a full window and a defined benchmark, in
     the same trend state (causal).
   * **Count:** model A's count per calendar block. Blocks are drawn in calendar order, without
     replacement. A shortfall keeps all candidates and is never padded.
   * Outcome values are read only after the draw, to average the drawn candles.
   * The defined-benchmark condition is the same unit rule model A's signals pass, so signals and
     controls are drawn from comparable candles.
3. **The 1.5× gap rule is frozen text** (`V6_CONT_CONFIG.md` §2), not a new operational choice;
   so are the 1.25× window rules (§5). V6-A1 item 2 only applies it at the touch candle.
4. **Gap cases** (timestamps of the 36 cached pairs since 2019 profiled; no prices read):

   | case | in the data | handling |
   |---|---|---|
   | missing candles | 587 gaps at 1H, 85 at 4H: exchange-wide outages of 11–12 h | gap |
   | irregular spacing (below nominal, or 1–1.5× nominal) | none | not a gap |
   | misaligned open times or duplicates | none | the loader index is strictly increasing; `v5_state.classify` refuses otherwise |
   | market sessions | none: crypto trades 24/7 | – |
   | **partial 4H candles** (built from fewer than 4 hourly candles) | 814 of 532,265 (0.15%) | treated as normal candles, not gaps. **Disclosed limitation**: the frozen rules have no partial-candle test; E4 (≥ 95% hourly completeness over 30 days) bounds their frequency per pair |
   | empty 4H buckets | dropped by the loader (no NaN rows) | appear as a gap |

   Regression tests are in `tests/test_v6_amendment.py`.
