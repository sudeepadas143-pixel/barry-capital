# V5 hypothesis register: four signal families

* **Supersedes** `V4_HYPOTHESIS_REGISTER.md` as the live register. That file and every earlier
  report stay unchanged as the historical record.
* **Companion documents**:
  * plan: [`V5_DEVELOPMENT_PLAN.md`](V5_DEVELOPMENT_PLAN.md);
  * data roles: [`V5_DATA_AUDIT.md`](V5_DATA_AUDIT.md);
  * gates and statistics: [`V5_VALIDATION_PROTOCOL.md`](V5_VALIDATION_PROTOCOL.md).
* **Not an outcome.** Registering a hypothesis here is not evidence for it. No V5 detector has
  been built or evaluated.
* **Two stages.** Each hypothesis is first explored on examined data, then confirmed on reserved
  data. The confirmatory parameters are frozen at gate G2 of the protocol, before the
  confirmatory data is examined.

## 1. What is already known (carried forward, with sources)

### Established (software, not prediction)

| item | evidence |
|---|---|
| Closed-candle signals never change after they print; HTF values come from completed HTF candles only (`f()[1]` + `lookahead_on`); the LTF reads only candles inside the closed chart candle | `tests/test_integrity.py`, `tests/test_engine_v2.py` (truncation, finality) |
| Pine logic equals the Python engine (hand transliteration) | `tests/test_pine_mirror.py`, `tests/test_engine_v2.py::test_pine_v2_logic_matches_engine` |
| Bullish and bearish engine logic are exact mirrors | `tests/test_v4_symmetry.py` |
| Python trade simulator reproduced by backtrader and backtesting.py | `reports/BACKTRADER_CROSSCHECK.md`, `reports/BACKTESTINGPY.md` |

### Rejected by evidence

| id | hypothesis | where |
|---|---|---|
| H0 | raw MTF structure break predicts continuation | V4 F1 |
| H2 | shipped MAJOR (realignment / pullback end) | V3, V4 |
| H3 | counter-HTF change of character as an early-reversal *trade entry* at horizon H | V3 C6, V4 |
| H4 | counter-HTF continuation | V4 |
| H5 | 14 confluence components, acceptance, strict HTF | v2 screening, audit, V3 |
| H1r-target | 4H crypto bullish continuation break (median −0.44 on the holdout) | V4.1 |

### Inconclusive

| id | hypothesis | status |
|---|---|---|
| H6 | HTF trend state alone | crypto 1H/4H two-sided mean premium, median ≤ 0; **frozen forward test**, V4.1 §9 |
| H7v | more realised range after compression breakouts | crypto 1H only; **frozen forward test** |
| H7d | breakout direction | no signal, wide CIs |
| H1r | break increment over the state | no passing cell |

### Untested

* Every hypothesis in §3.
* LTF triggers as defined below.
* Short-side borrow and funding costs.
* Real TradingView-export parity.
* The Pine strategy-twin stop-reset fix (V4 F5a).

**Implications carried into V5:**
* Structure breaks are not a source of edge by themselves.
* Equities showed short-horizon mean reversion inside HTF states (V4.1 H6), so trend-following
  continuation rules cannot be assumed to transfer across asset classes.
* Means are tail-driven almost everywhere, so medians are co-primary.

## 2. Target events (objective definitions; frozen 2026-10-27 before any label was counted)

### 2.1 Continuation outcomes (families A and B)

* **Entry and horizon.** Entry at the next open after the signal candle closes. Outcome r_h is
  the move in the signal's direction to candle H, in ATR14 at the signal, after costs:

  | TF | H (candles) | short horizon H/4 | long horizon 2H |
  |---|---:|---:|---:|
  | 1H | 24 | 6 | 48 |
  | 4H | 30 | 8 | 60 |
  | 1D | 20 | 5 | 40 |
  | 1W | 13 | 3 | 26 |

  These are the same horizons as v3–V4.1, so results stay comparable.
* **Also reported**: MFE and MAE over H; the +2/−1 ATR barrier; and a trade-level outcome with a
  structural stop (the trigger's invalidation level) and a time exit at 2H.

### 2.2 Major tops and major bottoms (families C and D)

Implemented in `research/v5_labels.py` and tested in `tests/test_v5_plan.py`. These labels use
future data and exist **only** to score detectors.

**Major top at candle t** (radius L, forward window F, size D in ATR14[t]):

* (a) high[t] is the highest high of t−L … t+L (first occurrence wins ties);
* (b) prior advance: high[t] − min(low[t−L … t]) ≥ D·ATR14[t];
* (c) within t+1 … t+F, price reaches high[t] − D·ATR14[t] *before* any high exceeds high[t].

**Major bottom at candle t**: a separate definition with the same structure on lows:

* (a) low[t] is the lowest low of t−L … t+L;
* (b) prior decline ≥ D·ATR14[t];
* (c) price reaches low[t] + D·ATR14[t] before any low undercuts low[t].

Parameters (`TOP_PARAMS` and `BOTTOM_PARAMS`, currently identical):

| TF | L (radius) | F (forward window) | D (size, ATR14) |
|---|---|---|---|
| 1H | 168 (1 week) | 336 | 8 |
| 4H | 126 (3 weeks) | 252 | 8 |
| 1D | 63 (≈ 3 months) | 126 | 8 |
| 1W | 26 (6 months) | 52 | 5 |

* **Why these numbers.** They were chosen a priori: a swing radius that a trader would call a
  major turn on that chart, and a size of several typical candle ranges.
* **Not a symmetry assumption.** Tops and bottoms start with the same numbers by registration,
  not because they are assumed to behave alike; each family is evaluated on its own labels.
* **Changing the definitions** requires a logged amendment with a reason and a date, before any
  confirmatory data is used.
* **The label counts** in `V5_DATA_AUDIT.md` are for sample planning only. They may not be used
  to retune L, F or D.

**Scoring a top/bottom detector** against the labels:

* **Recall.** The share of labelled events with a warning (or confirmation) in t−W … t+K.
  W (warning look-back) is L/2 candles; K (confirmation look-forward) is L candles.
* **Lead time.** Candles from the first warning to t; negative means the warning came after the
  extreme.
* **False alarms.**
  * A warning is false if no labelled event of its family falls in its window
    [s − K, s + W], where s is the signal candle.
  * A confirmation is false if none falls in [s − K, s].
  * Reported per 100 candles and as a share of signals.
* **Move remaining after confirmation.** `remaining_fraction(extreme, close at confirmation,
  final extreme)`, where the final extreme is the lowest low (tops) or highest high (bottoms)
  within F candles of t: 1 means confirmed at the extreme, 0 means at the end of the move.
* **Trade outcome.** r_h of a short (tops) or long (bottoms) entered at the next open, with
  costs. For shorts this includes the short-side costs in the protocol.

## 3. Hypotheses by workstream

Every hypothesis in this section starts with status **untested** and stage **exploration**.

Columns:
* *role*: **W** = early warning (exhaustion), **C** = confirmed signal.
* *falsified if*: what would reject the hypothesis at confirmation. The full acceptance criteria
  are in protocol §6.

### Workstream A: bullish continuation

| id | market behaviour | trigger (causal, closed candle) | benchmarks (matched) | falsified if |
|---|---|---|---|---|
| A1 | In a bullish HTF state, a pullback of a measured depth that then resumes continues further than the state alone | HTF bullish state; MTF pullback depth in an ATR band from the last swing high; LTF resumption trigger (e.g. the LTF closes back above its own last swing high inside the closed chart candle) | S (all bullish-state candles); M (ROC20 turn); **matched**: random candles in the same instrument, state and pullback-depth band | mean excess vs matched ≤ MEI, or median ≤ 0, at confirmation |
| A2 | Shallow pullbacks (strong trends) and deep pullbacks behave differently | A1 split by depth band | same | no depth band beats matched entries |

**Prior:** V4.1 found that the existing structure break adds nothing over the state (H1r). A1
differs in requiring a measured pullback and an LTF resumption, but the prior is weak.

### Workstream B: bearish continuation

Developed independently of A. **Not a mirror of A.**

| id | market behaviour | trigger | benchmarks | falsified if |
|---|---|---|---|---|
| B1 | Failed rally: in a bearish HTF state, a rally into the MTF EMA21 band that closes back below it continues lower | HTF bearish; MTF close crosses back below EMA21 after a close above it within k candles | S (bearish-state candles), M, matched failed-rally-free candles | as A1, **after short costs** |
| B2 | Breakdown: a close below the lowest low of the last N MTF candles in a bearish HTF state, with range expansion, continues | HTF bearish; close < N-candle low; true range ≥ q-percentile | S, M, matched | as A1 after short costs |
| B3 | Squeeze risk (descriptive, not a signal) | the share of B1/B2 signals with MAE ≥ 3 ATR within H; worst 1% of outcomes; gap-through-stop rate | the same statistics for S | reported; a family whose squeeze tail wipes out its mean is rejected for release |

### Workstream C: major tops and bearish reversals

Scored against the major-top labels.

| id | role | evidence | detector (causal) | benchmark |
|---|---|---|---|---|
| C1 | W | trend extension | MTF close ≥ x ATR above the HTF EMA21, or in the top percentile of its own extension history | random warnings at matched frequency within the same HTF-bullish state |
| C2 | W | momentum divergence | MTF confirmed pivot high above the previous pivot high, while RSI14 at the pivot is below RSI14 at the previous pivot | as C1, and C1 alone |
| C3 | W/C | failed breakout | close above the last confirmed swing high, then a close back below it within k candles | C1, C2 |
| C4 | W | volatility change | after an extension (C1), an ATR%-percentile jump on a down candle | C1 |
| C5 | C | structural failure | MTF bearish change of character after a C1–C4 warning, in a bullish or neutral HTF | HTF trend flip (bearish state onset), EMA20/50 cross, Supertrend flip, engine counter_reversal |

**Prior:** C5 resembles engine `counter_reversal`, which failed as a trade entry (H3). Here the
target is a labelled major top, which is a different question, but expectations are low.

### Workstream D: major bottoms and bullish reversals

Separate from C. Its own labels and its own evidence.

| id | role | evidence | detector (causal) | benchmark |
|---|---|---|---|---|
| D1 | W | selling exhaustion | MTF close ≥ x ATR below the HTF EMA21 with a range/volume climax (true range and relative volume in their top percentile; volume only where meaningful) | random warnings at matched frequency in the HTF-bearish state |
| D2 | W | bullish divergence | lower confirmed pivot low with a higher RSI14 | D1 |
| D3 | W/C | failed breakdown (sweep and reclaim) | a low below the last swing low, then a close back above it within k candles | D1, D2 |
| D4 | W | momentum recovery | RSI14 back above 50 and MACD histogram > 0 after a D1 warning | D1 |
| D5 | C | structural reclamation | MTF bullish change of character after a D1–D4 warning | HTF bullish-state onset, EMA20/50 cross, Supertrend flip, engine counter_reversal |

**Prior:** the v2 "liquidity sweep" component failed as a confluence filter. D3 tests it as a
reversal detector against labelled bottoms instead.

### Workstream E: architecture questions (decided by tests, not assumed)

| id | question | test |
|---|---|---|
| E1 | Does a shared market-state classifier (HTF state × volatility tercile × extension bucket) separate outcomes enough to condition every family? | between-state outcome differences with cluster CIs on exploration data, then confirmed |
| E2 | Do early warnings (W) and confirmed signals (C) need separate markers? | separate markers only if W shows lead time > 0 with recall above the matched-frequency benchmark **and** C shows a higher precision than W; otherwise one marker or none |
| E3 | Does an LTF trigger add value over the same MTF setup without it? | paired comparison: setup + trigger vs setup at the next MTF close |

## 4. Multiple testing and trial accounting

* **Exploration** may try variants freely, but every evaluated variant is logged with its date
  and result in a trial ledger (`reports/V5_TRIAL_LEDGER.md`, created by the first exploratory
  run). Exploratory results are never quoted as evidence of an edge.
* **Confirmation** follows a pre-registration per family that fixes:
  * at most **three** frozen variants per family (A, B, C, D);
  * the confirmatory cells (TF × group × side);
  * Holm within the family at α = 0.05, plus a global Holm across families as a sensitivity;
  * the exploration trial count, disclosed and used for a deflated-Sharpe-style sensitivity
    where a Sharpe ratio is reported.

## Amendments

### Amendment M1 (2026-10-27): workstream M, crypto market context

Hypotheses added for the crypto-only workstream M, stages A and B. They are defined, with gates,
cells, statistics and decision rules, in [`V5_M_B_CONFIG.md`](V5_M_B_CONFIG.md), which was
frozen before any M code was written or any M outcome computed. All start **untested**, at stage
**exploration**.

| id | statement (short) |
|---|---|
| M-A | price-only reference (S-eng, S-htf, S-ema, S-st, R-cr): no pass/fail rule |
| M-B1 | long continuation signals do better when BTC is bull, within the pair's own state |
| M-B2 | short continuation signals do better when BTC is bear, after short costs |
| M-B3 | continuation signals do better outside BTC high-volatility periods |
| M-B4 | reversal alerts land near labelled major turns more often when BTC is not with the old trend |

They do not change any earlier hypothesis, label or event definition.

### Amendment V6-1 (2026-10-28): HC-MTF 6.0 stage 1, continuation models A–D

The HC-MTF 6.0 track adds an EMA trend-and-pullback baseline (A) and three incremental filters:
RSI (B), MACD (C) and ATR extension (D). Definitions, ten predefined alternatives, contrasts and
decision rules are in [`V6_CONT_CONFIG.md`](V6_CONT_CONFIG.md), frozen before any V6 code or
outcome. Ledger ids: `V6-P` (primary config), `V6-S` (alternatives). Status: untested,
exploration. No earlier hypothesis or definition changes.

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
