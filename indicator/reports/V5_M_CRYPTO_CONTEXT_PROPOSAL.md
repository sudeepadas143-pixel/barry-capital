# V5 workstream M: crypto-native multi-market context, audit and research proposal

**Status: PROPOSAL.** Nothing in this document has been run.
* No data fetched, no experiment run, no code added, no Pine change.
* No hypothesis below has been tested.
* Nothing here claims or implies a predictive edge.

## 1. Repository state (verified 2026-10-27)

| item | state |
|---|---|
| branch / HEAD | `claude/mtf-conviction-indicator` at `21f0a0b`, equal to `origin`; working tree clean |
| test suite | 117 passed at `21f0a0b` (pytest exit 0, run with `pipefail`) |
| trial ledger | 18 records; hash chain valid; `verify_against_git` passes |
| data manifest | `V5_EXPLORATION_DATA_MANIFEST.json` verifies against the cache: 270 files, no missing/changed/extra |
| gate | review mode `self_audited_exploration_only`; confirmatory gate closed (2 blockers: no independent review, Amendment 1 not adopted for confirmatory scope) |
| frozen files | family C config unchanged since `74d5ae5`; `v5_labels.py` identical to `7fc7e68`; V4.1 protected files byte-identical (test P2 / manifest hashes) |

Research artifacts this proposal depends on:
* `V5_DEVELOPMENT_PLAN.md`
* `V5_HYPOTHESIS_REGISTER.md` (frozen event definitions §2)
* `V5_VALIDATION_PROTOCOL.md`
* `V5_C_EXPLORATION_CONFIG.md`, plus the results and summary for family C (x1)
* the V4.1 preregistration and its forward test (§9)

## 2. What family C established, and what it did not

**Established (exploratory, on already-examined data):**
* None of C1–C4 (extension, divergence, failed breakout, volatility jump) placed warnings near major tops more often than an
  ordinary warm candle in the same HTF state did. This held at 1H and 4H, on 96 instruments.
* The engine's bearish CHoCH (C5a/C5b) does cluster after tops: lift ≈ 1.25, p ≈ 0.0001. But:
  * it is the existing `counter_reversal` signal, not a new detector;
  * it is less precise than EMA-cross (1H) and HTF-flip (4H) at matched frequency;
  * it fires after the top (median −15 candles).
* Frozen outcome: family C at x1 is rejected at exploration. No variant goes to an untouched-data test.

**Not established:**
* That major tops are unpredictable. Only these eight frozen detectors were tested.
* Anything about bottoms (family D), or about continuation (families A/B).
* Anything about crypto-market context: no family-C variant used BTC, breadth, dominance or stablecoin data.
* Per-instrument behaviour. Results were stored per asset group only.
* Anything about trade profitability. The trading view was secondary.

## 3. Reuse

**Reusable without modification:**

| component | use in workstream M |
|---|---|
| `research/v5_data.py` (`load`, `load_funding`, freeze cut, integrity cut, reserve guard) | all price input; LUNA's token-swap cut is already applied |
| `research/v5_reserve.py` | freeze, reserve list, closed-candle rule |
| `research/v5_state.py` (`classify`) | the asset's own HTF state, **and the BTC regime**: the same classifier run on BTCUSDT, so no new regime thresholds |
| `research/v5_labels.py` (frozen) via `v5_eval.frozen_labels` | top and bottom labels (families C/D), unchanged |
| `research/v5_eval.py` | `score_alerts`, `detection_report`, `lift_units`, `trade`, `causal_benchmark`, `excess_causal` |
| `research/v5_baselines.py` | HTF flip, EMA cross, Supertrend flip, counter-reversal; `thin` for matched frequency, and for a matched-pass-rate random gate (§6) |
| `research/v5_costs.py` | crypto round trip; observed funding where cached, else marked as estimated |
| `research/v5_inference.py` | wild cluster bootstrap with CR1, calendar-block clusters |
| `research/v5_ledger.py`, `v5_manifest.py` | trial recording before computation; data fingerprints |

**Specific to the cross-asset family-C experiment (not to be reused as is):**
* **Groups.** The groups crypto/equities/commodities/rates and the "≥ 2 groups evaluable" eligibility rule mean nothing in
  a crypto-only universe. They need a crypto grouping (§4) and a per-instrument rule.
* **Gate.** `v5_gate.c_blockers` checks the family C config. Workstream M needs its own config check. The C gate stays
  as it is.
* **Runner.** `scripts/v5_c_explore.py` stores group-level results only. The new runner must store per-instrument
  results.

## 4. Universe (proposed; fixed before any result)

**Source.** Binance spot USDT pairs (`data-api.binance.vision` klines), already cached as 1H.
* 4H, 1D and 1W are resampled from 1H by the existing code.
* Binance USDⓈ-M perpetuals are used **only** for short holding cost (funding). They never count as a second instrument.

**Instruments.** The 36 cached crypto pairs, as below:

| tier | instruments | notes |
|---|---|---|
| reference | BTCUSDT | the regime source; **not** a target in Model B (its "BTC regime" is its own price) |
| majors | ETHUSDT, SOLUSDT | SOL from 2020-08 |
| altcoins | the other 33 cached pairs | listed 2017-11 to 2021-05 |

The altcoin tier keeps coins whose history ends or breaks, which partly offsets survivorship:
* LUNA: token swap 2022-05, integrity cut;
* SRM: history ends 2022-11;
* WAVES: ends 2024-06;
* MATIC: ends 2024-09 (rename);
* EOS: ends 2025-05;
* ICX: ends 2026-09;
* FTT: collapsed 2022-11, still listed.

**Exclusions:**
* BTC-USD (Yahoo): a duplicate of BTC.
* Any perp series as an instrument.
* Stablecoins, wrapped and leveraged tokens (none are cached).

**Point-in-time eligibility** (causal, computed at each candle). A candle is eligible only if:
1. the pair has ≥ 365 days of history (warm-up, and avoids listing-pump regimes);
2. its trailing 30-day median daily quote volume (base volume × close; the cache has no quote-volume column) is in the
   top 25 of the cached set **at that time**, and ≥ $5M;
3. it is before any integrity cut, and inside `exploration_closed`.

**Survivorship: residual bias, stated plainly.** The 36 pairs were chosen in 2024–2026 from coins already known to have
been large. Coins that were liquid in 2018–2020 but are not in the cache are missing (absent, never imputed). The
point-in-time liquidity rule removes hindsight *within* the set, but not the choice of the set. Every result will be
labelled "survivor-skewed universe".

**Timeframes.** 1H and 4H, using the existing ladder: 1H uses 4H and 1D; 4H uses 1D and 1W.

**Costs:**
* Round trip: 20 bp. This is Binance spot taker 0.1% per side, the existing assumption.
* Slippage is **not modelled**, and is reported as missing.
* A fixed sensitivity of +10 bp per round trip, for coins outside the top 10 by trailing volume, is reported alongside.
* Shorts:
  * Funding is observed for the 9 coins with cached funding. Elsewhere it is estimated at 10%/yr and labelled as
    estimated.
  * Whether a perp existed at a given date is **unknown** for uncached coins. So short results are primary only for the
    9 coins with funding; the rest is a sensitivity analysis.
* Missing costs are never set to 0.

## 5. Context data sources

**No network call was made to check any source.** Statements about third-party coverage are from documentation known
before this session, and must be verified before use.

| feature | candidate source | history / granularity | limitations |
|---|---|---|---|
| BTC regime | **cached** BTCUSDT 1H (2017-08 →) | 1H native | none new; same feed and close times as the targets |
| own-universe breadth (share of eligible coins above their HTF EMA / in a bull state; advance–decline) | **cached**, computed from the 36 pairs | 1H | survivor-skewed; a narrow universe of at most 25 eligible coins; not TOTAL |
| relative strength (ETHBTC, alt/BTC) | **cached** price ratios | 1H | a price ratio, **not** dominance |
| TOTAL, TOTAL2, TOTAL3, BTC.D, ETH.D, USDT.D, USDC.D | TradingView `CRYPTOCAP:` indices | TradingView-computed; intraday depth depends on account plan | no export API (manual CSV export only on paid plans; scraping is against TradingView's terms); methodology and constituents set by TradingView; history may be recalculated, so it is **not point-in-time**; not reproducible in Python without manual exports |
| market cap, dominance (rebuilt) | CoinGecko / CoinMarketCap | free CoinGecko history limited to the last 365 days; full history paid | circulating-supply revisions, so not point-in-time |
| stablecoin supply | DefiLlama stablecoins API (free) | daily, roughly 2017 → | daily only (usable at 1H/4H only from the previous completed UTC day); backfilled and revisable; supply is not flow |
| exchange flows / balances | CryptoQuant, Glassnode (paid) | varies | entity labels are revised retroactively, so not point-in-time; **proposed: excluded** |
| funding, open interest | Binance, **cached** for 9 / 7 coins | funding 2020 →; OI 2021-12 → | not in scope for stages A–B |

**Consequences:**
* Stages A and B, and an own-universe breadth version of stage C, need **no new data**.
* TOTAL*, dominance and stablecoin features (stages C–E) cannot be reproduced from TradingView in Python. They would need
  either:
  * a manual export, with the export date recorded and hashed; or
  * a third-party API, with a revision-risk disclosure.

  That is a data-source decision for you, not something to start now.
* **USDT.D and USDC.D are ratios.** They rise when crypto prices fall, so as features they partly restate price. Any test
  must control for BTC's own return over the same window.

## 6. Risks

**Leakage:**
* **Cross-asset timing.** A BTC candle that closes at t may be used for an altcoin candle that closes at t (same
  exchange, same clock), with entry at the next open.
* **HTF context.** Context is taken from completed HTF candles only, via `align`.
* **Daily series.** Third-party daily series are available only from the next UTC day.
* **Revision risk** in third-party series (above) cannot be removed, only disclosed.
* **Truncation tests** are required for every new context feature, as in `test_v5_detect_c`.

**Correlation:**
* Altcoins co-move with BTC, so N instruments are not N independent samples.
* BTC regime is a **time-only** variable, the same for every coin at once. Its effect is identified only by how often the
  regime changes. Over 2017–2026 that is a small number of bull/bear episodes. The number of BTC regime episodes per TF
  will be reported as the effective sample.
* Clusters are calendar blocks shared across instruments (1H: 1 month; 4H: 2 months).
* ETH, SOL and the altcoin tier are reported separately. The pooled mean is never the only evidence.
* **Reserve coins** (`V5_RESERVE["crypto"]`, 12 never-downloaded pairs) share the same calendar. For a BTC-regime
  hypothesis they add almost no independent evidence. **Only forward data can confirm a time-varying context effect.**

**Multiple testing:**
* Stage B is registered as a fixed list of cells: signals × side × TF × tier. Holm applies within the stage.
* Trial counts from families C and M are carried in the ledger and disclosed.
* No stage may add features after seeing results. Stage F (combined) may include only features that passed their own
  stage.

**Selection bias:**
* Model A's signals are fixed in advance: existing baselines and engine signals, no new tuning. A stage-B gain cannot
  come from a re-tuned Model A.

## 7. Minimal staged plan

All stages are **exploratory**, on already-examined cached data, in self-audited mode.

**Stage A: price-only reference (no new detector).**

Signals per side, all already implemented and causal:
* continuation: `htf_flip`, `ema_cross`, `supertrend_flip` (side ±1) and the engine's continuation output;
* reversal: `counter_reversal` (side −1 against frozen top labels, side +1 against frozen bottom labels).

Metrics:
* continuation: net r_h, median and mean, minus the causal benchmark; MAE; drawdown of the sequential daily book;
* reversal: precision, recall, false alarms and timing against the labels.

Reporting: per instrument, per tier, per TF, per side.

Stage A is the reference that stage B must beat. It has no pass/fail rule of its own.

**Stage B: BTC regime as the first incremental feature.**

BTC regime is `v5_state.classify(BTCUSDT)` on the same ladder:
* bull / bear / neutral (range) from `direction_label`;
* "unstable" = BTC `vol_regime` in the top tercile.

These are existing definitions, with no new thresholds. If BTC data is missing for a candle, its regime is
**unavailable** (excluded and counted), never neutral.

Hypotheses (registered before any outcome):

| id | statement | primary statistic |
|---|---|---|
| M-B1 | Long continuation signals on non-BTC coins do better when BTC is bull than when it is not, **within the coin's own HTF state** | Δ = mean/median net r_h excess (BTC-aligned − not aligned), within the own-state stratum |
| M-B2 | Short continuation signals do better when BTC is bear (tested separately, after short costs) | as M-B1 |
| M-B3 | Signals fired while BTC is unstable have worse net r_h and larger MAE | Δ (unstable − stable) |
| M-B4 | Top alerts (`counter_reversal` −1) on non-BTC coins have higher duplicate-free precision when BTC is not bull; bottom alerts (+1) when BTC is not bear | Δ precision* |

Controls:
* **Own-state stratification.** The coin's own state is highly correlated with BTC's, so without stratifying, BTC regime
  would just re-measure the coin's own trend.
* **Random gate at the same pass rate,** per instrument and block (`v5_baselines.thin`). The BTC filter must beat a
  random filter that removes the same number of signals.

Decision per cell:
* **adds value (exploratory)** if all of the following hold:
  * Δ mean > 0 and Δ median > 0;
  * one-sided p_wild < 0.05 after Holm across the stage-B cells;
  * Δ beats the random gate's 97.5th percentile;
  * Δ > 0 in ≥ 60% of eligible instruments.
* **no value** if the t-CI of Δ lies entirely ≤ 0, or Δ ≤ 0 in every cell.
* **inconclusive** otherwise.

The thresholds above are a proposal. They are fixed when the config is frozen, before any stage-B number is computed.

**Later stages (not proposed for implementation now):**
* **C: breadth.** Own-universe breadth first, because it needs no new data. TOTAL2/TOTAL3 only after a data-source
  decision.
* **D: dominance.** Needs exported or third-party data.
* **E: stablecoin supply.** DefiLlama, daily.
* **F: combined.** Only features that passed their own stage.

Each later stage gets its own config, frozen before its outcomes. It is tested against the best model that passed an
earlier stage, or against Model A if none did.

**Confirmation route (not before review):**
* **Only forward data** (after the 2026-10-27 freeze) can confirm a BTC-regime effect.
* The forward crypto candles are shared with the V4.1 H6/H7v forward test (earliest 1H evaluation 2027-07-01).
* Using them for M requires a documented protocol decision first. That decision must not alter the V4.1 test.

## 8. Files for the first implementation step (stage A + B config and code, no run)

| file | change |
|---|---|
| `reports/V5_M_B_CONFIG.md` | **add**: stage A/B pre-registration (universe, eligibility, signals, regime definitions, cells, statistics, decision rules, trial ids); DRAFT, then FROZEN in its own commit |
| `research/v5_context.py` | **add** (small): BTC regime aligned to a target index by close time; point-in-time liquidity eligibility; "unavailable" handling |
| `tests/test_v5_context.py` | **add**: truncation causality; alignment never uses a BTC candle that closes after the target candle; BTC excluded as target; missing BTC → unavailable; eligibility uses trailing data only |
| `research/v5_gate.py` | **modify**: add `m_blockers()` (M config frozen, waiver or review present); `c_blockers` unchanged |
| `reports/V5_HYPOTHESIS_REGISTER.md`, `V5_VALIDATION_PROTOCOL.md` | **modify, Amendments sections only**: workstream M hypotheses; crypto-only universe and per-instrument reporting |
| `reports/V5_DEVELOPMENT_PLAN.md` | **modify**: progress log and next task |

A second step, after the config is frozen:
* `scripts/v5_m_explore.py`: the runner, storing per-instrument results;
* `tests/test_v5_m_runner.py`: a synthetic end-to-end test.

Not touched:
* Pine scripts;
* `v5_labels.py`;
* family C config, results and ledger records;
* V4.1 protected files;
* the data cache (no fetch).

## 9. Data status

| data | status | allowed use |
|---|---|---|
| 36 cached Binance crypto spot pairs, 1H (+ derived 4H/1D/1W), 15m for 26 of them, all candles closing ≤ 2026-10-27 23:59:59 UTC | **already examined** (v2–V4.1 and V5 family C) | exploratory only; never "independent" |
| cached perp 1H / funding / OI (10 / 9 / 7 coins) | examined (used as cost inputs) | costs only |
| BTC-USD (Yahoo) | examined; duplicate of BTC | excluded |
| non-crypto instruments in the cache | examined | out of scope |
| `V5_RESERVE["crypto"]` (12 pairs, never downloaded) | **reserved** for a registered V5 confirmatory run | not fetched; adds cross-sectional but not temporal independence |
| every candle after the freeze, any instrument | **reserved**; shared with the V4.1 H6/H7v forward test | not loaded (enforced by `v5_data`) |
| TOTAL*, dominance, stablecoin series | **not in the repo** | needs a data-source decision; outcome prices remain examined, so results stay exploratory |

**Decisions needed before step 1:**
1. Approve the universe and eligibility rule (§4).
2. Approve the stage-B hypotheses and decision rule (§7).
3. Decide whether TradingView-exported or third-party context data is acceptable for stages C–E, given the point-in-time
   limitations above.
