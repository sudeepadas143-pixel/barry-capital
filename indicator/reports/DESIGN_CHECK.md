# Design check (development data only)

With-HTF breaks (continuation + realignment) on the 30 dev symbols before each holdout.

## crypto

| TF | split | n | mean r_h [95% CI] |
|---|---|---:|---:|
| 1H | one HTF agrees | 115 | -0.266 [-1.09, +0.43] |
| 1H | both HTFs agree | 10907 | +0.039 [-0.10, +0.19] |
| 1H | core 0-1 | 701 | +0.181 [-0.16, +0.53] |
| 1H | core 2 | 2027 | -0.011 [-0.31, +0.27] |
| 1H | core 3 | 4312 | -0.074 [-0.24, +0.09] |
| 1H | core 4 | 4008 | +0.153 [-0.05, +0.36] |
| 1H | both − one (90% CI) | | +0.305 [-0.39, +1.09] |
| 1H | core ≥3 − core ≤2 (90% CI) | | -0.003 [-0.20, +0.19] |
| 4H | one HTF agrees | 171 | +1.314 [+0.10, +2.31] |
| 4H | both HTFs agree | 2380 | +0.445 [+0.05, +0.85] |
| 4H | core 0-1 | 216 | +0.308 [-0.48, +1.02] |
| 4H | core 2 | 547 | +1.054 [+0.57, +1.54] |
| 4H | core 3 | 1026 | +0.042 [-0.43, +0.54] |
| 4H | core 4 | 795 | +0.772 [+0.21, +1.36] |
| 4H | both − one (90% CI) | | -0.870 [-1.73, +0.09] |
| 4H | core ≥3 − core ≤2 (90% CI) | | -0.482 [-0.90, -0.06] |
| 1D | one HTF agrees | 141 | +1.015 [+0.06, +2.01] |
| 1D | both HTFs agree | 278 | +1.126 [-0.02, +2.30] |
| 1D | core 0-1 | 41 | +2.966 [-0.10, +7.99] |
| 1D | core 2 | 116 | +0.174 [-0.69, +1.07] |
| 1D | core 3 | 183 | +1.471 [+0.60, +2.30] |
| 1D | core 4 | 138 | +0.856 [-0.09, +1.79] |
| 1D | both − one (90% CI) | | +0.111 [-1.18, +1.43] |
| 1D | core ≥3 − core ≤2 (90% CI) | | +0.303 [-0.97, +1.39] |
| 1W | one HTF agrees | 55 | +2.887 [-0.81, +8.03] |
| 1W | core 2 | 24 | +0.839 [-0.43, +2.40] |
| 1W | core 3 | 38 | +3.181 [-0.46, +8.28] |
| 1W | both − one (90% CI) | | +nan [+nan, +nan] |
| 1W | core ≥3 − core ≤2 (90% CI) | | +2.990 [-0.57, +7.45] |
| all | one HTF agrees | 482 | +1.029 [+0.25, +1.92] |
| all | both HTFs agree | 13566 | +0.132 [-0.04, +0.32] |
| all | core 0-1 | 969 | +0.322 [-0.01, +0.68] |
| all | core 2 | 2714 | +0.219 [-0.06, +0.49] |
| all | core 3 | 5559 | +0.020 [-0.19, +0.23] |
| all | core 4 | 4957 | +0.285 [+0.07, +0.52] |
| all | both − one (90% CI) | | -0.897 [-1.58, -0.27] |
| all | core ≥3 − core ≤2 (90% CI) | | -0.101 [-0.28, +0.09] |

## non-crypto

| TF | split | n | mean r_h [95% CI] |
|---|---|---:|---:|
| 1H | one HTF agrees | 54 | +2.112 [-0.27, +2.59] |
| 1H | both HTFs agree | 2747 | -0.103 [-0.32, +0.12] |
| 1H | core 0-1 | 300 | -0.149 [-0.66, +0.33] |
| 1H | core 2 | 934 | -0.099 [-0.48, +0.30] |
| 1H | core 3 | 1092 | -0.150 [-0.46, +0.17] |
| 1H | core 4 | 475 | +0.279 [-0.15, +0.74] |
| 1H | both − one (90% CI) | | -2.215 [-2.72, +0.25] |
| 1H | core ≥3 − core ≤2 (90% CI) | | +0.091 [-0.24, +0.46] |
| 4H | both HTFs agree | 710 | +0.033 [-0.40, +0.48] |
| 4H | core 0-1 | 90 | +0.157 [-0.85, +1.21] |
| 4H | core 2 | 286 | -0.137 [-0.73, +0.49] |
| 4H | core 3 | 268 | +0.113 [-0.51, +0.79] |
| 4H | core 4 | 66 | +0.280 [-0.90, +1.46] |
| 4H | both − one (90% CI) | | +nan [+nan, +nan] |
| 4H | core ≥3 − core ≤2 (90% CI) | | +0.213 [-0.67, +1.05] |
| 1D | one HTF agrees | 405 | +0.632 [+0.17, +1.07] |
| 1D | both HTFs agree | 6649 | +0.286 [+0.15, +0.42] |
| 1D | core 0-1 | 1634 | +0.307 [+0.09, +0.52] |
| 1D | core 2 | 2644 | +0.232 [+0.05, +0.40] |
| 1D | core 3 | 2173 | +0.393 [+0.20, +0.59] |
| 1D | core 4 | 727 | +0.203 [-0.08, +0.49] |
| 1D | both − one (90% CI) | | -0.346 [-0.72, +0.03] |
| 1D | core ≥3 − core ≤2 (90% CI) | | +0.085 [-0.09, +0.25] |
| 1W | one HTF agrees | 221 | +0.788 [+0.27, +1.25] |
| 1W | both HTFs agree | 1321 | +0.547 [+0.35, +0.75] |
| 1W | core 0-1 | 264 | +0.248 [-0.11, +0.60] |
| 1W | core 2 | 596 | +0.505 [+0.23, +0.76] |
| 1W | core 3 | 607 | +0.671 [+0.42, +0.92] |
| 1W | core 4 | 189 | +0.903 [+0.50, +1.29] |
| 1W | both − one (90% CI) | | -0.240 [-0.66, +0.20] |
| 1W | core ≥3 − core ≤2 (90% CI) | | +0.300 [+0.06, +0.54] |
| all | one HTF agrees | 680 | +0.800 [+0.42, +1.19] |
| all | both HTFs agree | 11427 | +0.207 [+0.10, +0.32] |
| all | core 0-1 | 2288 | +0.235 [+0.05, +0.42] |
| all | core 2 | 4460 | +0.175 [+0.01, +0.35] |
| all | core 3 | 4140 | +0.272 [+0.12, +0.44] |
| all | core 4 | 1457 | +0.322 [+0.09, +0.56] |
| all | both − one (90% CI) | | -0.593 [-0.91, -0.28] |
| all | core ≥3 − core ≤2 (90% CI) | | +0.090 [-0.07, +0.24] |

## counter-HTF reversals, by TF

| TF | market | n | mean r_h [95% CI] |
|---|---|---:|---:|
| 1H | crypto | 9351 | -0.306 [-0.38, -0.22] |
| 1H | non-crypto | 1942 | -0.238 [-0.44, -0.02] |
| 4H | crypto | 2274 | +0.066 [-0.17, +0.31] |
| 4H | non-crypto | 518 | -0.426 [-0.80, +0.02] |
| 1D | crypto | 274 | +0.281 [-0.35, +0.95] |
| 1D | non-crypto | 4161 | -0.234 [-0.38, -0.09] |
| 1W | crypto | 26 | +0.208 [-0.58, +0.89] |
| 1W | non-crypto | 794 | -0.324 [-0.55, -0.10] |

## Decision taken from this check (development data only, before any fresh-symbol run)

1. Screening kept no add-on condition, and the combined count of the v1 core conditions
   is not monotonic in outcome here. Evidence conditions therefore do not gate signals;
   they are still computed and shown in the label tooltip as context.
2. The HTF relation is the dimension that separates outcomes: with-HTF breaks are positive,
   counter-HTF reversals are negative on 1H (both markets) and on every non-crypto timeframe.
   Counter-HTF breaks never signal. A counter-HTF change of character is displayed as a
   WATCH (possible HTF reversal developing), evaluated separately, never MAJOR.
3. "Both HTFs agree" did not beat "one agrees, the other flat" (pooled, both markets it was
   worse). The 1D/1W "both must agree" rule is therefore not used; every profile uses
   "HTF1 + HTF2 >= 1 and neither against".
4. MAJOR = REALIGNMENT (the MTF structure turns back into the HTF direction after a
   counter move): one per pullback cycle by construction, the best class mean in both
   markets. CONFIRMED = CONTINUATION break with the HTFs. Cooldown as before.
5. Nothing is fitted. There are no tuned thresholds left in v2.
