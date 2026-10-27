# HC-MTF: high-conviction multi-timeframe trend signals

A TradingView indicator (`pine/HighConvictionMTF.pine`, Pine Script v6) that marks bullish and
bearish trend changes on 1H, 4H, 1D and 1W charts, and a Python research package (`hcmtf/`) that
implements the same rules and validates them out of sample on 30 symbols across six asset classes.

**Short version of the results:** the indicator does what it says on the integrity side (no
repainting, no look-ahead, closed-candle signals, tested), and the confluence score does carry
information: higher scores have better outcomes than lower scores out of sample, and the
filtered signals beat taking every structure break. But on the strict test that matters (do the
signals pick better *moments* than random entries in the same direction on the same symbols and
dates?) **no configuration has demonstrated an advantage.** The full verdicts and numbers are in
[`reports/RESULTS.md`](RESULTS.md) and summarised in [Results](#results) below. Treat
the labels as a structured, transparent read of trend and structure, not as a validated edge.

---

## Contents

```
pine/HighConvictionMTF.pine   the indicator (paste into the TradingView Pine editor)
hcmtf/                        research package
  universe.py                 the 30 symbols, asset classes, round-trip costs
  data.py                     downloads (Yahoo, Binance), caching, 4H/W/M/3M resampling
  ta.py                       Pine-exact EMA/RMA/ATR/RSI/DMI/MACD/Supertrend, causal pivots
  htf.py                      higher-timeframe alignment without look-ahead
  signals.py                  the signal engine (structure, evidence, tiers, warnings, cooldown)
  evaluate.py                 outcomes, trade simulation, baselines, timeliness
  walkforward.py              walk-forward threshold selection and the holdout
  metrics.py                  cluster-bootstrap CIs, random-entry baseline, portfolio stats
  report.py                   runs everything, writes reports/
scripts/fetch_data.py         download and cache all data, write data/MANIFEST.json
scripts/sync_pine.py          copy validated thresholds and evidence lines into the Pine file
tests/                        integrity tests, Pine-logic mirror, parity tests
reports/RESULTS.md            every number, per timeframe
reports/results.json          the same, machine-readable
reports/verdicts.json         DEMONSTRATED / PROMISING / UNPROVEN per timeframe and tier
```

## Using the indicator

1. TradingView → Pine Editor → paste `pine/HighConvictionMTF.pine` → *Add to chart*.
2. It picks a profile from the chart timeframe (≤2H → 1H, ≤8H → 4H, ≤2D → 1D, longer → 1W).
   The profile sets swing spans, cooldown, the two context timeframes and the thresholds.
3. Read a label like `MAJOR BULL / REVERSAL / 5/6 NAMSD·`:
   - **tier**: `MAJOR` (solid) or `CONFIRMED` (faded). No label = not enough evidence.
   - **kind**: `REVERSAL` breaks against the prevailing structure (a change of character);
     `CONTINUATION` breaks with it.
   - **score**: conditions met / conditions available, then a letter per condition that held
     (`·` = did not): **N** near-HTF trend, **A** anchor-HTF trend, **M** momentum,
     **S** trend strength, **D** displacement (volatility), **V** volume.
   - Hover a label for the full breakdown: the level broken, each HTF trend, RSI, MACD, ADX/DI,
     body size in ATR, relative volume, the thresholds, and the out-of-sample evidence line.
4. Small orange `!` marks are **early warnings**: momentum has turned against the structure
   (close back across EMA 21, RSI past 50, MACD histogram flipped) before any break. They are
   not signals and are evaluated separately.
5. The dashboard shows the 1H/4H/1D/1W trend from completed candles (lower timeframes than the
   chart show `—`), the structure state, a bias line that says **NEUTRAL** when evidence is
   mixed or thin, the last signal, the thresholds, and the validation verdict for the profile.
6. Alerts: `MAJOR bullish/bearish`, `CONFIRMED bullish/bearish`, `Early warning`, plus a JSON
   `alert()` payload. All fire once per closed candle.

### Context timeframes per profile

| chart | near (N) | anchor (A) | swing span (left/right) | cooldown |
|---|---|---|---|---|
| 1H | 4H | 1D | 5 / 3 | 12 bars |
| 4H | 1D | 1W | 5 / 3 | 6 bars |
| 1D | 1W | 1M | 5 / 2 | 5 bars |
| 1W | 1M | 3M | 4 / 2 | 4 bars |

HTF trend = close above (below) EMA 21 with that EMA rising (falling); anything else is flat.

## How a signal is built

1. **Trigger: a structure break.** Swing highs/lows are confirmed `right` bars after they form
   and only then become levels. A *close* beyond the latest unbroken level is a break. Each level
   can trigger once. A plain moving-average crossover is never a signal.
2. **Evidence**, checked on the break candle, each a different kind of information:

   | code | condition | what it adds |
   |---|---|---|
   | N | near HTF trend agrees | context one step up |
   | A | anchor HTF trend agrees | weekly/daily context; required for MAJOR |
   | M | RSI(14) vs 50 and MACD histogram vs 0 agree with the break | momentum |
   | S | ADX(14) ≥ 20 and the signal side's DI on top | trend strength |
   | D | break candle body ≥ 0.5 × ATR(14) | volatility / displacement |
   | V | volume ≥ 1.3 × 20-bar average | participation; skipped where volume is not meaningful |

   Score = met / available. Missing context (warm-up) and missing volume shrink the denominator
   rather than counting as "no". Volume is off for forex, indices and CFDs (TradingView's volume
   there is tick count or absent) and on for stocks, ETFs, futures and crypto; you can force it.
   The weights are equal on purpose: with a few hundred events per fold, fitted weights chase
   noise. Whether the score means anything is answered by the validation, not by the weights.
3. **Tiers.** `CONFIRMED` needs score ≥ *confirm*. `MAJOR` also needs score ≥ *major* and the
   anchor timeframe agreeing, so a lower-timeframe break against the weekly/daily trend can never
   be MAJOR. Both thresholds are picked per timeframe by walk-forward (below).
4. **De-duplication.** A same-direction signal needs `cooldown` bars since the last signal; an
   opposite signal is always allowed. Warnings fire at most once per structure leg.

## Integrity guarantees, and how they are tested

| guarantee | how |
|---|---|
| Signals only on closed candles | `barstate.isconfirmed` gate (default on). Off draws hollow "?" provisional labels. |
| No HTF look-ahead or repaint | `request.security(sym, tf, f()[1], lookahead = barmerge.lookahead_on)`: the previous *completed* HTF candle on history and realtime alike. Python `htf.align` reproduces it. |
| Swing points are not back-dated | A pivot is used only from the bar on which its right side has closed. |
| Signals never move | **Truncation test**: signals computed with data up to bar *k* equal the full-history signals up to *k*, at many *k*, with the still-forming HTF candle present (partial data) in the truncated run. A bar-by-bar variant checks every evidence value on the newest bar. |
| Tests catch real bugs | Mutation check: removing the HTF `[1]`, letting pivots peek two bars ahead, using the forming HTF candle, or filling at the signal close each make the suite fail. |
| Pine and Python agree | `tests/pine_mirror.py` is a statement-by-statement, bar-by-bar transliteration of the Pine logic (`var` state, `x[k]` history); it must produce exactly the engine's signals and warnings. Indicator math follows Pine's reference implementations (SMA-seeded EMA/RMA, Wilder ATR/RSI/DMI). |
| Realistic fills | Entry at the **next candle's open**; stops fill at the stop or at the open if gapped through; if target and stop are in the same candle, the stop wins; round-trip costs per asset class (crypto 20 bp, commodities 8, equities 6, indices/bonds 4, FX 3). |

What could still differ on TradingView: its data feed (bars, sessions, adjustments) is not
Yahoo's or Binance's, so individual signals will not match one for one. The Pine file was
syntax-checked with a Pine parser (`pynescript`), not compiled by TradingView in this
environment; if TradingView reports a compile error, it is a bug to fix, not a reason to
distrust the logic tests.

## Validation method

**Universe** (fixed before any result was seen, chosen by asset class and 2018 liquidity, laggards
included on purpose): SPY QQQ IWM EFA EEM · AAPL JPM XOM INTC BA PFE T F · TLT IEF · GLD SLV USO DBA
· EURUSD USDJPY GBPUSD AUDUSD · BTC ETH XRP LTC ADA BNB LINK (vs USDT). Daily/weekly use full
history (equities from the 1960s–2000s, crypto from 2017–19). Hourly data: crypto from 2017–19
(Binance), everything else only from Nov 2023 (Yahoo's limit), so intraday results lean on crypto.

**Outcome per signal** (from the next open, H bars: 1H 24, 4H 30, 1D 20, 1W 13): `r_h`, the
direction-adjusted move in ATR units after costs; *precision*, the share reaching +2 ATR before
−1 ATR; *false positive*, the share hitting −1 ATR first; MFE/MAE in ATR.

**Walk-forward.** Five consecutive test windows per timeframe (1D/1W: 2010–2024 in 3-year steps;
1H/4H: 2020–mid-2025 in 1-year steps). Before each window the two thresholds are chosen from a
small grid (confirm ∈ {0.5, 0.6, 0.67, 0.8}, major ∈ {0.8, 1.0}, major > confirm) using only
events whose outcome finished before the window (expanding window, purge gap), maximising the
t-statistic of mean `r_h`. Nothing else is tuned: lengths, spans, cooldowns, barriers and
horizons are fixed in code and were not changed after seeing results.

**Holdout.** 1D/1W from 2024-01-01, 1H/4H from 2025-07-01, to Oct 2026. Thresholds are chosen
once on everything before it and it is evaluated once. These are the thresholds the Pine file
ships with.

**Baselines.** (1) every structure break, unfiltered, isolating what the score adds; (2) EMA 20/50
crossover; (3) Supertrend(10, 3) flip; (4) **random entries**: 500 draws of the same number of
entries on the same symbols in the same windows with the same long/short mix, which isolates
*timing* skill from market drift; (5) buy & hold, for the trade simulation.

**Uncertainty.** 95% intervals from a bootstrap that resamples calendar months (signals on the
same dates across correlated assets are not independent). p-values against random entries;
Holm correction across all timeframe × tier tests. Sharpe intervals from a 20-day block bootstrap.

**Verdict rule** (written into `report.py` before the first full run):
*DEMONSTRATED* = OOS mean `r_h` CI above 0, beats random entries at Holm-adjusted p < 0.05, beats
the unfiltered baseline, and the holdout is positive. *PROMISING* = positive, beats random at
unadjusted p < 0.10 and beats the unfiltered baseline, but misses a stricter test.
*UNPROVEN* = anything else.

## Results

All figures are walk-forward out-of-sample unless marked *holdout*. `r` = mean move over the
horizon in ATR units after costs; "random" = same symbols, windows, count and long/short mix.
Full tables (by tier, reversal vs continuation, asset class, every baseline) are in
[`reports/RESULTS.md`](RESULTS.md).

### Verdicts

| timeframe | set | signals / symbol-year | precision (+2 ATR before −1) | r (95% CI) | random r | p vs random | holdout r vs random | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| **4H** | MAJOR | 9.5 | 36.8% (random 33.9%) | **+0.58** [+0.01, +1.16] | +0.26 | 0.040 (Holm 0.28) | **+0.46** vs +0.15 (p 0.14, n 271) | **PROMISING** |
| 4H | all signals | 60 | 35.6% | +0.15 [−0.10, +0.42] | +0.07 | 0.110 | +0.30 vs +0.09 (p 0.09) | UNPROVEN |
| **1H** | MAJOR | 38 | 33.3% (32.3%) | +0.19 [−0.03, +0.41] | −0.13 | **0.002** (Holm 0.016) | **−0.25** vs −0.19 (p 0.66) | PROMISING, **failed holdout** |
| 1H | all signals | 121 | 33.3% | −0.09 [−0.21, +0.03] | −0.14 | 0.092 | −0.30 vs −0.19 | UNPROVEN |
| 1D | MAJOR | 4.0 | 33.9% (35.3%) | +0.41 [+0.09, +0.72] | +0.40 | 0.46 | +0.23 vs +0.48 | UNPROVEN |
| 1D | all signals | 5.6 | 33.3% | +0.28 [+0.03, +0.54] | +0.30 | 0.66 | +0.29 vs +0.40 | UNPROVEN |
| 1W | MAJOR | 0.37 | 30.4% (35.1%) | +0.78 [+0.02, +1.63] | +0.76 | 0.43 | +0.45 vs +1.00 | UNPROVEN |
| 1W | all signals | 1.3 | 32.3% | +0.88 [+0.33, +1.58] | +0.59 | 0.054 | +0.39 vs +0.74 | PROMISING, **failed holdout** |

**Demonstrated: none.** No configuration passed every pre-set test.

### What the evidence supports

- **The score is informative, as a ranking.** Across all out-of-sample structure breaks, outcomes
  rise with the score on 4H (−0.24 → −0.09 → +0.02 → +0.20 → +0.64 ATR from the lowest to the
  highest bucket) and 1W (−0.19 → +1.03), and the filtered signals beat taking every break on all
  four timeframes. The two higher-timeframe conditions (N, A) have the largest individual lift
  on every timeframe, which is the "weekly/daily context matters" idea showing up in data.
- **4H MAJOR is the best candidate.** It beat random timing in walk-forward and was again
  ahead of random in the holdout (+0.46 vs +0.15 ATR, not significant on 271 signals). 80% of
  these signals are crypto, so it says little about other asset classes yet. Trade-simulated,
  it had a lower Sharpe than buy & hold in the same windows (0.31 vs 1.11 OOS; 0.69 vs 0.90
  holdout, intervals overlapping zero), at a far lower drawdown (−33% vs −77% OOS).
- **1H MAJOR** cleared the walk-forward random test by the widest margin (p 0.002, survives
  Holm), then was *worse* than random in the holdout. Treat it as not replicated.
- **1D and 1W signals made money mostly because markets rose.** Their positive `r` matches
  random entries with the same long/short mix; there is no evidence of timing skill there.
- **On 1H, CONFIRMED-tier signals were worse than random in both walk-forward (−0.22 vs −0.14)
  and holdout (−0.33 vs −0.18).** If you use 1H, consider turning off *Show CONFIRMED signals*.
- **Early warnings** have no edge as entries (−0.25 to −0.02 ATR in walk-forward, never better
  than random), but they come early: median 7–9 bars after a swing extreme with ~65% of the leg
  still ahead, versus 17–43 bars and ~32–48% for confirmed/major signals. Use them as a prompt
  to watch, which is what they are labelled as.
- **Timeliness is the price of selectivity.** Against ex-post 4-ATR swings, MAJOR signals catch
  19–32% of turns (median lag 28–43 bars); a Supertrend flip catches 91–96% (lag 9–13 bars) but
  with no better outcomes. MAJOR signals are rare by design: 0.4 per symbol-year on 1W, 4 on 1D,
  9.5 on 4H, 38 on 1H.
- **Reversals vs continuations**: MAJOR continuations did better than MAJOR reversals on every
  timeframe (e.g. 4H +0.74 vs 0.00 ATR, 1W +0.96 vs −0.17). Major reversals beat random only on
  1H in walk-forward (+0.15 vs −0.18, p 0.02), the timeframe whose holdout then failed. The
  REVERSAL label says the structure changed; it is not evidence that catching the turn pays.
- **Momentum (M) is not helping on 1D and 1W** (breaks with M had −0.33 and −0.41 ATR lower `r`
  than breaks without). That is a hypothesis for a future test on new data, not something the
  shipped rules were changed for: changing rules after seeing these numbers would turn the
  out-of-sample record into an in-sample one.

### Thresholds the Pine file ships with

Chosen once on all data before the holdout (`reports/results.json → holdout`):

| profile | CONFIRMED ≥ | MAJOR ≥ (+ anchor agrees) |
|---|---:|---:|
| 1H | 0.80 | 1.00 |
| 4H | 0.80 | 1.00 |
| 1D | 0.67 | 0.80 |
| 1W | 0.60 | 0.80 |

The walk-forward folds used slightly different values on 1H/4H (see RESULTS.md); the dashboard's
evidence line quotes the walk-forward record and the holdout for the profile on screen.

## Reference repositories reviewed

| repo | licence | what the code actually does | quality notes | used here |
|---|---|---|---|---|
| [aretephi/MTF-Confluence-Trend](https://github.com/aretephi/MTF-Confluence-Trend) | **none** (all rights reserved by default) | Supertrend flip + HTF Supertrend agreement + ADX/volume filter; Pine strategy and an MT5 port | Honest README (shows two disagreeing backtests, 48 vs 71 trades, one symbol). HTF call is `expr[1]` with `lookahead_off`: non-repainting but one extra HTF bar late on history. No out-of-sample test. | Idea only: HTF agreement as a filter, volume optional for FX. No code copied. |
| [ritstar/ritstar-algo-pine-script](https://github.com/ritstar/ritstar-algo-pine-script) | **none** | 6-factor 0–6 score (EMA trend, 20-bar breakout, RSI, MACD, ATR/body, volume) with a FLAT/LONG/SHORT state machine and cooldown | Clear structure, bar-close gating. Volume adds a point to *both* sides; weights arbitrary; "high-confidence" never measured; same HTF idiom as above. | Ideas only: one-leg state machine + cooldown, displacement (body vs ATR). No code copied. |
| [mitchell-917/tradingview-pinescript-lab](https://github.com/mitchell-917/tradingview-pinescript-lab) | MIT | Educational indicators: market structure HH/HL, MTF dashboard, liquidity sweeps, templates | Readable. Its no-repaint tutorial is **wrong**: it calls `request.security(..., close, lookahead_off)` "CORRECT – No repaint"; that repaints on realtime bars. Its structure tool labels pivots at the pivot bar (fine for display, not for signals). | HH/HL structure concept and MTF table layout, reimplemented with confirmed pivots. |
| [mementum/backtrader](https://github.com/mementum/backtrader) | GPL-3.0 | Event-driven backtesting framework | Mature. Default fills at next bar open; cheat-on-close is opt-in; slippage/commission schemes; analyzers (Sharpe, drawdown, SQN). | Execution conventions only (next-open fills, gap-through stops, costs). Not imported, to keep the package light and licence-clean. |
| [suyons/tradingview-indicators](https://github.com/suyons/tradingview-indicators) | **none** for the repo; one file (`01-machine-learning-momentum-index.pine`) is a third-party CC BY-NC-SA script | 34 personal scripts: RSI/BB/MA variants, MTF tables, volume tools, k-NN momentum | Several `request.security` calls with no offset and default lookahead, which repaint on realtime bars. No validation. | Nothing reused. |

None of the reference repositories publishes an out-of-sample test, so none of their
accuracy figures was carried over.

## Reproducing

```sh
cd indicator
pip install -r requirements.txt
python scripts/fetch_data.py         # ~10 min; caches to data/ and writes data/MANIFEST.json
python -m pytest -q tests            # integrity + parity tests (no network needed)
python -m hcmtf.report               # ~15 min; writes reports/RESULTS.md, results.json, verdicts.json
python scripts/sync_pine.py          # copies the holdout-free thresholds into the Pine file
```

Data is not committed (licence of the feeds); `data/MANIFEST.json` records the SHA-256, row count
and span of every file used for the published report, so a re-download can be compared. Yahoo
revises history occasionally and its hourly window rolls forward, so a later run will differ
slightly; the random-entry seeds are fixed.

## Limitations

- **Survivorship**: no delisted symbols (free data does not have them). Laggards are included,
  but a universe of survivors still flatters long-biased rules.
- **Intraday breadth**: non-crypto 1H/4H history is three years, so intraday conclusions are
  mostly about crypto.
- **Costs** are flat per asset class; real spreads widen in stress, which hurts breakout entries most.
- **Multiple testing**: Holm covers the eight headline tests; the per-kind and per-class tables
  are descriptive and many more comparisons than eight are shown.
- Futures, single-name FX crosses, small caps and illiquid altcoins are not in the sample; the
  indicator runs on them but nothing here speaks to how it behaves there.
