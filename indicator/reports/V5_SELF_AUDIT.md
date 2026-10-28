# V5 self-audit before the first family-C exploration (external review unavailable)

* **Date**: 2026-10-27. **Audited commit**: `684a546` plus the changes in the commit that adds
  this file.
* **Author.** The same agent that wrote the code. **This is not an independent review.** It is
  recorded as a self-audit and limits every result it enables to EXPLORATION ONLY
  (`V5_REVIEW_WAIVER.md`).

## 1. What was checked, and how

| item | check | result |
|---|---|---|
| Audit fixes A1–A4, B1–B5, C1, E1–E2, L1–L4 (`V5_INDEPENDENT_AUDIT.md`) | `tests/test_v5_audit.py` (18 tests; 16 fail on the pre-fix code); re-read each fix for regressions | pass; no regression found |
| Data guard (`research/v5_data.py`) | closed-candle freeze cut, reserved and unknown symbols, cache-only, incomplete RTH 4H edge, integrity cut (tests); re-read | pass |
| Exploration data fingerprint | `research.v5_manifest.verify` on the committed manifest | **0 missing, 0 changed, 0 extra**; combined sha256 `57e107b08c6912a0…` |
| Protected files | sha256 of `research/v41.py`, `research/universe41.py`, `scripts/v41_run.py`, `scripts/v41_fetch.py`, `reports/V4_1_PREREGISTRATION.md` vs `V4_1_DATA_MANIFEST.json`; `research/v5_labels.py` vs its registration commit `7fc7e68`; `git diff 84c9f13 -- pine hcmtf HC-MTF_*.txt reports/active_config.json` | all identical; production diff 0 lines |
| Baselines (`research/v5_baselines.py`) | truncation causality, both sides, warm-up transitions, matched-frequency thinning (tests); **new probe**: a missing-data (NaN) candle | see SA1 |
| Inference (`research/v5_inference.py`) | synthetic null simulation (G = 8: wild 3.8%, percentile 8.5% at nominal 5%); re-read the CR1 and wild-bootstrap algebra | pass; assumptions in §3 |
| Gate (`research/v5_gate.py`) | new review modes; confirmatory gate never accepts the waiver (tests) | pass |
| Configuration (`V5_C_EXPLORATION_CONFIG.md`, draft) | read for anything not fully specified before outcomes | see SA2 (resolved in the freezing commit, before any outcome) |
| Scoring at scale | traced the planned runner against `v5_eval` | see SA3–SA5 |

## 2. Findings

| id | severity | finding | resolution |
|---|---|---|---|
| SA1 | LOW | `hcmtf.evaluate.ema_cross` casts a NaN sign to int on a candle with missing OHLC (garbage direction). The baseline wrapper keeps only `dir == side`, so no bad alert can escape. `v5_data` never returns NaN rows anyway. | `hcmtf` is protected and not changed. A regression test asserts that no baseline alert appears on or because of a NaN candle |
| SA2 | MEDIUM | The draft configuration left several details implicit (percentile method for C1b, swing-level handling for C3, which warnings count for C5a, alert eligibility for baselines, window start, lift-benchmark eligibility, evaluability with G ≥ 10, what "r_h excess" means for trades) | resolved explicitly in the **freezing commit**, in a "Freezing clarifications" section, before any detector code ran or any outcome was computed |
| SA3 | MEDIUM | `v5_eval.lift_report` builds its benchmark from every scorable candle, but configuration §2 requires warm **and** scorable candles | runner computes lift with the warm restriction, using a new primitive `v5_eval.lift_units` (tested); `lift_report` is left unchanged |
| SA4 | MEDIUM | `score_instrument` recomputes the frozen labels on every call. Matched-frequency baselines need ~10⁵ scorings, which is infeasible. | added `v5_eval.top_labels` (computes the frozen labels once, ATR14 internal, symbol and freeze checks) and `score_alerts(labels, alerts, kind, start_i)`; `score_instrument` is now a thin wrapper (equivalence tested). `start_i` implements the configuration window |
| SA5 | LOW | `detection_report` marks a cell evaluable with ≥ 8 event clusters, while the configuration also needs G ≥ 10 for the lift test | runner applies both and reports each |
| SA6 | INFO | `r_h` (the register outcome at H) includes round-trip costs only; holding costs for shorts appear in the separate trade metric | stated in the report |

**No critical leakage or execution defect was found.**

## 3. Inference method selected (protocol Amendment 1, exploration scope)

* **Decision statistic**: wild cluster bootstrap with the null imposed (Rademacher weights if
  G ≥ 12, Webb weights otherwise; 9,999 replicates), one-sided.
* **Interval**: t(G−1).
* **Clusters**: calendar blocks shared across instruments (1H 1 month, 4H 2 months).
* **Assumptions**: independent blocks; arbitrary dependence within a block; cluster sizes not
  extreme (they are reported); benchmarks fixed per unit.
* **Limits on claims**:
  * exploration only;
  * no confirmatory statement;
  * cells with G < 10 are reported but never decide;
  * no correction for the exploration trial count beyond disclosure;
  * Holm reported for information.

## 4. Status

**Self-audit: COMPLETED.** Independent review: **UNAVAILABLE**. Evaluation scope permitted by
this audit: **EXPLORATION ONLY.**

Requirements before any G2 or G3 step:
* an independent review;
* Amendment 1 adopted for confirmatory scope.
