# V5 workstream M, stages A/B: does BTC-regime context improve crypto price-only signals? (summary)

> **EXPLORATORY ONLY.**
> * Every candle used was already examined in earlier studies.
> * Review mode is `self_audited_exploration_only`: no external review took place.
> * Nothing here is independent confirmation, and nothing shows a predictive edge or profitability.
> * Configuration [`V5_M_B_CONFIG.md`](V5_M_B_CONFIG.md): frozen in `498292f`, sha256 `f8d8b545…`, unchanged.
> * Code committed in `6fffd0c`.
> * Full tables: [`V5_M_B_RESULTS.md`](V5_M_B_RESULTS.md). Per-pair tables:
>   [`V5_M_B_PER_PAIR.md`](V5_M_B_PER_PAIR.md). Raw output: [`v5_m_b_results.json`](v5_m_b_results.json).

## Answer

**No measurable incremental value from BTC-regime context was found under the frozen rules.**

| hypothesis | gate (signals kept when …) | primary verdict (Holm within hypothesis) | stricter (Holm across 36 cells) |
|---|---|---|---|
| M-B1 | longs: BTC bull | **INCONCLUSIVE** (2 NO VALUE, 6 INCONCLUSIVE) | INCONCLUSIVE |
| M-B2 | shorts: BTC bear | **INCONCLUSIVE** (6 NO VALUE, 2 INCONCLUSIVE) | INCONCLUSIVE |
| M-B3 | BTC not in high volatility | **INCONCLUSIVE** (11 NO VALUE, 5 INCONCLUSIVE) | INCONCLUSIVE |
| M-B4 | reversal alerts: BTC not with the old trend | **INCONCLUSIVE** (3 NO VALUE, 1 INCONCLUSIVE) | INCONCLUSIVE |

**No cell ADDS VALUE.**
* All 36 cells were evaluable: no cell failed the minimum sample rules of §8.
* 22 cells are NO VALUE and 14 are INCONCLUSIVE.
* No hypothesis is REJECTED: each has at least one cell whose confidence interval still crosses
  zero.

**The two correction scopes agree on every cell and hypothesis.** The disagreement the
configuration guards against (a cell passing within-hypothesis Holm but failing all-cell Holm)
did not arise. No cell passed even the primary correction:
* The smallest decisive p was 0.044 (M-B1 · Supertrend · 1H).
* Within its 8-cell hypothesis that becomes 0.354; across 36 cells, 1.0.

## Run integrity

| check | result |
|---|---|
| pre-run | branch equal to origin at `6fffd0c`, clean tree; config unchanged since its freeze; manifest verifies (no missing/changed/extra); `m_blockers()` empty; review mode `self_audited_exploration_only` |
| trials | 10 of 10 recorded **and committed before computation** (`m-a-ref`, `m-b1`…`m-b4` × 1H, 4H; one commit each, `efab606` … `90086a8`); the 4H records were committed only after the 1H computation finished |
| ledger | 28 records (18 family C + 10 M); hash chain valid; `verify_against_git` passes; one config sha256 across all 10; no uncommitted code at record time |
| execution | 36/36 pairs computed at 1H and 4H; exit status 0; no worker exception |
| **test suite (failure, disclosed)** | **1 failing test at the run commit `6fffd0c`: `test_P1_only_the_evaluator_reads_the_retrospective_labels`** (136 passed). P1 greps git-tracked files for the string `v5_labels`. It matches (a) a docstring in `research/v5_context.py` that says the module does *not* import it, and (b) the runner's `CODE_FILES` list, which names the label file only so the ledger fingerprints it. Neither file imports the label module; the runner reads labels only through `v5_eval.frozen_labels`, like the family C runner. The pre-commit suite run reported 137 passed because the new files were still untracked and invisible to `git grep`: a process error. Results are unaffected. **Not fixed** pending the owner's decision (a docstring rewording plus either dropping the label file from `CODE_FILES` or allowing the runner in P1) |
| protections | family C config, results and ledger records, `v5_labels.py`, V4.1 protected files, reserve instruments, post-freeze candles and Pine scripts were untouched (no reserve or post-freeze data is loadable through `v5_data`) |

## Eligible data, exclusions, missing context

| | 1H | 4H |
|---|---|---|
| target pairs with eligible candles | 35 / 35 | 35 / 35 |
| eligible candles / candles in window | 1,264,741 / 1,890,609 (67%) | 316,298 / 472,862 (67%) |
| first failing rule (candles) | E2 liquidity 329,968; E3 rank 158,742; E1 history 134,988; E6 not warm 2,130; **E7 BTC context unavailable 40**; E4 completeness 0 | E2 82,503; E3 39,708; E1 32,065; E6 2,282; **E7 6**; E4 0 |
| candles with missing BTC context | 64 (excluded, never mapped to neutral) | 9 |
| signals lost to missing BTC context | 1 (R-cr, tops, 1H) | 0 |
| signals in S (per signal × side) | 10,702 – 14,361 | 1,699 – 3,492 |
| other exclusions | no exit in data: ≤ 11 per signal; outcome-window gap: 1; no causal benchmark: 0 | no exit ≤ 15; gap 2; no benchmark 0 |

**BTC regime episodes** (§2 definition: runs of the BTC trend state on its own HTF ladder, runs
shorter than H merged):

| TF | `btc_dir` episodes (bull / bear / neutral) | median length | `btc_unstable` episodes (stable / high-vol) |
|---|---|---|---|
| 1H | 767 (263 / 243 / 261) | 48–72 candles (2–3 days) | 638 (421 / 217) |
| 4H | 149 (46 / 37 / 66) | 60–132 candles (10–22 days) | 133 (84 / 49) |

**Read these counts carefully.**
* They are distinct BTC *trend-state* episodes on each chart's HTF ladder (4H/1D for 1H charts,
  1D/1W for 4H charts). They are **not** distinct macro bull or bear markets, of which
  2020–2026 holds only a handful.
* So the episode clustering (G = 508–751 at 1H, 107–148 at 4H) is the less conservative of the
  two.
* The calendar-block clustering (G = 82 at 1H, 40–41 at 4H) is the binding effective sample.
* In practice the two p-values were close in every cell, and the larger one decided.

## What the comparisons show

`rh_x` is the move to H candles in ATR, after costs, minus the pair's own past-only benchmark in
the same own HTF state. K = signals kept by the BTC gate; S∖K = signals removed.

**1. BTC-filtered vs the same price-only signals (signal quality):**
* **M-B1 (longs only when BTC is bull).** Mixed and not significant. The strongest cell is
  Supertrend at 1H:
  * Δ = +0.30 ATR [+0.02, +0.58] calendar t-CI; decisive p 0.044, Holm 0.35;
  * 72% of the 32 qualifying pairs positive; altcoin Δ +0.29; positive within all three own
    states;
  * it passes every condition except the multiple-testing correction.

  The engine continuation signal at 4H: Δ +0.91 [−0.17, +1.99], p 0.052. Only 3 pairs had ≥ 20
  removed signals, so the 8-qualifying-pair rule failed.

  EMA-cross and HTF-flip show nothing (Δ ≈ 0 or negative).
* **M-B2 (shorts only when BTC is bear).** No improvement. 6 of 8 cells are NO VALUE, and the
  point estimates are mostly negative (e.g. EMA-cross 1H Δ −0.29, 12% of pairs positive).
* **M-B3 (avoid BTC high-volatility periods).** No improvement, and for **longs** the estimates
  run in the *opposite* direction:
  * signals fired during BTC high volatility did better (e.g. HTF-flip 1H Δ −0.41
    [−0.71, −0.11]);
  * the test was one-sided (decision D6), so this is recorded as NO VALUE, **not** as evidence
    of the reverse effect;
  * claiming the reverse would be a post-hoc hypothesis.

  Shorts: small positive estimates (EMA-cross 1H Δ +0.24, decisive p 0.058; 84% of pairs positive), none
  significant after correction.
* **M-B4 (reversal alerts when BTC is not with the old trend).** No improvement.
  * Kept alerts landed near a labelled major turn **less** often than removed alerts at 1H
    (bottoms Δ −0.036, tops −0.004) and for bottoms at 4H (−0.062).
  * Tops at 4H: +0.012 [−0.055, +0.078].

**2. vs matched removal (an uninformed filter of the same selectivity):**
* Only 6 of 36 cells had mean(K) above the 97.5th percentile of random removal: M-B1
  Supertrend 1H, M-B1 engine 4H, M-B3 EMA-cross and Supertrend shorts 1H, M-B3 Supertrend shorts
  4H, and M-B4 tops 1H.
* Each failed another condition, mostly the Holm correction. M-B4 tops 1H also had Δ ≤ 0 and
  most other conditions failing.
* In most cells the BTC filter did **no better than removing the same number of signals at
  random**.

**3. vs the existing simple baselines:**
* **Reversal alerts.** The BTC-filtered alerts (K) had lower duplicate-free precision than
  EMA-cross matched to K's frequency in every side × TF:
  * bottoms 1H: 0.214 vs 0.245; tops 1H: 0.271 vs 0.296;
  * bottoms 4H: 0.205 vs 0.263; tops 4H: 0.259 vs 0.293.

  Against Supertrend they were lower for bottoms (0.214 vs 0.236 at 1H, 0.205 vs 0.237 at 4H)
  and about equal for tops (0.271 vs 0.271 at 1H, 0.259 vs 0.258 at 4H).
* **Continuation signals.** The Stage-A table compares all four price-only signals:
  * The engine continuation signal is not better than the simple baselines. At 1H its `rh_x`
    is negative on both sides: longs −0.16 [−0.38, +0.07], shorts −0.24 [−0.48, −0.00].
  * At 4H the shorts of the simple signals were positive: Supertrend +0.57 [+0.21, +0.94]
    (34/35 pairs positive), EMA-cross +0.45 [+0.02, +0.88].
  * Stage A has no pass/fail rule. These are 2 of 16 continuation cells. The benchmark is each
    pair's own past short track record in the same state, which in a rising market is a low
    bar. They are **not** evidence of a short edge.

**Pooled vs equal-weight vs per-pair.**
* Every cell reports the signal-weighted Δ, the equal-pair-weight Δ, the median per-pair Δ, the
  positive-pair share and the altcoin-tier Δ.
* They frequently disagree in sign, e.g. M-B1 HTF-flip 1H: pooled +0.08, equal-weight −0.20.
  That is one reason no cell passes.
* Per-pair tables for all 36 cells are in [`V5_M_B_PER_PAIR.md`](V5_M_B_PER_PAIR.md). For the
  strongest cell (M-B1 Supertrend 1H), per-pair Δ ranges from −1.81 (XTZ) to +1.03 (VET).

## Net trading results (separate from signal quality; never decisive)

* **Basis.** Structural stop, time exit at 2H, net of the 20 bp round trip and the short holding
  cost.
* **Longs.** Price-only continuation longs net +0.18% to +0.27% mean per trade at 1H, with a
  **negative** median in every long set (−0.2% to −1.8%). The means are carried by a minority
  of large winners.
* **Shorts.** Price-only shorts net −0.14% to −0.41% mean per trade at 1H.
* **Price-only vs BTC-filtered, longs:**
  * The BTC-bull filter on Supertrend longs at 1H raised the mean from +0.06% (removed) to
    +0.43% (kept): Δ +0.37% [−0.19%, +0.93%], p 0.094.
  * The engine continuation longs at 4H: Δ +3.6% [−0.4%, +7.6%], p 0.037. This is one of 36
    information-only trading tests, uncorrected.
  * Neither is a decision statistic.
* **Price-only vs BTC-filtered, shorts.** The BTC-bear filter on shorts made 1H net results
  worse in all four signals: Δ −0.09% to −0.55%.
* **Primary short table** (9 pairs with a cached perp, dates after the first cached perp
  candle): same picture.
  * At 1H, kept shorts lost more than removed ones for three of the four signals (Supertrend
    was the exception).
  * At 4H, M-B4 tops kept vs removed: +0.6% vs −1.4%, net Δ p 0.042 (uncorrected, information
    only).
* **Per-pair books** (one trade at a time) have large drawdowns. For M-B1 Supertrend 1H, the
  median maximum drawdown is −0.60 (kept) and −1.25 (removed) in log terms.

## Costs and their limits

* **Round trip.** 20 bp, Binance spot taker. **Slippage is not modelled.** The +10 bp
  sensitivity for pairs ranked below the top 10 lowers net means by about 0.05–0.06 percentage
  points and changes no sign above.
* **Short holding cost.**
  * Observed perp funding where cached: about 32–36% of short trades.
  * Otherwise an assumed 10% a year, labelled `estimated_crypto_10pct` in every table.
  * No cost was set to zero.
* **Shorts assume a perp,** with spot prices used for entries and exits. The perp basis is not
  modelled.
  * Perp existence is verified only for 9 cached pairs, and only from the first cached perp
    candle. That may be later than the actual listing: ETH's cache starts 2020-01-01.
* **Market impact** is not modelled.

## Limitations

1. **Already-examined data.**
   * Every pair and period was used in earlier studies.
   * Multiplicity: 10 trials and 36 decision cells in this run, plus 18 family C trials before.
     That makes 28 V5 exploratory trials.
2. **Survivorship.** The 35 pairs were chosen with hindsight from coins that became large. Coins
   liquid in 2020–2021 but not cached are absent. The point-in-time rules (E1–E4) remove
   hindsight only within the set.
3. **Effective sample.**
   * BTC regime is a time-only variable. The calendar-block G (82 at 1H, 40–41 at 4H) bounds the
     evidence, whatever the 35 pairs or the tens of thousands of signals suggest.
   * Altcoins co-move with BTC, so pairs are not independent observations.
4. **Matched-removal control.** It is not time-cluster-aware (by design), so it is a necessary
   condition only.
5. **Some 4H cells are thin per pair.** Qualifying pairs were as few as 3 (M-B1 engine, 4H)
   to 12. The 60%-of-pairs condition is weak there.
6. **Stage-A R-cr "near" row.**
   * This row reports the raw hit rate (about 0.30–0.36), and its p ≈ 0.0001 tests "> 0".
     That is not a test of anything useful.
   * The useful R-cr comparisons are the matched-baseline precision figures above.
7. **No independent review.** The confirmatory gate stays closed.
8. **Only forward data can confirm.** A time-varying BTC effect could be confirmed only on
   post-freeze data, which is shared with the frozen V4.1 H6/H7v forward test (§11 of the
   config).

## Recommendation

* **Do not add a BTC-regime filter (trend or volatility) to HC-MTF on this evidence.** Under the
  frozen rules it did not improve price-only signals, beat an uninformed filter of equal
  selectivity, or beat the simple baselines.
* **Two cells came closest:** M-B1 Supertrend longs at 1H and engine continuation longs at 4H.
  They are recorded as **exploratory leads only**:
  * they failed the frozen correction;
  * any test of them would need a new, pre-registered configuration with new trial ids;
  * and, for confirmation, forward data.

**Not done:**
* no configuration, threshold, label or rule changes;
* no follow-up experiment;
* no Pine changes.
