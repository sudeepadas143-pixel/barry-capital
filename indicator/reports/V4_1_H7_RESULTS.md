# V4.1 H7 results: volatility compression → expansion

Two separate claims, two separate decisions (pre-registration §4, §6):

| claim | decision (holdout) | one-line reason |
|---|---|---|
| **H7v**: breakouts from compression are followed by more realised range than other compressed candles | **INCONCLUSIVE** | passes in one group only (1H crypto); the rule needs ≥ 2 groups in one TF |
| **H7d**: the breakout direction predicts the direction of the move | **INCONCLUSIVE** | no cell passes on either side; pooled CIs too wide to reject |

## Definitions (fixed before any outcome was computed)

* **Compressed candle**: ATR%(14) below the 33.3rd percentile of its previous 200 candles.
* **Event**: the first close above (up event) or below (down event) the high/low box of a run of
  ≥ k compressed candles. k is 24 on 1H, 12 on 4H, 10 on 1D and 6 on 1W. One event per episode.
* **H7v outcome**: log(mean true range over the next H candles / ATR at the event). Primary
  benchmark **L** = all compressed candles of the same instrument.
* **H7m outcome** (secondary): |net move over H| in ATR, against L.
* **H7d outcome**: r_h in the breakout direction. Primary benchmark **L_d** = compressed candles
  of the same instrument, scored in the same direction. Up and down events are tested
  separately; expansion is not assumed to be bullish or bearish.
* **Minimum effect of interest**: 0.05 log-range (≈ 5%) for H7v; 0.10 ATR for H7d.

## H7v: realised range after the breakout (holdout)

Mean excess log-range vs L [95% CI]:

| TF | crypto | equities | commodities | rates & FX | pooled |
|---|---|---|---|---|---|
| 1H | **+0.091 [+0.076, +0.106]**, Holm 0.002, median +0.068, 3/3 spans → **passes** | −0.016 [−0.051, +0.025] | −0.053 [−0.102, −0.004] (n = 76, not evaluable) | −0.015 [−0.042, +0.009] | +0.070 [+0.057, +0.085] |
| 4H | +0.039 [+0.029, +0.051], Holm 0.002, below the minimum effect | −0.003 [−0.025, +0.020] | n = 59, not evaluable | +0.013 [−0.007, +0.035] | +0.031 [+0.021, +0.043] |
| 1D | +0.056 [+0.009, +0.096], Holm 0.08, median −0.001 | +0.008 [−0.002, +0.017] | +0.010 [−0.004, +0.024] | +0.015 [−0.001, +0.033] | +0.017 [+0.008, +0.026] |
| 1W | n = 16, not evaluable | +0.017 [+0.000, +0.035] | n = 78, not evaluable | +0.047 [+0.017, +0.084], Holm 0.004, median −0.012 | +0.032 [+0.018, +0.049] |

What the numbers say:

* **Crypto (1H, 4H, 1D).** Breakouts from compression *are* followed by more range than other
  compressed candles. The 1H effect (+9.1% realised range) is consistent across all three
  chronological spans and matches stage D (+0.107 [+0.096, +0.119]).
* **Equities, commodities, rates & FX.** At 1H/4H, the breakout adds nothing over simply being
  compressed: volatility mean-reverts upward either way. At 1D/1W the effects are about 1–5%,
  below the pre-set minimum, and their medians are ≤ 0.
* **The rule's verdict.** One group passing, in one TF, is not the ≥ 2 groups the rule requires.
  Under the global Holm across all four families, the 1H crypto, 4H crypto and 1W rates/FX
  cells stay significant, but only 1H crypto clears the minimum effect.

H7m, the absolute net move: 1H crypto +0.315 ATR [+0.180, +0.450] above compressed candles,
but with a median of −0.495. A few large moves follow some breakouts; the typical breakout
travels less far than a typical compressed candle.

## H7d: does the breakout direction predict the move? (holdout)

Mean excess r_h vs L_d [95% CI]. "Up" = bullish breakout, "down" = bearish breakout.

| TF | group | up | down |
|---|---|---|---|
| 1H | crypto | −0.179 [−0.494, +0.122] | +0.046 [−0.240, +0.327] |
| 1H | equities | +0.081 [−0.593, +0.578] | +0.587 [−0.151, +1.221] |
| 1H | rates & FX | +0.449 [−0.434, +1.246] | −0.144 [−0.968, +0.659] |
| 4H | crypto | +0.332 [−0.049, +0.710] (Holm 0.95) | +0.194 [−0.240, +0.607] |
| 1D | equities | +0.054 [−0.206, +0.295] | −0.147 [−0.544, +0.201] |
| 1D | rates & FX | +0.158 [−0.220, +0.559] | −0.088 [−0.541, +0.347] |
| 1W | equities | +0.081 [−0.319, +0.305] | −0.252 [−0.803, +0.116] |
| pooled 1H / 4H / 1D / 1W | all | −0.102 / +0.215 / +0.121 / +0.126 | +0.093 / +0.114 / −0.061 / +0.082 |

* No cell is significant after Holm, and no group has both directions positive in the same TF
  at the required strength.
* The intervals are wide: 22 evaluable tests with typical CI half-widths of 0.3–0.8 ATR. The
  data cannot rule out a 0.1–0.3 ATR directional effect, so the result is **INCONCLUSIVE** rather
  than REJECT.
* Point estimates scatter on both sides of zero with no pattern by group or direction. This is
  what no directional information looks like.
* The secondary "exit on a close back inside the box" outcome changes nothing; its means and
  medians are in `reports/v41_tables/h7_H.md`.

## Stage D (seen symbols, exploratory)

* H7v passes on 1H crypto, 1D crypto, 1W commodities and 1W rates/FX. The 1W pair met the
  ≥ 2-group rule there, so stage D alone would have given "RETAIN".
* **That 1W pair did not replicate on the holdout.** 1W commodities is not evaluable (n = 78);
  1W rates/FX falls below the minimum effect with a negative median. This is exactly why
  decisions were tied to stage H.
* H7d: nothing passed in stage D either.

## Limitations

* The compression definition (33.3 percentile, 200-candle lookback, fixed k) was not tuned; other
  reasonable definitions were not tried, by design.
* Range expansion after compression partly reflects ATR's own mean reversion. Benchmark L
  controls for that; benchmark U (all candles) gives much larger, uninformative "effects".
* Non-crypto intraday is ~35 months, and commodity intraday events are too few to evaluate.
* Full tables: `reports/v41_tables/h7_H.md` (holdout) and `h7_D.md` (seen symbols).
