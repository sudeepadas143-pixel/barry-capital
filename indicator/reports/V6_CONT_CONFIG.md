# HC-MTF 6.0, stage 1: continuation models A–D (EMA, RSI, MACD, extension), crypto 1H/4H

**Status: FROZEN** (2026-10-28).
* Drafted from [`V6_DEVELOPMENT_PROPOSAL.md`](V6_DEVELOPMENT_PROPOSAL.md) with the owner's eight
  clarifications (2026-10-28). Frozen in a commit of its own, before any V6 code was written or
  any V6 outcome computed.
* Nothing in this file may change once an outcome is computed. A defect found later needs a
  logged amendment, a new configuration version and new trial ids.

**Kind of study.** Exploration on **already-examined** data, in review mode
`self_audited_exploration_only`:
* No result here is out-of-sample, independent, or evidence of an edge.
* A stage-1 success does **not** authorise a Pine release (§12).

**Seen before freezing.** No outcome of models A–D, their alternatives, or the trend state
below has been computed. Related prior results:
* v2: an RSI/MACD "momentum" confluence filter on structure breaks was dropped.
* Workstream M stage A: EMA20/50 cross `rh_x` ≈ 0 at 1H.

## 1. Data, universe, window

| item | value |
|---|---|
| source | cached Binance spot USDT pairs via `research.v5_data.load` only: cache only, closed-candle freeze cut (2026-10-27 23:59:59 UTC), integrity cut. **No download, no reserve instrument, no post-freeze candle** |
| targets | the 35 non-BTC pairs `research.v5_context.TARGETS` |
| BTCUSDT | evaluated and reported **separately**; never pooled, never in a decision |
| tiers | majors: ETHUSDT, SOLUSDT; altcoins: the other 33 |
| timeframes | 1H (native) and 4H (`hcmtf.data` UTC 4-hour buckets). Chart timeframe only: no higher-timeframe input |
| signal window | signal candles opening ≥ 2020-01-01 00:00 UTC whose evaluation window lies inside the data (§5). Earlier candles are indicator history only |
| data identity | `reports/V5_EXPLORATION_DATA_MANIFEST.json`, combined sha256 `57e107b0…`; `v5_manifest.verify()` clean at the start of every trial |

**Per-candle eligibility at the signal candle i.** These are the frozen workstream-M rules E1–E6
(`v5_context.eligibility`, `V5_M_B_CONFIG.md` §1.1), unchanged:
* E1: ≥ 365 days of history;
* E2: 30-day median daily quote volume ≥ $5M (days ending at or before the candle's open);
* E3: liquidity rank ≤ 25 among the 35 pairs (ties broken by symbol);
* E4: ≥ 684/720 hourly candles present;
* E5: before any integrity cut;
* E6: `v5_state` warm.

E7 (BTC context) is **not used**: the eligibility call receives an all-true BTC-availability
array. E3 is not applied to BTCUSDT. A signal on an ineligible candle is excluded and tallied by
its first failing rule. The E3 rank is also used for slippage (§6).

## 2. Indicators (Pine-identical, `hcmtf.ta`; closed chart candles only)

| name | definition |
|---|---|
| EMA_f, EMA_m, EMA_s | `ta.ema(close, n)` with (f, m, s) = (20, 50, 200) primary; SMA-seeded, undefined until n values, as Pine |
| RSI | `ta.rsi(close, 14)` (Wilder) |
| MACD | `ta.macd(close, 12, 26, 9)`: line, signal, histogram = line − signal |
| ATR | `ta.atr(14)` (RMA of true range) |

* **Undefined input.** A candle whose required value is undefined (NaN) satisfies **no**
  condition. It is not a signal candle, and it ends an open pullback (§3.4).
* **Missing candles.** Indicators run over the candles that exist, as TradingView does; there is
  no synthetic filling.
* **Gap.** A gap before candle k means open time[k] − open time[k−1] > 1.5 × the nominal
  duration (1 h or 4 h).

## 3. Signal definitions

**Timing.** Every condition at candle i uses values of candles ≤ i only, all closed when candle i
closes. The signal is known at the close of candle i. Execution is at the open of the **next
existing candle** i+1 (§5).

### 3.1 Trend state (also the benchmark stratum)

`trend[k]` is:
* `up` if EMA_f[k] > EMA_m[k] > EMA_s[k], **and** EMA_m[k] − EMA_m[k−10] > 0, **and**
  EMA_s[k] − EMA_s[k−50] ≥ 0;
* `down` if EMA_f[k] < EMA_m[k] < EMA_s[k], **and** EMA_m[k] − EMA_m[k−10] < 0, **and**
  EMA_s[k] − EMA_s[k−50] ≤ 0;
* `none` otherwise;
* `unknown` if any input is undefined.

The lags 10 and 50 count candle rows.

### 3.2 Model A, long (EMA-only trend and pullback)

A per-pair state machine, run candle by candle in time order:

1. **Pullback start.** With no pullback open, a pullback starts at candle j if:
   * trend[j] = `up`;
   * low[j] ≤ EMA_f[j];
   * the pair is **armed**.

   It is **armed** at the start of the series and becomes armed again at any candle k with
   trend[k] = `up` and low[k] > EMA_f[k] (price above the fast EMA again). Starting a pullback
   disarms it.
2. **Trigger.** While a pullback opened at j is open, candle i (i ≥ j) **triggers** if:
   * trend[i] = `up`;
   * close[i] > EMA_f[i];
   * close[i] > high[i−1]. The prior-high reference is the high of the immediately preceding
     existing candle.
3. **Signal.** The first trigger of a pullback is a model-A long signal at i. The pullback then
   closes: **one signal per pullback**.
4. **Pullback ends without a signal** at the first candle i where any of these holds:
   * close[i] < EMA_m[i] (invalidation);
   * trend[i] ≠ `up`;
   * i − j > W, with W = 10 rows (the window; triggers are allowed on rows j … j+W);
   * there is a gap before i;
   * an undefined input at i.

   The end is checked **before** the trigger, so an invalidating candle cannot trigger.
5. After a pullback ends (with or without a signal), a new one needs the pair to be armed again
   (step 1).

### 3.3 Model A, short (defined and evaluated separately)

Same machine with:
* trend `down`;
* pullback start: high[j] ≥ EMA_f[j];
* arming: high[k] < EMA_f[k] in `down`;
* invalidation: close[i] > EMA_m[i];
* trigger: close[i] < EMA_f[i] **and** close[i] < low[i−1].

### 3.4 Filters B, C, D (applied to model-A signals at the same candle i; they never create a new signal time)

All windows below run over the pullback rows j … i of that A signal.

| model | long condition at i | short condition at i |
|---|---|---|
| **B = A + RSI** | min RSI[j..i] ≤ 45 **and** RSI[i] ≥ 50 **and** RSI[i] > RSI[i−1] | max RSI[j..i] ≥ 55 **and** RSI[i] ≤ 50 **and** RSI[i] < RSI[i−1] |
| **C = B + MACD** | B **and** histogram[i] > histogram[i−1] | B **and** histogram[i] < histogram[i−1] |
| **D = A + extension** | A **and** (close[i] − EMA_m[i]) / ATR[i] ≤ 3 | A **and** (EMA_m[i] − close[i]) / ATR[i] ≤ 3 |

**D's parent is fixed as A** (owner's clarification 4). It is not chosen from results: the
extension filter is its own incremental hypothesis on the EMA baseline. Extension on top of B
or C is **not** evaluated in this version.

### 3.5 Predefined alternatives

Each alternative changes **one** setting; everything else stays primary. All are run, all are
reported, all are in the multiple-testing families of §8, and **none is selected**.

| config id | change | affects |
|---|---|---|
| `P` | primary: EMA 20/50/200, W 10, RSI 45/50 (short 55/50), MACD histogram rising, extension cap 3 | A, B, C, D |
| `E1` | EMA 10/30/100 | A, B, C, D |
| `E2` | EMA 30/70/200 | A, B, C, D |
| `W1` | W = 6 | A, B, C, D |
| `W2` | W = 15 | A, B, C, D |
| `R1` | RSI dip ≤ 40, recover ≥ 50 (short: peak ≥ 60, fall ≤ 50) | B, C |
| `R2` | RSI dip ≤ 50, recover ≥ 55 (short: peak ≥ 50, fall ≤ 45) | B, C |
| `M1` | MACD line[i] > signal[i] (short: <) instead of histogram rising | C |
| `M2` | MACD line crossed above 0 within i−4 … i: line[k] > 0 ≥ line[k−1] for some k (short: mirror) | C |
| `X1` | extension cap 2 | D |
| `X2` | extension cap 4 | D |

The slope lags (10, 50) and the RSI-slope / histogram one-step comparisons are fixed in every
config.

## 4. Comparators (existing code; same eligibility, costs and outcome)

* EMA20/50 cross (`v5_baselines.ema_cross`);
* Supertrend(10, 3) flip (`supertrend_flip`);
* HTF-state onset (`htf_flip`, `v5_state`);
* **matched random entry** (§7).

Comparators are reported, side by side and per side. Only the matched random entry is decisive
(for A).

## 5. Outcomes, entry and exit (identical for every model and comparator)

**Entry.**
* At the open of candle i+1, the next existing candle.
* If there is a gap before i+1, or i+1 does not exist, the signal is excluded (`entry_gap` /
  `no_exit_in_data`) for every model alike.

**Signal quality** (decision metric):
* `rh` = side × (close[i+H] − open[i+1]) / ATR[i], minus total cost × open[i+1] / ATR[i]
  (§6), with H = 24 (1H) or 30 (4H) **rows**.
* Computed with `hcmtf.evaluate.bar_outcomes` (cost 0) minus the cost term.
* Excluded and counted:
  * signals whose window i+1 … i+H runs past the data (`no_exit_in_data`);
  * signals whose window spans more than 1.25 × H nominal durations (`gap`).
* `rh_x` = `rh` − `v5_eval.causal_benchmark(table, "rh", ["trend"], H, 200)`, computed per side.
  The table holds every candle of the pair, with `rh` NaN on candles that are not E6-warm or have
  undefined trend inputs. The benchmark is the past-only mean of the same pair in the same trend
  state, using outcomes known at i. Units without a benchmark are counted and excluded.
* **Also reported** (never decisive): MFE and MAE over H in ATR; the +2/−1 ATR barrier;
  `rh` median.

**Trading outcome** (separate tables; never decisive): `v5_eval.trade(o, h, l, c, idx, i, side,
hold = 2H, stop, "crypto", funding)` with the rules below.

| element | rule |
|---|---|
| stop (long) | min(low[j..i]) − 0.5 × ATR[i]. The pullback extreme over the pullback rows; ATR of the signal candle i, closed at the signal |
| stop (short) | max(high[j..i]) + 0.5 × ATR[i] |
| entry at or through the stop | if open[i+1] ≤ stop (long) / ≥ stop (short), the trade exits at open[i+1] (`stop_gap`) |
| gap through the stop later | exit at that candle's open (`stop_gap`) |
| intrabar stop | exit at the stop price |
| target | **none**, so there is no same-bar stop/target conflict. Any future target rule must resolve a conflict as stop first |
| time exit | close of candle i + 2H rows (1H: 48, 4H: 60); holding time to that close (`v5_eval._close_time`) |
| unavailable data | exit candle past the data: `no_exit_in_data`, excluded and counted. Holding window spanning > 1.25 × 2H nominal durations: `trade_gap`, excluded and counted |
| sizing | one unit per trade; per-pair book one trade at a time (`v5_eval.sequential_daily`); no pyramiding |

**Trading metrics:**
* net per trade: mean, median, distribution 5/25/50/75/95%;
* worst trade; trade MAE (5/50/95%);
* per-pair book total log return and maximum drawdown;
* the share of total net P&L from the top 1% of trades and from the top 5 pairs (dominance).

## 6. Costs (charged identically in `rh` and in trades)

| item | value |
|---|---|
| fees | 20 bp round trip (Binance spot taker 0.1% per side) |
| slippage (primary) | +10 bp round trip if the pair's E3 rank at the signal candle is ≤ 10; +20 bp if 11–25 |
| slippage sensitivity | × 0 and × 2, reported for every primary cell. Never used for decisions |
| funding, longs | none (spot) |
| funding, shorts | `v5_costs.short_holding_cost`: observed cached perp funding when it covers the holding period (`observed_funding`); otherwise **10% a year** (`estimated_crypto_10pct`). Source counts shown in every table. A missing cost is never 0 |
| short feasibility | spot cannot be shorted; shorts assume a perp at spot prices (basis not modelled). The primary **short trading** tables use only the 9 cached-perp pairs (ADA, BNB, DOGE, ETH, LINK, LTC, SOL, TRX, XRP), after each pair's first cached perp candle; other pairs appear in a separate table. Short **signal quality** uses every eligible pair |

## 7. Baselines and contrasts

**C0: A vs matched random entry** (the absolute test of A), per side and TF:
* **Primary statistic:** mean `rh_x` of A > 0. The causal benchmark is random entry in the same
  pair and trend state, past-only.
* **Matched random entry:** 200 seeded replicates (`default_rng(20261027)`). Within each
  (pair, calendar block), draw as many candles as A has there, uniformly without replacement.
  The pool is the eligible, in-window candles with trend = `up` (longs) / `down` (shorts) and a
  full `rh` window. A shortfall (fewer candidates than signals) keeps all candidates and is
  reported.
* Statistic: mean `rh` of A vs the 2.5/50/97.5 percentiles of the replicate means.

**Incremental contrasts:**

| contrast | kept set | removed set |
|---|---|---|
| C1: RSI (B vs A) | B signals | A signals not in B |
| C2: MACD (C vs B) | C | B ∖ C |
| C3: extension (D vs A) | D | A ∖ D |

* Statistic: Δ = mean `rh_x`(kept) − mean `rh_x`(removed). Units are signals.
* **Matched removal control:** 200 replicates of a random subset of the parent set, with K's
  count per pair (`v5_context.matched_removal_means`, strata = pair).
* **C vs A** is reported, not decided.

## 8. Uncertainty, evaluability, multiple testing

**Uncertainty.** Wild cluster bootstrap with t(G−1) (`v5_inference.cluster_mean_test` for C0,
`cluster_diff_test` for C1–C3):
* 9,999 replicates; Rademacher if G ≥ 12, else Webb; seed 20261027; one-sided.
* Clusters are **calendar blocks shared by all pairs** (1H: 1 month; 4H: 2 months;
  `research.v41.cluster_id` on the signal candle). One weight multiplies every pair in a block,
  covering time dependence and cross-pair correlation together.

**Evaluability.** A cell is evaluable only if:
* C0: ≥ 100 signals from ≥ 10 pairs, and G ≥ 10;
* C1–C3: ≥ 100 kept **and** ≥ 100 removed units, ≥ 10 pairs with ≥ 1 of each, and G ≥ 10.

An underpowered cell's verdict is **INCONCLUSIVE (underpowered)**. Its p enters Holm as 1, and
no threshold is relaxed.

**Per-pair quantities:**
* **qualifying pair** = ≥ 20 kept and ≥ 20 removed units for C1–C3, or ≥ 20 signals for C0;
* per-pair Δ (C0: per-pair mean `rh_x`);
* median over qualifying pairs;
* **positive share**: Δ_p > 0 strictly, over qualifying pairs;
* equal-pair-weight mean over pairs with a defined value;
* altcoin-tier Δ.

**Robustness quantities** (per evaluable cell):
* `trim5`: Δ (or C0 mean) recomputed after dropping the units whose |`rh`| is in the top 5% of
  the cell's units (kept and removed together);
* `drop_best`: Δ recomputed after dropping every unit of the pair with the largest per-pair Δ
  (C0: largest per-pair mean) among pairs where it is defined.

**Multiple-testing families** (Holm, one-sided p):

| family | cells (config × side × TF) | size |
|---|---|---:|
| V6-A (C0) | {P, E1, E2, W1, W2} × 2 × 2 | 20 |
| V6-B (C1) | {P, E1, E2, W1, W2, R1, R2} × 2 × 2 | 28 |
| V6-C (C2) | {P, E1, E2, W1, W2, R1, R2, M1, M2} × 2 × 2 | 36 |
| V6-D (C3) | {P, E1, E2, W1, W2, X1, X2} × 2 × 2 | 28 |

* **Primary:** Holm within each family.
* **Stricter sensitivity:** Holm across all 112 cells, reported in its own column, never
  replacing the primary.
* Every predefined alternative is inside its family's correction. Non-evaluable cells enter
  with p = 1. Family sizes never shrink.

## 9. Decision rules (mechanical)

**C0 cell (A vs random entry):**
* **BEATS BASELINE** if all of:
  * mean `rh_x` > 0, and Holm p < 0.05;
  * mean `rh` > the 97.5th percentile of matched random entry;
  * equal-pair mean > 0;
  * ≥ 8 qualifying pairs, with median > 0 and positive share ≥ 0.60;
  * altcoin-tier mean > 0;
  * `trim5` > 0 and `drop_best` > 0.
* **NO VALUE** if the t-CI upper bound ≤ 0, or the pooled and equal-pair means are both ≤ 0.
* **INCONCLUSIVE** otherwise, including underpowered cells.

**C1–C3 cell:**
* **ADDS VALUE** if all of:
  * Δ > 0, and Holm p < 0.05;
  * kept mean > the 97.5th percentile of matched removal;
  * equal-pair Δ > 0;
  * ≥ 8 qualifying pairs, with median Δ > 0 and positive share ≥ 0.60;
  * altcoin-tier Δ > 0;
  * `trim5` Δ > 0 and `drop_best` Δ > 0.
* **NO VALUE / INCONCLUSIVE** as for C0.

**Per side, using config `P` only.** The alternatives are reported per cell, with a count of how
many agree in sign. They are never selected and never used to rescue a primary verdict.
* **A qualifies** for a side if a `P` cell BEATS BASELINE at one TF and the other TF's `P` cell
  is not NO VALUE.
* **RSI qualifies** for a side on the same rule for C1.
* **MACD qualifies** on C2 **only if RSI qualifies** for that side.
* **Extension qualifies** on C3.

**Stage-1 outcome:**
* **SUCCESS (exploratory)** if, for at least one side, A qualifies, at least one of RSI, MACD or
  extension qualifies, **and** the corresponding model's `P` net trading median per pair is ≥ 0
  at primary costs, at a TF where the feature's cell ADDS VALUE.
* **REJECTED** if every `P` C0 cell is NO VALUE, **or** every `P` C1–C3 cell is NO VALUE.
* **INCONCLUSIVE** otherwise.

**Disclosure.** Every cell and outcome is shown under both Holm scopes. Any disagreement between
the primary and the stricter all-cell result is stated explicitly.

## 10. Reporting

* Every config × model × side × TF, with counts and exclusions by reason.
* Per-pair tables.
* Pooled, equal-weight and tier results.
* Signal-quality and trading results in **separate** tables, with long and short separated.
* By year and by `v5_state` volatility tercile at the signal (descriptive).
* Comparators.
* Dominance (§5).
* Slippage sensitivity.
* BTCUSDT separately.

## 11. Integrity, causality, ledger

1. **Truncation.** Signals of every model and config at candle i are identical when all candles
   after i are removed (synthetic tests).
2. **No label access.** `research/v6_signals.py` imports neither the label module nor the
   evaluator.
3. **Gate.** `v5_gate.v6_blockers()` returns no blocker only if:
   * this file is committed, unmodified and `Status: FROZEN`;
   * the review mode is valid;
   * the manifest verifies;
   * baselines, `research/v6_signals.py`, `research/v5_context.py`, `research/v5_inference.py`
     and `scripts/v6_cont_explore.py` are committed and unmodified.

   `c_blockers`, `m_blockers` and `confirmatory_blockers` are unchanged.
4. **Ledger.** 22 trials, `v6-{config}-{TF}` for the 11 configs × 2 TFs:
   * hypothesis id `V6-P` for config P and `V6-S` for the alternatives;
   * each recorded with `v5_ledger.record` **before** its computation (`config_file` = this
     file, `outcomes_accessed = True`), then committed, with `verify_against_git`.

   Earlier V5 records stay as they are. After this run the V5/V6 exploratory trial count will be
   50.

## 12. Data roles and the Pine gate

* **Reads:** only the 36 cached crypto pairs up to the freeze (already examined).
* **Not read:**
  * `V5_RESERVE` pairs;
  * post-freeze candles (shared with the frozen V4.1 H6/H7v forward test);
  * labels (stage 1 does not score reversals).
* **Pine release gate.** A stage-1 SUCCESS is exploratory. A Pine release requires a separately
  governed confirmatory test: a frozen G2 pre-registration on reserved data, which needs an
  independent review. `confirmatory_blockers` rejects the self-audit waiver.
* **Production Pine scripts** are unchanged in this stage.
