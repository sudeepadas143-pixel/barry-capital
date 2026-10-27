# V4.1 incremental value: does a structure break add anything to the HTF state? (H1r)

**Decision (holdout): INCONCLUSIVE overall. The register's target cell is REJECTED.**

* No group × timeframe × side cell passes the pre-registered rule.
* In the best-powered cells the break is **neither better than the state alone nor better than a
  plain momentum trigger**.
* The one place it looks better on the mean, crypto bullish 4H, fails on the median.

## Design (pre-registration §4)

Three sets of entries, built on identical candles. Every entry sits inside the HTF state of the
same side and uses the same r_h outcome (next-open entry, H candles, ATR units, costs):

| set | definition |
|---|---|
| **S** (state alone) | every candle in the state. This is the benchmark, the H6 baseline |
| **B** (state + structure break) | candles where `hcmtf.engine.breaks` (shipped pivots, no filters) reports a with-HTF break, continuation or realignment, with no cooldown |
| **M** (state + momentum) | candles where ROC(20) turns to the state's direction |

* **Primary statistic**: mean excess of B over S, for the same instrument and side.
* **Also reported**: M over S, and B − M on the same bootstrap replicates.

## Results (holdout, mean excess over S in ATR [95% CI])

| TF | group | B bullish | B bearish | B − M bullish | B − M bearish |
|---|---|---|---|---|---|
| 1H | crypto | +0.002 [−0.082, +0.088] | **−0.127 [−0.234, −0.016]** | −0.019 [−0.148, +0.113] | −0.168 [−0.334, +0.006] |
| 1H | equities | −0.043 [−0.296, +0.179] | +0.039 [−0.245, +0.289] | +0.027 | −0.224 |
| 1H | rates & FX | −0.200 [−0.438, +0.002] | −0.048 [−0.217, +0.092] | **−0.377 [−0.716, −0.077]** | −0.153 |
| 4H | crypto | **+0.374 [+0.066, +0.617]** (Holm 0.22, median −0.487) | +0.048 [−0.175, +0.289] | **+0.393 [+0.022, +0.668]** | −0.029 |
| 4H | equities | −0.074 [−0.355, +0.146] | −0.088 [−0.611, +0.372] | +0.277 | −0.539 |
| 4H | rates & FX | **−0.355 [−0.729, −0.024]** | −0.189 [−0.589, +0.124] | **−0.632 [−1.036, −0.244]** | −0.081 |
| 1D | crypto | +0.460 [−0.171, +0.931] | +0.032 [−0.463, +0.517] | +0.714 [+0.077, +1.090] | −0.228 |
| 1D | equities | −0.088 [−0.221, +0.033] | −0.095 [−0.498, +0.212] | −0.172 | −0.060 |
| 1D | rates & FX | +0.089 [−0.132, +0.304] | −0.127 [−0.536, +0.196] | +0.131 | −0.276 |
| 1W | equities | −0.152 [−0.374, +0.047] | n = 38 | −0.062 | – |
| 1W | rates & FX | +0.182 [−0.109, +0.464] | n = 33 | +0.340 | – |

Pooled (all groups), B vs S:

| TF | bullish | bearish |
|---|---|---|
| 1H | −0.037 [−0.110, +0.027] | **−0.095 [−0.186, −0.008]** |
| 4H | +0.132 [−0.059, +0.280] | −0.017 [−0.211, +0.176] |
| 1D | −0.022 [−0.142, +0.085] | −0.019 [−0.231, +0.150] |
| 1W | −0.028 [−0.210, +0.107] | −0.104 [−0.484, +0.123] |

The commodities rows and every non-evaluable cell are in `reports/v41_tables/h1r_H.md`.

## Reading

* **Hourly: the break subtracts value or adds none.** 1H bearish breaks are worse than random
  bearish-state candles, both in crypto and pooled. On 1H bullish crypto, with 5,918 breaks, the
  break adds +0.002.
* **Rates & FX: the break is clearly worse than a momentum trigger** on 1H and 4H bullish.
* **4H and 1D crypto bullish is the only place the mean favours the break**, over both S and M.
  * On the 4H cell, the median excess is −0.487 and the effect fades across the three
    chronological spans: +0.57, then +0.30, then +0.06.
  * The mean comes from 2020–2022 crypto trend runs, the same pattern V4 found on the seen data.
  * It does not survive Holm (0.22).
* **Realignment (= the shipped MAJOR signal, before cooldown) and continuation separately**: no
  evaluable cell passes. Tables are in `h1r_H.md`.

### The register's target cell: 4H crypto bullish continuation

* Holdout: n = 805, mean excess over S **+0.451 [+0.092, +0.741]**, median **−0.441**.
* The pre-registered rule rejects if the CI includes 0 **or the median ≤ 0**. The median is −0.44,
  so it is **REJECTED**, the same outcome as stage D (+0.749 [+0.424, +0.973], median −0.327).
* The positive mean replicated, and so did the negative median. Most continuation breaks
  underperform the average state candle; a minority of very large runs carries the mean.

## What this means for the indicator

On new instruments, the HTF-direction structure break does not credibly improve on simply being
in the HTF state, and does not beat a 20-candle momentum trigger. This is the third independent
look (V3, V4, V4.1 holdout) to find no robust incremental value in the structure break.

Limitations:
* B and M are each a single, untuned definition.
* Most non-crypto break cells have 100–700 events, so effects of about ±0.2 ATR cannot be
  excluded there.
* Same calendar period as the seen data (see the pre-registration §0).
