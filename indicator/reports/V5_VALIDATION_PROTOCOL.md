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
