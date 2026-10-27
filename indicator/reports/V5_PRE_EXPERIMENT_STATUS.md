# V5 family C: pre-experiment status and review checklist

* **The first major-top evaluation remains BLOCKED.** No detector exists, no signal family was
  evaluated, and no detector outcome was computed or inspected.
* **No data was fetched.**
* **Unchanged**: production Pine code, the frozen label definitions and the protected H6/H7v
  files (checked by the test suite).

## Deliverables

| audit blocker | deliverable | evidence |
|---|---|---|
| B2 baselines | `research/v5_baselines.py`: HTF-state flip, EMA20/50 cross, Supertrend(10, 3) flip, engine counter-reversal, for tops (bearish) and bottoms (bullish); `thin()` for matched frequency | `tests/test_v5_baselines.py`: both sides fire, one alert per candle, causality under truncation at two cuts, warm-up transitions are not flips; per-block matching exact, never pads, shortfall reported, reproducible, duplicate detector alerts counted once, empty/out-of-range edges |
| B4 data fingerprint | `research/v5_manifest.py` → `reports/V5_EXPLORATION_DATA_MANIFEST.json` | 270 cached files of 109 exploration instruments (BTC-USD flagged as excluded from pooling); per file: symbol, kind, bytes, rows, first and last timestamp, sha256; per instrument: guarded 1H/4H/1D/1W coverage; combined sha256 `57e107b08c6912a08042639c633604b90e612a60e06fe024b88b84a20e40530d`. `verify()` detects changed, missing and extra files; `build()` refuses a reserved instrument (tests). The committed manifest matches the cache (test) |
| B3 FX | excluded from the first experiment | Yahoo FX daily boundaries cannot be reproduced exactly from hourly bars (audit U2), so causal HTF alignment is not demonstrably safe; reasons in `V5_C_EXPLORATION_CONFIG.md` §1.1 |
| B5 configuration | `reports/V5_C_EXPLORATION_CONFIG.md` (**DRAFT**) | covers universe, data identity, state, labels and windows, 7 detector variants with fixed parameters and rationale, baselines and matching, metrics, uncertainty, multiple testing, 18 trial ids, the G2 selection rule, rejection criteria and an integrity checklist |
| S1 small clusters | `research/v5_inference.py` (wild cluster bootstrap with the null imposed, CR1 t with G−1 df) and `reports/V5_PROTOCOL_AMENDMENT_1.md` (**PROPOSED, not in force**; listed in the protocol's new "Amendments" table) | synthetic null check, one-sided 5%: percentile bootstrap rejects 7–9.5%; wild bootstrap 3.8–5.8%; t(G−1) 3.3–6.0% (G = 8, 12, 20). A test re-checks G = 8 |
| gate | `research/v5_gate.py`: `require_c_ready()` lists and enforces every blocker | a test asserts it currently refuses: no review, configuration draft, no detector code |

## Bug found while doing this

* **What:** `v5_baselines.htf_flip` first used `np.r_` with a string. That raises because numpy
  reads the string as a directive.
* **Fixed** before commit; the test that found it stays.

## Still blocking the first evaluation

1. **B1.** A review by someone other than the author of:
   * the audit fixes (`V5_INDEPENDENT_AUDIT.md`);
   * this work;
   * the draft configuration;
   * proposed Amendment 1.

   The reviewer writes `reports/V5_EXTERNAL_REVIEW.md` with "Decision: APPROVED", "Reviewer is
   not the author: yes" and "Reviewed commit: <hash>". The gate checks those strings; it cannot
   verify who wrote them.
2. **Freeze** the configuration after review: change its status line, in its own commit.
3. **Write `research/v5_detect_c.py`** exactly as configuration §3, with causality tests on
   synthetic data. Commit it and run the full suite.
4. **Before any confirmatory (G3) run:** adopt or replace Amendment 1.

## Known limitations carried forward

* The reviewer's identity cannot be checked by code.
* `outcomes_accessed` is self-reported.
* Matched-frequency thinning uses within-block detector counts: a benchmark device, not a
  tradable signal.
* Excluding FX narrows the experiment to 96 instruments.
* Non-crypto intraday data covers about 35 months, so 4H non-crypto cells will have ~17 blocks.
  These cells meet the exploration minimum of G ≥ 10, but not the proposed confirmatory minimum
  of G ≥ 20.
* All exploration data was examined before; any result remains exploratory.

## Update 2026-10-27: external review unavailable (explicit limitation)

* **External review.** No reviewer other than the author is available, and the project owner
  instructed not to wait for one.
  * Independent review is **not complete**, and nothing here says it is.
  * Replaced, for exploration only, by a documented self-audit (`V5_SELF_AUDIT.md`) and a waiver
    (`V5_REVIEW_WAIVER.md`).
* **What that limits.** Results of the first family-C exploration are labelled
  `self_audited_exploration_only`. They cannot be used for G2 selection, G3 or any confirmatory
  claim until an independent review happens (`research.v5_gate.confirmatory_blockers()`).
* **Protocol Amendment 1.** Adopted for exploration scope only; confirmatory scope not adopted.
