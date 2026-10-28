# HC-MTF 6.0: indicator-overhaul development proposal (continuation stage first)

**Status: PROPOSAL** (2026-10-28).
* Nothing here has been run. No V6 code, no V6 configuration, and no V6 outcome exists.
* No Pine change.
* Nothing here claims or implies a predictive edge.

**Next step.** After review, a stage-1 configuration (`reports/V6_CONT_CONFIG.md`) is drafted from
§3–§7, resolved, and frozen in a commit of its own. It must be frozen before any V6 code that
touches outcomes is written.

## 1. Audit (verified 2026-10-28)

| item | state |
|---|---|
| branch | `claude/mtf-conviction-indicator`, equal to origin, clean |
| P1 regression | **fixed** in a separate commit: literal label-module references removed from the workstream-M docstring and runner fingerprint list. No behaviour change: neither file imported the label module, and the label file stays protected by P2. **Full suite on the committed, clean tree: 137 passed, pytest exit 0** |
| production Pine | `pine/HighConvictionMTF.pine` (v6 indicator, 365 lines) and `pine/HighConvictionMTF_strategy.pine` (398). Structure-break engine on an LTF/MTF/HTF ladder: HTF trend = EMA21 via `request.security(…, f()[1], lookahead_on)`; momentum confluence from RSI14 / MACD(12,26,9); LTF via `request.security_lower_tf`. **Unchanged; stays unchanged in this stage** |
| reusable research code | `research/v5_data` (guarded cache loader, freeze cut, integrity cut), `v5_state`, `v5_baselines` (EMA-cross, Supertrend, HTF flip), `v5_eval` (frozen labels, `bar_outcomes` r_h, causal benchmark, `trade`, `sequential_daily`), `v5_costs`, `v5_context` (point-in-time eligibility E1–E6), `v5_inference` (`cluster_diff_test`, `cluster_mean_test`), `v5_ledger`, `v5_manifest`, `v5_gate`; `hcmtf.ta` (Pine-identical EMA/RSI/MACD/ATR) |
| frozen, not to be changed | family C config, results and ledger records; workstream M config, results and ledger records; `v5_labels.py` (P2); V4.1 protected files; the 28 existing ledger records |

**Relevant prior evidence.** It is evidence against the configurations tested, not against
technical analysis in general.

| prior result | where | relevance to V6 |
|---|---|---|
| RSI/MACD "momentum" confluence as a filter on structure breaks: **dropped** (crypto difference +0.03 [−0.14, +0.20], 1/4 TFs > 0) | v2 screening | weak prior for RSI/MACD as filters; but there the base signal was a structure break, not an EMA pullback |
| EMA20/50 cross as a continuation signal on these 35 crypto pairs: `rh_x` ≈ 0 at 1H (both sides); 4H shorts +0.45 [+0.02, +0.88], 1 of 16 reference cells | workstream M stage A | **already examined**: the EMA family on this data is not fresh |
| RSI divergence (C2) and extension (C1) as major-top warnings: no lift | family C | relevant to the later reversal stage, not to continuation |
| BTC-regime gates: no measurable increment | workstream M | V6 stage 1 uses no cross-market context |

## 2. Data roles (identified from code and manifests; no protected outcome accessed)

| data | role in V6 | allowed use |
|---|---|---|
| 35 cached non-BTC Binance spot USDT pairs + BTCUSDT, 1H native (4H resampled), candles closing ≤ 2026-10-27 23:59:59 UTC | **already examined** (v2 → V5 M) | **exploratory only**; never described as out-of-sample or independent |
| cached perp funding (9 pairs), perp 1H (10) | examined | costs only |
| `V5_RESERVE["crypto"]`: 12 pairs never downloaded | **reserved** | A V6 confirmatory test may use them only after (a) a frozen V6 G2 pre-registration and (b) an independent review: the confirmatory gate rejects the self-audit waiver (§8). For an asset-specific continuation rule they give real cross-sectional, but not temporal, independence |
| every candle after the freeze, any instrument | **reserved**; shared with the frozen V4.1 H6/H7v forward test (earliest 1H evaluation 2027-07-01) | not loaded (enforced by `v5_data`). A V6 forward test needs a documented protocol decision that leaves V4.1 unchanged |
| non-crypto instruments, BTC-USD (Yahoo duplicate) | out of scope | none |

## 3. Universe, timing and costs (to be frozen; same safeguards as workstream M)

* **Universe.** The 35 non-BTC pairs, eligible per candle by the frozen workstream-M rules E1–E6
  (`v5_context.eligibility`):
  * ≥ 365 days of history;
  * 30-day median quote volume ≥ $5M;
  * liquidity rank ≤ 25;
  * ≥ 95% candle completeness;
  * before any integrity cut;
  * warm indicators.

  E7 (BTC context) is not used. BTCUSDT is reported separately and never pooled.
* **Timeframes.** 1H and 4H. Signals from 2020-01-01; earlier candles serve only as indicator
  warm-up.
* **Single chart timeframe.** Model A–D signals use the chart TF only, with no
  `request.security`. This keeps the eventual Pine implementation causal without HTF alignment
  (§9).
* **Entry.** Signal decided at the close of candle i; entry at the open of i+1.
* **Signal-quality outcome** (register §2.1, unchanged): `rh` = move to H candles (1H: 24,
  4H: 30) in ATR14, after costs. `rh_x` = `rh` minus the pair's past-only benchmark in the same
  EMA trend state (§4).
* **Trading outcome, kept separate.** The entry rule is fixed; exits are fixed separately and are
  never used to select signals.
  * Stop = the pullback extreme (lowest low / highest high since the pullback began) minus /
    plus 0.5 ATR14.
  * Time exit at 2H candles.
  * No position sizing: one unit per trade, one trade at a time per pair in the book view.
* **Costs.**
  * Fees: 20 bp round trip (Binance spot taker).
  * **Slippage, now modelled as a fixed assumption:** +10 bp round trip for pairs ranked ≤ 10
    on liquidity at the signal, +20 bp for ranks 11–25. Sensitivity at 0× and 2×.
  * Shorts: observed perp funding where cached, otherwise 10%/yr (labelled estimated).
  * A missing cost is reported as missing, never as 0.
  * Short results are primary only on the 9 pairs with a cached perp, after its first cached
    candle.

## 4. Stage 1 models (continuation only; one primary definition each; long and short defined and reported separately)

All indicators are standard (`hcmtf.ta`, Pine-identical) and evaluated on closed chart candles:
* EMA20, EMA50, EMA200;
* RSI14 (Wilder);
* MACD(12, 26, 9);
* ATR14.

Longs are written below. Shorts are defined separately with the mirrored conditions and are
evaluated and decided separately. A mirror is the registered starting point, not an assumption
that the two sides behave alike.

**Trend state** (also the benchmark stratum):
* `up`: EMA20 > EMA50 > EMA200, **and** EMA50 slope > 0 (EMA50[i] − EMA50[i−10] > 0), **and**
  EMA200 slope ≥ 0 (EMA200[i] − EMA200[i−50] ≥ 0);
* `down`: the mirror;
* `none` otherwise.

| model | long signal at candle i (all conditions on closed candles ≤ i) | adds |
|---|---|---|
| **A: EMA-only trend and pullback** (baseline) | `up` at i; a **pullback** began at the first candle j ≤ i with low[j] ≤ EMA20[j] in the current `up` run, with i − j ≤ 10 and no close < EMA50 in j … i; **trigger**: close[i] > EMA20[i] **and** close[i] > high[i−1]; **one signal per pullback** (the first trigger after j) | – |
| **B: A + RSI recovery** | A at i, **and** min RSI14 over j … i ≤ 45 (the pullback really reset momentum), **and** RSI14[i] ≥ 50 with RSI14[i] > RSI14[i−1] | trend-conditioned RSI threshold plus slope |
| **C: B + MACD** | B at i, **and** MACD histogram[i] > histogram[i−1] (momentum turning up) | MACD increment over RSI |
| **D: best of A–C + extension** | the best **qualifying** model among A, B, C by §6 (A if none qualifies), **and** (close[i] − EMA50[i]) / ATR14[i] ≤ 3 (not over-extended at entry) | volatility-normalised extension |

**Shorts** (`down`, rally to EMA20):
* B uses max RSI14 ≥ 55 and RSI14[i] ≤ 50, falling.
* C uses histogram[i] < histogram[i−1].
* D uses (EMA50 − close)/ATR ≤ 3.

**Sensitivity set.** Fixed now; reported, **never** used to select a model.

| parameter | primary | alternatives |
|---|---|---|
| EMA periods | 20/50/200 | 10/30/100 and 30/70/200 |
| pullback window | 10 | 6, 15 |
| RSI recovery threshold | 45 / 50 | 40 / 50, 50 / 55 |
| extension cap | 3 ATR | 2, 4 |
| MACD condition | histogram rising | MACD line > signal line; MACD line crossing above 0 within 5 candles |

That is at most 10 alternative runs. They are recorded as trials in their own right.

**Simple trend-following comparators** (existing code, same eligibility, same costs):
* EMA20/50 cross;
* Supertrend(10, 3) flip;
* HTF-state onset (`v5_baselines`);
* a **random entry in the same trend state** (the causal benchmark that defines `rh_x`).

## 5. Statistics (reusing workstream-M machinery)

**Incremental contrasts:**
* B vs A, C vs B and D vs its base. Each is a filter of the previous model's signals, so the
  test is **Δ = mean `rh_x`(kept) − mean `rh_x`(filtered out)**, per side and per TF.
* Plus **kept vs matched random removal**: the same number removed per (pair, trend state),
  with no indicator information; 200 replicates.

**Absolute check of A.** Mean `rh_x`(A) > 0, i.e. A beats a random entry in the same trend
state, and A vs each comparator.

**Uncertainty:**
* `cluster_diff_test` / `cluster_mean_test`: wild cluster bootstrap with t(G−1).
* Clusters = calendar blocks shared by all pairs (1H: 1 month, G ≈ 82; 4H: 2 months, G ≈ 41).
  This covers time dependence and cross-pair correlation together.

**Robustness**, required for a pass (§6):
* per-pair Δ: ≥ 8 qualifying pairs (≥ 20 signals on each side of the contrast), median > 0, and
  ≥ 60% of them positive;
* equal-pair-weight Δ > 0;
* altcoin-tier Δ > 0;
* Δ > 0 after removing the top 5% of `rh` outcomes by absolute value;
* Δ > 0 after removing the single most favourable pair.

**Multiple testing.** Holm across the stage-1 decision cells (3 contrasts × 2 sides × 2 TFs =
12), plus A's absolute test (4 cells) as its own family. Sensitivity runs are not tested.

**Reported, never decisive:**
* MFE/MAE;
* the +2/−1 ATR barrier rate;
* net trading results with drawdown;
* results by trend/volatility regime (`v5_state` vol tercile) and by year.

## 6. Success, rejection, inconclusive (per cell; frozen before outcomes)

**ADDS VALUE (exploratory)** — all of:
1. Δ > 0;
2. Holm-adjusted p < 0.05;
3. the kept mean exceeds the 97.5th percentile of matched removal;
4. all robustness conditions of §5 hold.

**NO VALUE** if either:
* the t-CI of Δ lies entirely ≤ 0; or
* pooled and equal-pair Δ are both ≤ 0.

**INCONCLUSIVE** otherwise.

**Model status:**
* a model **qualifies** if its contrast ADDS VALUE in ≥ 1 TF for a side, and is not NO VALUE at
  the other TF;
* RSI (B) is judged on B vs A;
* MACD (C) is judged on C vs B. If B does not qualify, C vs A is reported, but MACD cannot
  qualify on top of a non-qualifying RSI step;
* extension (D) is judged on D vs its base.

**What counts as success for HC-MTF 6.0 stage 1:**
* A beats random in-state entry (absolute test), **and**
* at least one of RSI / MACD / extension ADDS VALUE on top of it,
* **and** net trading median per pair ≥ 0 after fees, slippage and funding.

**Rejection:** A fails its absolute test in every cell, **or** every incremental contrast is NO
VALUE.

**Inconclusive:** anything else.

**Implementation gate.** Even a stage-1 success is **exploratory**. A model reaches Pine only
after a frozen G2 pre-registration passes on reserved data (the 12 reserve pairs and/or forward
data). That needs an independent review, which the current gate (`confirmatory_blockers`)
requires and the self-audit waiver cannot satisfy.

## 7. Stage 2 (later, separate configuration): major tops and bottoms

* **Labels.** The frozen major-top/bottom labels (`v5_labels`, unchanged) and the frozen scoring:
  recall, precision excluding duplicates, lead, move remaining.
* **Candidate features:**
  * RSI/MACD-histogram divergence at a confirmed pivot;
  * failed recovery: a rally into EMA20/50 that fails after a `up` → `none` transition;
  * structural deterioration: a close below EMA50 with EMA20 slope turning down.

  No EMA50/200 cross is used as the initial trigger.
* **Comparators:** family C's detectors and baselines at matched frequency.
* Developed only after stage 1 is reported. Tops and bottoms each get their own hypotheses.

## 8. Minimal files (stage 1)

| file | change |
|---|---|
| `reports/V6_CONT_CONFIG.md` | **add**: stage-1 pre-registration (§3–§6 made exact); DRAFT, then FROZEN in its own commit |
| `research/v6_signals.py` | **add**: trend state and models A–D for both sides, plus the sensitivity variants. Pure functions of OHLC, no label or evaluator import |
| `scripts/v6_cont_explore.py` | **add**: runner reusing `v5_data`, `v5_context` (E1–E6), `v5_eval`, `v5_costs`, `v5_inference`, `v5_ledger`; per-pair storage; render |
| `tests/test_v6_signals.py` | **add**: truncation (signals unchanged when later candles are appended), one signal per pullback, no label import, slippage/cost tables, synthetic end-to-end |
| `research/v5_gate.py` | **modify**: add `v6_blockers()` (V6 config frozen and committed, review mode valid, manifest verifies, V6 code committed) |
| `research/v5_ledger.py` | **modify**: register hypothesis ids `V6-A`, `V6-B`, `V6-C`, `V6-D`, `V6-S` (sensitivity) |
| register / protocol | Amendments sections only |

**Trials:** `v6-a`, `v6-b`, `v6-c`, `v6-d` × {1H, 4H} = 8, plus ≤ 10 sensitivity trials.

**Third-party repositories.** None is needed for stage 1: every indicator above is standard and
already implemented Pine-identically in `hcmtf.ta`. They will be inspected (source and licence)
only if a later stage needs a concept they implement.

## 9. Pine (after a confirmed candidate only)

* Chart-timeframe calculations only, so there is no HTF repaint surface.
* Signals on `barstate.isconfirmed`.
* One `alertcondition` per side.
* Arrows for continuation; distinct markers for major reversals.
* Diagnostics behind an input toggle.
* Signal logic separate from the strategy twin's exits.
* A Python mirror test proving Pine == research logic, as was done for v2.

## 10. Decisions needed before the configuration is drafted

1. Approve the stage-1 definitions of models A–D and the sensitivity set (§4).
2. Approve the slippage assumption (+10 / +20 bp round trip by liquidity rank) and the stop
   rule (pullback extreme ∓ 0.5 ATR).
3. Approve the success / rejection / inconclusive criteria and the implementation gate (§6).
   In particular, accept that a Pine release requires a confirmatory pass that needs an
   independent review.
