# V4.1 pre-registration: H6 (trend state), H7 (compression/expansion), H1r (incremental structure-break value)

Written and committed **before any V4.1 code was written, any V4.1 data was downloaded, or any
V4.1 number was computed**. Changes after this commit are allowed only as numbered amendments
below, each committed before the holdout run, with its reason. The production indicator
(`pine/`, `HC-MTF_*.txt`) and the engine (`hcmtf/`) are not modified.

## 0. What kind of study this is

* **No untouched forward data exists.** The cache ends 2026-10-27, which is today. Every date
  up to today has been examined in v1–V4 on the 70 existing symbols.
* **The holdout is cross-sectional.** It uses 38 instruments that have never been downloaded
  (`ls indicator/data`), loaded or referenced in code. The only mention anywhere in git history
  is the proposal list in `reports/V4_DATA_AND_VALIDATION_GAPS.md` §4, verified with `git grep`
  over all revisions on 2026-10-27; the hits for `CAT` are unrelated art code. Four rates
  instruments and four FX pairs were added here for the rates/FX group and are equally unused.
* **They cover the same calendar period as the seen data.** Many are correlated with seen
  instruments (e.g. XLK with QQQ, XLF with JPM, USD pairs with USD pairs). So this guards
  against symbol-selection overfitting, but **not** against period or regime overfitting.
* **What the holdout can and cannot give.** A positive holdout result is therefore at most
  **RETAIN FOR FURTHER TESTING**, never "confirmed out of sample". Confirmation is reserved for
  the forward test in §9.
* **The 70 seen symbols are run too.** This is stage **D** (exploratory). It is used for code
  debugging and context only, and **no decision uses stage D**. Decisions use stage **H**
  (the holdout).
* **These hypotheses were not formed blind.** H6, H7 and H1r were formulated after V3/V4 results
  on the seen symbols (`V4_HYPOTHESIS_REGISTER.md`). The holdout data has not influenced them.

## 1. Data

### Stage H: holdout instruments (never used before)

| group | instruments | source | class / round-trip cost |
|---|---|---|---|
| crypto | AVAXUSDT, NEARUSDT, UNIUSDT, AAVEUSDT, XTZUSDT, EOSUSDT, VETUSDT, THETAUSDT, HBARUSDT, ICPUSDT | Binance spot | crypto, 20 bp |
| equities | ORCL, CSCO, HD, MRK, PG, UNH, CAT, MMM, PEP, ADBE | Yahoo | equity, 6 bp |
| equities (ETFs) | XLE, XLF, XLK, XLU, EWG, EWU | Yahoo | equity_index, 4 bp |
| commodities | PPLT, PALL, WEAT, DBB | Yahoo | commodity, 8 bp |
| rates & FX | TIP, SHY, MUB, EMB | Yahoo | bond, 4 bp |
| rates & FX | USDSEK=X, USDNOK=X, USDMXN=X, USDZAR=X | Yahoo | fx, 3 bp |

* Volume flag: true except FX. Session: `24h` for crypto and FX, `rth` otherwise. This follows
  the existing `universe.py` conventions.
* **Stage D (exploratory)**: `universe.UNIVERSE + universe.FRESH` (70 symbols), already cached.
* **Native data**: 1h and 1d, fetched by the existing `hcmtf.data` functions. 4H, 1W, 1M and 3M
  are resampled by the existing `hcmtf.data.load`. Yahoo 1h is limited to the last ~730 days.

**Evaluation windows**, with the start chosen to match v3:

| TF | start | end |
|---|---|---|
| 1H, 4H | the later of 2020-01-01 and the first candle | last complete candle in the frozen data |
| 1D, 1W | the later of 2010-01-01 and the first candle | last complete candle in the frozen data |

Earlier history is used for warm-up only.

**Mechanical exclusions**, decided on counts only and never on outcomes:

* an instrument × TF with fewer than 300 candles in its window is dropped;
* an instrument whose download fails after the existing retry logic is dropped and listed.

A **data-freeze manifest** (`reports/V4_1_DATA_MANIFEST.json`: sha256, rows and span of every
holdout file) is committed after download and **before** the holdout run.

## 2. The HTF trend state (defined from the existing code, unchanged)

* **HTF trend**, `hcmtf.htf.trend_state(df, n=21)`, on the HTF candle:
  * `+1` if close > EMA21 and EMA21 > EMA21[1];
  * `−1` if close < EMA21 and EMA21 < EMA21[1];
  * `0` otherwise (NaN during warm-up).
* **Alignment**, `hcmtf.htf.align`: each chart candle gets the value of the last **completed**
  HTF candle. This is the Pine `request.security(..., f()[1], lookahead_on)` idiom.
* **Ladder**, `hcmtf.engine.LADDER`:

  | chart | HTF1 | HTF2 |
  |---|---|---|
  | 1H | 4H | 1D |
  | 4H | 1D | 1W |
  | 1D | 1W | 1M |
  | 1W | 1M | 3M |

* **State for side d** (+1 bullish, −1 bearish), exactly as `engine.breaks`:
  * a1 = nan_to_num(t1·d) and a2 = nan_to_num(t2·d);
  * **against** = a1 < 0 or a2 < 0;
  * **with** = a1 + a2 ≥ 1 and not against;
  * **neutral** otherwise.

  A NaN HTF2 counts as 0, as in the engine. On TradingView it is `na`, and the code treats it the
  same way.
* **Bullish state** = with(+1). **Bearish state** = with(−1). A chart candle is eligible only
  when ATR(14) and t1 are defined.

## 3. Outcomes (unchanged from v3/V4)

* Signal known at the close of candle i. Entry at the open of i+1.
* **r_h** = d·(close[i+H] − open[i+1])/ATR14[i] − cost·open[i+1]/ATR14[i], from
  `hcmtf.evaluate.bar_outcomes`.
* **Primary horizon H**: 1H 24, 4H 30, 1D 20, 1W 13 candles. **Secondary**: H/4 (min 3) and 2H.
* **Costs**: as in §1, round trip.

## 4. Hypotheses, events and benchmarks

All benchmarks are per-instrument means of the same outcome over a stated set of candles in the
same evaluation window. **Excess** = event outcome − benchmark.

### H6. HTF trend state alone (time-series momentum)

* **Units**: every eligible candle in the bullish state (long, d = +1) and, separately, every
  eligible candle in the bearish state (short, d = −1).
* **Primary statistic**: mean excess of r_h over **U** = the same instrument, same side, all
  eligible candles. This tests whether being in the state beats static exposure; constant
  drift cancels.
* **Secondary benchmarks**:
  * **V**, causal regime: same instrument, same side, same ATR%-tercile at the candle.
    ATR% = ATR14/close; tercile from `engine.percentrank` over the previous 200 candles,
    cut at 33.3 and 66.7.
  * **Y**, ex-post drift diagnostic: same instrument, same side, same calendar year. Not causal;
    it measures timing within a year.
* **Secondary variants**:
  * onset events, i.e. the first candle of each bullish/bearish run, against U;
  * the state lagged by one extra HTF1 candle (timing sensitivity);
  * horizons H/4 and 2H.
* **Trading view (secondary)**: per instrument, hold +1 in the bullish state (long test) or −1 in
  the bearish state (short test), 0 otherwise. The position is decided at a candle's close and
  held open-to-open from the next candle. Cost = half the round trip per unit of position change.
  Instruments are equal-weighted daily. Compared with static always-long / always-short.
  Reports CAGR, volatility, Sharpe with a 20-day block-bootstrap 95% CI, and max drawdown,
  using `hcmtf.metrics._perf`.
* **Drift question**:
  * premium > 0 against U on **both** sides → the state predicts time variation in returns;
  * premium only on one side, the other ≤ 0 → consistent with drift/asymmetry, not two-sided
    prediction;
  * Y is reported to show how much of any premium is slow (year-level) drift variation.

### H7. Volatility compression → expansion

* **Compressed candle**: ATR%-percentile < 33.3 (as in V above).
* **Run**: consecutive compressed candles.
* **Minimum run length** k, fixed from `V4_HYPOTHESIS_REGISTER.md`: 1H 24, 4H 12, 1D 10, 1W 6.
* **Event**:
  * Event at candle t when (i) the run of compressed candles ending at t−1 has length ≥ k and
    (ii) close_t > box high (up event) or close_t < box low (down event).
  * Box high and box low are the highest high and lowest low of that run (from its first
    candle to t−1).
  * After an event the run counter restarts at t+1; one event per episode.
  * All inputs are known at the close of t.
* **H7v, volatility claim** (direction-free). Outcome:
  * RVR = log( mean true range over candles t+1..t+H / ATR14[t] ).
  * Primary benchmark **L**: same instrument, all compressed candles (same outcome).
  * Secondary benchmark U: all eligible candles.
* **H7m, magnitude** (direction-free, secondary). |close[t+H] − open[t+1]|/ATR14[t] against L.
* **H7d, direction claim**, up and down events separately. Outcome r_h in the event's direction.
  * Primary benchmark **L_d**: same instrument, same side, all compressed candles.
  * Secondary benchmark: U.
* **Secondary exit**: the earlier of a close back inside the box and H candles.

Expansion is **not** assumed bullish or bearish; up and down events are tested separately and
H7v/H7m ignore direction.

### H1r. Incremental value of a structure break over the state

Three event sets on identical candles, all inside the state of the same side d, with the same
outcome r_h:

* **S, state alone** (the H6 units): the benchmark.
* **B, state + structure break**: candles where `hcmtf.engine.breaks` (shipped `DEFAULTS`
  pivots, no evidence, no filters) reports a break in direction d with `htf_with` true, i.e.
  continuation + realignment = v3 C1, no cooldown.
  * Secondary sub-sets: continuation only; realignment only (= MAJOR before cooldown).
* **M, state + simple momentum**: candles where ROC20 = close/close[20] − 1 changes sign to d
  (sign(ROC20_t) = d and sign(ROC20_{t−1}) ≠ d), no cooldown.

Primary statistic: **mean excess of B over S** (same instrument, same side, all state candles).
Secondary: M over S, and B − M (difference of the two excesses, same clusters).

**Target cell** (from the register): 4H crypto bullish **continuation** over S. It is rejected if
the 95% CI of the mean excess includes 0 or the median excess ≤ 0.

## 5. Inference

* **Cells**: TF × group × side. Groups:
  * crypto;
  * equities (stocks + ETFs);
  * commodities;
  * rates & FX.

  An all-groups pooled cell is reported per TF × side for the rejection rule.
* **Dependence**: block cluster bootstrap, 5,000 replicates, seed 20261027. A cluster is a
  calendar block of fixed length, shared by **all instruments in the cell**, which handles
  cross-asset dependence:

  | TF | cluster length | longest horizon in calendar time |
  |---|---|---|
  | 1H | 1 month | ≤ ~4 trading days |
  | 4H | 2 months | ≤ ~3 weeks |
  | 1D | 3 months | ~4 weeks |
  | 1W | 12 months | ~3 months |

  Residual overlap of outcome windows across block edges is disclosed, not removed.
* **Re-estimation**: in every replicate the per-instrument (and per-stratum) benchmark means are
  recomputed from the resampled clusters, so benchmark uncertainty is included.
* **Reported per cell**:
  * n units, instruments and clusters;
  * mean excess with its 95% percentile CI;
  * one-sided p = (1 + #replicates with mean ≤ 0)/(5,001);
  * median excess (point);
  * mean outcome, median outcome;
  * MFE/MAE where applicable;
  * mean without the top 1% of units.
* **Chronological consistency (forward-ordered, purged)**:
  * Each cell's window is split into three equal calendar spans.
  * A unit counts in a span only if its outcome window (candle i+H) also ends inside that span:
    this purges overlap across span boundaries.
  * Mean excess per span is reported (benchmark = the instrument's full-window benchmark).
* **Regimes**: causal ATR%-tercile at the unit; the three chronological spans.
* **Evaluable cell**: ≥ 100 units, ≥ 3 instruments and ≥ 8 clusters with units. Decided from
  counts only. Non-evaluable cells are reported and not tested.
* **Multiple comparisons**:
  * Holm over the evaluable primary tests within each family:
    * H6, up to 32;
    * H7v, up to 16;
    * H7d, up to 32;
    * H1r, up to 32 + the target cell.
  * A global Holm over all families is reported as a sensitivity.
  * Earlier experimentation on the seen symbols (hundreds of comparisons) shaped the hypotheses,
    not the holdout data. It is disclosed, not corrected for.
* **Minimum effect of interest** (decided now):

  | statistic | MEI |
  |---|---|
  | r_h-based (H6, H7d, H1r) | 0.10 ATR per H-horizon after costs |
  | RVR (H7v) | 0.05 (≈ 5% more realised range) |

## 6. Decision rules (one decision per hypothesis, from stage H only)

A **passing cell** meets all of:

* Holm-adjusted p < 0.05 within its family;
* mean excess ≥ MEI;
* median excess > 0;
* mean excess > 0 in ≥ 2 of the 3 purged chronological spans.

| hypothesis | RETAIN FOR FURTHER TESTING | REJECT | INCONCLUSIVE |
|---|---|---|---|
| H6 | in at least one TF, ≥ 2 groups have passing cells on **both** sides | no passing cell on either side, **and** for every TF × side the all-groups pooled mean excess has a 95% CI upper bound < MEI | otherwise, including one-sided-only passes |
| H7v | in at least one TF, ≥ 2 groups pass | no passing cell, and every TF's pooled CI upper bound < MEI | otherwise |
| H7d | in at least one TF, ≥ 2 groups pass on **both** up and down events | as H6 | otherwise, including one-sided-only passes |
| H1r | in at least one TF and side, ≥ 2 groups pass, **and** in each of them B − M ≥ 0 (point estimate) | as H6 | otherwise |

The H1r target cell is decided separately by its register rule (§4) and reported.

"Merely market drift" for H6 is reported as a finding when passing cells are one-sided. That
case gives INCONCLUSIVE, never RETAIN.

## 7. Procedure and freeze points

1. This file is committed.
2. Code: `research/v41.py`, `research/universe41.py`, `scripts/v41_fetch.py`, `scripts/v41_run.py`,
   `tests/test_v41.py`. Unit tests on synthetic data cover:
   * causality: truncating the future never changes a state or an event;
   * the event definitions;
   * the bootstrap with re-estimated benchmarks.
3. Stage D run (exploratory) on the 70 seen symbols. **Bugs may be fixed. Definitions in §2–§6 may
   not change** except by a numbered amendment committed before step 5.
4. Holdout data fetched; `V4_1_DATA_MANIFEST.json` committed with the sha256 of the frozen code
   files (**configuration hash**).
5. Stage H run, **once**, with the frozen code. Its results are reported whatever they are.
6. Reports:
   * `V4_1_H6_RESULTS.md`;
   * `V4_1_H7_RESULTS.md`;
   * `V4_1_INCREMENTAL_VALUE.md`;
   * `V4_1_FINAL_RECOMMENDATION.md`.

## 8. What is not done

* No production change.
* No new indicator unless a hypothesis meets RETAIN *and* later passes §9.
* No tuning of k, n, EMA length, horizons or thresholds.
* No new dependencies.

## 9. Forward confirmation (registered now, run later)

* **Data**: all 108 instruments (70 seen + 38 holdout), candles **opening after
  2026-10-27 23:59 UTC**, with the same definitions and code hash.
* **Earliest evaluation dates**, chosen so the forward set has roughly ≥ 8 clusters:

  | TF | earliest evaluation |
  |---|---|
  | 1H | 2027-07-01 |
  | 4H | 2028-01-01 |
  | 1D | 2029-01-01 |
  | 1W | not before 2034 (likely never adequately sampled) |

* Only hypotheses RETAINED here are tested forward.

## Amendments

### Amendment 1 (committed 2026-10-27, after the stage D debug run, before any holdout computation)

* **Trigger.** Stage D's trading view showed an always-long crypto volatility of ~3,967% a year.
  The cause is LUNAUSDT: its daily open-to-open price moves ×3,124 on 2022-05-13, and the ticker
  later trades a different token (LUNA 2.0). That is a token swap or relisting, not a market move.
* **Rule.** For every instrument, find the first day whose next daily open is more than 20× or
  less than 1/20 of its own open. All its candles from that day on are excluded on every TF,
  together with their HTF frames (`research.v41.integrity_cut`).
* **Scope.** Applied to both stages.
* **Thresholds.** The 20× threshold is fixed here. Moves that are large but real stay in. In the
  seen data:
  * DOGE ×4.9 (2021-01-28);
  * FIL ×6.3 (2020-10-15);
  * SRM ×14.2 on its first trading day.
* **What it changes.** Only LUNAUSDT is affected in the seen data, from 2022-05-12. Holdout
  instruments are screened by the same code at run time, and any cut is reported. No definition
  in §2–§6 changes.
* **Disclosure.** The same LUNAUSDT artifact is present in the v3 and V4 data. It is noted in the
  V4.1 reports and was not re-run.
