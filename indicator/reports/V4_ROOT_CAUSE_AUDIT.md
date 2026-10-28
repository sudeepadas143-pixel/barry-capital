# V4 root-cause audit: why the HC-MTF signal engine fails

**Decision: REPLACE HYPOTHESIS.** The engine does what its code says, without look-ahead.
But the market behaviour it is built on has no measurable predictive value once the obvious
controls are applied. That behaviour is that a confirmed swing-structure break, taken in the
higher-timeframe (HTF) direction, is a good entry. Adding filters to it would be selecting
from noise.

Scope and honesty notes:

* Every number here comes from data already examined in v1 to v3, so it is **diagnostic, not
  confirmatory**. The analysis plan ([`V4_ANALYSIS_PLAN.md`](V4_ANALYSIS_PLAN.md), commit
  `e62033f`) was committed before any V4 number existed.
* Full tables: [`V4_TABLES.md`](V4_TABLES.md). Raw output: `reports/v4_root_cause.json`.
  Script: `scripts/v4_root_cause.py`.
* Nothing in `pine/`, `hcmtf/`, `HC-MTF_*.txt` or `reports/active_config.json` was changed
  (see the change log in [`V4_FINAL_HANDOFF_REPORT.md`](V4_FINAL_HANDOFF_REPORT.md) §7).

How to read the numbers:

* **r_h** is the move in the signal's direction to candle H, in ATR(14), after costs.
  H is 24 candles on 1H, 30 on 4H, 20 on 1D and 13 on 1W.
* **Excess** = r_h minus a per-event control on the same symbol and side. The controls are:
  * **R0**: every candle of that symbol.
  * **R1a**: the 2H candles right after the event.
  * **R2**: candles of the same year in the same HTF state.
* The results show mean [95% month-cluster CI].

## 1. What the engine actually does, stage by stage

| # | stage | code | actual condition | how it creates or blocks a signal |
|---|---|---|---|---|
| 1 | inputs | `hcmtf/data.py` `load`, `study.build_ctx` | OHLCV; 4H/1W/1M/3M resampled (weeks start Monday, US-session 4H); LTF 15m only for Binance crypto | Non-crypto intraday data starts 2023-11-28 (Yahoo limit), so those cells cover only ~35 months |
| 2 | swings | `ta.pivots` | a high is strictly above the `left` bars before it and at least as high as the `right` bars after it; reported `right` bars later (1H/4H 5/3, 1D 5/2, 1W 4/2) | the source of lag: a swing is known 2–3 candles after it forms |
| 3 | break / CHoCH | `engine.breaks` L299–331 | close beyond the latest unused swing high/low; a level is used once; `choch` = break against the current MTF structure | ~1 break per 10–15 candles; each level fires once |
| 4 | HTF context | `htf.trend_state`, `htf.align`, `engine.breaks` L340–350 | HTF trend = close vs EMA21 and EMA slope agree, read from the **previous completed** HTF candle; with = HTF1+HTF2 ≥ 1 and neither against | removes everything not in the HTF direction; on 1W the HTFs are 1M/3M (EMA21 ≈ 1.75 / 5.25 years) |
| 5 | evidence and filters | `engine.score` | `reports/active_config.json`: evidence = (), filters = () | no effect in the shipped configuration (screening kept nothing) |
| 6 | classes | `engine.breaks` L349 | continuation, realignment (CHoCH back into the HTF direction), counter_reversal, counter_continuation, neutral | |
| 7 | tiers | `engine.classify` L456–497 | MAJOR = realignment with HTF; CONFIRMED = continuation with HTF; counter_reversal = WATCH (never drawn) | **the only drawn signal is the end of a pullback inside an existing HTF trend** |
| 8 | de-duplication | `engine.classify` L483 | same direction within `cooldown` candles (12/6/5/4) of the last MAJOR/CONFIRMED is skipped | shared between tiers; suppresses repeats |
| 9 | drawing | `pine/HighConvictionMTF.pine` `showSig` | MAJOR only unless "Also mark continuation breaks" is on | |
| 10 | strategy twin | `pine/HighConvictionMTF_strategy.pine` trade block; Python `evaluate.simulate` | next-open entry, 2 ATR initial stop, 3 ATR trail from the best close, reversal on an opposite signal, time exit 72/60/60/26 | see finding F5: Pine resets the stop and the time clock on a same-direction signal |

**Symmetry.** Bullish and bearish logic are exact mirror images. This was checked by code reading
and by a new test, `tests/test_v4_symmetry.py`: with every price negated, the engine gives the
same breaks, classes and signals on the same candles, with the direction flipped, including the
HTF states. The single asymmetry in the code is the tie-break when one candle closes through
both swing levels: bullish if close ≥ open (`engine.breaks` L321). Its frequency was not
measured; the symmetry test never hit it. **Directional imbalance in the output therefore comes
from the data**, through the trending HTF filter, not from asymmetric code.

## 2. Ranked findings

### F1 (highest impact). A structure break carries no timing information after controls. CONFIRMED

Measurement: every warm break on 70 symbols × 4 timeframes, split by class, group and side.
That gives 364 cells, of which 302 are adequately sampled (≥ 100 events in ≥ 24 months).

* **Pre-declared rule** (CI lower bound > 0 against both the local ±2H control and R2, median > 0,
  robust to dropping the top 1%): **0 of 302** cells pass.
* **Post-hoc variant** using the after-only local control R1a: **3 of 302** pass (about 1%, a rate
  chance alone can produce):
  * 4H crypto bullish continuation and CONFIRMED (largely the same events);
  * 1D crypto bearish **EMA 20/50 cross**, which is a baseline, not the engine.
* **All breaks against unconditional random entries on the same symbol and side (R0)**:

  | TF · group | bullish | bearish |
  |---|---|---|
  | 1H crypto | +0.02 [−0.14, +0.17] | −0.01 [−0.16, +0.14] |
  | 1D equities | −0.11 [−0.39, +0.16] | −0.19 [−0.54, +0.23] |
  | 1W equities | −0.05 [−0.32, +0.22] | −0.41 [−0.76, −0.03] |

* **All breaks against the same year and HTF state (R2)**: zero or negative almost everywhere.
  On 1D/1W, 11 of the 16 non-crypto group × side cells have a 95% CI upper bound ≤ 0.00, among them:

  | TF · group · side | xR2 |
  |---|---|
  | 1D equities bullish | −0.24 [−0.50, −0.00] |
  | 1W equities bullish | −0.37 [−0.58, −0.17] |
  | 1W commodities bearish | −0.44 [−0.74, −0.13] |

  A break is, if anything, a slightly worse entry than a random candle in the same HTF state.
* **"Looks right on the chart" does not mean predictive.** The share of signals that reach
  +2 ATR within H is the same as, or lower than, for random candles nearby:

  | TF | MAJOR bullish | random nearby | MAJOR bearish | random nearby |
  |---|---:|---:|---:|---:|
  | 1H | 56% | 58% | 53% | 56% |
  | 4H | 61% | 64% | 54% | 60% |
  | 1D | 52% | 57% | 45% | 49% |
  | 1W | 50% | 49% | 28% | 33% |

  Arrows sit near swings because a break is defined by a swing, not because the swing predicts
  what follows.

Why it matters: the filters, tiers, LTF warnings and HTF ladder all select from these events.
If the events carry no information, no selection rule can add it reliably. That is consistent
with every add-on component failing screening in v2 and with purged CPCV in v3 most often
preferring C0, "every structure break".

### F2. What looks like an edge is trend and drift exposure, not the break. CONFIRMED for the cells tested; mechanism inferred

The HTF gate was the only layer with fairly consistent incremental value in v3. V4 shows that
inside an HTF state, the break adds nothing over a random candle in that same state. Every cell
where the shipped signal beats unconditional random entries stops being significant once
matched on HTF state and year:

| cell | n | mean r_h | median r_h | xR0 | xR2 |
|---|---:|---:|---:|---|---|
| 1H crypto bullish MAJOR | 4,348 | +0.27 | **−0.21** | +0.38 [+0.14, +0.60] | +0.17 [−0.06, +0.36] |
| 4H crypto bullish MAJOR | 983 | +0.84 | **−0.01** | +0.60 [+0.00, +1.22] | +0.20 [−0.34, +0.75] |
| 4H crypto bearish MAJOR | 1,605 | +0.01 | −0.17 | +0.35 [−0.16, +0.88] | +0.12 [−0.40, +0.66] |
| 1D crypto bullish CONFIRMED | 621 | +2.19 | +0.42 | +1.57 [+0.34, +2.80] | +0.98 [−0.15, +2.06] |
| 4H crypto bullish CONFIRMED | 2,322 | +1.37 | +0.28 | +1.13 [+0.51, +1.71] | +0.66 [+0.07, +1.18], median −0.33 |

The last row is the one cell that stays positive after matching. Even there, the median excess
against R2 is negative, so the mean rests on a minority of large crypto trend runs.

The bullish/bearish asymmetry in absolute results is mostly drift, which matching removes:

* backtesting.py profit factors were 1.18–3.53 bullish and 0.44–1.10 bearish (`BACKTESTINGPY.md`);
* against controls, the two sides look alike: bullish and bearish all-break excess against R0
  is within ±0.4 ATR of zero, with CIs spanning zero, in most cells.

Inference, not yet tested: the predictive content, if any, is in the HTF trend state itself,
i.e. time-series momentum. That is hypothesis **H6** in the register, and it is untested.

### F3. The shipped signal is late, and its construction does not match its stated purpose. CONFIRMED

* **Purpose mismatch.** The indicator is described as a trend-change indicator. But MAJOR is a
  realignment: an MTF change of character *back into* an existing HTF trend (`engine.classify`).
  By construction it is a with-trend pullback entry and never an HTF trend change. Breaks
  against the HTF (counter_reversal) are the only early-reversal path, and they are suppressed
  as WATCH and not drawn.
* **Lateness.** At the signal candle, price has typically already moved 3.0–3.9 ATR (median)
  from the swing extreme since the previous break, 8–12 candles earlier. In 60–89% of events
  that move already made is larger than the best move after the signal (MFE within H). The
  1 ATR stop of the outcome definition sits well inside the structure the signal is based on.
* **Detection of large swings** (ex-post zigzag swings ≥ 4 ATR; future data used only to score):

  | | detected | median lag | share of the swing still ahead |
  |---|---:|---:|---:|
  | any break | 86–96% | 10–14 candles | about half |
  | MAJOR | 7–47% | 14–54 candles | |
  | MAJOR, bearish equities (1H/4H/1D/1W) | 7–19% | | |

  MAJOR misses most swings and is later on the ones it catches.
* **Stale HTFs.** The slower HTF's state lasts a median of 41 candles (1W) to 168 candles
  (4H crypto, about 4 weeks), and it is read from the previous completed HTF candle. A
  with-HTF bearish signal is possible on only 13% (1W) and 17% (1D) of equity candles, against
  72% and 59% for bullish. This causes missing bearish signals, not a bug: the gate follows
  slow trends that rarely turn down in a rising sample.

### F4. Heavy tails and dependence make averages misleading, and the v3 statistics overstated certainty. CONFIRMED

* **Heavy tails.** The best 5% of events produce 18–68% (median 31%) of each cell's gross gains.
  Of the 119 adequately sampled cells with a positive mean, 33 have a median ≤ 0.
* **v3 p-values ignored dependence.** The v3 random benchmark draws iid candles, so its p-value
  does not include the clustered sampling error of the signal mean. Example: v3 reported 4H
  crypto bearish MAJOR at p = 0.005, yet the month-cluster CI of the excess over random is
  +0.35 [−0.16, +0.88]. The "PROMISING" labels in `V3_SUMMARY.md` rest on these p-values.
  Of the three PROMISING cells, 1H crypto bullish keeps a CI clearly above 0 against R0.
  4H bullish sits at the edge (lower bound +0.00), and 4H bearish does not (lower bound −0.16).
  None of the three stays significant against R2.
* **v3 deflated-Sharpe reading was wrong in places.** The weekly-bucket Sharpe ratio fed to the
  DSR is negative for 1H crypto bullish (−0.18) and 4H crypto bearish (−0.16), although their
  per-event means are positive. Their DSR ≈ 0 comes from the bucket series being negative (busy
  weeks carry the gains), not from deflating for 60 trials as `V3_SUMMARY.md` states.
* **Overlap.** 64–91% of raw breaks have their next same-side break on the same symbol inside
  the outcome window. MAJOR is 2–10% because of the cooldown. Cross-symbol dependence is
  handled by month clusters. On 1W the 13-week horizon spans ~3 months, so month clusters
  understate uncertainty there; quarter clusters are in the json (`xR1_q`).

### F5. The software is correct where tested; the strategy twin has one divergent path, and one V4 control was biased. CONFIRMED by code and measurement; TradingView behaviour NOT TESTED

* **Look-ahead and repainting.** The truncation and finality tests pass (40/40 including the new
  symmetry test). HTF reads use the completed-candle `f()[1]` with `lookahead_on` idiom, and the
  LTF reads only candles inside the closed chart candle. The left-edge history dependence
  documented in `AUDIT.md` remains (1W up to ~7 months).
* **Strategy twin divergence.** In `HighConvictionMTF_strategy.pine`, a same-direction signal
  while a trade is open is ignored by `strategy.entry` (pyramiding 0). But the block still
  resets `stopPx`, `sigAtr`, `best` and `entryBar`, and on the next candle re-anchors the stop
  to `position_avg_price − 2 × the new ATR`. The effect is to loosen a trailed stop and restart
  the time exit. `evaluate.simulate` (and so the backtesting.py cross-check) ignores such
  signals. Frequency on the 70 symbols:

  | TF | trades affected | of |
  |---|---:|---:|
  | 1H | 340 (2.6%) | 13,318 |
  | 4H | 100 (2.8%) | 3,606 |
  | 1D | 138 (3.4%) | 4,117 |
  | 1W | 27 (3.2%) | 831 |

  The backtesting.py agreement therefore validates the Python simulator, **not** the Pine twin.
  Left unfixed in this phase (production freeze).
* **A biased control of my own (post hoc).** The pre-declared local control R1 (±2H around the
  event) includes candles *before* the break, whose forward windows contain the very rally that
  defines the break. Split by side, the before-only part is strongly negative: all-break xR1b is
  −0.85 to −1.24 ATR, against −0.03 to +0.19 for the after-only R1a. R1 is therefore biased
  against breaks, and the pre-declared "information" rule is too strict. R1a is the corrected
  control, but it was chosen after seeing the bias. R0 and R2 do not have this problem, and they
  lead to the same conclusion.

## 3. Broken implementation or weak hypothesis?

A weak hypothesis. Each stage computes what its code and documentation say:

* the mirror test passes;
* the truncation tests pass;
* the Python mirror of the Pine logic matches the engine.

The breaks are valid structure breaks. They just do not predict returns over 1–2× the
pullback horizon better than random candles in the same trend state. The one implementation
defect found (the Pine twin's stop reset) affects trade accounting in ~3% of trades and cannot
explain the absence of signal value.

## 4. Proposed changes (none implemented in this phase)

| # | change | failure it addresses | mechanism | experiment | falsified if | proposed |
|---|---|---|---|---|---|---|
| P1 | Stop treating the structure break as the predictive core; test the HTF trend state alone (H6) as the hypothesis, with breaks used only for timing or risk | F1, F2 | time-series momentum: returns persist at multi-week horizons | candle-level long/short in the HTF state vs flat and vs buy-and-hold, on fresh symbols plus forward data (register H6) | excess over R0 ≤ 0 or CI includes 0 on the untouched set | **after** V3 (HTF gate result) and after V4 F2 |
| P2 | Fix the Pine twin so same-direction signals in an open trade leave stop and clock untouched | F5 | parity with `evaluate.simulate` | TradingView List-of-Trades export vs `evaluate.simulate` on the same candles | any trade differs beyond fill rounding | after reading the code (no result needed) |
| P3 | Replace v3's iid random p-value with a paired, cluster-bootstrap excess test against R0/R2 | F4 | the test then includes the dependence it ignored | rerun v3 verdicts with the new test | n/a (method fix) | after V3 |
| P4 | Report medians and trimmed means as co-primary; require same sign | F4 | stops tail-driven means passing | apply to all future verdicts | n/a | after V3 |
| P5 | Do not add filters, components or repositories to the break engine | F1 | nothing to select from | none | — | after V4 |

Decision, with evidence: see [`V4_FINAL_HANDOFF_REPORT.md`](V4_FINAL_HANDOFF_REPORT.md) §1.
Hypotheses: [`V4_HYPOTHESIS_REGISTER.md`](V4_HYPOTHESIS_REGISTER.md). Gaps:
[`V4_DATA_AND_VALIDATION_GAPS.md`](V4_DATA_AND_VALIDATION_GAPS.md).
