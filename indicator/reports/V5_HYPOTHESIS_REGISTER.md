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

