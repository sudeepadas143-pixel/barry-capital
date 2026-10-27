# HC-MTF: multi-timeframe trend-change indicator, with its evidence

A TradingView indicator (`pine/HighConvictionMTF.pine`, Pine Script v6) that reads every chart on a
**lower / middle / higher timeframe ladder** and marks bullish and bearish structure changes, plus a
Python research package (`hcmtf/`) that runs the same rules and tests them out of sample on 70
symbols (30 development, 40 never-used "fresh" ones) across crypto, equities, indices, bonds,
commodities and FX, on 1H, 4H, 1D and 1W.

**Short version.** The integrity side is done and tested: no repainting, no look-ahead (the tests
caught two real leaks during v2 development, both fixed), closed-candle signals, completed-HTF data,
bar-for-bar agreement between the Pine logic and the research engine, and an independent backtrader
re-simulation that reproduces every trade. The predictive side is where the honest answer is
uncomfortable: **of fourteen candidate confirmations drawn from the eight reference repositories
(momentum, ADX, displacement, fair-value gaps, volume, liquidity sweeps, LTF momentum, funding,
basis, open interest, regime/shock/spike/weekend filters), none improved outcomes under a rule fixed
before testing**, and the one dimension that did separate outcomes on development data, the
relation to the higher timeframes, beat random timing on unseen symbols only on **crypto 1H and
4H** (rated PROMISING, not DEMONSTRATED) and nowhere on non-crypto markets. See [Results](#results). The indicator is
therefore built to *refuse to manufacture confidence*: it shows the evidence it computes, gates
signals only on what testing supported, prints its out-of-sample record on the chart, and stays
neutral otherwise.

v1 (single-timeframe scoring, walk-forward thresholds) is archived in `pine/v1/` and `reports/v1/`.

---

## Contents

```
pine/HighConvictionMTF.pine     the indicator (v2)
pine/v1/                        the v1 indicator, kept for reference
hcmtf/
  universe.py                   70 symbols: 30 DEV + 40 FRESH (incl. delisted coins), costs
  data.py, derivs.py            Yahoo + Binance spot, 15m LTF, perps, funding, open interest
  ta.py                         Pine-exact EMA/RMA/ATR/RSI/DMI/MACD/Supertrend, causal pivots
  htf.py                        completed-HTF alignment (Pine: f()[1] + lookahead_on)
  engine.py                     v2 engine: ladder, break classes, evidence, tiers, warnings
  study.py, report2.py          building contexts, evaluation, verdicts → reports/
  evaluate.py, metrics.py       outcomes, trade simulation, baselines, bootstraps
  signals.py, walkforward.py, report.py   v1 engine and study (archived results)
scripts/
  fetch_data.py, fetch_v2.py, fetch_fresh_15m.py   downloads (cached)
  screen_components.py          pre-registered component screening (dev data only)
  apply_screening.py            screening decisions → reports/active_config.json
  design_check.py               the tier design check (dev data only)
  sync_pine.py                  writes tested config + out-of-sample record into the Pine file
  compare_tv_export.py          TradingView-vs-Python parity on TradingView's own candles
crosscheck/backtrader_check.py  independent re-simulation in backtrader (GPL-3, kept separate)
tests/                          integrity, look-ahead, Pine mirrors, parity tooling
reports/
  RESULTS.md, results.json, verdicts.json   v2 validation
  SCREENING.md, screening.json               component screening
  DESIGN_CHECK.md                            the tier decision and its data
  BACKTRADER_CROSSCHECK.md                   simulator equivalence
  active_config.json                         what the engine and Pine run with
  v1/                                        v1 results and README
```

## Using the indicator

1. TradingView → Pine Editor → paste `pine/HighConvictionMTF.pine` → *Add to chart*. Works on any
   symbol and chart type TradingView gives OHLC for.
2. The **profile** follows the chart timeframe and sets the ladder (each level can be overridden):

   | chart (MTF) | LTF (timing, warnings) | HTF1 | HTF2 | swing span | cooldown |
   |---|---|---|---|---|---|
   | ≤2H → 1H profile | 15m | 4H | 1D | 5 / 3 | 12 candles |
   | ≤8H → 4H | 1H | 1D | 1W | 5 / 3 | 6 |
   | ≤2D → 1D | 4H | 1W | 1M | 5 / 2 | 5 |
   | longer → 1W | 1D | 1M | 3M | 4 / 2 | 4 |

3. What appears on the chart: two signal types, nothing else.

   | mark | meaning |
   |---|---|
   | **▲ Bullish** (blue arrow below the candle, word underneath) | The chart-timeframe structure turned back up into the higher-timeframe direction after a pullback (HTF1 + HTF2 with it, neither against). At most one per pullback. |
   | **▼ Bearish** (red arrow above the candle, word on top) | The same, downward. |
   | nothing | Neutral: most candles. |

   Drawn with native `plotshape(shape.arrowup / shape.arrowdown)` at `location.belowbar /
   abovebar`, so arrows sit clear of the wick; the word uses the chart's text colour. No dashboard,
   no tables, no swing lines, no status-line values, no diagnostics. *Also mark continuation
   breaks* (off by default) adds the same arrows for further breaks in the HTF direction.
   Preview (rendered offline from the engine's signals, not a TradingView screenshot):
   [`reports/preview_BTCUSDT_1H.png`](reports/preview_BTCUSDT_1H.png).
4. Alerts: Bullish and Bearish (exactly the arrows shown), plus a JSON `alert()` payload. Once per
   closed candle.
5. The diagnostics that used to be on the chart (HTF/LTF trends, alignment, out-of-sample record)
   are documented here and in `reports/`; the optional *Parity export* writes codes to the data
   window only, for `scripts/compare_tv_export.py`.
6. *Use the tested configuration* (default on). Off lets you switch the context conditions into
   gates and set thresholds, for research. The dashboard then says **CUSTOM — unvalidated**.

### Crypto first, every market

- **24/7 sessions**: HTF candles come from TradingView's own HTF series, so no daily close is
  assumed; crypto weeks start Monday 00:00 UTC as on TradingView. The research data uses the same
  convention (Binance), and 4H candles on exchange-hours markets are anchored to the session.
- **Volume** is used as reported and only where it means something: *Auto* turns it off on forex,
  indices and CFDs (tick or no volume). Exchange-specific crypto volume is not treated as market-wide.
  In the shipped configuration volume gates nothing.
- **Spikes**: a signal needs a *closed* candle beyond a *confirmed* swing level; a wick through a
  level does nothing. The spike/liquidation-wick, volatility-shock and weekend filters were tested
  (see Screening) and are available as research toggles.
- **Perpetual-futures data** (funding, spot/perp basis, open interest) is not available to standard
  Pine for most symbols. It was tested in Python from Binance's public archive. None of the three
  features passed screening, so the indicator does not depend on any of them and there is nothing to
  fall back from. If a later test keeps one, it must come in through optional symbol inputs (e.g.
  `BINANCE:BTCUSDT.P` for basis, an exchange `_OI` ticker for open interest) with the core unchanged
  when they are blank; `scripts/sync_pine.py` refuses to sync a perp feature that has no Pine input.
- Nothing in the engine is crypto-specific: everything is measured in ATR units of the instrument
  itself, so the same rules apply to BTC, a thin altcoin, EURUSD or a bond ETF. Results are reported
  per market so you can see where it works and where it does not.

## Integrity guarantees, and how they are tested

| guarantee | how | test |
|---|---|---|
| Closed-candle signals | `barstate.isconfirmed` gate, default on; off shows hollow "?" provisional labels | — |
| HTF without look-ahead | `request.security(sym, tf, f()[1], lookahead = barmerge.lookahead_on)`: previous completed HTF candle, history and realtime alike | unit + truncation tests |
| LTF without look-ahead | `request.security_lower_tf`, last LTF candle inside the *closed* chart candle; Python reads the last LTF candle that opened before the chart close | `test_ltf_reads_only_candles_inside_the_closed_chart_candle` |
| Swing points not back-dated | a pivot is used only from the candle its right side closes | unit test |
| Signals never move | **Truncation**: signals, WATCH rows and warnings computed with data up to candle *k* (forming HTF candles from partial data, LTF and perp series cut at *k*'s close) equal the full-history ones up to *k*. A bar-by-bar version checks every HTF, LTF, perp and volatility reading on the newest candle | `test_v2_signals_never_change_after_they_print`, `test_v2_last_bar_context_is_final` |
| The tests catch leaks | During v2 the truncation test caught funding/basis/OI features switched on by the *total* series length (future-dependent) and an LTF length gate; both removed. In v1 four injected bugs (HTF without `[1]`, pivots peeking ahead, forming HTF candle, fill at signal close) each failed the suite | — |
| Pine and Python agree | `tests/pine_mirror_v2.py` transliterates the Pine logic statement by statement (`var` state, `x[k]` history) and must reproduce the engine's signals, WATCH rows and warnings for several component/filter combinations; constants are cross-checked against the Pine source | `test_pine_v2_logic_matches_engine`, `test_pine_v2_source_matches_engine_constants` |
| Pine on TradingView's data | Parity mode plots per-candle signal, WATCH, warning, HTF and LTF codes; `scripts/compare_tv_export.py` re-runs the engine on the exported candles and lists every disagreement | `test_tradingview_parity_script_round_trip` (plumbing only) |
| Simulator is right | backtrader re-implementation (next-open market fills, Stop orders, close-of-candle time exit), trades read from backtrader's own fills | [`reports/BACKTRADER_CROSSCHECK.md`](reports/BACKTRADER_CROSSCHECK.md): 9 cases, 1,718 trades, all identical |
| Realistic fills | entry at the next candle's open; stops at the stop or the gapped open; a stop wins a tie with the target; round-trip costs per asset class (crypto 20 bp, commodities 8, equities 6, indices/bonds 4, FX 3) | `test_simulated_stop_fills_at_open_when_gapped`, `test_outcomes_enter_on_next_open_not_signal_close` |

**Not checked here:** the Pine file was parsed with `pynescript` but not compiled by TradingView,
which this environment cannot reach. To check it: add it to a chart, tick *Parity export*, *Export
chart data*, then `python scripts/compare_tv_export.py export.csv --profile 4H --crypto`. A compile
error or a mismatch there is a bug to fix.

## Validation method

**Three data roles, kept apart.**
1. *DEV*: the original 30 symbols, up to each timeframe's holdout start (1H/4H 2025-07-01, 1D/1W
   2024-01-01). Every design decision was made here.
2. *FRESH*: 40 symbols added before any v2 result existed and never used for any decision: 19 crypto
   (4 large caps, 6 mid caps, 4 thin small caps, 5 that collapsed or were delisted: LUNA, FTT, SRM,
   WAVES, MATIC) and 21 others (8 stocks, 4 index ETFs, 2 bond ETFs, 3 commodity ETFs, 4 FX pairs),
   from 2010 (daily/weekly) or 2020 (intraday). **The primary test.**
3. *DEV holdout*: looked at once in v1, so reported but flagged as no longer untouched.

**Step 1, screening** (`scripts/screen_components.py`, rule in its docstring, fixed before it ran).
Every MTF structure break on DEV data; for each candidate, mean outcome with vs without it, 90%
month-cluster bootstrap. Keep for all markets if the crypto difference is positive with CI above 0,
positive on ≥3 of 4 timeframes, and non-crypto is not significantly negative; keep for crypto only if
non-crypto is significantly negative; drop otherwise. Filters likewise. Families correlated at
|phi| > 0.5 would be merged so correlated evidence is never counted twice (none were; the largest
was displacement–volume at 0.26).

**Step 2, design check** (`scripts/design_check.py`, DEV only): with nothing kept, what could still
separate tiers? Decision and data in [`reports/DESIGN_CHECK.md`](reports/DESIGN_CHECK.md).

**Step 3, evaluation** (`hcmtf/report2.py`). Outcome per signal from the next open over H candles
(1H 24, 4H 30, 1D 20, 1W 13): `r_h` (direction-adjusted move in ATR after costs), precision (+2 ATR
before −1 ATR), false positives (−1 ATR first), MFE/MAE. Baselines: every structure break
unfiltered, EMA 20/50 cross, Supertrend(10,3) flip, and **random entries** on the same symbols and
dates with the same count and long/short mix, which separates timing from market drift. Trade
simulation (ATR trailing stop, reversal on opposite signal, time stop; equal weight across symbols)
against buy & hold. Timeliness against ex-post 4-ATR swings. 95% month-cluster CIs; Holm correction
across the eight timeframe × market verdicts.

**Verdict rule** (fixed in `hcmtf/report2.py` before the first fresh run), per timeframe, separately
for crypto and non-crypto fresh symbols, for MAJOR signals: *DEMONSTRATED* = CI above 0, beats random
at Holm p < 0.05, beats unfiltered breaks, and the DEV record also beat random (p < 0.10).
*PROMISING* = positive, beats random at p < 0.10, beats unfiltered breaks. *UNPROVEN* otherwise.

## Results

All numbers: MAJOR signals (realignments), **fresh symbols** unless stated. `r` = mean move over the
horizon in ATR after costs; "random" = same symbols, dates, count and long/short mix. Full tables
(every tier, WATCH, warnings, baselines, holdout windows, crypto tiers, simulations, timeliness) in
[`reports/RESULTS.md`](reports/RESULTS.md).

### Verdicts

| TF | market | MAJOR per symbol-year | precision (+2 before −1 ATR) | r [95% CI] | random r | p vs random (Holm) | dev symbols, all markets: p vs random | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| **1H** | crypto (19) | 58 | 33.2% | +0.07 [−0.08, +0.22] | −0.18 | 0.003 (0.027) | 0.033 | **PROMISING** |
| 1H | non-crypto (21) | 19 | 33.7% | −0.30 [−0.55, −0.05] | −0.12 | 0.92 | — | UNPROVEN |
| **4H** | crypto | 15.5 | 36.4% | **+0.43 [+0.04, +0.85]** | −0.11 | 0.003 (0.027) | 0.53 | **PROMISING** |
| 4H | non-crypto | 5.0 | 35.0% | −0.24 [−0.86, +0.33] | +0.23 | 0.97 | — | UNPROVEN |
| 1D | crypto | 3.0 | 32.4% | −0.12 [−0.73, +0.43] | −0.18 | 0.42 | 0.78 | UNPROVEN |
| 1D | non-crypto | 2.6 | 34.2% | +0.10 [−0.15, +0.35] | +0.20 | 0.82 | — | UNPROVEN |
| 1W | crypto | 0.4 | 15.2% | −0.33 [−2.73, +1.55] (n = 46) | −0.76 | 0.48 | 0.95 | UNPROVEN |
| 1W | non-crypto | 0.6 | 34.7% | +0.40 [−0.02, +0.75] | +0.44 | 0.58 | — | UNPROVEN |

**Demonstrated: none.** Neither PROMISING row clears every pre-set test: 1H crypto's interval
includes zero (it beats random entries, which lose −0.18 ATR after a 20 bp round trip, but its own
mean is only +0.07); 4H crypto did not beat random on the development symbols (p 0.53).

### What the evidence supports

- **Crypto, 1H**: MAJOR realignments picked better moments than random entries on unseen coins *and*
  on the development coins, in every liquidity tier (large +0.05 vs −0.23, mid +0.02 vs −0.17, small
  +0.15 vs −0.16, collapsed/delisted +0.10 vs −0.15). The relative edge is consistent; the absolute
  one is thin. After costs it does not pay on its own: the trade simulation lost slightly (Sharpe
  −0.26, profit factor 0.98), better than every baseline (unfiltered breaks −1.66, Supertrend −1.81).
  In the recent window (from 2025-07) it was worse than random (−0.37 vs −0.16).
- **Crypto, 4H**: the largest effect (+0.43 ATR, +0.88 on large caps, positive on every tier) and
  a trade simulation with Sharpe 0.38 [−0.39, 0.98], max drawdown −26% versus −77% for buy & hold of
  the same coins. But it showed nothing on the development coins and was negative in the recent
  window (−0.45 vs +0.10). Treat as a lead to re-test on future data, not as an edge.
- **Crypto structure breaks in general** beat random timing on unseen coins on 4H and 1D (every
  break, unfiltered: +0.24 and +0.51 ATR, p 0.003). That is trend persistence in crypto, and the HTF
  gate does not add to it on 1D (MAJOR −0.12 there).
- **Non-crypto (stocks, index ETFs, bonds, commodities, FX)**: no timeframe beat random. 1H MAJOR was
  significantly negative (−0.30). The indicator's signals should not be read as an edge on these
  markets.
- **Higher timeframes are more selective but not more accurate.** MAJOR frequency falls from 58
  (1H crypto) to 15.5 (4H), 3 (1D) and 0.4 (1W) per symbol-year, as asked, but 1D and 1W outcomes are
  indistinguishable from random entries with the same direction mix.
- **WATCH (counter-HTF reversals)** were strongly negative on 1H (−0.30 crypto, −0.20 non-crypto),
  negative on non-crypto 1D/1W, and mixed on crypto 4H/1D. Labelling them as information, not
  signals, is supported.
- **LTF early warnings** come early (median 5–7 candles after a swing extreme, ~72% of the leg still
  ahead, versus 16–24 candles and ~45% for MAJOR) but have no edge as entries (−0.14 to −0.33 ATR on
  crypto 1H–1D). They are timing information.
- **Timeliness**: MAJOR catches 18–29% of 4-ATR swings; a Supertrend flip catches ~90% of them and
  sooner (11–14 vs 16–24 candles) with no better outcomes. Selectivity here means rarer signals, not
  better ones.
- **Simulator**: every trade above was reproduced exactly by backtrader (`reports/BACKTRADER_CROSSCHECK.md`).

### Component screening (development data)

| candidate (source) | crypto with − without [90% CI] | non-crypto | decision |
|---|---:|---:|---|
| momentum: RSI/MACD (ritstar, v1) | +0.03 [−0.14, +0.20] | −0.09 | drop |
| strength: ADX/DI (MTF-Confluence, ritstar) | +0.09 [−0.02, +0.19] | +0.01 | drop |
| displacement: body ≥ 0.5 ATR (ritstar) | +0.05 [−0.11, +0.19] | −0.05 | drop |
| fair-value gap (SM Radar) | +0.05 [−0.04, +0.15] | +0.02 | drop |
| volume ≥ 1.3× (all) | +0.03 [−0.09, +0.14] | +0.07 | drop |
| liquidity sweep before break (SM Radar, Capital41) | −0.08 [−0.21, +0.04] | **−0.18** [−0.29, −0.08] | drop |
| LTF momentum agrees (ladder) | +0.07 [−0.19, +0.34] | −0.43 | drop |
| funding not crowded (Capital41 idea) | +0.07 [−0.17, +0.32] | n/a | drop |
| basis not stretched (Capital41) | +0.10 [−0.10, +0.32] | n/a | drop |
| open interest rising (Capital41) | +0.10 [−0.04, +0.26] | n/a | drop |
| filter: not a range, ADX ≥ 18 (Regime Detector) | −0.00 [−0.13, +0.11] | −0.02 | drop |
| filter: not a volatility shock (Regime Detector) | +0.23 [−0.01, +0.44] | **+0.30** [+0.10, +0.51] | drop (closest) |
| filter: no spike/liquidation wick (Capital41) | +0.09 [−0.09, +0.26] | +0.19 | drop |
| filter: not a crypto weekend (Capital41) | **+0.31** [+0.13, +0.49], but positive on 1 of 3 TFs | n/a | drop |
| counter-HTF reversal MAJOR path (sweep required) | reversals after a sweep averaged −0.16 | | closed |

Full table with per-timeframe values: [`reports/SCREENING.md`](reports/SCREENING.md). No two
conditions from different families were correlated above |phi| 0.26, so nothing would have been
double-counted.

### Which configurations to use, and how

| use | status | how to read it |
|---|---|---|
| 1H / 4H on crypto, MAJOR | PROMISING | Better-than-random timing on unseen coins; thin (1H) or unconfirmed on dev data and recent months (4H). Use as structure-and-context reading, not as a standalone system. |
| 1H / 4H on crypto, CONFIRMED | not separately rated | 1H −0.05 vs −0.17 random; 4H +0.58 vs −0.10 (see RESULTS.md). |
| 1D / 1W, any market | UNPROVEN | Clean, rare labels with HTF context, but no timing edge was found. |
| Any timeframe, non-crypto | UNPROVEN | No edge found; 1H MAJOR was negative. |
| WATCH, early warnings | information | Not entries. |
| Custom evidence gating | unvalidated | Every gate tested here failed screening. |

## Reference repositories

| repo | licence | what the code does | quality / integrity notes | used here |
|---|---|---|---|---|
| [aretephi/MTF-Confluence-Trend](https://github.com/aretephi/MTF-Confluence-Trend) | **none** (all rights reserved) | Chart Supertrend flip confirmed by HTF Supertrend + ADX/volume; Pine v6 + MT5 port | Clean, honest README (two disagreeing backtests, one symbol). HTF via `expr[1]` + `lookahead_off`: no repaint, one extra HTF candle of lag on history. | **The architecture**: chart signal confirmed by HTF, trend-strength filter, closed-candle handling, volume optional for FX. Reimplemented with a dynamic LTF/MTF/HTF ladder, the `[1]` + `lookahead_on` idiom and reversal classes. No code copied (no licence). Its Supertrend flip is a baseline. |
| [ritstar/ritstar-algo-pine-script](https://github.com/ritstar/ritstar-algo-pine-script) | **none** | 6-factor 0–6 score, FLAT/LONG/SHORT state machine, cooldown | Volume point added to both sides; arbitrary weights; same HTF idiom. | Ideas only: state machine + cooldown, body-vs-ATR displacement. Its multi-factor scoring idea was tested and did not hold up. |
| [mitchell-917/tradingview-pinescript-lab](https://github.com/mitchell-917/tradingview-pinescript-lab) | MIT | Educational MTF trend analyzer, HH/HL structure, divergence, S/R, liquidity sweeps | Its no-repaint tutorial calls `request.security(..., close, lookahead_off)` "No repaint": that repaints on realtime candles. Its structure tool labels pivots at the pivot candle (fine for display, not for signals). | HH/HL/BOS structure and the MTF table, reimplemented with confirmed pivots. |
| [mementum/backtrader](https://github.com/mementum/backtrader) | GPL-3.0 | Event-driven backtester | Mature. Two traps met here: `notify_order` receives clones (compare `ref`, not identity), and cheat-on-close also applies to orders placed in `next_open` unless the order opts out with `info['coc']=False`. | **Independent re-simulation** in `crosscheck/`, kept separate so the package carries no GPL dependency. Reproduces every trade. |
| [suyons/tradingview-indicators](https://github.com/suyons/tradingview-indicators) | **none** (one third-party file CC BY-NC-SA) | 34 personal RSI/BB/MA/volume/MTF scripts | Several `request.security` calls without offset or lookahead: repaint on realtime. | Nothing reused. |
| [CedInvest/sm-radar-pine](https://github.com/CedInvest/sm-radar-pine) | MPL-2.0 | Smart-money concepts: BOS/CHoCH, order blocks, FVGs, equal highs/lows and their sweeps, previous D/W/M levels | Clear structure logic. Previous-period levels use `[high[1], low[1]]` with `lookahead_off`: history shows the period before last while realtime shows the last one, so history ≠ realtime. | **BOS/CHoCH → the continuation / realignment / counter-reversal classes**; liquidity sweeps and FVGs tested as evidence (dropped; sweeps before counter-HTF reversals averaged −0.16 ATR on crypto). Reimplemented, not copied. |
| [damianpitt/capital41-indicators](https://github.com/damianpitt/capital41-indicators) (Crypto Perp Stress) | MIT | Basis, OI impulse, liquidation wick, weekend factors | Defaults set spot and perp to the chart symbol (basis always 0); without an OI symbol it silently uses *volume* as "OI"; weekend factors are unexplained constants. | **Tested properly** in Python with real Binance funding, perp/spot basis and open interest, plus the liquidation-wick and weekend ideas as filters. None passed screening. |
| [regimerisk/bitcoin-market-regime-detector](https://github.com/regimerisk/bitcoin-market-regime-detector) | MPL-2.0 | Regime = volatility percentile → ADX range → EMA trend → transition | Simple, transparent, no requests so no repaint risk; thresholds are untested inputs. | Range (ADX < 18) and volatility-shock (ATR-percentile ≥ 95) filters, tested; neither passed (shock was closest: crypto +0.23 ATR [−0.01, +0.44], non-crypto +0.30 [+0.10, +0.51]). |

None of the eight publishes an out-of-sample test; none of their performance claims was carried
over. Ideas were reimplemented, not copied, so this repository contains no third-party code.

## Reproducing

```sh
cd indicator
pip install -r requirements.txt          # backtrader is only needed for crosscheck/
python scripts/fetch_data.py              # DEV spot data (~10 min, cached)
python scripts/fetch_v2.py                # FRESH symbols, 15m LTF, perps, funding, OI (~1 h, cached)
python scripts/fetch_fresh_15m.py         # 15m for fresh crypto, in parallel
python -m pytest -q tests                 # no network needed
python scripts/screen_components.py       # DEV only → reports/SCREENING.md
python scripts/apply_screening.py         # → reports/active_config.json
python scripts/design_check.py            # DEV only → reports/DESIGN_CHECK.md
python -m hcmtf.report2                   # → reports/RESULTS.md
python crosscheck/backtrader_check.py     # → reports/BACKTRADER_CROSSCHECK.md
python scripts/sync_pine.py               # writes config + record into the Pine file
```

Data is not committed; `data/MANIFEST.json` records SHA-256, rows and span of every file used.
Bootstrap and random-entry seeds are fixed.

## Limitations

- Yahoo hourly history starts Nov 2023, so non-crypto 1H/4H results rest on about three years.
- Delisted *stocks* are absent (free data); delisted coins are included.
- Perp data ends 2026-09-30 (archive lag); open interest from Dec 2021 and for DEV crypto only.
- Costs are flat per asset class; spreads widen in stress, which hurts breakout entries most.
- Many more comparisons are shown than the eight Holm-corrected verdicts; treat breakdown tables as
  descriptive.
- The screening rule is strict on purpose. A looser rule would have kept the volatility-shock filter
  (and, on 1H crypto only, the weekend filter); they are the first candidates for a future test on
  data that did not exist when this was written.
