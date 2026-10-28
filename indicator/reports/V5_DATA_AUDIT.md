# V5 data audit: what may be explored, what is frozen, what is reserved

Audited 2026-10-27 from the repository itself:
* the data cache;
* `data/MANIFEST.json`;
* `reports/V4_1_DATA_MANIFEST.json`;
* git history;
* `hcmtf/universe.py` and `research/universe41.py`.

Enforced in code by `research/v5_reserve.py` and checked by `tests/test_v5_plan.py`. This
supersedes `V4_DATA_AND_VALIDATION_GAPS.md` for data roles; that file stays as the V4 record.

## 1. Inventory (cache `data/`, git-ignored except `MANIFEST.json`)

* **270 files for 109 instruments**: 70 seen + 38 V4.1 holdout + the BTC-USD audit series.
  The cache contains no instrument that is not registered.
* **Native series**:

  | series | files | first | last |
  |---|---:|---|---|
  | 1d | 109 | 1962-01-02 | 2026-10-27 00:00 UTC |
  | 1h | 109 | 2017-08-17 | 2026-10-27 12:00 UTC |
  | 15m (Binance crypto only) | 26 | | |
  | funding | 9 | | |
  | perp 1h | 10 | | |
  | open interest | 7 | | |

* **4H, 1W, 1M and 3M** are resampled by `hcmtf.data.load`.
* **The newest candle in the cache is 2026-10-27 12:00 UTC.** No candle opens after the freeze
  (2026-10-27 23:59:59 UTC). `test_exploration_cache_has_no_forward_candles` enforces this.
  Forward data must be stored outside `data/`.

| group | instruments (seen + V4.1 holdout) | 1H/4H history | 1D/1W history |
|---|---|---|---|
| crypto | 26 + 10 (Binance spot, 5 defunct coins incl. LUNA, FTT) | 2017–2020 listing → 2026-10-27 | same |
| equities (stocks, index/sector/country ETFs) | 25 + 16 | **2023-11-28 → 2026-10-26 only** (Yahoo 730-day limit) | 1962 / IPO → 2026-10 |
| commodities (ETFs, not futures) | 7 + 4 | 2023-11-28 → 2026-10-26 | 2004+ |
| rates & FX (bond ETFs, FX pairs) | 12 + 8 | 2023-11-28 / 2024-01-10 → 2026-10-27 | 2002+ |

## 2. Examination status (none of this data is untouched)

| instrument set | dates | examined by | V5 role |
|---|---|---|---|
| DEV (30) | all cached | v1 design, v2 screening and design, v3, V4, V4.1 stage D | **exploration** |
| FRESH (40) | all cached | v2 primary test, v3, V4, V4.1 stage D | **exploration** |
| V4.1 HOLDOUT (38) | all cached | V4.1 stage H (H6, H7, H1r statistics) | **exploration**; no longer independent |
| BTC-USD audit | all cached | BTC audit | exploration |
| all 108 + V5 reserve | candles opening **after 2026-10-27 23:59:59 UTC** | nobody | **reserved (forward)**: see §3 |
| V5 reserve (46) | all dates | nobody (never downloaded; checked over the whole git history) | **reserved (cross-sectional)**: see §3 |

Rules for this data:

* Results on the exploration set are **exploratory** whatever the method. They are never quoted
  as confirmation, including when they "replicate" an earlier exploratory result.
* The V4.1 holdout instruments lost their independence when stage H ran. V5 treats them exactly
  like the seen symbols.

## 3. Frozen and reserved items

| item | status | protection |
|---|---|---|
| V4.1 H6 / H7v forward test: definitions, code and pre-registration | **frozen**; evaluate per V4.1 §9 (1H ≥ 2027-07-01, 4H ≥ 2028-01-01) | sha256 of `research/v41.py`, `research/universe41.py`, `scripts/v41_run.py`, `scripts/v41_fetch.py`, `reports/V4_1_PREREGISTRATION.md` must equal `reports/V4_1_DATA_MANIFEST.json` → `test_frozen_v41_forward_test_files_are_unchanged` |
| forward candles (after 2026-10-27 23:59:59 UTC) | **reserved** for pre-registered confirmatory runs only | `research.v5_reserve.exploration_only()`; the cache test above |
| V5 reserve instruments (46) | **reserved**; not to be downloaded until a V5 confirmatory pre-registration names them | `test_reserved_instruments_are_unused_and_not_cached` |

### Forward data is shared, and the rules for sharing it

V5 and the frozen V4.1 test will both use forward candles. That does not invalidate V4.1,
because its definitions and code are fixed by hash and nothing V5 learns can change them. The
rules:

* (a) No V5 run computes H6 or H7v statistics on forward data before their V4.1 evaluation
  dates.
* (b) Forward data is read only by confirmatory runs whose pre-registration is committed first.
* (c) Every confirmatory read is logged with the commit, date and data window.

### The V5 reserve

* **How the instruments were chosen.** By a rule fixed before looking at any of their data:
  * liquid, listed for most of 2015–2026;
  * spread across sectors and countries;
  * laggards and a delisted name (WBA) included on purpose.
* **The list**:

  | group | instruments |
  |---|---|
  | crypto | FET, INJ, RUNE, AR, GRT, SAND, MANA, CRV, KAVA, IOTA, DASH, ONE (USDT pairs) |
  | equities | JNJ, LIN, NEE, AMT, HON, COST, GS, IBM, WBA, GE, KHC, CL |
  | equity ETFs | XLV, XLI, XLP, XLY, XLB, EWA, EWC, EWW |
  | commodities | DBC, GSG, BNO, UGA, SOYB, CANE |
  | rates & FX | IEI, BND, MBB, AGG; USDPLN, USDHUF, USDCZK, USDTRY |

* **What the reserve adds.** Its history covers the **same calendar period** as the exploration
  data, so it adds cross-sectional independence only, not temporal independence. It can support
  at most "retain for forward testing", never "confirmed". Its forward candles join the forward
  set.

## 4. Known data issues

| issue | effect | handling |
|---|---|---|
| LUNAUSDT token swap: ×3,124 on 2022-05-13, then LUNA 2.0 | invalid prices after 2022-05-12 | V4.1 Amendment 1 rule (`research.v41.integrity_cut`, > 20× daily open jump); V5 uses the same rule. v3/V4 rows were not re-run (disclosed) |
| EOSUSDT ends 2025-05-26 (delisted) | shorter series | kept up to delisting (avoids survivorship bias) |
| Yahoo intraday only ~730 days | non-crypto 1H/4H ≈ 35 months | intraday cells for non-crypto are low-powered. Forward data accumulates slowly. Multi-year intraday would need a licensed vendor (not added: no demonstrated need yet) |
| commodities as ETFs (roll and contango, RTH only) | differs from futures charts | stated; futures only if commodities become a release target |
| no delisted equities in seen data | survivorship bias in equities | reserve includes WBA; point-in-time data not available for free |
| volume missing or meaningless for FX | volume-based evidence (D1 climax) cannot apply to FX | detectors must fall back explicitly; tested per group |
| no shorting cost data (borrow fees, perp funding only for 9 coins) | short-side families B and C understate cost | protocol §4 fixes conservative short-cost assumptions |
| TradingView's own candles never compared | data parity unknown | release gate G5 requires a TradingView export comparison |

## 5. Label base rates on exploration data (planning only)

* **Source**: `python scripts/v5_label_counts.py` → `reports/v5_label_counts.json`.
* **Definitions**: the frozen ones in `V5_HYPOTHESIS_REGISTER.md` §2.2, committed in `7fc7e68`
  **before** this count ran.
* **Use**: these numbers size the samples. They must not be used to retune L, F or D.

Labelled events, tops / bottoms, with the number of distinct calendar months containing at least
one event in parentheses:

| TF | crypto | equities | commodities | rates & FX | all |
|---|---|---|---|---|---|
| 1H | 3,261 / 3,091 (82 / 82) | 391 / 373 (34 / 34) | 101 / 96 (27 / 30) | 419 / 432 (34 / 34) | 4,172 / 3,992 |
| 4H | 838 / 885 (80 / 77) | 129 / 114 (28 / 25) | 44 / 38 (16 / 13) | 130 / 125 (31 / 30) | 1,141 / 1,162 |
| 1D | 114 / 242 (36 / 48) | 525 / 381 (132 / 97) | 159 / 135 (85 / 75) | 159 / 158 (85 / 85) | 957 / 916 |
| 1W | 89 / 56 (24 / 17) | 195 / 188 (81 / 57) | 54 / 44 (44 / 33) | 82 / 93 (58 / 51) | 420 / 381 |

What the base rates imply:

* **1H/4H** have enough labelled events everywhere except 4H commodities.
* **1D crypto: tops and bottoms are not symmetric.** There are 114 tops but 242 bottoms. This is
  noted, not acted on.
* **1W crypto tops cluster in 24 months.** That is a handful of cycle tops, too few for any
  confirmatory claim.

**Forward-data feasibility.** Assume the base rates hold, and count all 154 instruments (108 plus
46 reserve):

| TF | labelled events per forward year (approx.) | when a confirmatory test becomes possible |
|---|---|---|
| 1H | hundreds per group | evaluable after ~8–12 months of forward data (cluster requirement) |
| 4H | ~150–200 in crypto, tens elsewhere | ~2 years |
| 1D | ~100 in total | 3+ years, because events cluster in a few market-wide months |
| 1W | ~45 in total, in very few independent episodes | **cannot be confirmed within this decade**; 1W stays exploratory and is not released as a validated signal |
