# HC-MTF V5 development plan (canonical roadmap)

* **This is the single live roadmap for the indicator.** It supersedes the forward-looking
  sections of:
  * `V4_HYPOTHESIS_REGISTER.md` (now `V5_HYPOTHESIS_REGISTER.md`);
  * `V4_DATA_AND_VALIDATION_GAPS.md` (now `V5_DATA_AUDIT.md`);
  * the "next steps" of `V4_1_FINAL_RECOMMENDATION.md`.
* **Those files are not edited.** They remain the historical record.
* **Before this plan**, the repository had no canonical indicator plan. The root `PROMPT.md`
  belongs to the website project.

## 1. Objective

A single multi-timeframe TradingView indicator that can mark four signal families, each with
useful timeliness, without repainting, across crypto, equities, commodities and several
timeframes:

| family | meaning | intended marker |
|---|---|---|
| A | bullish trend continuation | ▲ up arrow |
| B | bearish trend continuation | ▼ down arrow |
| C | major top / bearish reversal | a distinguishable top marker, only if justified |
| D | major bottom / bullish reversal | a distinguishable bottom marker, only if justified |

Non-goals and promises:

* **No predictive performance is claimed or promised.** Every family must pass its own gates in
  [`V5_VALIDATION_PROTOCOL.md`](V5_VALIDATION_PROTOCOL.md).
* **Any family may be rejected or redesigned.** The product is "four useful signal types if the
  evidence supports them". Shipping fewer families, or none beyond today's, is an acceptable
  outcome.
* **The interface stays minimal.** Arrows, plus top/bottom markers only if justified. Separate
  early-warning markers only if register E2 shows warnings and confirmations behave differently.

## 2. Where things stand (evidence)

### Software

Established:

* non-repainting closed-candle signals;
* completed-HTF alignment;
* Pine ↔ Python mirror;
* bull/bear mirror symmetry;
* simulator cross-checks.

Open:

* **TradingView-export parity** has never been run on real TradingView data.
* **The Pine strategy twin** resets its stop and time-exit clock on same-direction signals
  (V4 F5a). This is unfixed.

### Prediction

| hypothesis | status |
|---|---|
| structure-break signals (H0, H2, H3, H4), 14 confluence components (H5), the 4H crypto continuation cell (H1r-target) | **rejected** |
| HTF trend state alone (H6), compression → range (H7v) | **inconclusive**; frozen forward test (1H 2027-07-01, 4H 2028-01-01) |
| breakout direction (H7d), break increment (H1r) | **inconclusive** |

Lessons carried forward:

* **Do not mirror bull and bear rules blindly.** Equities mean-reverted inside HTF states, while
  crypto trended.
* **Medians matter.** Means are carried by a minority of large moves.
* **Earlier "independent" sets are spent.** Every cached candle has now been examined.

### Production

`pine/HighConvictionMTF.pine` (= `HC-MTF_TradingView.txt`) and its strategy twin are unchanged
since V4. They stay unchanged until a V5 family passes gate G5.

## 3. Workstreams and dependency order

```
E0 shared research infrastructure ──┬── A bullish continuation ─┐
  (state classifier, label harness,  ├── B bearish continuation ─┤
   matched benchmarks, trial ledger, ├── C major tops ───────────┼── E integration (state machine) ── F Pine port / release
   cost model incl. short costs)     └── D major bottoms ────────┘
                                         (each passes G1→G3 on its own)
V4.1 H6/H7v forward test (frozen) ── runs on its own calendar; its outcome informs A/B and E1 but is not a dependency
```

| step | workstream | depends on | output |
|---|---|---|---|
| 0 | **E0 infrastructure** | this plan | `research/v5_state.py` (causal state classifier: HTF state × volatility tercile × extension bucket); `research/v5_eval.py` (matched benchmarks, label scoring: recall, lead, false alarms, remaining move; short-cost model; trial ledger writer); tests for causality and scoring on synthetic data |
| 1 | **A**: pullback + resumption (A1, A2) | E0 | G1 exploration, ≤ 3 variants or dropped |
| 1 | **B**: failed rally, breakdown, squeeze risk (B1–B3), built independently of A | E0 | G1, with short costs |
| 1 | **C**: extension, divergence, failed breakout, volatility change, structural failure (C1–C5) | E0 + top labels | G1: warnings and confirmations scored separately |
| 1 | **D**: exhaustion, divergence, failed breakdown, momentum recovery, reclamation (D1–D5), built independently of C | E0 + bottom labels | G1 |
| 2 | each family | its G1 | G2 freeze → G3a reserve-instrument check (one run) |
| 3 | each family | G3a pass + forward data size | G3b forward confirmation (dates in §5) |
| 4 | **E**: integration | ≥ 1 family at G3b (G3a for a design dry-run only) | state machine and conflict rules; combined-system evaluation |
| 5 | **F**: Pine | G4 | port, parity, release |

A, B, C and D can run in parallel after E0. None waits for another, and none is merged until E.

## 4. Unified MTF architecture (to be built in research first; Pine only at G5)

* **Timeframe roles** (ladder unchanged, `engine.LADDER`):

  | role | meaning |
  |---|---|
  | HTF | context: trend state, extension; read from completed HTF candles only |
  | MTF | the chart: setups (pullback, rally, divergence, failure) |
  | LTF | triggers: read from LTF candles **inside the closed chart candle** |

  Every value used at a signal must be computable at that candle's close. Truncation tests are
  required for every detector.
* **Shared state classifier.** One causal function returns HTF state, volatility tercile and
  extension bucket. All families condition on it. Whether this conditioning helps is register
  question E1, not an assumption.
* **Separate family detectors.** A, B, C and D are independent modules with their own parameters,
  tests and verdicts. Bullish and bearish rules are developed separately.
* **State machine (E).** It decides what is drawn once detectors fire:
  * one active signal per family per instrument;
  * per-family cooldowns;
  * reversal confirmations (C/D) take precedence over continuation of the opposite direction on
    the same candle;
  * no simultaneous opposite markers;
  * early warnings never upgrade silently into confirmations (separate states, separate tests).

  All decisions are made on the closed chart candle.
* **Markers.** ▲ for A and D-confirmed, ▼ for B and C-confirmed. Distinct top/bottom shapes and
  separate warning markers only if E2 passes. Anything else stays in the data window.

## 5. Calendar (earliest possible, assuming forward data accumulates)

| date | event |
|---|---|
| now | E0 infrastructure, then G1 exploration for A–D on exploration data |
| after each family's G2 | G3a on the V5 reserve instruments (requires downloading them; the first download is part of that family's G2 commit) |
| 2027-07-01 | V4.1 H6/H7v 1H forward evaluation (frozen, separate) |
| ≈ 2027-08 onward | earliest G3b for 1H V5 families (≥ 8 monthly clusters) |
| 2028-01-01 | V4.1 H6/H7v 4H forward evaluation |
| ≈ 2028–2029 | earliest G3b for 4H families |
| ≥ 2029–2030 | earliest G3b for 1D families |
| none planned | 1W stays exploratory; no validated 1W release is expected within this decade (`V5_DATA_AUDIT.md` §5) |

## 6. Decision rules (summary)

* **Per family**: retained for forward testing (G3a pass), confirmed (G3b pass), rejected, or
  redesign. A redesign restarts at G1 with a new version id, and its trial count carries over.
* **Integration only uses families that passed G3b.** A family that passed only G3a may be shown
  only in a research build, never in the published indicator.
* **Narrow passes** (one asset group or one TF) can ship only with that scope stated on the chart
  and in the alert text.

## 7. Risks

| risk | mitigation |
|---|---|
| Rare events (1D/1W tops and bottoms) make confirmation slow or impossible | state it; do not release unconfirmed families; prefer 1H/4H first |
| Exploration data is fully examined; overfitting by iteration | trial ledger; ≤ 3 frozen variants per family; reserve and forward data only after G2 |
| Shared forward data across V4.1 and V5 | V4.1 frozen by hash; V5 never computes H6/H7v on forward data early; access log |
| Short-side costs and squeeze tails understated | conservative borrow and funding model; squeeze-tail criterion for B |
| Non-crypto intraday history is short (Yahoo 730 days) | non-crypto intraday cells mostly underpowered; licensed data only if a family needs it |
| TradingView data and runtime differ from Python | G5 export parity is mandatory |
| Pressure to ship four families | the plan explicitly allows rejecting any family |

## 8. Progress log

* **2026-10-27: E0 shared infrastructure implemented** (`research/v5_state.py`, `v5_eval.py`,
  `v5_costs.py`, `v5_ledger.py`, `v5_data.py`; tests in `tests/test_v5_infra.py`).
  * Full suite 75 passed. Mutation checks confirm the lookahead, double-claim and freeze tests
    fail when the protections are removed.
  * Design, review findings and limitations: [`V5_INFRASTRUCTURE_REPORT.md`](V5_INFRASTRUCTURE_REPORT.md).
  * No detector built, nothing evaluated, no trial recorded.
  * Format change, recorded here: the trial ledger is `reports/V5_TRIAL_LEDGER.jsonl`
    (hash-chained JSON Lines), not the `.md` named in the register.
* **Blockers before the first family evaluation (C, major tops, 1H/4H exploration):**
  * (1) an independent review of the E0 modules for leakage and statistical errors;
  * (2) a committed evaluation configuration (variants, cells, metrics, trial ids).

  Both are open.

* **2026-10-27: adversarial audit of E0** ([`V5_INDEPENDENT_AUDIT.md`](V5_INDEPENDENT_AUDIT.md)).
  * Found 1 critical defect (weekly/monthly candles absorbing post-freeze prices), 4 high, 7
    medium and 3 low. All fixed with regression tests (`tests/test_v5_audit.py`); 16 of 18 fail on
    the pre-fix code, the other 2 are protection checks. Full suite 93 passed.
  * Frozen labels, V4.1 files and production code unchanged.
  * **Decision: NO-GO for the first family-C evaluation.** Five blockers remain open:
    * B1 review by someone other than the author;
    * B2 matched-frequency baseline generators;
    * B3 FX daily-boundary handling;
    * B4 exploration data manifest;
    * B5 committed C exploration configuration.
  * A protocol amendment on small-cluster inference (S1) is required before any G3.

* **2026-10-27: pre-experiment work for family C** (no detector built or evaluated):
  * B2 done: `research/v5_baselines.py` (HTF flip, EMA cross, Supertrend flip, counter-reversal;
    matched-frequency thinning per instrument and block).
  * B4 done: `reports/V5_EXPLORATION_DATA_MANIFEST.json`, 270 files, combined sha256 `57e107b0…`
    (`research/v5_manifest.py` builds and verifies it).
  * B3 decided: FX excluded (causal daily alignment not demonstrably safe).
  * B5 drafted: `reports/V5_C_EXPLORATION_CONFIG.md` (Status: DRAFT).
  * Small-cluster inference: `research/v5_inference.py`, plus **proposed** protocol Amendment 1
    (`V5_PROTOCOL_AMENDMENT_1.md`, not in force).
  * Readiness gate: `research/v5_gate.py`; `require_c_ready()` currently refuses.
  * Status report: [`V5_PRE_EXPERIMENT_STATUS.md`](V5_PRE_EXPERIMENT_STATUS.md).
  * **Still blocked:**
    * B1 external review;
    * freezing the configuration after review;
    * writing and committing `research/v5_detect_c.py`.

## 9. Next executable task (original wording, kept for the record)

*Done 2026-10-27 (see §8).* Build **E0**: `research/v5_state.py` and `research/v5_eval.py`. They need:

* the causal state classifier;
* matched-benchmark builders for A/B;
* label scoring for C/D (recall, lead time, false alarms, remaining move, lift against
  matched-frequency random warnings);
* the short-cost model;
* the trial-ledger writer.

Its tests must cover:

* truncation causality;
* scoring correctness on synthetic paths;
* refusal to read candles after the freeze (`exploration_only`).

No detector is evaluated in that task. The first evaluation, family C on 1H/4H exploration data,
starts only after E0 is merged and the trial ledger exists.

## 10. Next executable task (superseded by the audit; kept for the record)

1. **Independent review** of the E0 modules against `V5_INFRASTRUCTURE_REPORT.md`, with every
   finding fixed and logged.
2. **Write and commit** `reports/V5_C_EXPLORATION_CONFIG.md`:
   * detectors C1–C5 as registered;
   * 1H/4H cells on exploration data;
   * the metrics requested from `research.v5_eval`;
   * ledger trial ids.
3. Only then run the first exploratory family-C trial through `research.v5_ledger.record`.

## 11. Next executable task (after the audit; superseded, kept for the record)

* Close audit blockers B1–B5 (`V5_INDEPENDENT_AUDIT.md` §5) without computing any detector output.
* Then, and only then, record the first exploratory family-C trial through
  `research.v5_ledger.record`.

## 12. Next executable task (current)

1. **External review** (B1) of the audit fixes and of this pre-experiment work, at the commit
   that adds them, using `V5_PRE_EXPERIMENT_STATUS.md` as the checklist. The reviewer records the
   outcome in `reports/V5_EXTERNAL_REVIEW.md`, in the format `research/v5_gate.py` requires, and
   decides on Amendment 1.
2. After approval:
   * freeze `V5_C_EXPLORATION_CONFIG.md` (status line, own commit);
   * implement `research/v5_detect_c.py` exactly as §3, with causality tests on synthetic data;
   * commit, and run the full suite.
3. Only when `require_c_ready()` passes, run the first trial `c-x1-C1a-W-1H`.
