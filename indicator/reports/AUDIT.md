# Audit: BTC weekly bearish signals, "invalidated" signals, mobile visibility

Scripts: `scripts/audit_fixes.py` (→ `audit_fixes.json`), `scripts/audit_btc.py`
(→ `BTC_AUDIT.md`, `btc_audit.json`), `scripts/preview_markers.py` (→ `preview_*.png`).

## 1. Why BTC weekly shows no bearish signal

**Mechanism (verified).** On the 1W profile the ladder is LTF 1D / HTF1 1M / HTF2 3M, and each
HTF trend is close vs EMA(21) of that timeframe with the EMA's slope. EMA(21) of *quarterly*
candles spans ~5¼ years and EMA(21) of monthly candles ~1¾ years. BTC's bear markets are shorter
than either, so when the weekly structure breaks down, at least one HTF is still "up" and the break
is classified counter-HTF, which never signals by design.

On long-history BTC (BTC-USD from 2014, close to what TradingView loads for BTCUSD):

| weekly structure breaks | bullish | bearish |
|---|---:|---:|
| continuation | 13 | 1 |
| realignment (would be MAJOR) | 5 | **0** |
| counter-HTF reversal (blocked) | 3 | 8 |
| counter-HTF continuation (blocked) | 4 | 5 |

The tops of 2021-05 and 2022-01 were counter-HTF (monthly and quarterly up). 2022-05 had the monthly
turned down but the quarterly still up. The only bearish weekly signal is a CONFIRMED continuation
in Nov 2022, which is not drawn by default.

**Data-feed dependence (a real consistency defect).** The quarterly EMA needs 22 quarters
(5½ years) of history before it exists. On Binance BTCUSDT (listed 2017) it is missing until 2023, so
the same rule produced a bearish MAJOR on 2022-05 there and not on long-history BTC. The 1D profile
has the same issue in milder form (monthly EMA21, 22 months of warm-up): BTC 1D MAJOR signals are
22 bullish / 11 bearish since 2014, CONFIRMED 88 / 17. 1H and 4H are balanced (MAJOR 273/258 and
63/73).

**Candidate fix tested: 1W profile without the quarterly HTF2** (rule fixed before running: adopt
unless dev-data mean outcome gets significantly worse).

| | dev symbols (to 2024) | fresh symbols |
|---|---|---|
| 1W signals old → new | 727 → 875 | 995 → 1,129 |
| mean r_h old → new | +0.73 → +0.57 ATR | +0.38 → +0.32 |
| new − old [90% CI] | **−0.15 [−0.24, −0.07]** | −0.06 [−0.12, +0.01] |
| bearish signals added | 93, mean −0.30 ATR, 69% stopped first | 72, mean −0.59, 75% stopped first |
| on long-history BTC | +2 bearish signals (both worked, n = 2) | |

**Decision: rejected.** The quarterly filter does suppress bearish weekly signals, but across 70
symbols the bearish signals it suppresses lose money on average; weekly bearish signals that pass
the filter are themselves negative (dev −0.18, fresh −0.31). Making BTC show weekly bearish arrows
would mean adding signals that, on the evidence, are mostly false. Bearish setups are still
*detected*: the engine classifies them (counter-HTF breaks); they are just not promoted to signals.
Bearish signals do appear on BTC 1H, 4H and 1D.

## 2. Are historical signals repainting, or failing?

**No repainting on closed candles.** Evidence:
- Truncation tests (signals computed with data up to candle *k* equal the full-history signals up to
  *k*, with forming HTF candles built from partial data) and a newest-candle check of every HTF, LTF
  and perp reading pass; the acceptance option has its own truncation test.
- The Pine logic is reproduced bar by bar by `tests/pine_mirror_v2.py` (now including acceptance).
- HTF values come from completed HTF candles only (`f()[1]` + `lookahead_on`); signals are gated on
  `barstate.isconfirmed`.

**One real history effect, now documented.** The engine carries state from candle to candle
(structure, cooldown). If the chart's loaded history starts later (a phone or a lower plan loads
fewer candles; scrolling back loads more), signals in the first part of the loaded history can
differ until the state converges. Measured on BTC by restarting the history at different points:
no difference on 1H; up to ~5 days on 4H; ~25 days on 1D; up to ~7 months on 1W when only two years
are loaded. After that the signals are identical. This can make a signal near the left edge of a
chart appear or disappear when more history loads; it does not move signals on the right.

**What "invalidated" really is.** About 45% of signals (dev symbols, all timeframes) see a close
back through the broken level within 3 candles. That is ordinary breakout behaviour, and it is why
precision against a +2 / −1 ATR barrier is ~33–37% for both the signals and random entries.

**Candidate fix tested: next-candle acceptance** (rule fixed before running: adopt only if pooled
dev mean outcome improves with 90% CI above 0 and signals fall by less than half).

| | dev symbols | fresh symbols |
|---|---|---|
| signals | 22,814 → 17,470 (−23%) | 36,224 → 27,390 (−24%) |
| invalidated within 3 candles | 45% → 32% | 46% → 32% |
| mean r_h | +0.224 → +0.244 | +0.081 → +0.077 |
| new − old [90% CI] | +0.020 [−0.017, +0.059] | −0.003 [−0.033, +0.029] |

**Decision: not adopted as default** (no evidence it improves outcomes). It is available as the
*Require next-candle acceptance* option, off by default, because it does remove the most visibly
"invalidated" signals, at the cost of a one-candle delay and a quarter of the signals. It is not an
improvement in expected outcome and is not presented as one.

## 3. BTC performance by direction and timeframe

Full table: [`BTC_AUDIT.md`](BTC_AUDIT.md). MAJOR (the default markers), BTCUSDT for 1H/4H, BTC-USD
(2014+) for 1D/1W; "design" = before the holdout start, "recent" = holdout start (2025-07 intraday,
2024-01 daily/weekly) to Oct 2026, not used for any v2 design decision.

| TF | side | period | n | false pos. | mean r_h [95% CI] | random r_h | p |
|---|---|---|---:|---:|---:|---:|---:|
| 1H | bullish | design | 241 | 64% | −0.02 [−0.61, +0.57] | −0.08 | 0.41 |
| 1H | bullish | recent | 32 | 69% | −0.15 [−1.09, +0.98] | −0.41 | 0.35 |
| 1H | bearish | design | 214 | 59% | −0.43 [−1.00, +0.13] | −0.49 | 0.45 |
| 1H | bearish | recent | 44 | 68% | −0.64 [−2.04, +0.93] | −0.43 | 0.64 |
| 4H | bullish | design | 57 | 63% | +0.26 [−0.81, +1.41] | +0.34 | 0.52 |
| 4H | bullish | recent | 6 | 83% | −0.92 [−1.76, −0.20] | −0.01 | 0.66 |
| 4H | bearish | design | 58 | 64% | −0.25 [−1.60, +1.30] | −0.66 | 0.24 |
| 4H | bearish | recent | 15 | 53% | +0.16 [−1.46, +2.92] | −0.28 | 0.41 |
| 1D | bullish | design | 16 | 38% | +2.05 [+0.10, +4.06] | +1.34 | 0.28 |
| 1D | bullish | recent | 6 | 67% | +1.50 [−1.66, +5.27] | +0.57 | 0.25 |
| 1D | bearish | design | 9 | 67% | −0.00 [−1.39, +1.35] | −1.58 | 0.22 |
| 1D | bearish | recent | 2 | 100% | +1.46 | −0.54 | 0.20 |
| 1W | bullish | design | 3 | 100% | −1.08 | +2.89 | 0.95 |
| 1W | bullish | recent | 2 | 50% | +2.20 | +0.51 | 0.18 |
| 1W | bearish | both | 0 | | | | |

**Reading it.** On BTC alone, no timeframe/direction shows MAJOR signals beating random entries
with statistical confidence; daily and weekly samples are far too small to say anything (n ≤ 16).
Bearish signals are weaker than bullish ones on every timeframe, in line with the cross-market
results. Including CONFIRMED (continuation) signals did better on BTC 1D/1W bullish in the design
period (BTC-USD 1D +4.08 ATR vs +1.41 random, p 0.003; 1W +6.01 vs +2.80, p 0.03) but not
significantly in the recent window; that tier is available via *Also mark continuation breaks*.
**No improvement is claimed.**

## 4. Mobile visibility

**Cause.** The previous version drew `plotshape(shape.arrowup/arrowdown, size.small)`: a thin arrow
with a small word. Arrow shapes are among the least visible marks on a phone, and on BTC 1W only
five MAJOR signals exist since 2014 (two in the last two years), so a phone screen of recent weekly
candles shows at most two of them.

**Fix.** Solid labels (`label.style_label_up / _down`, `size.normal`) with white bold text
"▲ BULLISH" / "▼ BEARISH", placed with `yloc.belowbar / abovebar` so they never cover the candle;
fills #2962FF / #D32F2F give ≥ 3.6:1 against white, TradingView dark (#131722) and pure black, and
the white text is ~4.9:1 on either fill. No transparency, no theme-dependent text colour, no offsets.
Previews at phone and desktop size, light and dark: `preview_BTC-USD_1D_*.png`. These are rendered
offline from the engine's signals, not TradingView screenshots; a check on a real device is still
needed (see README, "Not checked here").

## 5. Clean chart

Only the two markers are drawn. No dashboard, table, swing lines, status-line values or text.

## 6. Script type

`pine/HighConvictionMTF.pine` is declared with `indicator(...)`. It draws markers and fires alerts
and places no orders. Nothing here assumes how the private 5_0_Strategy script is declared or built.
