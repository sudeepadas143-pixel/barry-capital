# V4 data and validation gaps

What the existing data and research design can and cannot support. Every entry is checked against
code or measurements; "how established" says which.

## 1. Missing or weak datasets

| gap | effect on conclusions | how established | what would close it |
|---|---|---|---|
| **Non-crypto intraday history is only ~35 months.** Yahoo 1H/4H for equities, ETFs, commodities and FX starts 2023-11-28 | 1H/4H non-crypto cells cover one market regime; the 4H commodity and equity-bearish cells are insufficient (MAJOR n = 48 / 23 / 64) | `data.load("SPY","1H")` → 2023-11-28; `V4_TABLES.md` month counts (35) | multi-year intraday from a licensed vendor or exchange futures data. **Not installed in this phase**: it is needed only if H6/H7 are tested on non-crypto intraday |
| Commodities are ETFs (GLD, SLV, USO, DBA, UNG, CPER, CORN), not futures | ETF roll/contango and RTH sessions differ from the futures TradingView users chart | `universe.py` | continuous futures if commodities are a target market |
| No delisted equities | survivorship bias in equities (crypto has 5 defunct coins) | `universe.py` docstring | point-in-time constituent data |
| LTF 15m exists only for Binance crypto | early warnings fall back to the MTF rule elsewhere. Signals are unaffected: no evidence gates | `study._ltf_frame` | none needed unless LTF features return |
| Perp funding/basis/OI cached for 9 crypto symbols only | positioning features were screened on a thin, single-venue sample | `ls data/*funding*` | only if positioning hypotheses are revived (they are not in the register) |
| Costs are fixed per asset class (crypto 20 bp, commodities 8, equities 6, indices/bonds 4, FX 3) | no spread, impact or funding-carry data. Conclusions about *no edge* are robust to this; any small positive edge would not be | `universe.COST_BPS` | venue spread data for the target markets |
| No TradingView export has been compared | parity between Pine on TradingView's candles and the Python engine is unverified on real TV data; only a Python transliteration of the Pine is tested | `tests/test_engine_v2.py::test_tradingview_parity_script_round_trip` tests plumbing only | export chart data with parity mode on, run `scripts/compare_tv_export.py` |

## 2. Sample sizes and what a null result means

"No information" is only "no effect larger than the minimum detectable effect" (MDE: 80% power,
two-sided 5%, ≈ 1.43 × CI half-width, in ATR). The table gives MDE values from
`reports/v4_root_cause.json`.

All structure breaks (bullish / bearish):

| TF | crypto | equities | commodities | rates & FX |
|---|---|---|---|---|
| 1H | 0.22 / 0.22 | 0.39 / 0.46 | 0.53 / 0.66 | 0.19 / 0.28 |
| 4H | 0.62 / 0.50 | 0.91 / 0.82 | 1.32 / 1.14 | 0.38 / 0.71 |
| 1D | 1.11 / 0.73 | 0.40 / 0.55 | 0.53 / 0.43 | 0.26 / 0.31 |
| 1W | 3.16 / 0.62 | 0.39 / 0.54 | 0.73 / 0.56 | 0.46 / 0.52 |

Shipped MAJOR signals: MDE 0.28–0.33 on 1H crypto; 0.5–1.2 on most other cells; 1.4–4.1 on
the insufficient 1W and 4H-commodity cells. The insufficient MAJOR cells (fewer than 100 events
or 24 months) are:

* 1W crypto bull n = 16 and bear n = 49;
* 1W equities bear n = 22;
* 1W commodities bull n = 23 and bear n = 56;
* 1W rates & FX bull n = 67 and bear n = 43;
* 4H equities bear n = 64;
* 4H commodities bull n = 48 and bear n = 23.

Consequences:

* The rejection of H0 (structure breaks) is **strongest where it is best powered**: 1H crypto,
  1H and 1D rates & FX, 1D and 1W equities, where effects of ~0.2–0.4 ATR would have been seen.
* For MAJOR outside 1H crypto, the data can only rule out effects above ~0.5–1 ATR per signal.
  A realistic edge is 0.1–0.3 ATR, so those cells are **underpowered, not negative**.
* 1W results rest on 12–200 months per cell, and the 13-week horizon overlaps month clusters.
  Treat every weekly conclusion as weak.

## 3. Validation weaknesses (research audit)

| # | item | finding | status |
|---|---|---|---|
| V1 | **Untouched final holdout** | **None remains.** v2 used the FRESH symbols as its primary test, and v3 ran all 70 symbols over all dates, including the DEV holdout windows (`hcmtf/v3.py` `collect`: `St.prepare(tf, UNIVERSE + FRESH)`, start = first window, no end bound). V4 used the same data | CONFIRMED by code |
| V2 | Random benchmark matching (v3) | Matched: same symbol, whole window, count, side mix (permuted within symbol), horizon, costs (`metrics.random_baseline`). **Not matched**: HTF state/regime, volatility, calendar timing, clustering of events. The p-value treats random draws as iid and ignores the dependence of the signal mean, so it is anti-conservative (e.g. 4H crypto bearish MAJOR p = 0.005 vs cluster CI of excess +0.35 [−0.16, +0.88]) | CONFIRMED |
| V3 | Dependence | Cross-symbol dependence is handled by calendar-month cluster bootstraps (`metrics.cluster_ci`, `boot_diff`). Overlapping outcome windows of the same symbol share a cluster only when they fall in the same month: 64–91% of raw breaks overlap the next break's window. On 1W the 13-week horizon spans ~3 months, so month clusters understate uncertainty (quarter-cluster variant in json, `xR1_q`) | CONFIRMED, partly mitigated |
| V4 | Purging and embargo | `purgedcv.CombinatorialPurgedCV(6 groups, 2 test, embargo 1%)` on time buckets with t1 = bucket end + H (× 1.6 calendar factor on 1D/1W) (`v3.cpcv_selection`). Implemented as pre-registered (amendment 1). But no rule is fitted, so purging only protects the "pick the best of C0–C6" step; it adds no protection to the fixed-rule verdicts | CONFIRMED; limited relevance |
| V5 | PBO | CSCV over 7 nested, highly correlated configurations, with zero-filled buckets for months without events. It swung 0.00–0.98 by cell and with the weighting choice. A weak and unstable instrument for this question; v3 reported it as such | CONFIRMED |
| V6 | Deflated Sharpe | Computed on bucket-mean series (zero buckets dropped) against SR = 0, not against random entries. Trial variance comes from the 7 nested candidates. n_trials = 60 is an estimate. Where the bucket SR is itself negative (1H crypto bullish −0.18, 4H crypto bearish −0.16), DSR ≈ 0 is not a multiple-testing effect, contrary to `V3_SUMMARY.md` | CONFIRMED |
| V7 | Count of experiments | v1 threshold grids (confirm × major per TF), v2 14 components + tier and HTF variants, the audit's 3M-removal and acceptance tests, v3 9 configurations × 40 cells, V4 364 cells × 4–6 controls. The honest count is in the hundreds of comparisons, not 60. Only Holm within v3, and the pre-declared V4 rule, account for any of it | CONFIRMED (count approximate) |
| V8 | Pre-registration separation | v3: plan `5c3fbfa` 08:36 → amendment `873e572` 08:40 → results `12a8803` 09:12 (git timestamps, same day). Post-hoc v3 items (event-weighted PBO/CPCV) are labelled in `V3_RESULTS.md`. V4: plan `e62033f` before the diagnostics `e9509b2`. V4 post-hoc items: the R1a/R1b split, the `information_R1a` rule, singling out H1r. Timestamps show order only; they cannot prove nothing was computed beforehand | CONFIRMED as far as git can show |
| V9 | Second-engine agreement | backtesting.py reproduced `evaluate.simulate` on 5,279 trades from hcmtf's own signals. This shows the trade simulator is implemented consistently. It does **not** test signal generation (same input), the Pine strategy twin (which differs, `V4_ROOT_CAUSE_AUDIT.md` F5), or predictive validity | CONFIRMED |
| V10 | Pine ↔ Python parity | `tests/pine_mirror_v2.py` is a hand transliteration of the Pine into Python, compared against the engine. It catches drift between the two code bases, not differences in TradingView's runtime or data | CONFIRMED |
| V11 | V4 control bias | The pre-declared ±2H local control R1 is biased against breaks: before-only xR1b runs −0.85 to −1.24 ATR vs after-only −0.03 to +0.19. The pre-declared "information" rule is therefore too strict. The conclusion rests on R0 and R2, which do not have this bias | CONFIRMED (my error, post hoc) |
| V12 | Horizons differ in calendar time across markets | H = 24 1H candles is 1 day on crypto but ~3.7 trading days on US equities (RTH) | CONFIRMED; affects comparisons across groups, not within |
| V13 | Fixed outcome definition | r_h at one horizon with a +2/−1 ATR barrier; no exit tied to structure | by design; the short H/4 and long 2H horizons in `V4_TABLES.md` do not change the picture, but they use the biased R1 |

## 4. What the next phase needs before testing anything

1. **Declare untouched data now, before any fetch or look.**
   * (a) **Forward data**: every candle after 2026-10-27 for the 70 existing symbols.
   * (b) **New symbols, never used**. Proposed list, to be frozen in the next plan:
     * crypto (Binance spot): AVAX, NEAR, UNI, AAVE, XTZ, EOS, VET, THETA, HBAR, ICP;
     * stocks: ORCL, CSCO, HD, MRK, PG, UNH, CAT, MMM, PEP, ADBE;
     * ETFs: XLE, XLF, XLK, XLU, EWG, EWU, TIP, SHY;
     * commodities: PPLT, PALL, WEAT, DBB.

   Intraday non-crypto will still be limited to ~2 years.
2. Commit a plan for H6/H7/H1r (`V4_HYPOTHESIS_REGISTER.md` §B) with:
   * the cluster-bootstrap excess test against R0/R2 replacing the iid p-value;
   * median and trimmed mean as co-primary statistics;
   * Holm across the register's cells.
3. Decide the minimum effect worth trading (after costs) **before** testing, and size the
   untouched set so the MDE is below it. Otherwise a null result will again be uninformative.
4. Fix the Pine strategy twin's same-direction path (P2) only when production changes are
   allowed again, and verify it against a TradingView List-of-Trades export.
