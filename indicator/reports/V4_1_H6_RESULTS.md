# V4.1 H6 results: does the HTF trend state alone predict returns?

**Decision (pre-registered rule, holdout stage H): INCONCLUSIVE.**
* **No cell passes.** No group × timeframe × side cell passes the rule of
  [`V4_1_PREREGISTRATION.md`](V4_1_PREREGISTRATION.md) §6 (Holm < 0.05, mean ≥ 0.10 ATR,
  median > 0, ≥ 2 of 3 purged spans positive).
* **Rejection is not met either.** The pooled 1H and 4H confidence intervals still include
  premiums above the 0.10 ATR minimum effect.
* **The crypto signal is weak.** It is a small, positive, two-sided crypto intraday premium,
  carried by a minority of large moves (the median is ≤ 0).
* **Equities show the opposite** of what the hypothesis predicts.

## Setup

* **State definition.** As in the engine:
  * HTF1/HTF2 trend = close vs EMA21 with an agreeing slope, read from the last **completed**
    HTF candle;
  * bullish state = with(+1), bearish state = with(−1);
  * full rules in prereg §2.
* **Unit.** Every eligible candle in the state.
* **Outcome.** r_h = move in the state's direction to candle H (1H 24, 4H 30, 1D 20, 1W 13), in
  ATR, after round-trip costs (crypto 20 bp, equities 6, index/sector ETFs 4, commodities 8,
  bonds 4, FX 3).
* **Primary statistic.** Mean excess over **U** (same instrument, same side, every eligible
  candle).
* **Inference.** Calendar-block cluster bootstrap (5,000 replicates; benchmarks re-estimated in
  each), Holm within the H6 family (30 evaluable tests).

### Holdout sample (38 never-used instruments; stage H)

| TF | crypto (10) | equities (16) | commodities (4) | rates & FX (8) |
|---|---|---|---|---|
| 1H | 2020-01-01 → 2026-10-27, 546,242 candles | 2023-11-28 → 2026-10-26, 79,587 | 2023-11-28 → 2026-10-26, 19,884 | 2023-11-28 → 2026-10-27, 88,155 |
| 4H | 2020-01-01 → 2026-10-27, 135,823 | 2023-11-28 → 2026-10-26, 22,544 | same, 5,636 | same, 23,251 |
| 1D | 2018-05-28 → 2026-10-25, 22,634 | 2010-01-01 → 2026-10-23, 67,328 | 2010-01-01 → 2026-10-23, 16,083 | 2010-01-01 → 2026-10-26, 34,262 |
| 1W | 2018-05-28 → 2026-10-19, 2,239 (9 instr.; ICPUSDT < 300 candles) | 2010-01-01 → 2026-10-19, 13,824 | 3,082 | 6,912 |

Exclusions and data notes:
* EOSUSDT ends 2025-05-26 (delisted); it is kept up to then.
* No instrument triggered the Amendment 1 integrity cut.
* Full coverage per instrument: `reports/v41_tables/cov_H.md`.

## Primary results, holdout

Mean excess over U, r_h in ATR at horizon H, [95% cluster-bootstrap CI]. One-sided p and
Holm-adjusted p.

| TF | group | bullish state | Holm p | median | bearish state | Holm p | median |
|---|---|---|---:|---:|---|---:|---:|
| 1H | crypto | **+0.188 [+0.065, +0.301]** | 0.066 | −0.147 | **+0.130 [+0.035, +0.221]** | 0.110 | −0.002 |
| 1H | equities | −0.113 [−0.261, −0.005] | 1 | −0.022 | −0.120 [−0.319, +0.019] | 1 | −0.113 |
| 1H | commodities | +0.128 [−0.278, +0.495] | 1 | −0.195 | +0.174 [−0.203, +0.491] | 1 | +0.018 |
| 1H | rates & FX | −0.076 [−0.289, +0.127] | 1 | −0.082 | +0.021 [−0.182, +0.205] | 1 | +0.004 |
| 4H | crypto | **+0.491 [+0.038, +0.869]** | 0.487 | −0.163 | +0.219 [−0.012, +0.444] | 0.842 | +0.346 |
| 4H | equities | −0.268 [−0.548, −0.097] | 1 | −0.268 | −0.448 [−0.897, −0.116] | 1 | −0.371 |
| 4H | commodities | +0.011 [−1.029, +0.848] | 1 | −0.359 | +0.166 [−0.602, +0.891] | 1 | +0.375 |
| 4H | rates & FX | −0.000 [−0.301, +0.240] | 1 | +0.003 | −0.120 [−0.462, +0.148] | 1 | −0.111 |
| 1D | crypto | −0.231 [−0.894, +0.444] | 1 | −0.865 | +0.047 [−0.278, +0.303] | 1 | +0.647 |
| 1D | equities | −0.102 [−0.209, −0.011] | 1 | +0.107 | −0.240 [−0.556, +0.042] | 1 | −0.451 |
| 1D | commodities | +0.171 [−0.227, +0.526] | 1 | +0.075 | −0.032 [−0.303, +0.206] | 1 | +0.057 |
| 1D | rates & FX | +0.041 [−0.131, +0.216] | 1 | +0.091 | +0.045 [−0.362, +0.449] | 1 | +0.201 |
| 1W | crypto | −0.518 [−1.251, +0.338] (not evaluable: 6 clusters) | – | −1.332 | −0.253 [−0.753, +0.106] (not evaluable) | – | +0.532 |
| 1W | equities | +0.006 [−0.095, +0.079] | 1 | +0.064 | +0.053 [−0.378, +0.475] | 1 | −0.230 |
| 1W | commodities | +0.167 [−0.325, +0.620] | 1 | −0.057 | +0.251 [−0.063, +0.508] | 1 | +0.279 |
| 1W | rates & FX | −0.028 [−0.204, +0.147] | 1 | −0.022 | −0.247 [−0.623, +0.172] | 1 | −0.047 |

Pooled (all groups; used only for the rejection rule):

| TF | bullish | bearish |
|---|---|---|
| 1H | +0.106 [+0.006, +0.189] | +0.094 [+0.011, +0.166] |
| 4H | +0.245 [−0.066, +0.503] | +0.132 [−0.068, +0.314] |
| 1D | −0.053 [−0.179, +0.053] | −0.041 [−0.249, +0.107] |
| 1W | −0.013 [−0.121, +0.073] | −0.029 [−0.273, +0.195] |

All cells, the V/Y benchmarks, horizons, onset and lag variants, spans and volatility terciles:
`reports/v41_tables/h6_H.md`.

## Does the state predict returns, or only expose you to drift?

* **Static drift is removed by design.** U is the same instrument and side over the whole window,
  so a market that simply rises cannot produce a positive premium. A premium means the state
  separates better periods from worse ones.
* **Crypto intraday: yes, weakly, on both sides.**
  * On 1H crypto both sides are positive, with CIs above 0 before correction. That is the
    two-sided pattern prediction requires.
  * It replicates the seen-symbol estimate almost exactly: stage D gave bullish +0.208
    [+0.098, +0.305] and bearish +0.140 [+0.046, +0.228].
  * It holds against the causal volatility-matched benchmark V: bullish +0.165 [+0.042, +0.278],
    bearish +0.129 [+0.034, +0.219].
  * It holds at H/4 (bullish +0.066 [+0.033, +0.096]) and at 2H (+0.324 [+0.089, +0.536]).
  * It is positive in all 3 purged chronological spans on both sides.
  * But it **fails Holm** (0.066 / 0.110), and the **median excess is ≤ 0** (−0.147 / −0.002).
    It is a premium paid by a minority of large trend runs; the typical state candle does not
    beat static exposure.
* **Most of the premium is slow drift.**
  * Against **Y** (same calendar year; not causal) the 1H crypto premium shrinks to +0.134
    [−0.017, +0.216] bullish and +0.090 [−0.019, +0.156] bearish, with CIs including 0.
  * On 4H crypto it is +0.191 [−0.311, +0.426] bullish.
  * So the state mostly identifies which months and years trend, rather than timing within them.
* **Equities point the other way.**
  * Every evaluable equity cell at 1H, 4H and 1D has a negative point estimate.
  * Four have CIs entirely below 0: 1H bullish, 4H bullish −0.268 [−0.548, −0.097], 4H
    bearish −0.448 [−0.897, −0.116] and 1D bullish.
  * Being in the HTF state was worse than static exposure, consistent with short-horizon mean
    reversion in single stocks and sector ETFs.
  * The same sign appeared on the seen equities (stage D 4H: −0.321 / −0.552).
* **Commodities and rates/FX** show no evidence either way (wide CIs around 0).
* **1D and 1W** show nothing anywhere.
* **Timing within a state matters little.**
  * Onset candles (the first candle of a state) are not better than state candles in general:
    1H crypto bullish onset +0.118 [−0.031, +0.262].
  * Lagging HTF1 by one more candle barely changes anything: 1H crypto bullish +0.183, 4H
    +0.466.

## Trading view (secondary; drawdowns)

* **Rule.** Hold +1 in the bullish state, flat otherwise (or −1 in the bearish state). Each
  instrument is traded open-to-open with costs, and instruments are equal-weighted daily.
* **The timed rule always trades less**, so its CAGR and drawdown are both smaller than static
  exposure.
* **The useful comparison is the Sharpe ratio.**

| TF · group · side | timed CAGR | timed Sharpe | timed max DD | static CAGR | static Sharpe | static max DD |
|---|---:|---:|---:|---:|---:|---:|
| 1H crypto bullish | +29.1% | +0.83 | −59% | +69.9% | +0.93 | −88% |
| 4H crypto bullish | +54.4% | **+1.25** | −53% | +69.9% | +0.93 | −88% |
| 4H crypto bearish | −13.8% | −0.05 | −79% | −69.3% | −0.84 | −100% |
| 1D crypto bullish | +10.1% | +0.45 | −55% | +27.2% | +0.69 | −89% |
| 1D equities bullish | +5.6% | +0.84 | −14% | +13.9% | +1.11 | −31% |
| 4H equities bullish | +4.4% | +0.87 | −9% | +13.5% | +1.24 | −17% |
| 1W equities bullish | +8.8% | +0.82 | −21% | +13.7% | +0.93 | −31% |

* **Among long-side rules, only 4H crypto bullish improves the Sharpe ratio** over static
  exposure (+1.25 vs +0.93). Its block-bootstrap CIs overlap heavily (table in `h6_H.md`).
* **For every other long-side rule**, the state reduces drawdowns roughly in proportion to the
  exposure it removes, and lowers the Sharpe ratio. That is risk reduction, not prediction.
* **Short-side timed rules have Sharpe ratios ≤ 0 in every group except 1W commodities**
  (+0.09). They lose less than always-short, which is what U already measures.

## Stage D (seen symbols, exploratory, not used for the decision)

* **1H crypto** is the same picture: +0.208 / +0.140, medians −0.135 / −0.040.
* **4H crypto bullish**: +0.374 [+0.033, +0.661].
* **Equities** are negative at 1H/4H.
* **Stage D decision**: also INCONCLUSIVE.
* Full tables: `reports/v41_tables/h6_D.md`.

## Limitations

* **Same calendar period as the seen data.** Crypto 2020–2026 contains two large bull runs and
  one long bear market for every coin, held in common across instruments. Ten new coins are not
  ten independent tests.
* **Non-crypto intraday is short.** It covers only ~35 months (Yahoo limit), so the 4H
  commodity and rates cells have 17–18 clusters and wide CIs.
* **1W crypto is not evaluable** (6–7 yearly clusters).
* **Residual overlap.** Outcome windows still overlap across cluster edges (disclosed in prereg
  §5).
* **Heavy tails.** The mean is the primary statistic and the median rule is strict on purpose.
  A strategy-level view could rate the crypto premium more favourably than the per-candle median
  does; that is a different question from the one pre-registered.

Reproduce:

```bash
python scripts/v41_run.py H
python scripts/v41_tables.py
```

The frozen code hashes are in `reports/V4_1_DATA_MANIFEST.json` and `reports/v41_H.json`
(`config_hash`).
