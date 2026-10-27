# V5 workstream M, stages A and B: crypto price-only reference and BTC-regime context (1H/4H)

**Status: FROZEN** (2026-10-27).
* Frozen in a commit of its own, with decisions D1–D6 at their defaults (owner's instruction,
  2026-10-27; D2 clarified in §7).
* No code for this configuration existed, and no outcome under it had been computed, when it was
  frozen.
* Nothing in this file may change once any outcome is computed. A defect found later needs a
  logged amendment, a new configuration version and new trial ids.

**Basis:**
* [`V5_M_CRYPTO_CONTEXT_PROPOSAL.md`](V5_M_CRYPTO_CONTEXT_PROPOSAL.md), approved with the owner's
  eight decisions (2026-10-27);
* the frozen event definitions in `V5_HYPOTHESIS_REGISTER.md` §2;
* `V5_VALIDATION_PROTOCOL.md`.

**Kind of study.** Exploration on already-examined data:
* Review mode is `self_audited_exploration_only` (`V5_REVIEW_WAIVER.md`).
* No result under this configuration is independent confirmation or evidence of an edge.
* A confirmatory test of any BTC-regime effect needs forward data (§11).

**What has been seen before drafting.** No outcome of any signal split by BTC regime has been
computed in this repository. Related prior results:
* V4 H0: raw structure breaks were rejected.
* V4.1 H6: HTF state alone on crypto 1H/4H was inconclusive.
* V5 family C (x1): no top detector beat its baselines. The engine CHoCH (`counter_reversal`) had
  lift, but no more than EMA-cross / HTF-flip at matched frequency.

**External code.** None of the optional reference repositories (CCXT, SM Radar Pine, Market
Structure, Market Data Stream Processor) informs this configuration. Every signal below is
existing, already-tested HC-MTF code. Per the owner's priority, external integrations are deferred.

## 1. Data, universe and dates

| item | value |
|---|---|
| source | cached Binance **spot** USDT pairs, 1H native; 4H resampled by `hcmtf.data` (UTC 4-hour buckets). Loaded **only** through `research.v5_data.load` (cache only, closed-candle freeze cut, integrity cut) |
| regime source | `BTCUSDT`, same feed, same candle boundaries |
| target instruments | the 35 cached non-BTC crypto pairs in `v5_data.EVAL_SYMBOLS`: ETH XRP LTC ADA BNB LINK SOL DOGE TRX BCH DOT ATOM ETC XLM FIL ALGO NEO ZEC ICX ZIL LUNA FTT SRM WAVES MATIC AVAX NEAR UNI AAVE XTZ EOS VET THETA HBAR ICP (all `…USDT`) |
| tiers (reporting) | **majors**: ETHUSDT, SOLUSDT. **altcoins**: the other 33 |
| BTCUSDT as a target | Stage A only, reported **separately** and never pooled. Stage B: excluded, because its "BTC regime" is its own price |
| excluded | BTC-USD (Yahoo duplicate); every perp series as an instrument (perp data are used only for costs, §6); every non-crypto instrument; every `V5_RESERVE` instrument |
| timeframes | 1H (HTFs 4H/1D) and 4H (HTFs 1D/1W), from `engine.LADDER` |
| signal window | signals on candles opening ≥ **2020-01-01 00:00 UTC** (decision D1), through the last candle whose outcome is fully inside data closing by the freeze. Earlier candles are used only as indicator warm-up |
| data identity | `reports/V5_EXPLORATION_DATA_MANIFEST.json` (combined sha256 `57e107b0…`). `v5_manifest.verify()` must report no missing, changed or extra file at the start of every trial |
| new data | **none**: no download, no external series, no TradingView export |

### 1.1 Point-in-time eligibility (objective; computed from data closed before the decision)

A target candle i (UTC open time t) is **eligible** only if **every** condition below holds.

**Reference day.** D(t) = the UTC calendar date of t minus one day, i.e. the last UTC day that
ended at or before t (the candle's **open**). The 30-day window is days D(t)−29 … D(t). This is
stricter than the close of candle i, and the same rule serves 1H and 4H.

**Daily quote volume** of a pair on a UTC day:
* the sum over that day's cached 1H candles of `volume` × `close`;
* `volume` is Binance base-asset volume, and USDT is taken as USD;
* a missing 1H candle contributes 0;
* a day with no 1H candle at all has quote volume 0.

| id | rule | rationale |
|---|---|---|
| E1 history | the pair's first cached 1H candle (after `v5_data.load`) opens ≤ t − 365 days | warm-up; excludes listing-pump months |
| E2 liquidity | median of the 30 daily quote volumes of days D(t)−29 … D(t) ≥ **$5,000,000**. Undefined, so the candle fails, if the pair's first cached 1H candle opens after day D(t)−29 begins | absolute floor (decision D5) |
| E3 relative liquidity | the pair's E2 median ranks **≤ 25** (rank 1 = largest; ties broken by symbol name, ascending) among the **non-BTC** target pairs whose E2 median is defined for the same D(t). Rank uses E2 medians whether or not those pairs pass E1, E2 or E4. **Not applied to BTCUSDT** (stage A only) | point-in-time "large and liquid" without hindsight on today's survivors |
| E4 completeness | ≥ 684 of the 720 expected 1H candles (95%) are present in days D(t)−29 … D(t) | exchange outages and gaps |
| E5 integrity | the candle is before the pair's integrity cut (V4.1 Amendment 1, already applied by `v5_data.load`) | token swaps (LUNA) |
| E6 warm | the target's `v5_state.classify(...)["warm"]` is True | as family C |
| E7 BTC context available | a BTCUSDT candle of the same TF with **the same open time** exists in the loaded BTC frame, **and** its BTC state is warm (so `direction_label` ∈ {bull, bear, neutral} and `vol_regime` ∈ {low, mid, high}). Applies to non-BTC targets only | missing context is never "neutral" |

**Unavailable context is enforced, not just counted:**
* A target candle failing E7 is **context-unavailable**.
* It is excluded from Model A **and** Model B, so both are evaluated on the identical unit set.
  It is never mapped to neutral, stable, or any gate value.
* The number of Model-A signals lost to E7 is reported per pair, signal, side and TF, next to
  the number lost to each of E1–E6. Exclusions are tallied in the order E5, E6, E1, E2, E3, E4,
  E7; a candle is tallied under the first rule it fails.
* The context module returns an explicit `available` flag. Gate values for unavailable candles
  are stored as the string `"unavailable"`, so any gate comparison on them is False **and** they
  are dropped before the comparison (tested).

**Evaluation-only exclusion (applied identically to every signal set):** a signal whose outcome
window i+1 … i+H spans more than 1.25 × H nominal candle durations (a data gap or outage) is
excluded and counted. This rule reads post-signal timestamps, never prices. It is an evaluation
filter, not a signal input.

**No splicing.** Ended or renamed pairs end where their data end:
* MATIC (2024-09), WAVES (2024-06), SRM (2022-11), EOS (2025-05), ICX (2026-09);
* LUNA at its integrity cut;
* FTT stays.

A signal whose outcome window runs past the data end is counted as `no_exit_in_data`.

**Survivorship disclosure** (to be printed in the results): the 35 pairs were chosen with
hindsight from coins that became large. Coins that were liquid in 2020–2021 but are not cached
are absent, not imputed. E2/E3 remove hindsight **within** the set only.

## 2. BTC regime (context feature; no new thresholds)

`research.v5_state.classify` (default `StateConfig`) is run on BTCUSDT with the same ladder as
the target chart. For target candle i with open time t, the BTC regime is the BTC state row with
open time t. Both candles close at the same instant, and the signal executes at the next open.

| regime field | values | source |
|---|---|---|
| `btc_dir` | bull / bear / neutral | BTC `direction_label`: HTF1/HTF2 trend agreement, completed HTF candles only via `hcmtf.htf.align` |
| `btc_unstable` | True if BTC `vol_regime == "high"` (ATR% above the 66.7th percentile of its previous 200 values), else False | existing tercile cut |

"Range" is `btc_dir == neutral`. No other BTC feature is used in stage B.

**Information set at the signal.** Both BTC fields are columns of `classify` on BTCUSDT and are
known at the close of the BTC candle:
* the HTF trend uses only HTF candles that were complete when the chart candle opened
  (`hcmtf.htf.align`, Pine `[1]` with `lookahead_on`);
* `vol_regime` compares the candle's own closed ATR% with the previous 200 values;
* the BTC candle and the target candle close at the same instant, and the entry is the next
  open.

A forming or later BTC candle is never read.

**BTC episodes** (an evaluation unit for clustering; never a signal input):
* Built per TF and per field (`btc_dir` or `btc_unstable`) on the BTC candles that open inside
  the signal window and have a warm BTC state, in time order. Unwarm BTC candles are skipped,
  not treated as a value.
* **Runs.** A run is a maximal sequence of consecutive such candles with the same value.
* **Merging.** Runs are processed in time order:
  * a run of fewer than H candles (§3) is appended to the preceding episode;
  * if there is no preceding episode, it is prepended to the next run;
  * an episode's **value** is the value of the run that opened it.
* Every eligible signal gets the episode id of its BTC candle.
* An episode **counts for a gate value** if its value satisfies the gate (for M-B4,
  "≠ bull" / "≠ bear").

Reported, per TF and per value:
* the number of raw runs;
* the number of episodes;
* episode durations (median, min, max);
* the number of episodes containing at least one eligible signal of the cell.

## 3. Outcomes (frozen register §2; nothing new)

| TF | H | 2H (trade time exit) |
|---|---:|---:|
| 1H | 24 | 48 |
| 4H | 30 | 60 |

**Signal quality** (decision metrics for M-B1 to M-B3):
* `rh`, per side, for every candle i of the pair (register §2.1 "after costs"):
  * `hcmtf.evaluate.bar_outcomes(…, H, 20 bp)["r_h"]`: side × (close[i+H] − open[i+1]) /
    ATR14[i], minus the round trip × open[i+1] / ATR14[i];
  * shorts only: minus the short holding cost × open[i+1] / ATR14[i]. The holding cost is
    `v5_costs.short_holding_cost("crypto", entry = open time of i+1, exit = close time of i+H
    as in `v5_eval._close_time`, funding)`. It may be computed vectorised, provided a test
    shows it equals `v5_costs` on sampled candles.
* `rh_x`: `rh` minus the **causal** benchmark `v5_eval.causal_benchmark(table, "rh",
  ["direction_label"], H, 200)`, computed separately per side:
  * the table holds every candle of the pair, with `rh` set to NaN on candles that are not warm;
  * so the benchmark is the past-only mean over earlier warm candles of the same pair and own
    state whose outcome was known at i;
  * eligibility E1–E4/E7 is **not** applied to benchmark history (it describes the pair's own
    track record).

  Units without a benchmark are counted and excluded.
* Also reported, never decisive:
  * MFE and MAE over H, in ATR;
  * the +2/−1 ATR barrier hit rate;
  * the median of `rh`.

**Event quality** (decision metric for M-B4; frozen labels `v5_labels.TOP_PARAMS` /
`BOTTOM_PARAMS`, unchanged since `7fc7e68`):
* `near`: 1 if a labelled event of the side's family lies in the alert's confirmation range
  [s − K, s] (K = L), else 0. Computed by `v5_eval.lift_units` with the scorable-region rule.
  Censored alerts are counted.
* Also reported: recall, strict precision, precision excluding duplicates, lead time and move
  remaining (`v5_eval.detection_report`).

**Trading outcome** (separate tables; never a decision metric in stage B):
* `v5_eval.trade(..., hold=2H, stop=structural)`:
  * longs: stop = lowest low of i−19 … i;
  * shorts: stop = highest high of i−19 … i.
* Net return as a fraction of notional.
* Trade MAE = the worst price move against the position between entry and exit, as a fraction
  of the entry price, from the candle highs/lows of entry … exit.
* Per pair, the one-at-a-time book `v5_eval.sequential_daily`:
  * total log return;
  * maximum drawdown of the cumulative log return;
  * worst trade;
  * MAE distribution (5/50/95%).
* Reported per pair, per tier and pooled, for S, K and S∖K of every stage-B cell.

## 4. Model A: price-only signals (stage A; frozen list, no tuning)

Every signal is existing code, evaluated on closed candles, at most one per candle, with no
cooldown. Side +1 = long / bullish, −1 = short / bearish.

| id | role | definition | code |
|---|---|---|---|
| S-eng | continuation | engine break with `cls == "continuation"`, `warm`, `dir == side` (shipped `engine.DEFAULTS[tf]`): the existing HC-MTF price-only continuation logic | `hcmtf.engine.breaks`, as in `v5_baselines.counter_reversal` |
| S-htf | continuation | HTF-state onset to the side | `v5_baselines.htf_flip` |
| S-ema | continuation | EMA20/EMA50 cross to the side | `v5_baselines.ema_cross` |
| S-st | continuation | Supertrend(10, 3) flip to the side | `v5_baselines.supertrend_flip` |
| R-cr | reversal | engine counter-HTF change of character to the side. side −1 is scored against **top** labels, side +1 against **bottom** labels | `v5_baselines.counter_reversal` |

**Stage A metrics.** For every signal, side, TF, pair, tier and pooled:
* counts;
* `rh` and `rh_x` (mean, median, cluster CI);
* MFE/MAE and barrier rate;
* trading tables.

For R-cr, the detection metrics, plus the other three baselines as comparators at matched
frequency (`v5_baselines.thin`, as in family C).

Stage A has **no pass/fail rule**. It is the reference that stage B is measured against.

## 5. Model B: BTC-regime context (stage B hypotheses)

Each hypothesis splits a Model-A signal set S into a **kept** set K (the context gate is true) and
a **removed** set S∖K. Whether a signal is kept depends only on the BTC regime at the signal
candle.

| id | signals (S) | side | gate (K) | expected behaviour if BTC context is useful | decision metric |
|---|---|---|---|---|---|
| **M-B1** | S-eng, S-htf, S-ema, S-st | +1 | `btc_dir == bull` | kept longs have higher `rh_x` than removed longs | Δ `rh_x` |
| **M-B2** | S-eng, S-htf, S-ema, S-st | −1 | `btc_dir == bear` | kept shorts have higher `rh_x` (after short costs) | Δ `rh_x` |
| **M-B3** | S-eng, S-htf, S-ema, S-st | +1 and −1, separately | `btc_unstable == False` | signals outside BTC high-volatility periods have higher `rh_x` | Δ `rh_x`; MAE reported |
| **M-B4** | R-cr | −1 (tops) and +1 (bottoms), separately | tops: `btc_dir ≠ bull`; bottoms: `btc_dir ≠ bear` (decision D4) | kept reversal alerts land near a labelled major turn more often | Δ `near` |

**Cells** (36 in total; each is a signal × side × TF):

| hypothesis | cells |
|---|---|
| M-B1 | 4 signals × 2 TF = 8 |
| M-B2 | 8 |
| M-B3 | 4 signals × 2 sides × 2 TF = 16 |
| M-B4 | 2 sides × 2 TF = 4 |

**Unit set S of a cell** (identical for Model A and Model B). A Model-A signal on a non-BTC
pair is in S only if all of these hold:
* its candle opens in the signal window and passes E1–E7;
* for M-B1–M-B3, `rh_x` is defined: full outcome window, no evaluation-only gap exclusion, and a
  causal benchmark;
* for M-B4, the alert is scorable under `lift_units`: warm, and its confirmation range inside
  the scorable region with start index = first candle of the signal window.

Each exclusion is counted. K = the units of S whose gate is true; S∖K = the rest.

**Δ (primary contrast)** = mean metric over K − mean metric over S∖K, pooled over all units of
S, so each signal weighs equally.

**Three comparisons per cell.** All are reported, and the first two are decisive.

1. **Context vs the same price-only signals.** Kept K vs removed S∖K (Δ), and K vs all of S.
2. **Context vs matched removal (no BTC information).** 200 seeded replicates (numpy
   `default_rng(20261027)`) of a random subset R ⊂ S:
   * Within each (pair, own `direction_label` at the signal) stratum, R draws, uniformly
     without replacement, exactly as many units as K has in that stratum.
   * The draw uses no timestamps and no BTC value; the only BTC-derived input is K's
     **total count** per stratum, i.e. its pass rate.
   * Count matching per calendar block is deliberately **not** used: it would copy the BTC
     gate's timing into the control (§13).
   * Statistic: mean(K) vs the 2.5/50/97.5 percentiles of mean(R) over replicates, where the
     mean is pooled over units, as for Δ.
   * Matching is exact by construction (R ⊂ S, same counts per stratum), so no shortfall can
     occur.
   * **Not a dependence-aware test.** The random subsets ignore time clustering. This check
     only asks whether the gate does better than an equally selective, uninformed filter; the
     dependence-aware evidence is the cluster test of §7.
3. **Context vs existing simple baselines** (reported, not decisive; decision D3):
   * M-B1 to M-B3: `rh_x` of K vs each of the other three continuation signals, unthinned and
     gated by the same rule.
   * M-B4: precision* and recall of K vs `htf_flip`, `ema_cross` and `supertrend_flip` thinned to
     K's frequency (`v5_baselines.thin`, 50 replicates; shortfall reported).

**Own-state control.** Each target's own `direction_label` is strongly correlated with BTC's. So:
* the matched-removal control is stratified by the own state;
* Δ is also reported **within** each own-state stratum (bull / bear / neutral).

## 6. Costs and shorting

| item | value |
|---|---|
| round trip | 20 bp (`hcmtf.universe.COST_BPS["crypto"]`: Binance spot taker 0.1% per side) |
| slippage | **not modelled; reported as missing**. Sensitivity: +10 bp per round trip for pairs ranked > 10 on E3 at the signal, shown next to the base case in the trading tables |
| long holding cost | none (spot) |
| short holding cost | `v5_costs.short_holding_cost`: observed cached perp funding where it covers the holding period (`observed_funding`), otherwise 10%/yr (`estimated_crypto_10pct`). Every table shows the counts per source. Never 0 by default |
| short feasibility | spot cannot be shorted, so shorts assume a perp; spot prices are used (perp basis not modelled, disclosed). **Primary short trading table**: only the 9 non-BTC pairs with a cached perp series (ADA, BNB, DOGE, ETH, LINK, LTC, SOL, TRX, XRP), and only after each pair's first cached perp candle. The other pairs appear in a separate "perp existence unverified" table. **Signal quality** (`rh`, `rh_x`) for shorts uses every eligible pair, with the costs above |

## 7. Uncertainty and dependence

BTC regime is the same for every pair at a given time. Every test therefore uses **time**
clusters shared across pairs; the number of pairs never adds independent clusters.

**Test** for Δ: a new `research.v5_inference.cluster_diff_test(x, kept, clusters)`.
* OLS of x on [1, kept]. Δ is the slope, which equals mean(K) − mean(S∖K).
* CR1 standard error with factor G/(G−1), as `cluster_mean_test`; t(G−1) 95% CI.
* Wild cluster **restricted** bootstrap: x* = x̄ + w_g (x − x̄), the null Δ = 0 imposed, with
  one weight per cluster shared by every unit (every pair) in it. Rademacher if G ≥ 12, else
  Webb; 9,999 replicates; seed 20261027.
* One-sided p for Δ > 0: (1 + #{t* ≥ t}) / (reps + 1).
* Valid only if G ≥ 10.

It is run under **two** clusterings, and both are reported:
* **(a) calendar blocks** (`research.v41.cluster_id`: 1H 1 month, 4H 2 months);
* **(b) BTC episodes** of the gate's field (§2): `btc_dir` episodes for M-B1/B2/B4,
  `btc_unstable` episodes for M-B3.

**Decisive p** = the larger of the two. G and the number of episodes are printed next to every p.

**Per-pair quantities** (exact definitions; reported for every cell):

| quantity | definition |
|---|---|
| per-pair Δ_p | mean metric over K ∩ pair p − mean over (S∖K) ∩ pair p; defined if both are non-empty |
| **qualifying pair** | a non-BTC pair with ≥ **20** units in K **and** ≥ **20** in S∖K, in this cell |
| positive-pair share | #{qualifying pairs with Δ_p > 0} / #{qualifying pairs}. Δ_p = 0 counts as not positive |
| median per-pair Δ | median of Δ_p over **qualifying** pairs |
| equal-pair-weight Δ | unweighted mean of Δ_p over all pairs where Δ_p is defined |
| altcoin-tier Δ | Δ pooled over the units of the 33 altcoin-tier pairs (all target pairs except ETHUSDT and SOLUSDT); defined only if both K and S∖K have altcoin units |
| majors-tier Δ | the same over ETHUSDT and SOLUSDT; reported only |

No per-pair p-values are used for any decision.

**Multiple testing** (decision D2, clarified by the owner on 2026-10-27; both scopes fixed now):
* **Primary decision.** Holm within each of the four hypotheses, over all of its cells (M-B1 8,
  M-B2 8, M-B3 16, M-B4 4). A non-evaluable cell enters with p = 1, so the family size never
  shrinks after seeing data.
* **Stricter sensitivity.** Holm across all 36 cells, same p-values and the same p = 1 rule.
  Every cell verdict is recomputed with this p in a separate column, along with the hypothesis
  verdicts that would follow.
* **No switching.** The primary verdicts are the only verdicts. The sensitivity column never
  replaces them, whatever the results.
* **Disclosure.** The results report must state, for every cell and hypothesis where the two
  scopes disagree, that the primary (within-hypothesis) decision does not survive the stricter
  all-cell correction.
* Stage-A results carry no tests that feed a decision.

## 8. Evaluability (per cell)

A cell is **evaluable** only if all of these hold:
* ≥ 100 units in K and ≥ 100 in S∖K;
* ≥ 10 pairs with at least one unit in K and at least one in S∖K;
* G ≥ 10 under **both** clusterings, counting clusters that contain ≥ 1 unit of S;
* ≥ 3 BTC episodes (§2, the gate's field) whose value satisfies the gate **and** ≥ 3 whose
  value does not, each containing ≥ 1 unit of S.

A non-evaluable cell is reported as such and is neither "adds value" nor "no value".

## 9. Decision rules (frozen with this file; applied mechanically)

**Per evaluable cell:**
* **ADDS VALUE (exploratory)** if **all** of:
  1. pooled Δ > 0 **and** equal-pair-weight Δ > 0;
  2. there are **≥ 8 qualifying pairs**, the median per-pair Δ over them is > 0, and the
     positive-pair share is ≥ **0.60** (§7). With fewer than 8 qualifying pairs this
     condition fails, so the cell cannot ADD VALUE, and the shortfall is reported;
  3. Holm-adjusted decisive p < 0.05 (§7, within-hypothesis scope);
  4. mean(K) > the 97.5th percentile of the matched-removal replicate means (§5, comparison 2);
  5. altcoin-tier Δ is defined and > 0, so pooled results cannot rest on ETH/SOL alone.
* **NO VALUE** if the t(G−1) 95% CI of Δ lies entirely ≤ 0 under either clustering, or the
  pooled Δ ≤ 0 **and** the equal-pair-weight Δ ≤ 0.
* **INCONCLUSIVE** otherwise.

**Per hypothesis:**
* **SUPPORTED (exploratory)** if ≥ 1 cell ADDS VALUE **and** no cell of the same signal × side is
  NO VALUE at the other TF.
* **REJECTED** if every evaluable cell is NO VALUE.
* **INCONCLUSIVE** otherwise.
* **NOT EVALUABLE** if no cell is evaluable.

**Consequences:**
* A SUPPORTED hypothesis makes its gate eligible for stage F (combined) and for a future
  **forward** confirmatory registration (§11).
* No hypothesis, whatever its result, changes a threshold, a gate or a signal in this file.
* A redesign is a new configuration version with new trial ids. The trial count carries over.

## 10. Causality, missing data and integrity

Required before any trial; each check is enforced by a test or by the gate.

1. **Truncation.** Gate values, eligibility flags (E1–E7) and every signal at candle i are
   identical when all data after candle i are removed, from both the target **and** BTCUSDT
   (synthetic data; tests in `tests/test_v5_context.py`).
2. **Alignment.** The BTC row used for target candle i has the same open time. A BTC candle
   closing after the target candle is never read; a missing BTC candle gives
   context-unavailable (E7), never neutral.
3. **No label access.** The context module imports nothing from `v5_labels` / `v5_eval` (as test
   P1 does for detectors).
4. **Reserve / forward guard.** Every frame comes from `v5_data.load`, which refuses reserve
   symbols and post-freeze candles.
5. **Gate.** A new `v5_gate.m_blockers()` returns no blocker only if:
   * this file says `Status: FROZEN`;
   * it is committed and unmodified;
   * review mode is `independent` or `self_audited_exploration_only`;
   * the manifest verifies;
   * the context module and runner are committed.

   `c_blockers` and `confirmatory_blockers` are unchanged.
6. **Ledger.** Each trial below is recorded with `research.v5_ledger.record` **before** its
   computation (`config_file` = this file; `data_files` from `v5_manifest.files_for`;
   `outcomes_accessed = True`), followed by a git commit and `verify_against_git`.

**Trials** (10):

| trial id | content | hypothesis id |
|---|---|---|
| `m-a-ref-1H`, `m-a-ref-4H` | stage A reference: all five signals, both sides | M-A |
| `m-b1-1H`, `m-b1-4H` | M-B1 cells | M-B1 |
| `m-b2-1H`, `m-b2-4H` | M-B2 cells | M-B2 |
| `m-b3-1H`, `m-b3-4H` | M-B3 cells | M-B3 |
| `m-b4-1H`, `m-b4-4H` | M-B4 cells | M-B4 |

The family C trial count (18) is disclosed alongside; the total V5 exploratory trial count after
this run will be 28.

## 11. Data roles and protections

| data | role here |
|---|---|
| 36 cached crypto pairs, candles closing ≤ 2026-10-27 23:59:59 UTC | **already examined**; the only data this configuration reads |
| `V5_RESERVE["crypto"]` (12 never-downloaded pairs) | **not read**. For a time-varying BTC effect they add almost no independent evidence (same calendar) |
| every post-freeze candle | **not read**. It is shared with the frozen V4.1 H6/H7v forward test (earliest 1H evaluation 2027-07-01). Using it to confirm an M result needs a separate protocol decision that leaves the V4.1 test unchanged |
| family C config, results, ledger records; `v5_labels.py`; V4.1 protected files; Pine scripts | unchanged |

## 12. Decisions (resolved at freezing: all defaults)

The owner chose the defaults for D1–D6 on 2026-10-27. D2 is clarified in §7.

| id | decision | recommended default | alternative and trade-off |
|---|---|---|---|
| D1 | signal window start | **2020-01-01**, as in family C and V4.1. Cached perp/funding data start 2020 (realistic shorts), and early alt liquidity is thin | 2018-01-01 adds the 2018 bear market (more BTC episodes), but has no funding data and very thin alt books |
| D2 | multiple-testing scope for decisions | **Holm within each hypothesis**, with global Holm reported | global Holm over 36 cells: fewer false positives, lower power |
| D3 | are simple-baseline comparisons decisive? | **No.** Reported only: the question is the *incremental* value of BTC context, judged against the same signals and matched removal | make them decisive: answers "is the gated signal the best signal", a different question |
| D4 | M-B4 gates | tops kept when BTC is **not bull**; bottoms kept when BTC is **not bear** | strict (tops only when BTC bear): BTC's HTF state lags, so it would remove most alerts near alt tops |
| D5 | liquidity thresholds | **$5M** median daily quote volume and rank **≤ 25** of the non-BTC pairs | lower or higher thresholds; fixed now either way |
| D6 | M-B3 direction | one-sided: **stable** (not high-vol) better | two-sided: no prior on direction, at the cost of half the power |

**Code to be written only after freezing (minimum):**

| file | change |
|---|---|
| `research/v5_context.py` | **add**: BTC regime alignment, E1–E7 eligibility, BTC episodes |
| `research/v5_inference.py` | **add** `cluster_diff_test` |
| `research/v5_gate.py` | **add** `m_blockers` |
| `scripts/v5_m_explore.py` | **add**: runner, per-pair storage, report rendering |
| `tests/test_v5_context.py`, `tests/test_v5_m_runner.py` | **add**: truncation, alignment, missing data, diff test size on synthetic null, synthetic end-to-end |
| `reports/V5_HYPOTHESIS_REGISTER.md`, `reports/V5_VALIDATION_PROTOCOL.md` | Amendments sections only (workstream M) |

## 13. Pre-freeze verification (2026-10-27, by reasoning over the specification and existing code; no data read)

**1. Matched-removal control: no selection or timing leakage.**
* R is a uniform random subset of S within (pair, own state), so its expected composition by pair
  and own state equals K's. Any difference between K and R therefore comes from **which**
  signals the BTC gate keeps.
* The only BTC-derived input to R is K's count per stratum. R never sees timestamps, BTC values
  or outcomes.
* Calendar-block count matching (the family-C convention) was considered and rejected. If BTC
  is bull for a whole block, K keeps every long in that block and the bear blocks contribute
  none. A block-matched R would then select exactly the same blocks, absorbing the very
  between-period effect being tested.
* Own-state stratification stops a gate that merely re-expresses the pair's own trend (strongly
  correlated with BTC's) from being credited as BTC information.
* Residual limitation: the control is not time-cluster-aware, so it is a necessary condition
  only (§5).

**2. BTC regime and volatility use only information available at the signal.**
* Both are `classify` columns on BTCUSDT, decided at the BTC candle's close (§2).
* The BTC candle shares the target candle's open and close times, and entry is the next open.
* Missing or unwarm BTC gives context-unavailable (E7), never a gate value.
* The eligibility rules use only completed UTC days ending at or before the candle's open.
* The trailing, possibly incomplete, 4H/1D candles at the cache end carry no outcome, because
  their outcome windows run past the data end. They are excluded as `no_exit_in_data` and never
  enter S.
* Truncation tests on both the target and BTC frames are required (§10.1).

**3. The bootstrap preserves temporal and cross-pair dependence.**
* Clusters are time units shared by all pairs (calendar blocks; BTC episodes). Each wild weight
  multiplies every unit of every pair in its cluster, so cross-pair co-movement within a period
  is carried into the bootstrap distribution intact.
* Serial dependence within a block or episode is preserved: blocks are ≥ 1 month and episodes ≥
  H candles, against outcome windows of H candles.
* Dependence across adjacent clusters is ignored, as stated in `v5_inference`.
* Using the larger p of the two clusterings guards against an unlucky choice of cluster
  boundary.
* The number of pairs never enters G.

**4. Rules made precise in this version:**
* the reference day, the daily quote-volume formula and the rank tie-break (E2/E3, §1.1);
* the E4 count (684 of 720);
* the E7 definition and its mechanical enforcement (§1.1);
* the unit set S, shared by Models A and B (§5);
* episode construction and the value of a merged episode (§2);
* qualifying pairs (≥ 20 units in each of K and S∖K), the minimum of 8 qualifying pairs, the
  positive-pair share with Δ_p = 0 not positive, and the equal-pair-weight and tier definitions
  (§7, §9);
* Holm family sizes fixed, with p = 1 for non-evaluable cells (§7).
