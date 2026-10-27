# V5 workstream M, stages A and B: crypto price-only reference and BTC-regime context (1H/4H)

**Status: DRAFT** (2026-10-27). **Not frozen.**
* No code for this configuration exists yet, and no outcome under it has been computed.
* Open decisions are listed in §12. They must be resolved, and this file frozen in a commit of
  its own, before any detector, runner or outcome code for workstream M is written.

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
"Completed UTC days" means days that ended at or before t (the candle's **open**). This is
stricter than the close of candle i, so the same rule serves 1H and 4H.

| id | rule | rationale |
|---|---|---|
| E1 history | the pair's first cached 1H candle is ≥ 365 days before t | warm-up; excludes listing-pump months |
| E2 liquidity | the median, over the previous 30 **completed** UTC days, of daily quote volume ≥ **$5,000,000**. Daily quote volume = Σ over that day's 1H candles of volume × close; `volume` is Binance base volume, and USDT is taken as USD | absolute floor (decision D5) |
| E3 relative liquidity | on the previous completed UTC day, the pair's 30-day median from E2 ranks **≤ 25** among the non-BTC pairs that have a value that day | point-in-time "large and liquid" without hindsight on today's survivors |
| E4 completeness | ≥ 95% of the expected 1H candles are present in the previous 30 completed UTC days | exchange outages and gaps |
| E5 integrity | the candle is before the pair's integrity cut (V4.1 Amendment 1, already applied by `v5_data.load`) | token swaps (LUNA) |
| E6 warm | the target's `v5_state.classify(...)["warm"]` is True | as family C |
| E7 BTC available | a BTCUSDT candle with **the same open time** exists, and its state is warm (`direction_label` and `vol_regime` known) | missing context is never "neutral" |

**Failures are counted, not hidden.** A candle failing E7 is counted as **context-unavailable**,
per trial, per TF and per pair, and excluded from both stages. It is never kept as neutral, and
the count is reported.

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

**BTC episodes** (an evaluation unit, not a signal input):
* An episode of a field is a maximal run of candles with a constant value.
* A run shorter than H candles (§3) is merged into the preceding run. A leading short run merges
  into the following one.
* Episodes are computed per TF over the signal window.

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
* `rh`: side × (close[i+H] − open[i+1]) / ATR14[i], minus round trip and holding cost converted
  to ATR14[i] units. This is register §2.1 "after costs", computed through `v5_eval.trade(...,
  hold=H, stop=None)` net × open[i+1] / ATR14[i].
* `rh_x`: `rh` minus the **causal** benchmark (`v5_eval.causal_benchmark`):
  * stratum = (target `direction_label`, side);
  * `min_history` 200;
  * past-only.

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
* Per pair, the one-at-a-time book `v5_eval.sequential_daily`:
  * total log return;
  * maximum drawdown;
  * worst trade;
  * MAE distribution (5/50/95%).
* Reported per pair, per tier and pooled.

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

**Δ (primary contrast)** = mean metric over K − mean metric over S∖K, pooled over the eligible
non-BTC pairs. Units are signals.

**Three comparisons per cell.** All are reported, and the first two are decisive.

1. **Context vs the same price-only signals.** Kept K vs removed S∖K (Δ), and K vs all of S.
2. **Context vs matched removal (no BTC information).** 200 seeded replicates (seed 20261027)
   of a random subset R ⊂ S. Within each (pair, own `direction_label`) stratum, R has exactly as
   many signals as K. It uses only K's **total** count per stratum, never its timing.
   * Count matching per calendar block is not used: it would copy the BTC gate's timing into the
     control.
   * Statistic: mean(K) vs the 2.5/50/97.5 percentiles of mean(R) over replicates.
   * Matching is exact by construction (R ⊂ S, same counts). No shortfall can occur.
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
* OLS of x on [1, kept]. Δ is the coefficient.
* CR1 standard error, t(G−1) 95% CI.
* Wild cluster **restricted** bootstrap (Δ = 0 imposed): Rademacher if G ≥ 12, else Webb;
  9,999 replicates; seed 20261027.
* One-sided p for Δ > 0.
* Valid only if G ≥ 10.

It is run under **two** clusterings, and both are reported:
* **(a) calendar blocks** (`research.v41.cluster_id`: 1H 1 month, 4H 2 months);
* **(b) BTC episodes** of the gate's field (§2): `btc_dir` episodes for M-B1/B2/B4,
  `btc_unstable` episodes for M-B3.

**Decisive p** = the larger of the two. G and the number of episodes are printed next to every p.

**Per-pair results** (reported for every cell):
* Δ, n(K) and n(S∖K) per pair;
* the median of per-pair Δ over pairs with ≥ 20 signals in both K and S∖K;
* the share of those pairs with Δ > 0;
* an equal-pair-weight pooled Δ;
* tier-level Δ (majors, altcoins).

No per-pair p-values are used for any decision.

**Multiple testing.**
* Holm within each hypothesis, over its cells: M-B1 8, M-B2 8, M-B3 16, M-B4 4. This is the
  decision (decision D2).
* Holm across all 36 cells is reported as a sensitivity.
* Stage-A results carry no tests that feed a decision.

## 8. Evaluability (per cell)

A cell is **evaluable** only if all of these hold:
* ≥ 100 kept and ≥ 100 removed signals;
* ≥ 10 pairs with at least one signal in each set;
* G ≥ 10 under **both** clusterings;
* ≥ 3 BTC episodes of the gate value **and** ≥ 3 of its complement containing eligible signals.

A non-evaluable cell is reported as such and is neither "adds value" nor "no value".

## 9. Decision rules (frozen with this file; applied mechanically)

**Per evaluable cell:**
* **ADDS VALUE (exploratory)** if **all** of:
  1. pooled Δ > 0 **and** equal-pair-weight Δ > 0;
  2. the median of per-pair Δ > 0, and Δ > 0 in ≥ 60% of the qualifying pairs (§7);
  3. Holm-adjusted decisive p < 0.05 (§7);
  4. mean(K) > the 97.5th percentile of the matched-removal replicates (§5, comparison 2);
  5. altcoin-tier Δ > 0. Pooled results must not rest on ETH/SOL alone.
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

## 12. Decisions before freezing

Each decision has a recommended default. The file is frozen with the defaults unless the owner
chooses otherwise.

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
