# v3 summary: does the indicator earn attention?

Pre-registration: [`PREREG_V3.md`](PREREG_V3.md) (committed before any v3 run, plus one amendment,
also before results). Full numbers: [`V3_RESULTS.md`](V3_RESULTS.md) (every timeframe × side ×
market group × configuration), [`BACKTESTINGPY.md`](BACKTESTINGPY.md) (independent trade-level
backtest). Outcome: next-open entry, H candles (1H 24, 4H 30, 1D 20, 1W 13), r_h in ATR after
costs; success = +2 ATR before −1 ATR. 70 symbols: crypto (26), equities (25: 16 stocks + 9 index ETFs),
commodities (7), rates & FX (12).

## Answer

**No configuration demonstrated predictive value under the pre-registered criteria.** None of the
32 timeframe × side × market cells of the shipped MAJOR signal passed all four tests (beat random
after Holm correction, deflated Sharpe > 0.95 with 60 trials, positive in ≥ 4 of 6 periods, beat
"every structure break"). Three cells are PROMISING (beat random at p < 0.10, unadjusted), all
crypto:

| cell | n | mean r_h [95% CI] | random | p (Holm) | deflated Sharpe |
|---|---:|---:|---:|---:|---:|
| 1H bullish crypto | 4,348 | +0.27 [+0.02, +0.49] | −0.12 | 0.005 (0.14) | 0.00 |
| 4H bullish crypto | 983 | +0.84 [+0.23, +1.48] | +0.26 | 0.005 (0.14) | 0.18 |
| 4H bearish crypto | 1,605 | +0.01 [−0.50, +0.55] | −0.34 | 0.005 (0.14) | 0.00 |

The deflated Sharpe ratios are near zero: once ~60 configurations tried across v1–v3 are accounted
for, these results are what the best of many unrelated rules would look like by chance.

## What each part of the system contributes (paired, same data; 90% CI)

* **HTF gate (C1 vs C0)** is the one component with fairly consistent value: +0.20 [+0.12, +0.28]
  ATR on 1H bullish, +0.38 [+0.14, +0.62] on 4H bullish, +0.67 on 4H bullish crypto, +0.24
  [+0.05, +0.43] on 1W bearish; elsewhere small or within noise.
* **Realignment-only (C2 vs C1, i.e. MAJOR vs MAJOR+CONFIRMED)** is not an improvement: +0.07 on 1H
  bullish (CI includes 0), −0.26 on 4H bullish, −1.57 [−2.33, −0.66] on 1D bullish crypto. Showing
  only realignments makes signals rarer, not better. (Continuation signals are available via *Also
  mark continuation breaks*.)
* **Acceptance (C4 vs C2)**: small and inconsistent (+0.06 on 1H bullish, −0.31 on 1D bearish
  crypto). Stays an off-by-default option.
* **Selection reliability.** Probability of backtest overfitting across C0–C6 ranges from 0.00 to
  0.98 by cell and changes a lot with how outcomes are weighted (per week vs per event); with
  event weighting, purged CPCV most often picks **C0, every structure break**. There is no robust
  evidence that any of the filtering layers beats simply taking every break, once heavy-tailed
  trend weeks are weighted by how many signals they produce.
* **Heavy tails.** Mean and median disagree everywhere (e.g. crypto 4H bullish breaks: mean
  +0.79 ATR per event, median negative, −0.20 per average week). Most signals lose a little; a few
  trend runs make the average. Any reading of "accuracy" must keep that in mind.

## Why bearish signals are underrepresented

| TF | structure breaks bull / bear | MAJOR bull / bear | suppressed counter-HTF reversals bull / bear |
|---|---:|---:|---:|
| 1H | 55,005 / 52,275 | 5,756 / 6,393 | 18,700 / 18,050 |
| 4H | 13,800 / 13,027 | 1,457 / 1,801 | 4,670 / 4,339 |
| 1D | 11,082 / 9,054 | 1,464 / 973 | 2,629 / 3,118 |
| 1W | 2,161 / 1,590 | 302 / 170 | 455 / 605 |

Intraday signals are balanced. Daily and weekly lean bullish because most of the sample's assets
rose over 2010–2026 and the HTF filter follows the trend; on 1W the HTFs are monthly and quarterly
trends that rarely turn down. **Are legitimate reversals being suppressed?** The suppressed
counter-HTF reversals (C6) were, against MAJOR (C2): 1H bearish −0.13 [−0.28, +0.01], 4H bearish
−0.28 [−0.65, +0.10], 1D bearish −0.22 [−0.57, +0.16], 1W bearish −0.42 [−0.95, +0.26]; weekly
crypto bearish was the one exception (+1.01 [−0.24, +3.06], n = 58, within noise). The filter
removes reversals that, on average, did worse than the signals it keeps; it does not remove a
hidden group of good bearish signals.

## Independent trade-level check (backtesting.py)

backtesting.py, an independent engine, reproduced the in-house simulator on 5,279 MAJOR-signal
trades (18 symbols, 4 timeframes): identical entry candles for every trade, identical exits for all
non-time exits, total returns within 1.3%. By side, bullish trades had profit factors 1.18–3.53 and
positive mean returns in every timeframe × group; bearish trades had profit factors 0.44–1.10 and
lost in most cells. Per-symbol drawdowns at full allocation were large (median −9% to −71%). These
are absolute results that include market drift; they are not evidence of timing skill, which the
random-entry comparison above measures.

## What this means for using the indicator

Treat the markers as a disciplined, non-repainting read of structure turning in the
higher-timeframe direction. Do not treat them as validated trade signals. If anything is worth
watching, it is crypto 1H/4H, and bullish markers more than bearish ones; even there the evidence
does not survive correction for repeated testing.
