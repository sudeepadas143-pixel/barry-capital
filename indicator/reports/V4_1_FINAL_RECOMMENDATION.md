# V4.1 final recommendation

## Decisions (pre-registered rules, holdout stage H, single run)

| hypothesis | decision | the evidence in one line |
|---|---|---|
| **H6**: the HTF trend state alone predicts returns | **INCONCLUSIVE** | 1H crypto premium on both sides (+0.19 / +0.13 ATR, replicating the seen symbols), but it fails Holm (0.07 / 0.11) and its median is ≤ 0. Equities go the *opposite* way (4H −0.27 / −0.45, CI < 0). 1D/1W: nothing |
| **H7v**: breakouts from compression are followed by more volatility than other compressed candles | **INCONCLUSIVE** | Real in crypto (1H +9.1% realised range, CI [+7.6%, +10.6%], all spans, passes), but in no other group; the rule needs two |
| **H7d**: the breakout direction predicts the direction of the move | **INCONCLUSIVE** | No cell significant; estimates scatter around 0 with no pattern; CIs too wide to reject 0.1–0.3 ATR |
| **H1r**: a structure break adds value to the state | **INCONCLUSIVE** (no passing cell; not rejectable at the pre-set precision) | Hourly breaks add nothing or subtract value (1H crypto bearish −0.13 [−0.23, −0.02]). Breaks lose to a momentum trigger in rates/FX. Only crypto bullish 4H/1D favours the break on the mean, with a negative median |
| **H1r target**: 4H crypto bullish continuation | **REJECT** | n = 805, mean +0.45 [+0.09, +0.74], **median −0.44**; the pre-registered rule requires median > 0 |

**No hypothesis demonstrated credible incremental predictive value. As instructed, no new
indicator is generated and the production indicator is unchanged.**

## What to do next

1. **Do not rebuild HC-MTF around structure breaks.** Three studies agree that the break carries
   no robust information beyond the trend state: V3, V4 (seen data) and V4.1 (new instruments).
   The register's best surviving cell has now been rejected under its own pre-registered rule.
2. **Keep exactly two narrow candidates, and test them only on forward data.** This is the
   forward test pre-registered in [`V4_1_PREREGISTRATION.md`](V4_1_PREREGISTRATION.md) §9, using
   candles after 2026-10-27, the same code hashes, and these definitions:
   * **H6, crypto 1H/4H.** Two-sided premium over static exposure, on new symbols and in the
     seen data alike.
   * **H7v, crypto 1H.** More realised range after compression breakouts.

   The earliest honest evaluation is 1H on 2027-07-01 and 4H on 2028-01-01.
3. **Make no new rule from these results in the meantime.**
   * Do not lower the bar.
   * Do not drop the median requirement after the fact.
   * Do not try other compression settings, momentum lengths or EMA lengths.

   Each of those would spend the forward test before it starts.
4. **If you want a chart tool now, describe it honestly.** A crypto HTF-state shading or a
   "compression → expect a bigger range" marker could be built. But neither is a validated
   directional signal, and H7 says nothing about direction.

## What this study can and cannot claim

* **New instruments, old calendar.** The holdout is 38 instruments never used before (checked
  over the whole git history), but it covers the same calendar period as the seen data. It
  guards against symbol-selection overfitting, not against regime overfitting. Even a RETAIN
  would not have been out-of-sample confirmation.
* **Real replication, not confirmation.** The crypto H6 and H7v estimates on the new coins are
  close to the seen-symbol estimates (H6 1H: +0.188 vs +0.208 bullish; H7v 1H: +0.091 vs +0.107).
  That is real cross-sectional replication. It is not the same as working in the future.
* **Dependence across instruments.** Crypto coins move together, so ten new coins over 2020–2026
  are closer to one long noisy sample than to ten independent tests. The calendar-block bootstrap
  accounts for this, which is why the CIs are wide.
* **Non-crypto intraday is short.** It is ~35 months long (Yahoo limit). Most commodity and
  rates/FX intraday cells can only rule out effects larger than about 0.2–0.5 ATR.
* **Repeated experimentation.**
  * Within V4.1 it is handled by Holm per family, with a global Holm as a sensitivity. Under the
    global Holm, only H7v crypto 1H/4H and 1W rates/FX remain significant.
  * The hypotheses themselves were chosen after V3/V4 on the seen symbols. That history affects
    the choice of hypotheses, not the holdout data.
* **Data issue found and disclosed.** LUNAUSDT in the seen data contains a token swap
  (×3,124 on 2022-05-13, then LUNA 2.0). Amendment 1 cut it from V4.1. The same rows are in the
  v3 and V4 data; their ATR-normalised outcomes limit the effect, but those studies were not
  re-run.

## Record of the procedure

| step | commit | time (UTC) |
|---|---|---|
| pre-registration (before any code, data or result) | `2cf1d2f` | 2026-10-27 11:49 |
| code + unit tests + Amendment 1 (integrity screen), before any holdout computation | `a51cb5c` | 11:57 |
| stage D results (seen symbols, exploratory) | `3361884` | |
| holdout data-freeze manifest (76 files, sha256) + configuration hash | `aadf28d` | 12:24 |
| stage H run, once, with the frozen code | `5c01983` | |
| reports | this commit | |

Configuration hash (sha256), also in `reports/v41_H.json` → `config_hash`:

| file | sha256 |
|---|---|
| `research/v41.py` | `b38607a2…04de4b` |
| `research/universe41.py` | `94ea367f…815b96` |
| `scripts/v41_run.py` | `e7b6d00c…93b0dc` |
| `reports/V4_1_PREREGISTRATION.md` (with Amendment 1) | `51c2e6ca…406a093` |

**Tests.** `python -m pytest -q` → **44 passed**. That is the 40 earlier tests plus 4 V4.1 tests:
* event definitions;
* causality under truncation for states, compression events and momentum events;
* the bootstrap with re-estimated benchmarks.

**Production unchanged.** `git diff 84c9f13 -- pine hcmtf HC-MTF_TradingView.txt
HC-MTF_StrategyTester.txt reports/active_config.json` returns 0 lines.
`pine/HighConvictionMTF.pine` sha256 `eb95dd5b…` equals `HC-MTF_TradingView.txt`.

**Reproduce:**

```bash
cd indicator
python scripts/v41_fetch.py        # holdout data → data/ (git-ignored) + reports/V4_1_DATA_MANIFEST.json
python scripts/v41_run.py D        # seen symbols, exploratory → reports/v41_D.json
python scripts/v41_run.py H        # holdout → reports/v41_H.json (decisions)
python scripts/v41_tables.py       # → reports/v41_tables/*.md
python -m pytest -q
```

Vendors revise history, so a fresh download may not match the frozen sha256 values. Compare
against `V4_1_DATA_MANIFEST.json` before trusting a re-run.

## Reports

* [`V4_1_PREREGISTRATION.md`](V4_1_PREREGISTRATION.md)
* [`V4_1_H6_RESULTS.md`](V4_1_H6_RESULTS.md)
* [`V4_1_H7_RESULTS.md`](V4_1_H7_RESULTS.md)
* [`V4_1_INCREMENTAL_VALUE.md`](V4_1_INCREMENTAL_VALUE.md)
* Full tables: `reports/v41_tables/` (`*_H.md` holdout, `*_D.md` seen symbols)
