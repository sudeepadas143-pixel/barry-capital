# V4 hypothesis register

What the indicator could be trying to predict, stated so each claim can be falsified.

Every row records:
* its status: **REJECTED BY EVIDENCE**, **TESTED, INCONCLUSIVE**, or **NOT TESTED**;
* the evidence behind that status;
* whether the hypothesis was proposed before or after the relevant results were seen.

Evidence from v1 to V4 all uses the same 70 symbols and dates. It can reject a hypothesis
(an absence of signal does not become stronger on fresh data), but it cannot confirm one.
Anything that survives needs the untouched data described in
[`V4_DATA_AND_VALIDATION_GAPS.md`](V4_DATA_AND_VALIDATION_GAPS.md).

Common definitions for every row:

* **r_h**: move in the trade's direction to candle H, in ATR(14), after costs. H is 1H 24,
  4H 30, 1D 20, 1W 13 candles. Costs per round trip: crypto 20 bp, commodities 8, equities 6,
  indices and bonds 4, FX 3.
* **Excess**: r_h minus a control on the same symbol and side:
  * R0: every candle;
  * R1a: the 2H candles after the event;
  * R2: same year and same HTF state.
* **CI**: 95% month-cluster bootstrap. Bullish and bearish are always evaluated separately.

## A. Hypotheses already tested

| id | hypothesis (market behaviour) | where in the engine | status | evidence | proposed |
|---|---|---|---|---|---|
| H0 | A confirmed swing-structure break (close beyond the latest unused swing) predicts continuation in its direction over H | `engine.breaks`, every class (v3 C0) | **REJECTED BY EVIDENCE** | V4: 0/302 adequately sampled cells pass the pre-declared rule, 3/302 the post-hoc variant (≈ chance). All-break excess vs R0 and R2 is within ±0.4 ATR of 0, or negative, in every group × TF × side. 1D/1W non-crypto vs R2: 11/16 cells have a CI upper bound ≤ 0.00. ([`V4_ROOT_CAUSE_AUDIT.md`](V4_ROOT_CAUSE_AUDIT.md) F1) | v1, before any results |
| H1 | **A. Continuation.** A break with MTF structure and with the HTFs continues (CONFIRMED) | class `continuation` (v3 C3) | **REJECTED as a general rule. One residual cell is INCONCLUSIVE**: 4H crypto bullish | V4 general: no excess vs R2 (CI > 0) in 27 of the 28 adequately sampled group × TF × side cells. Residual: 4H crypto bullish CONFIRMED, n = 2,322, xR0 +1.13 [+0.51, +1.71], xR1a +0.70 [+0.29, +1.03], xR2 +0.66 [+0.07, +1.18], but median xR2 −0.33 and selected out of 364 cells | v2, before results; the residual cell was singled out **after** V4 results |
| H2 | **C. Pullback end.** An MTF change of character back into the HTF trend (shipped MAJOR) | class `realignment` (v3 C2) | **REJECTED BY EVIDENCE** | v3: no DEMONSTRATED cell. V4: none of the 22 adequately sampled cells has an excess vs R2 with CI > 0. Best cell, 1H crypto bullish: xR2 +0.17 [−0.06, +0.36], median r_h −0.21, mean without the top 1% only +0.08. Detects 7–47% of ≥ 4 ATR swings, median 14–54 candles late | v2, before results (chosen in `DESIGN_CHECK.md` on development data) |
| H3 | **B. Early reversal.** An MTF change of character against the HTFs starts a reversal before any HTF turns | class `counter_reversal` (WATCH, v3 C6) | **REJECTED BY EVIDENCE** | v3: worse than MAJOR on every TF bearish (e.g. 1H −0.13 [−0.28, +0.01]). V4: 1H crypto bullish xR0 −0.20 [−0.35, −0.05], xR1a −0.13 [−0.23, −0.04]; no cell with CI > 0 vs R2 | v2, before results |
| H4 | Breaks with MTF structure but against the HTFs continue | class `counter_continuation` | **REJECTED BY EVIDENCE** | V4: no information in any cell; 1W bearish xR2 −1.13 [−1.48, −0.81] | never advanced as a signal; reported for completeness |
| H5 | Confluence components improve the selection of breaks: momentum, ADX strength, displacement, FVG, relative volume, liquidity sweep, LTF momentum, funding, basis, OI, range/shock/spike/weekend filters, next-candle acceptance, both HTFs agreeing | `engine.score`, `Params.accept`, `strict_htf` | **REJECTED BY EVIDENCE** | v2 screening: none passed (`SCREENING.md`). Acceptance: invalidations 45% → 32% but no outcome gain (`AUDIT.md`), v3 C4 vs C2 inconsistent. Strict HTF did worse (`DESIGN_CHECK.md`). Under H0 there is nothing for a selector to select | v2, before results |
| H5b | The HTF gate adds value over all breaks | `htf_with` (v3 C1 vs C0) | **TESTED; the effect exists, but it belongs to the HTF state, not the break** | v3: +0.20 [+0.12, +0.28] on 1H bullish, +0.38 [+0.14, +0.62] on 4H bullish. V4: inside the HTF state, breaks ≈ random candles (xR2 ≈ 0). This motivates H6 | v2 design, before results; the reinterpretation is **after** V4 |

## B. Hypotheses not yet tested (the smallest set worth a fair test)

Three, in priority order. Each must be run on the untouched data in the gaps report, under a
plan committed before any number is computed. Bullish and bearish are evaluated separately, and
Holm correction is applied over every cell of this register's B section.

### H6. The HTF trend state alone (time-series momentum)

* **Behaviour.** When the HTF1/HTF2 trend state (close vs EMA21 with agreeing slope, read from
  completed HTF candles) points one way, forward returns in that direction exceed the symbol's
  unconditional forward returns. Equivalent to asking whether the HTF gate's v3 value is
  tradable on its own.
* **Entry timing.** Any candle in the state, so no timing claim is made. Test it as (a) every
  candle in the state and (b) entry only on the candle the state turns on.
* **Holding.** Same H as v3. Secondary: until the state turns, capped at 2H.
* **Invalidation.** The state turns neutral or against.
* **Benchmark.** R0 (all candles, same symbol and side), buy-and-hold, and the same rule with a
  one-HTF-candle delay. If the delayed version is no worse, fast timing is not the source.
* **Rejected if** the excess vs R0 has a 95% cluster CI including 0 in every TF for both sides,
  or is positive only on the bullish side of rising assets with the bearish side ≤ 0. The second
  outcome would make it drift, not information.
* **Proposed** after V3 (HTF gate) and after V4 F2. Literature prior: time-series momentum is
  documented at 1–12 month horizons on futures; whether it holds at these chart horizons and
  costs is the open question.

### H7. D. Volatility expansion after compression

* **Behaviour.** After ATR% sits in its lowest tercile of the last 200 candles for ≥ k candles
  (k fixed in advance per TF: 1H 24, 4H 12, 1D 10, 1W 6), the first close outside the
  compression range is followed by realised range expansion. The direction claim is tested
  separately.
* **Entry timing.** The next open after the first close outside the compression high or low.
* **Holding.** H. Also a volatility-only outcome: realised ATR over H / ATR at entry.
* **Invalidation.** A close back inside the compression range.
* **Benchmark.** (i) For the volatility claim: random candles in the same vol tercile and
  year (R3). (ii) For the direction claim: R0 and R2. Report the two claims separately; a
  volatility edge without a direction edge is not a directional signal.
* **Rejected if** realised volatility expansion is not above R3 (CI includes 0), or the direction
  excess vs R0 and R2 includes 0, per TF, side and group.
* **Proposed** in V4 Phase 4 from the brief's hypothesis list. It was not motivated by any
  result: the engine has no compression logic, so nothing about it has been measured.

### H1r. Residual check: 4H crypto bullish continuation

* **Behaviour.** As H1, restricted to 4H crypto, bullish side only.
* **Entry, holding, invalidation.** As the shipped CONFIRMED tier: next open after the break,
  H = 30 candles, invalidation at the opposite structure break.
* **Benchmark.** R0, R1a and R2. Median excess is required to be > 0 as well as the mean.
* **Rejected if** the mean excess vs R2 has a CI including 0, or the median excess vs R2 ≤ 0, on
  the untouched set. Note its existing median excess vs R2 is already −0.33, so the prior is
  against it.
* **Proposed after** the V4 results: it is the single survivor of 364 cells, which is exactly the
  kind of result that needs replication before it means anything.

### Considered and not proposed

* **Earlier pullback entry inside the HTF trend.** Buy the retrace into the prior swing zone
  instead of waiting for the break (addresses F3 lateness). This depends on H6: if being in the
  HTF state carries no information, an earlier entry inside it cannot either. Proposed only if
  H6 survives.
* **HTF trend flip as a confirmed reversal signal.** This is H6's entry variant (b), so it is
  not listed separately.
* **Further confluence components and new repositories.** H5 is rejected and H0 leaves nothing
  to filter.

## C. What would change the decision

A fresh-data pass for H6 or H7 that clears the rejection criteria above, consistently across at
least two asset groups. A pass for H1r alone would not be enough: it would be one cell, on one
asset class and side, in one market regime (crypto 2020–2026).
