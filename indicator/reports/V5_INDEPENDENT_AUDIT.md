# V5 research-infrastructure audit (adversarial)

**Decision: NO-GO for the first major-top evaluation.** The infrastructure defects found are fixed
and have regression tests. Five open items still block the evaluation (§5). No signal family was
evaluated, no outcome was inspected, no data was fetched, no threshold was tuned, and no
production or frozen file changed.

## 0. Scope and an honest caveat about independence

* **Audited**:
  * code at commit `6476691` (branch `claude/mtf-conviction-indicator`; working tree clean and
    equal to `origin` before the audit started);
  * `research/v5_state.py`, `v5_eval.py`, `v5_costs.py`, `v5_ledger.py`, `v5_data.py`,
    `v5_labels.py`, `v5_reserve.py`;
  * their tests;
  * the V5 plan, register and protocol;
  * the V3/V4/V4.1 methodological record (iid p-values, the biased ±2H control, tail-driven
    means, the LUNA artifact).
* **This audit is adversarial but not independent.** It was performed by the same agent that
  wrote the infrastructure. It found real defects (one critical) that the author's own tests
  missed, but a review by someone other than the author remains a release condition (§5, B1).
* **Method.** Read every function for leakage and statistical errors, then try to break each
  protection on purpose.
* **What the tests prove.** Every fix has a regression test in `tests/test_v5_audit.py`. The
  audit tests were also run against the **pre-fix** code: **16 of 18 fail there**. The two that
  pass on both versions are protection checks:
  * `P1`, label-import isolation;
  * `P2`, the frozen labels being byte-identical.

## 1. Findings, by severity

Status: **FIXED** (with a test), **OPEN** (blocks), **LIMITATION** (documented; acceptable for
exploration).

| id | severity | area | finding | evidence / reproduction | status |
|---|---|---|---|---|---|
| A1 | **CRITICAL** | temporal / data | `v5_data.load` cut candles by **open** time. Weekly, monthly and quarterly candles that open before the freeze but close after it were kept, so post-freeze daily prices leaked into exploration frames. | Planting forward daily candles (high = 10,000) in a temp copy of the SPY cache made `DG.load("SPY","1W")` and `("SPY","1M")` return a last candle with high 10,000 | **FIXED**: `v5_reserve.exploration_closed` keeps only candles that **close** by the freeze; `v5_data` uses it for every frame and the integrity rule; `check_partition` checks close times too. Test `A1` |
| A2 | HIGH | temporal / state | `extension_atr` mixed feeds: chart close (Yahoo hourly) minus HTF1 EMA from the Yahoo **daily** feed, which is dividend-adjusted on a different basis. Biased on every 4H non-crypto chart (HTF1 = 1D). | SPY daily vs hourly high/low disagree by a median 1.6% over 400 days; a 4H ATR is ≈ 1% of price, so ≈ 1–2 ATR of bias | **FIXED**: HTF1 closes are taken from the chart feed (`_htf_close_from_chart`), still read only via the completed-candle `align`. Test `A2` (extension invariant to scaling the HTF feed) |
| E1 | HIGH | costs | FX carry is "not modelled" but `short_holding_cost` returned **0.0**, so FX shorts entered net returns as if carry were zero | `C.short_holding_cost("fx", …)` → `(0.0, "unavailable_fx_carry")` | **FIXED**: returns NaN; `trade()` sets `net` = NaN and `cost_complete=False`; `sequential_daily` raises unless `unavailable_cost_as_zero=True` is passed explicitly; `cost_sources()` reports counts. Test `E1` |
| L1 | HIGH | protection | The ledger did not require the experiment configuration to be committed. Reserved partitions were unlocked by **any** existing file path (README.md passed). | `record(..., partitions=["forward"], confirmatory_prereg="README.md")` succeeded | **FIXED**: every trial must name a committed, unmodified `config_file`. Reserved partitions need a committed, unmodified `reports/V5_*PREREG*.md` that names the hypothesis id. Tests `L1`, `L2` |
| B2 | HIGH | label integrity | `score_instrument` took ATR from the caller, so a different volatility measure could silently change the frozen label definition | signature `score_instrument(h, l, c, atr, …)` | **FIXED**: ATR14 (Pine-exact) is computed inside; the parameter is removed. Test `B2` |
| S1 | HIGH (for confirmation) | statistics | Percentile cluster bootstrap with the protocol's minimum of 8 clusters is anti-conservative (too few clusters for percentile intervals). Bootstrap p-values are approximations. | The minimum of 8 is in protocol §5 | **OPEN, needs a protocol amendment before any G3.** Not blocking exploration. Proposed: ≥ 20 clusters for confirmatory cells, plus a small-G cluster-robust t with G−1 df as a required sensitivity |
| A3 | MEDIUM | temporal / data | `hcmtf.data.to_4h` builds exchange-hours 4H buckets without checking the session finished. The cache's last SPY 4H candle (17:30 UTC on 2026-10-26) held only one of its hours. | `DG.load("SPY","4H")` ended at 2026-10-26 17:30, but the last hourly bar is 17:30 UTC (13:30 ET) | **FIXED**: `_drop_incomplete_rth_4h` drops it when the last hourly bar is not the 15:30 ET bar. Test `A3` |
| B1 | MEDIUM | statistics | BTC-USD (audit series) and BTCUSDT are the same asset; the exploration set contained both, so pooling would double-count BTC | `v5_data.EXPLORATION` | **FIXED**: `EVAL_SYMBOLS` (108, no BTC-USD) is the pooling universe. Test `B1` |
| B3 | MEDIUM | protection | The evaluators accepted any symbol name; code that bypassed `v5_data` could score a reserve instrument | `candle_table("JNJ", …)` worked | **FIXED**: `candle_table` and `score_instrument` call `check_symbol`. Test `B3` |
| B5 | MEDIUM | statistics | Units whose stratum had no benchmark were dropped from the point estimate but kept in `n`, `mean_value`, medians and the lift base, giving an inconsistent `lift` | `excess()` mixed populations | **FIXED**: such units are removed up front and counted as `units_without_benchmark`. Test `B5` |
| C1 | MEDIUM | benchmark validity | The S, matched and lift benchmarks are whole-window (ex-post) averages per instrument and stratum. Matching *keys* are causal, but the benchmark *values* use outcomes from after the signal. Valid as "a random entry in the same state during the same period", not as something knowable at the time. | design (as in V4.1) | **FIXED (added)**: `causal_benchmark` (mean of outcomes already **known** at the decision, j + H ≤ i, same instrument and stratum, `min_history`) and `excess_causal`. The configuration must say which is primary. Test `C1` |
| E2 | MEDIUM | costs / execution | Holding time ran to the **next candle's open**, adding overnight and weekend time after an exit at a session's last bar (borrow over-charged) | equity 1H trade exiting on the 15:30 ET bar was charged until the next 09:30 | **FIXED**: holding time runs to the exit candle's close (next open capped at open + median past spacing). Test `E2` |
| L3 | MEDIUM | protection | A hash chain cannot detect deletion of the newest records or of the whole file | design | **FIXED (mitigated)**: `verify_against_git` requires the committed ledger to be a prefix of the working one. Commit the ledger after every trial. Test `L3` |
| L4 | LOW | protection | Concurrent writers could fork the chain | design | **FIXED**: exclusive `flock` around verify + append. Test `L4` (12 records from 4 processes → one valid chain) |
| A4 | LOW | temporal | `gap_steps` used the whole-series median spacing (diagnostic column, but non-causal if ever used as a feature) | a future change in spacing altered past values | **FIXED**: median of previous spacings only. Test `A4` (fails on the pre-fix code) |
| B4 | LOW | statistics | Off by one: `t_end` was the open of candle i+H, while the outcome ends at its close. `overlap` counted units exactly H apart as overlapping. | windows i+1…i+H and i+H+1… are disjoint | **FIXED**: `t_end` = open of i+H+1; overlap iff Δi < H; effective-n greedy uses ≥ H. Test `B4` |
| U1 | LIMITATION | label integrity | Frozen `major_tops` / `major_bottoms` evaluate a truncated radius and forward window near a series end, so they are unreliable there if called directly | `research/v5_labels.py` | **Not changed (frozen).** The evaluator censors events outside [L, n−1−max(L, F)] and alerts whose range leaves it. Test `P1` restricts who may import the labels |
| U2 | LIMITATION (FX) | temporal | Yahoo FX daily candles cannot be reproduced exactly from Yahoo hourly bars. The best-fitting window is 00:00–24:00 UTC (median high/low error 2–7·10⁻⁴), so a few hours of overlap with the next UTC day cannot be ruled out. That would leak into FX 1H/4H states (HTF2 or HTF1 = 1D). | daily-window offset fit on EURUSD, USDJPY, GBPUSD, USDMXN (prices only) | **OPEN for FX**: the configuration must exclude FX from the first 1H/4H experiment, or build FX 1D from the hourly feed (a state-source change, to be declared) |
| U3 | LIMITATION | benchmark validity | "Causal" columns are declared by the caller. The outcome-name filter is a guard, not a proof. | design | Configuration must list every causal column and its producing function (only `v5_state` outputs and registered detector features) |
| U4 | LIMITATION | protection | `outcomes_accessed` in the ledger is self-reported | design | Recorded; cannot be verified by code |
| U5 | LIMITATION | statistics | Calendar blocks do not remove dependence across block edges. 1D/1W label windows (L + F up to 9 and 18 months) exceed their 3- and 12-month blocks. | design | Acceptable for 1H/4H (L ≤ 3 weeks); 1D/1W need longer blocks before evaluation |
| U6 | **OPEN (gap)** | experiment | Protocol §3 requires C/D confirmations to be compared with baselines (HTF state-flip onset, EMA20/50 cross, Supertrend flip, engine `counter_reversal`) **at matched signal frequency**. No baseline generator and no frequency-matching method exists yet. | `research/v5_eval.py` | **Blocks** the C evaluation until implemented and frozen in the configuration |
| U7 | LIMITATION | costs | Long holding cost is assumed zero (spot); a perp long pays funding. Hard-to-borrow fees and FX carry are not modelled. Crypto shorts use perp funding on spot prices (basis ignored). Intrabar stops are charged to the candle close. | `v5_costs` | Reported with every trading metric via cost sources |
| U8 | LIMITATION | temporal | `decided_at` caps with the next candle's open. It is timestamp metadata only, not an input. | `v5_state` | Documented |

## 2. Area conclusions

### Temporal integrity

After A1–A4, every state field and causal benchmark uses only data available at the candle's
close:

* **HTF values**: only the HTF candle before the one containing the chart candle's open (tested
  at boundaries, with a corrupted forming HTF candle, and by truncation).
* **Volatility percentile**: previous values only.
* **Gaps**: causal, and never filled.
* **Missing OHLC**: `unknown`.
* **Warm-up**: explicit.
* **Incomplete trailing candles**: dropped (forming last bar, incomplete week/month/quarter,
  incomplete exchange-hours 4H).
* **Data edges**: the freeze is enforced on candle closes.

**Revised candles.** Vendors revise history, so every trial now records a sha256 per data file it
read. The exploration cache itself should be frozen by a committed manifest before the first
trial (§5, B4).

**Residual risk**: FX daily boundaries (U2).

### Event-label integrity

* **Labels are retrospective only.** Major-top and major-bottom labels use up to L candles before
  and max(L, F) after the event. They are evaluation targets that are never available in real
  time. A top at t is knowable at the earliest when condition (c) completes, up to F candles
  later.
* **Only the evaluator reads them.** `research/v5_eval.py` is the only reader, and `P1` fails if
  any other research module, script, engine or Pine file imports them.
* **Matching** is one-to-one and maximum (checked against brute force on 400 random cases). Each
  event can be claimed once; duplicates are counted apart from false alarms; confirmations
  cannot claim future events.
* **Censoring**: events outside the fully observable region are excluded from recall; alerts
  whose range leaves it are excluded from precision; both counts are reported.
* **Overlapping events**: an alert eligible for two events takes the earliest.
* **Ordering**: alerts are de-duplicated per candle and matched in time order.

### Benchmark validity

* **Same-state and matched comparisons** use causal keys. Their values are whole-window averages
  per instrument and stratum: an ex-post benchmark, valid for "beats a random entry in the same
  state over the same period". They include the signal candles themselves (negligible for sparse
  signals). They can be selection-biased only if signals concentrate in sub-periods whose drift
  differs from the state's average, which is the reason for the time-sensitive checks (purged
  thirds) and the new **causal benchmark** (C1).
* **Benchmark eligibility.** It should equal the detector's eligibility: if a detector needs a
  longer warm-up, the benchmark must be restricted to the same candles. This is a configuration
  item.
* **The V4 ±2H local control is not used** (V4 showed it is biased).

### Statistical validity

What the method supports:

* **Approximate inference** about the mean excess (and lift) of a pooled cell, robust to
  within-block dependence across instruments and overlapping horizons. Blocks are calendar
  periods shared by all instruments, and benchmarks are re-estimated per replicate.
* **Medians, trimmed means, leave-one-instrument-out and purged thirds** expose heavy tails and
  single-asset dependence.

What it does not support:

* **Exact p-values.** Percentile bootstrap.
* **Valid intervals with few clusters** (S1).
* **Independence across block edges, or across 1D/1W label windows** (U5).
* **Multiplicity correction on its own.** Holm per family is applied by the study script, not by
  these primitives (`hcmtf.metrics.holm` exists).
* **Correction for the exploration trial count.** The ledger counts trials but does not adjust
  for them.

**Exploratory results remain exploratory regardless of any p-value.**

### Cost and execution validity

* **Units**: fractions of notional, actual/365.25.
* **Funding**: the sign is correct (shorts receive positive funding), and coverage is checked for
  gaps and edges.
* **Fills**: gap stops fill at the open; intrabar stops at the stop.
* **Holding period**: now ends at the exit candle's close.
* **Unavailable costs**: never zero unless explicitly requested.

**Remaining**: U7.

### Data protection

Attempted, and now refused or detected:

* forward candles inside the cache (open-time and close-time cases);
* reserve symbols at the loader and at the evaluators;
* unknown and differently-cased symbols;
* a missing cache file, with downloads monkeypatched to fail;
* a duplicate trial id;
* an edited, reordered, truncated or concurrently written ledger;
* reserved partitions with no pre-registration, a non-V5 pre-registration (README, the V4.1
  pre-registration), or an uncommitted one.

Checks that the protected files are untouched:

* the frozen V4.1 files' sha256 equal `V4_1_DATA_MANIFEST.json`;
* `research/v5_labels.py` is byte-identical to its registration commit `7fc7e68` (test `P2`);
* production `git diff` is 0 lines.

**Not protectable by code:** a researcher calling `hcmtf.data` directly, outside `v5_data`. The
evaluators now refuse reserve symbols and post-freeze candles, which closes the practical routes.

## 3. Can the first major-top 1H/4H experiment be pre-registered without looking at outcomes?

**Yes.** Every choice below can be fixed from the register, the protocol and first principles.
Only the label base rates (`V5_DATA_AUDIT.md` §5) have been seen, and those are counts of targets,
not detector outcomes. The prior V3–V4.1 results for related features (H3 counter_reversal,
sweeps) were seen and must be disclosed.

These must be frozen in `reports/V5_C_EXPLORATION_CONFIG.md`, committed before the first trial:

1. **Data.** Instruments = `EVAL_SYMBOLS` minus FX (U2), or FX with a declared hourly-built
   1D; groups; timeframes 1H and 4H; evaluation window (start 2020-01-01, end = freeze via
   `v5_data`); and the data manifest (B4).
2. **Detectors C1–C5.** For each: an exact formula and every parameter.

   | detector | parameters to fix |
   |---|---|
   | C1 extension | threshold x in ATR, or percentile and its lookback |
   | C2 divergence | pivot left/right, RSI length, which previous pivot, maximum distance between pivots |
   | C3 failed breakout | swing definition, k candles |
   | C4 volatility jump | percentile jump size, lookback, the extension precondition |
   | C5 structural failure | change-of-character pivots, which warnings qualify, the window after a warning |

   Plus each detector's role (warning or confirmation), and its warm-up and eligibility mask.
3. **Alert emission rules.** Once per candle (enforced); whether a detector re-fires within an
   episode; cooldown.
4. **Target and scoring.** Frozen labels (`TOP_PARAMS`); K = L, W = L/2; the censoring rule;
   one-to-one matching; the metric list (recall, strict and duplicate-free precision, false
   alarms per 100 candles and per instrument-year, lead median and IQR, move remaining median
   and share > 0.5).
5. **Benchmarks.**
   * lift stratum (e.g. `direction_label` only, or `direction_label × vol_regime`);
   * the baselines of U6, with a frequency-matching method;
   * which of whole-window and causal (C1) is primary, and `min_history` for the causal one.
6. **Trading metrics** (secondary). Short entry at the next open; structural stop definition;
   2H time exit; costs per `v5_costs`, with FX excluded or flagged.
7. **Uncertainty.** Calendar blocks (1H 1 month, 4H 2 months); 5,000 replicates; seed; the
   evaluability minimums.
8. **Selection rule for G2.** How ≤ 3 variants are chosen from exploration (for example the
   highest lower lift bound among cells meeting the minimums, ties broken by median lead time),
   fixed in advance.
9. **Rejection criteria at exploration.** A detector is dropped if its lift CI lies below 1, or
   its median lead time is ≤ 0 for a warning, in every evaluable cell.
10. **Trial ids and the ledger.** One trial id per detector × kind × TF, listed up front.
    `outcomes_accessed=True` for every scoring run. Commit the ledger after each trial.

## 4. Test evidence

* **Full suite: 93 passed.**

  | group | tests |
  |---|---:|
  | V1–V4.1 and integrity | 44 |
  | V5 plan safeguards | 7 |
  | V5 infrastructure (24 existing, updated to the corrected semantics) | 24 |
  | V5 audit regressions (`tests/test_v5_audit.py`) | 18 |

* **Against the pre-fix code** (`6476691` versions of the six modules swapped in temporarily,
  then restored): 16 of the 18 audit tests fail. The 2 that pass on both versions are protection
  checks (`P1`, `P2`).
* **Unchanged** (git diff 0 lines; sha256 of the V4.1 files equal to `V4_1_DATA_MANIFEST.json`):
  * `pine/`, `hcmtf/`, `HC-MTF_*.txt`, `reports/active_config.json`;
  * `research/v41.py`, `research/universe41.py`, `scripts/v41_run.py`, `scripts/v41_fetch.py`,
    `reports/V4_1_PREREGISTRATION.md`;
  * `research/v5_labels.py`.
* **No trial ledger was created.** Every ledger test writes to temporary paths.

## 5. Decision

**NO-GO for the first major-top evaluation.** The infrastructure is materially safer than at
`6476691`, but it is not ready to be relied on until these are closed:

* **B1** A review by someone other than the author of the post-audit code (this commit) against
  this report.
* **B2** Implement and test the matched-frequency baseline generators for C confirmations (U6).
* **B3** Decide FX handling for 1H/4H (U2): exclude, or hourly-built 1D, declared in the
  configuration.
* **B4** Commit an exploration data manifest (sha256 of every cached file used), so revised
  candles are detectable at trial time.
* **B5** Commit `reports/V5_C_EXPLORATION_CONFIG.md` with every item of §3.

Before any confirmatory (G3) run, a versioned amendment to `V5_VALIDATION_PROTOCOL.md` must
resolve S1 (small-cluster inference) and U5 for 1D/1W. These do not block exploration.

**No frozen hypothesis or label definition needed changing.** No defect required an amendment to
a pre-registered definition.

**Exact next step.** Have a reviewer other than the author audit this commit against §1 and §2.
In parallel, implement B2 (baseline generators with tests on synthetic data only) and write B4
and B5 without computing any detector output.
