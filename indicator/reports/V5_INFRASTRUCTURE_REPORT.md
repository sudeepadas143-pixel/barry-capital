# V5 shared research infrastructure (workstream E0): design, tests, limitations

* **Scope.** The shared tools that every V5 signal family will be scored with.
* **No evaluation was run.** No detector was built, no signal family was evaluated, no
  threshold was tuned, no data was fetched, and no trial was recorded (the ledger file does not
  exist yet).
* **No production change.** Production Pine code is unchanged.

**Repository state checked first:** branch `claude/mtf-conviction-indicator`, HEAD `2013b12`,
clean working tree, equal to `origin`.

## Modules

| file | purpose |
|---|---|
| `research/v5_state.py` | causal market-state classifier (research feature and benchmark stratum, **not** a predictor) |
| `research/v5_eval.py` | evaluation primitives: matched-benchmark excess, continuation report, one-to-one alert matching, top/bottom detection metrics, lift, per-signal trades, sequential portfolio |
| `research/v5_costs.py` | pre-registered short-side cost model (protocol §4) |
| `research/v5_ledger.py` | append-only, hash-chained trial ledger |
| `research/v5_data.py` | guarded exploration loader (extends `research/v5_reserve.py` without weakening it) |
| `tests/test_v5_infra.py` | 24 tests, synthetic data only |

Unchanged:
* `research/v5_labels.py` and `research/v5_reserve.py` (the frozen definitions and guards);
* the V4.1 H6/H7v files (sha256 still equal to `V4_1_DATA_MANIFEST.json`, checked by
  `test_frozen_v41_forward_test_files_are_unchanged`);
* `pine/`, `hcmtf/` and the `HC-MTF_*.txt` copies (`git diff 84c9f13 -- pine hcmtf
  HC-MTF_TradingView.txt HC-MTF_StrategyTester.txt reports/active_config.json` → 0 lines).

## Design choices

### State classifier (`v5_state.classify`)

* **Timing.** One row per chart candle, decided at its close.
* **HTF values.** These come only from the HTF candle **before** the one containing the chart
  candle's open (`hcmtf.htf.align`, Pine `f()[1]` + `lookahead_on`). This lags by one HTF candle
  on the chart candle that closes together with an HTF candle, which is conservative and
  identical on history and live.
* **Causal computations only.** The volatility percentile compares with the previous 200
  values. EMA/RMA/ATR/ADX are recursive. There are no centred windows and no backward fills.
* **Four separate dimensions**, each with fixed, untuned cut points:

  | dimension | definition |
  |---|---|
  | direction | the HTF bias exactly as the engine and V4.1 H6 |
  | strength | ADX14: weak < 20 ≤ moderate < 30 ≤ strong |
  | volatility | ATR% percentile terciles |
  | extension | (close − last completed HTF1 EMA21) / ATR14, in five buckets |

* **Warm-up and missing data.**
  * Every field is `unknown` (or NaN) until its inputs exist.
  * A candle with missing OHLC is `unknown` and its NaN propagates until the indicators re-warm.
  * Missing candles are not filled: indicators run over the candles that exist, as TradingView
    does, and `gap_steps` reports gaps without changing any state.
  * A non-increasing index raises.

### Exploration guard (`v5_data`)

* **Exploration set only.** Only the 108 examined instruments plus BTC-USD load. Reserve and
  unknown symbols raise `ReservedDataError`.
* **Cache only.** A missing cache file raises instead of letting `hcmtf.data` or `hcmtf.derivs`
  download, which they do on a cache miss.
* **Every frame is cut at the freeze**, even if forward candles are later added to the cache.
* **The V4.1 integrity rule** (> 20× daily open jump) is applied on exploration-window data.
* **No confirmatory loader exists.** The evaluator itself (`check_partition`) also refuses
  post-freeze candles and any partition other than `exploration`.

### Continuation (`excess`, `continuation_report`)

* **Benchmarks.** One side at a time, signals are compared with:
  * **S**: every candle in the same HTF state;
  * **matched**: the same state and the same declared causal strata (for example volatility
    regime, extension bucket, pullback band);
  * the momentum set **M**, with B − M paired on identical bootstrap replicates.
* **Matching rule.** Matching uses only columns declared causal when the candle table is built.
  Outcome-like names and undeclared columns raise `MatchingError`.
* **Duplicates and exclusions.** Duplicate signals on one candle count once. Signals outside the
  state, or not warm, are counted and excluded.
* **Uncertainty.** Calendar-block cluster bootstrap shared by all instruments in the cell, with
  benchmarks re-estimated per replicate. This reuses `research.v41.boot_excess` unchanged.
* **Also reported:**
  * median excess;
  * mean without the top 1%;
  * purged chronological thirds;
  * leave-one-instrument-out range and largest-instrument share;
  * overlap share and effective (non-overlapping) n;
  * evaluability minimums (protocol §5).

### Tops and bottoms (`score_instrument`, `detection_report`, `lift_report`)

* **Labels** are the frozen definitions only.
* **Eligible ranges** (register §2.2): K = L candles after the extreme, W = L/2 before it.
  * A warning at s may claim an event in [s−K, s+W].
  * A confirmation may claim one only in [s−K, s], so it can never claim an event that has not
    happened.
* **One-to-one matching.**
  * Alerts are de-duplicated per candle. Each alert, in time order, takes the earliest
    unclaimed event in its range.
  * Because both ends of the range rise with s, this is a maximum matching. It is checked
    against brute-force augmenting-path matching on 400 random cases.
  * Unmatched alerts are labelled `duplicate` (range holds only already-claimed events) or
    `false_alarm`.
* **Censoring.**
  * Events outside [L, n−1−max(L, F)] are censored and excluded from recall.
  * An alert is scorable only if its whole range lies inside that region; others are excluded
    from precision.
  * Both censoring counts are reported.
* **Detection metrics.**
  * recall and precision (strict: duplicates count against it), plus precision excluding
    duplicates;
  * false alarms per 100 candles and per instrument-year;
  * lead time: median with cluster-bootstrap CI, and IQR;
  * move remaining: median, and share > 0.5.

  Uncertainty uses calendar-block clusters shared across instruments.
* **Lift.** The rate of "an event in range" for alerts versus every scorable candle of the same
  instrument and state, with the same excess machinery. Lift > 1 exactly when the excess > 0.
  This is frequency-independent, so it does not depend on how often a detector fires.

### Trading (kept separate)

* `trade()` enters at the next open. A stop fills at the open on a gap, otherwise at the stop;
  otherwise the trade exits at the close of the holding period. Round-trip and holding costs are
  attached with their source labels.
* `sequential_daily()` trades one position at a time per instrument (overlapping signals
  skipped) for daily-return portfolios via `hcmtf.metrics._perf`.
* Detection metrics never use returns.

### Costs (`v5_costs`) — exactly protocol §4

| position | rule | source label |
|---|---|---|
| short, equities and all ETF classes | 1.0% a year general-collateral borrow, calendar actual/365.25 | `estimated_gc_borrow_1pct` |
| short, crypto, funding covers the whole holding period | observed perp funding: shorts receive positive funding; cost = −Σ rate | `observed_funding` |
| short, crypto, funding missing, ends, or has a > 2-day gap | 10% a year | `estimated_crypto_10pct` |
| short, FX | carry not modelled | `unavailable_fx_carry` (never an "observed zero") |
| long | spot, no holding cost (an assumption) | `none_long_spot` |

### Trial ledger (`v5_ledger`)

* **Format.** `reports/V5_TRIAL_LEDGER.jsonl`, append-only. It is JSON Lines, not the `.md`
  named in the register, so the hash chain can be machine-checked; the plan records the change.
* **Fields per record**:
  * trial id and hypothesis id (registered ids only);
  * partitions;
  * UTC timestamp;
  * code fingerprint (sha256 per file + git HEAD + an uncommitted-changes flag);
  * config sha256;
  * metrics requested;
  * whether outcomes were accessed;
  * prev_hash and record_hash.
* **Protections.**
  * Duplicate trial ids are refused.
  * Edits, deletions or reordering of earlier records break `verify()`, and `record()` refuses
    to append to a broken chain.
  * Reserved partitions need an existing confirmatory pre-registration file.

## Test evidence

* **Full suite: `python -m pytest -q` → 75 passed** (the earlier 51 plus 24 new).
* **The new tests include adversarial cases:**
  * truncation at three cuts;
  * wild future prices;
  * a corrupted forming HTF candle;
  * an HTF-boundary alignment check;
  * NaN candles, dropped candles and no HTF history;
  * repeated alerts on one event;
  * one alert eligible for two events;
  * a confirmation before its event;
  * censored events and alerts at the data end;
  * outcome or undeclared matching keys;
  * forward candles injected into the cache;
  * a reserve symbol;
  * a missing cache file with downloads monkeypatched to fail;
  * ledger duplicates, tampering and reserved partitions;
  * funding gaps and partial coverage;
  * annualisation units.
* **Mutation checks** (temporary, reverted, files verified byte-identical afterwards):

  | mutation | tests failed |
  |---|---|
  | HTF read without the one-candle lag (lookahead) | 2 |
  | events claimable twice | 4 |
  | freeze cut removed from the loader | 1 |

  The tests detect the failures they target.

## Review findings (from reading the code, not from tests)

1. **The frozen label functions are not boundary-safe on their own.** Near the end of a series,
   `major_tops` and `major_bottoms` evaluate a truncated radius and forward window. The evaluator
   handles this by censoring, but any direct caller of `v5_labels` would get unreliable labels
   near the end. The definitions were **not** changed (frozen); this report records it.
2. **The S, matched and lift benchmarks are in-sample averages.** They are averages over the
   instrument's whole exploration window, so they are benchmarks, not tradable rules (as in
   V4.1). They are re-estimated in every bootstrap replicate. Only the matching *keys* must be
   causal, and they are.
3. **Residual dependence.** Outcome windows still overlap across calendar-block edges.
   Percentile-bootstrap p-values are approximations. Both points are disclosed rather than
   corrected.
4. **Lift versus precision.** Lift uses the frequency-independent "event in range" rate, while
   strict precision penalises repeated alerts. Both are reported; neither replaces the other.
5. **Trading approximations.** An intrabar stop's holding cost runs to the candle close. Long
   holding costs are assumed zero (spot); a perp long would pay funding. Hard-to-borrow fees and
   FX carry are not modelled.
6. **Candles, not calendar time.** Label radius and windows are in candles, so on equities
   (session hours) they span more calendar time than on crypto. This is consistent with the
   frozen definitions and was not changed.

## Is the first evaluation safe to begin?

**Not yet. It is blocked on two items, by design:**

1. **An independent review** of `research/v5_state.py`, `research/v5_eval.py`,
   `research/v5_costs.py`, `research/v5_ledger.py` and `research/v5_data.py`, focused on
   leakage and the statistics, by someone other than the author.
2. **A committed evaluation configuration** for the first family (C, major tops, 1H/4H,
   exploration data). It must fix:
   * the detector variants to try (C1–C5);
   * the cells;
   * the metrics requested;
   * the ledger trial ids.

   It must be committed before any detector is scored.

No other blockers were found: the data needed for 1H/4H exploration is cached, guarded and
inside the freeze.
