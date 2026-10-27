# v3 validation

Pre-registered in [`PREREG_V3.md`](PREREG_V3.md). All 70 symbols, signals measured from the next
candle's open over H candles (1H 24, 4H 30, 1D 20, 1W 13), r_h in ATR after costs, 95% month-
cluster CIs, random = same symbols/dates/count/side, DSR with 60 trials. Bullish and bearish
are evaluated separately.

## Verdicts for the shipped MAJOR signal (C2)

| TF / side / group | verdict | evidence |
|---|---|---|
| 1H / bullish / crypto | **PROMISING** | n=4348, r +0.27 [+0.02, +0.49] vs random -0.12, p 0.005 (Holm 0.139), DSR 0.00, positive in 3/6 periods, C0 -0.10 |
| 1H / bullish / equities | **UNPROVEN** | n=630, r -0.10 [-0.53, +0.35] vs random +0.27, p 0.975 (Holm 1.000), DSR 0.15, positive in 3/6 periods, C0 +0.13 |
| 1H / bullish / commodities | **UNPROVEN** | n=156, r +0.77 [-0.11, +1.61] vs random +0.32, p 0.144 (Holm 1.000), DSR 0.33, positive in 5/6 periods, C0 +0.22 |
| 1H / bullish / rates_fx | **UNPROVEN** | n=622, r -0.33 [-0.69, -0.01] vs random -0.25, p 0.731 (Holm 1.000), DSR 0.00, positive in 2/6 periods, C0 -0.31 |
| 1H / bearish / crypto | **UNPROVEN** | n=5386, r -0.13 [-0.34, +0.07] vs random -0.25, p 0.010 (Holm 0.249), DSR 0.00, positive in 2/6 periods, C0 -0.27 |
| 1H / bearish / equities | **UNPROVEN** | n=415, r -0.68 [-1.13, -0.24] vs random -0.34, p 0.955 (Holm 1.000), DSR 0.00, positive in 0/6 periods, C0 -0.43 |
| 1H / bearish / commodities | **UNPROVEN** | n=118, r -0.79 [-1.46, -0.18] vs random -0.51, p 0.697 (Holm 1.000), DSR 0.00, positive in 1/6 periods, C0 -0.72 |
| 1H / bearish / rates_fx | **UNPROVEN** | n=474, r -0.15 [-0.61, +0.29] vs random -0.23, p 0.338 (Holm 1.000), DSR 0.00, positive in 2/6 periods, C0 -0.31 |
| 4H / bullish / crypto | **PROMISING** | n=983, r +0.84 [+0.23, +1.48] vs random +0.26, p 0.005 (Holm 0.139), DSR 0.18, positive in 4/6 periods, C0 +0.55 |
| 4H / bullish / equities | **UNPROVEN** | n=229, r +0.38 [-0.53, +1.18] vs random +0.85, p 0.915 (Holm 1.000), DSR 0.39, positive in 4/6 periods, C0 +0.45 |
| 4H / bullish / commodities | **UNPROVEN** | n=48, r +1.51 [-0.27, +3.35] vs random +1.46, p 0.468 (Holm 1.000), DSR 0.77, positive in 4/6 periods, C0 +1.12 |
| 4H / bullish / rates_fx | **UNPROVEN** | n=197, r -0.66 [-1.33, -0.01] vs random -0.20, p 0.950 (Holm 1.000), DSR 0.00, positive in 2/6 periods, C0 -0.31 |
| 4H / bearish / crypto | **PROMISING** | n=1605, r +0.01 [-0.50, +0.55] vs random -0.34, p 0.005 (Holm 0.139), DSR 0.00, positive in 4/6 periods, C0 -0.12 |
| 4H / bearish / equities | **UNPROVEN** | n=64, r +0.05 [-1.20, +1.43] vs random -0.20, p 0.333 (Holm 1.000), DSR 0.05, positive in 4/6 periods, C0 -0.83 |
| 4H / bearish / commodities | **UNPROVEN** | n=23 MAJOR signals (< 30) |
| 4H / bearish / rates_fx | **UNPROVEN** | n=109, r +0.27 [-0.81, +1.46] vs random -0.05, p 0.174 (Holm 1.000), DSR 0.00, positive in 3/6 periods, C0 -0.32 |
| 1D / bullish / crypto | **UNPROVEN** | n=177, r +0.14 [-0.74, +0.99] vs random +0.64, p 0.940 (Holm 1.000), DSR 0.17, positive in 2/6 periods, C0 +1.30 |
| 1D / bullish / equities | **UNPROVEN** | n=849, r +0.56 [+0.11, +0.97] vs random +0.51, p 0.313 (Holm 1.000), DSR 0.40, positive in 5/6 periods, C0 +0.37 |
| 1D / bullish / commodities | **UNPROVEN** | n=125, r -0.15 [-1.00, +0.69] vs random +0.20, p 0.831 (Holm 1.000), DSR 0.06, positive in 1/6 periods, C0 +0.12 |
| 1D / bullish / rates_fx | **UNPROVEN** | n=313, r +0.39 [+0.03, +0.77] vs random +0.17, p 0.119 (Holm 1.000), DSR 0.45, positive in 5/6 periods, C0 +0.13 |
| 1D / bearish / crypto | **UNPROVEN** | n=389, r -0.20 [-1.09, +0.57] vs random -0.51, p 0.109 (Holm 1.000), DSR 0.00, positive in 2/6 periods, C0 -0.19 |
| 1D / bearish / equities | **UNPROVEN** | n=230, r -0.43 [-1.06, +0.19] vs random -0.43, p 0.522 (Holm 1.000), DSR 0.00, positive in 1/6 periods, C0 -0.70 |
| 1D / bearish / commodities | **UNPROVEN** | n=160, r -0.39 [-0.92, +0.14] vs random -0.03, p 0.905 (Holm 1.000), DSR 0.00, positive in 1/6 periods, C0 -0.26 |
| 1D / bearish / rates_fx | **UNPROVEN** | n=194, r -0.04 [-0.52, +0.44] vs random -0.08, p 0.423 (Holm 1.000), DSR 0.02, positive in 3/6 periods, C0 -0.21 |
| 1W / bullish / crypto | **UNPROVEN** | n=16 MAJOR signals (< 30) |
| 1W / bullish / equities | **UNPROVEN** | n=196, r +0.77 [+0.27, +1.24] vs random +0.75, p 0.438 (Holm 1.000), DSR 0.95, positive in 5/6 periods, C0 +0.67 |
| 1W / bullish / commodities | **UNPROVEN** | n=23 MAJOR signals (< 30) |
| 1W / bullish / rates_fx | **UNPROVEN** | n=67, r +0.35 [-0.49, +1.07] vs random +0.37, p 0.522 (Holm 1.000), DSR 0.31, positive in 4/6 periods, C0 +0.29 |
| 1W / bearish / crypto | **UNPROVEN** | n=49, r -0.96 [-3.48, +0.26] vs random -1.29, p 0.542 (Holm 1.000), DSR 0.00, positive in 1/4 periods, C0 -0.39 |
| 1W / bearish / equities | **UNPROVEN** | n=22 MAJOR signals (< 30) |
| 1W / bearish / commodities | **UNPROVEN** | n=56, r -0.05 [-0.95, +0.86] vs random -0.05, p 0.493 (Holm 1.000), DSR 0.06, positive in 2/5 periods, C0 -0.11 |
| 1W / bearish / rates_fx | **UNPROVEN** | n=43, r -0.27 [-0.87, +0.32] vs random -0.06, p 0.736 (Holm 1.000), DSR 0.03, positive in 1/6 periods, C0 -0.28 |

## 1H  (70 symbols, 2020-01-01 → 2026-10-28)

### Bearish representation

| group | breaks bull / bear | MAJOR bull / bear | suppressed counter-HTF reversals bull / bear |
|---|---:|---:|---:|
| crypto | 43791 / 42362 | 4348 / 5386 | 15468 / 14410 |
| equities | 4672 / 3972 | 630 / 415 | 1228 / 1444 |
| commodities | 1390 / 1165 | 156 / 118 | 366 / 408 |
| rates_fx | 5152 / 4776 | 622 / 474 | 1638 / 1788 |
| all | 55005 / 52275 | 5756 / 6393 | 18700 / 18050 |

### bullish · crypto

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 43791 | 31% | 67% | -0.10 [-0.27, +0.06] | -0.43 | -0.07 | 2.08 / 2.19 | -0.12 | 0.179 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 13537 | 32% | 67% | +0.15 [-0.05, +0.34] | -0.43 | +0.29 | 2.29 / 2.34 | -0.12 | 0.005 | 0.00 |
| C2 MAJOR (shipped) | 4348 | 34% | 64% | +0.27 [+0.02, +0.49] | -0.21 | +0.39 | 2.41 / 2.13 | -0.12 | 0.005 | 0.00 |
| C3 CONFIRMED | 9189 | 31% | 69% | +0.10 [-0.13, +0.30] | -0.52 | +0.24 | 2.23 / 2.44 | -0.12 | 0.005 | 0.00 |
| C4 MAJOR + acceptance | 3110 | 33% | 66% | +0.36 [+0.11, +0.58] | -0.15 | +0.48 | 2.37 / 2.09 | -0.11 | 0.005 | 0.00 |
| C5 with-HTF + acceptance | 10187 | 31% | 68% | +0.20 [-0.01, +0.38] | -0.39 | +0.33 | 2.28 / 2.29 | -0.11 | 0.005 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 15468 | 31% | 66% | -0.32 [-0.47, -0.16] | -0.40 | -0.36 | 1.93 / 2.01 | -0.12 | 1.000 | 0.00 |
| B1 EMA 20/50 cross | 13807 | 33% | 65% | -0.06 [-0.23, +0.10] | -0.22 | +0.02 | 2.10 / 1.99 | -0.12 | 0.045 | 0.00 |
| B2 Supertrend flip | 16319 | 32% | 65% | -0.12 [-0.29, +0.05] | -0.29 | -0.08 | 2.07 / 2.06 | -0.12 | 0.542 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.25 [+0.15, +0.36]; realignment only +0.12 [-0.00, +0.23]; acceptance on MAJOR +0.09 [+0.01, +0.17]; acceptance on with-HTF +0.05 [+0.01, +0.08]; suppressed reversals vs MAJOR -0.59 [-0.78, -0.39]
PBO across C0–C6: **0.00** (352 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.05.
Purged CPCV, event-weighted (post-hoc): picks {'C5': 6, 'C1': 6, 'C4': 3}; mean OOS rank of the pick 0.41.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 13, 'C4': 2}; mean OOS r_h of the pick -0.13; mean OOS rank of the pick 0.08 (0 = best, 1 = worst); path means [-0.07, -0.23, -0.11, -0.17, -0.07].

### bullish · equities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 4672 | 35% | 64% | +0.13 [-0.16, +0.40] | +0.20 | +0.09 | 2.51 / 2.27 | +0.23 | 0.935 | 0.13 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 2234 | 37% | 63% | +0.16 [-0.15, +0.45] | +0.21 | +0.09 | 2.56 / 2.31 | +0.24 | 0.811 | 0.23 |
| C2 MAJOR (shipped) | 630 | 35% | 64% | -0.10 [-0.53, +0.35] | +0.12 | -0.06 | 2.49 / 2.18 | +0.27 | 0.975 | 0.15 |
| C3 CONFIRMED | 1604 | 37% | 62% | +0.26 [-0.07, +0.57] | +0.27 | +0.15 | 2.58 / 2.37 | +0.25 | 0.473 | 0.20 |
| C4 MAJOR + acceptance | 509 | 37% | 63% | -0.17 [-0.66, +0.29] | +0.01 | -0.06 | 2.39 / 2.19 | +0.27 | 0.985 | 0.14 |
| C5 with-HTF + acceptance | 1878 | 36% | 63% | +0.18 [-0.13, +0.45] | +0.30 | +0.11 | 2.50 / 2.25 | +0.25 | 0.796 | 0.13 |
| C6 counter-HTF reversals (suppressed) | 1228 | 33% | 66% | +0.12 [-0.25, +0.49] | +0.24 | +0.12 | 2.36 / 2.20 | +0.20 | 0.751 | 0.07 |
| B1 EMA 20/50 cross | 1224 | 38% | 60% | +0.27 [-0.16, +0.67] | +0.37 | +0.17 | 2.57 / 2.21 | +0.19 | 0.284 | 0.32 |
| B2 Supertrend flip | 2070 | 34% | 65% | +0.23 [-0.07, +0.52] | +0.31 | +0.17 | 2.53 / 2.20 | +0.23 | 0.502 | 0.51 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.03 [-0.10, +0.16]; realignment only -0.26 [-0.53, +0.01]; acceptance on MAJOR -0.08 [-0.26, +0.10]; acceptance on with-HTF +0.02 [-0.09, +0.12]; suppressed reversals vs MAJOR +0.21 [-0.15, +0.62]
PBO across C0–C6: **0.98** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.69.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 8, 'C3': 7}; mean OOS rank of the pick 0.51.
Purged CPCV, best-in-train config chosen per split: picks {'C4': 3, 'C6': 3, 'C2': 3, 'C3': 3, 'C1': 2, 'C0': 1}; mean OOS r_h of the pick -0.30; mean OOS rank of the pick 0.82 (0 = best, 1 = worst); path means [-0.38, -0.42, -0.18, -0.29, -0.23].

### bullish · commodities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 1390 | 39% | 61% | +0.22 [-0.13, +0.60] | +0.17 | +0.12 | 2.98 / 2.53 | +0.29 | 0.711 | 0.15 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 604 | 37% | 62% | +0.17 [-0.30, +0.62] | +0.10 | +0.07 | 3.13 / 2.65 | +0.29 | 0.751 | 0.08 |
| C2 MAJOR (shipped) | 156 | 35% | 65% | +0.77 [-0.11, +1.61] | +0.63 | +0.37 | 3.38 / 2.03 | +0.32 | 0.144 | 0.33 |
| C3 CONFIRMED | 448 | 38% | 62% | -0.04 [-0.70, +0.57] | -0.09 | -0.03 | 3.05 / 2.80 | +0.30 | 0.900 | 0.09 |
| C4 MAJOR + acceptance | 128 | 38% | 61% | +0.49 [-0.60, +1.62] | +0.62 | +0.16 | 2.84 / 2.28 | +0.31 | 0.348 | 0.20 |
| C5 with-HTF + acceptance | 521 | 38% | 61% | +0.28 [-0.16, +0.73] | -0.02 | +0.16 | 3.12 / 2.61 | +0.33 | 0.572 | 0.18 |
| C6 counter-HTF reversals (suppressed) | 366 | 37% | 62% | +0.38 [-0.10, +0.87] | +0.38 | +0.13 | 2.85 / 2.16 | +0.22 | 0.244 | 0.50 |
| B1 EMA 20/50 cross | 337 | 37% | 62% | +0.26 [-0.31, +0.87] | -0.05 | +0.25 | 2.96 / 2.45 | +0.24 | 0.483 | 0.32 |
| B2 Supertrend flip | 682 | 38% | 61% | +0.43 [-0.07, +0.95] | +0.27 | +0.07 | 2.88 / 2.17 | +0.24 | 0.204 | 0.56 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate -0.06 [-0.23, +0.12]; realignment only +0.60 [-0.15, +1.39]; acceptance on MAJOR -0.27 [-0.58, +0.07]; acceptance on with-HTF +0.12 [-0.05, +0.28]; suppressed reversals vs MAJOR -0.39 [-1.13, +0.42]
PBO across C0–C6: **0.58** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.61.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 12, 'C2': 3}; mean OOS rank of the pick 0.53.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 7, 'C2': 5, 'C5': 3}; mean OOS r_h of the pick -0.10; mean OOS rank of the pick 0.63 (0 = best, 1 = worst); path means [-0.38, -0.3, 0.04, -0.1, 0.2].

### bullish · rates_fx

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 5152 | 31% | 67% | -0.31 [-0.44, -0.18] | -0.23 | -0.04 | 2.05 / 2.24 | -0.26 | 0.871 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 1751 | 33% | 65% | -0.35 [-0.56, -0.16] | -0.19 | -0.05 | 2.14 / 2.29 | -0.25 | 0.896 | 0.00 |
| C2 MAJOR (shipped) | 622 | 33% | 65% | -0.33 [-0.69, -0.01] | -0.29 | -0.05 | 2.08 / 2.40 | -0.25 | 0.731 | 0.00 |
| C3 CONFIRMED | 1129 | 33% | 66% | -0.37 [-0.63, -0.13] | -0.14 | -0.06 | 2.20 / 2.21 | -0.26 | 0.801 | 0.00 |
| C4 MAJOR + acceptance | 453 | 33% | 65% | -0.19 [-0.52, +0.12] | -0.24 | -0.03 | 2.03 / 2.14 | -0.25 | 0.343 | 0.00 |
| C5 with-HTF + acceptance | 1355 | 33% | 66% | -0.32 [-0.56, -0.10] | -0.12 | -0.05 | 2.15 / 2.21 | -0.24 | 0.756 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 1638 | 29% | 69% | -0.21 [-0.40, -0.02] | -0.25 | -0.03 | 2.09 / 2.18 | -0.26 | 0.284 | 0.00 |
| B1 EMA 20/50 cross | 1505 | 32% | 66% | -0.17 [-0.37, +0.04] | -0.07 | -0.01 | 2.09 / 2.02 | -0.27 | 0.154 | 0.00 |
| B2 Supertrend flip | 2162 | 31% | 68% | -0.29 [-0.49, -0.07] | -0.27 | -0.04 | 2.03 / 2.16 | -0.28 | 0.547 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate -0.04 [-0.18, +0.09]; realignment only +0.03 [-0.22, +0.25]; acceptance on MAJOR +0.14 [-0.02, +0.31]; acceptance on with-HTF +0.04 [-0.05, +0.12]; suppressed reversals vs MAJOR +0.12 [-0.20, +0.45]
PBO across C0–C6: **0.18** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.44.
Purged CPCV, event-weighted (post-hoc): picks {'C4': 15}; mean OOS rank of the pick 0.04.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 6, 'C2': 6, 'C4': 3}; mean OOS r_h of the pick -0.41; mean OOS rank of the pick 0.59 (0 = best, 1 = worst); path means [-0.42, -0.36, -0.44, -0.4, -0.46].

### bullish · all

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 55005 | 32% | 66% | -0.09 [-0.23, +0.03] | -0.35 | -0.05 | 2.13 / 2.21 | -0.09 | 0.552 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 18126 | 33% | 66% | +0.10 [-0.06, +0.26] | -0.31 | +0.22 | 2.33 / 2.34 | -0.07 | 0.005 | 0.00 |
| C2 MAJOR (shipped) | 5756 | 34% | 64% | +0.18 [-0.03, +0.36] | -0.16 | +0.30 | 2.38 / 2.15 | -0.08 | 0.005 | 0.00 |
| C3 CONFIRMED | 12370 | 32% | 67% | +0.07 [-0.10, +0.23] | -0.38 | +0.19 | 2.30 / 2.42 | -0.07 | 0.005 | 0.00 |
| C4 MAJOR + acceptance | 4200 | 34% | 65% | +0.24 [+0.03, +0.43] | -0.13 | +0.35 | 2.35 / 2.12 | -0.06 | 0.005 | 0.00 |
| C5 with-HTF + acceptance | 13941 | 32% | 67% | +0.15 [-0.01, +0.31] | -0.27 | +0.26 | 2.31 / 2.29 | -0.06 | 0.005 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 18700 | 31% | 66% | -0.27 [-0.41, -0.13] | -0.34 | -0.29 | 1.98 / 2.03 | -0.11 | 1.000 | 0.00 |
| B1 EMA 20/50 cross | 16873 | 33% | 64% | -0.04 [-0.19, +0.10] | -0.17 | +0.03 | 2.15 / 2.01 | -0.10 | 0.020 | 0.00 |
| B2 Supertrend flip | 21233 | 32% | 65% | -0.09 [-0.22, +0.06] | -0.21 | -0.05 | 2.12 / 2.08 | -0.09 | 0.438 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.20 [+0.12, +0.28]; realignment only +0.07 [-0.02, +0.16]; acceptance on MAJOR +0.06 [-0.01, +0.13]; acceptance on with-HTF +0.04 [+0.01, +0.08]; suppressed reversals vs MAJOR -0.45 [-0.61, -0.28]
PBO across C0–C6: **0.01** (352 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.08.
Purged CPCV, event-weighted (post-hoc): picks {'C5': 7, 'C1': 5, 'C4': 3}; mean OOS rank of the pick 0.43.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 13, 'C4': 2}; mean OOS r_h of the pick -0.12; mean OOS rank of the pick 0.10 (0 = best, 1 = worst); path means [-0.07, -0.22, -0.08, -0.17, -0.07].

### bearish · crypto

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 42362 | 33% | 65% | -0.27 [-0.42, -0.11] | -0.46 | -8.72 | 2.10 / 2.06 | -0.25 | 0.756 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 14988 | 34% | 65% | -0.18 [-0.35, -0.01] | -0.56 | -23.56 | 2.21 / 2.15 | -0.24 | 0.015 | 0.00 |
| C2 MAJOR (shipped) | 5386 | 33% | 65% | -0.13 [-0.34, +0.07] | -0.42 | -0.15 | 2.22 / 2.05 | -0.25 | 0.010 | 0.00 |
| C3 CONFIRMED | 9602 | 34% | 64% | -0.20 [-0.42, +0.01] | -0.64 | -36.69 | 2.21 / 2.21 | -0.24 | 0.179 | 0.00 |
| C4 MAJOR + acceptance | 3793 | 34% | 63% | -0.11 [-0.35, +0.11] | -0.43 | -0.17 | 2.19 / 2.00 | -0.24 | 0.020 | 0.00 |
| C5 with-HTF + acceptance | 11271 | 34% | 64% | -0.19 [-0.39, -0.01] | -0.58 | -211.62 | 2.17 / 2.10 | -0.24 | 0.119 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 14410 | 32% | 65% | -0.30 [-0.47, -0.12] | -0.30 | -0.54 | 2.02 / 1.93 | -0.26 | 0.816 | 0.00 |
| B1 EMA 20/50 cross | 13806 | 33% | 63% | -0.23 [-0.40, -0.07] | -0.29 | -0.39 | 2.03 / 1.90 | -0.26 | 0.254 | 0.00 |
| B2 Supertrend flip | 16314 | 31% | 66% | -0.31 [-0.49, -0.14] | -0.39 | -0.57 | 2.00 / 2.02 | -0.26 | 0.980 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.09 [+0.00, +0.18]; realignment only +0.05 [-0.09, +0.18]; acceptance on MAJOR +0.02 [-0.06, +0.11]; acceptance on with-HTF -0.02 [-0.08, +0.04]; suppressed reversals vs MAJOR -0.17 [-0.33, +0.00]
PBO across C0–C6: **0.00** (352 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.37.
Purged CPCV, event-weighted (post-hoc): picks {'C4': 12, 'C2': 3}; mean OOS rank of the pick 0.16.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 15}; mean OOS r_h of the pick -0.09; mean OOS rank of the pick 0.00 (0 = best, 1 = worst); path means [-0.09, -0.09, -0.09, -0.09, -0.09].

### bearish · equities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 3972 | 30% | 69% | -0.43 [-0.76, -0.09] | -0.51 | -0.30 | 2.13 / 2.71 | -0.38 | 0.701 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 1341 | 29% | 70% | -0.49 [-0.80, -0.19] | -0.76 | -0.44 | 1.95 / 2.73 | -0.34 | 0.886 | 0.00 |
| C2 MAJOR (shipped) | 415 | 30% | 69% | -0.68 [-1.13, -0.24] | -0.93 | -0.65 | 1.94 / 2.64 | -0.34 | 0.955 | 0.00 |
| C3 CONFIRMED | 926 | 28% | 70% | -0.41 [-0.82, -0.00] | -0.61 | -0.34 | 1.97 / 2.78 | -0.33 | 0.716 | 0.00 |
| C4 MAJOR + acceptance | 326 | 32% | 67% | -0.52 [-1.01, +0.02] | -0.57 | -0.51 | 2.08 / 2.56 | -0.34 | 0.701 | 0.00 |
| C5 with-HTF + acceptance | 1083 | 30% | 69% | -0.38 [-0.74, -0.04] | -0.54 | -0.34 | 2.02 / 2.59 | -0.34 | 0.617 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 1444 | 30% | 69% | -0.35 [-0.71, +0.04] | -0.46 | -0.19 | 2.23 / 2.66 | -0.41 | 0.284 | 0.00 |
| B1 EMA 20/50 cross | 1225 | 32% | 67% | -0.43 [-0.86, +0.01] | -0.42 | -0.22 | 2.33 / 2.60 | -0.40 | 0.602 | 0.00 |
| B2 Supertrend flip | 2056 | 33% | 66% | -0.36 [-0.69, -0.03] | -0.40 | -0.19 | 2.32 / 2.46 | -0.40 | 0.378 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate -0.07 [-0.27, +0.13]; realignment only -0.19 [-0.54, +0.17]; acceptance on MAJOR +0.16 [-0.04, +0.38]; acceptance on with-HTF +0.11 [-0.04, +0.27]; suppressed reversals vs MAJOR +0.33 [-0.11, +0.78]
PBO across C0–C6: **0.28** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.86.
Purged CPCV, event-weighted (post-hoc): picks {'C4': 10, 'C3': 5}; mean OOS rank of the pick 0.36.
Purged CPCV, best-in-train config chosen per split: picks {'C4': 10, 'C6': 3, 'C3': 1, 'C5': 1}; mean OOS r_h of the pick -0.63; mean OOS rank of the pick 0.34 (0 = best, 1 = worst); path means [-0.88, -0.57, -0.6, -0.67, -0.42].

### bearish · commodities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 1165 | 30% | 69% | -0.72 [-1.21, -0.29] | -0.61 | -0.45 | 2.19 / 2.82 | -0.54 | 0.866 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 434 | 29% | 70% | -0.65 [-1.14, -0.14] | -0.59 | -0.43 | 2.13 / 2.64 | -0.47 | 0.761 | 0.00 |
| C2 MAJOR (shipped) | 118 | 30% | 69% | -0.79 [-1.46, -0.18] | -0.96 | -0.46 | 1.92 / 2.70 | -0.51 | 0.697 | 0.00 |
| C3 CONFIRMED | 316 | 29% | 70% | -0.59 [-1.32, +0.12] | -0.53 | -0.41 | 2.18 / 2.64 | -0.45 | 0.687 | 0.00 |
| C4 MAJOR + acceptance | 99 | 29% | 70% | -1.01 [-1.73, -0.41] | -0.81 | -0.56 | 2.08 / 2.64 | -0.43 | 0.896 | 0.00 |
| C5 with-HTF + acceptance | 385 | 32% | 67% | -0.53 [-1.06, -0.04] | -0.57 | -0.41 | 2.15 / 2.57 | -0.48 | 0.597 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 408 | 28% | 71% | -0.74 [-1.37, -0.09] | -0.59 | -0.42 | 2.25 / 2.88 | -0.58 | 0.721 | 0.00 |
| B1 EMA 20/50 cross | 337 | 36% | 63% | -0.49 [-1.04, +0.07] | -0.18 | -0.20 | 2.35 / 2.45 | -0.54 | 0.483 | 0.00 |
| B2 Supertrend flip | 680 | 32% | 68% | -0.70 [-1.18, -0.24] | -0.52 | -0.31 | 2.25 / 2.65 | -0.57 | 0.796 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.08 [-0.18, +0.37]; realignment only -0.14 [-0.91, +0.55]; acceptance on MAJOR -0.23 [-0.54, +0.07]; acceptance on with-HTF +0.12 [-0.03, +0.27]; suppressed reversals vs MAJOR +0.05 [-0.66, +0.82]
PBO across C0–C6: **0.25** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.74.
Purged CPCV, event-weighted (post-hoc): picks {'C2': 9, 'C4': 4, 'C3': 2}; mean OOS rank of the pick 0.29.
Purged CPCV, best-in-train config chosen per split: picks {'C2': 14, 'C4': 1}; mean OOS r_h of the pick -0.43; mean OOS rank of the pick 0.11 (0 = best, 1 = worst); path means [-0.46, -0.46, -0.41, -0.41, -0.41].

### bearish · rates_fx

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 4776 | 33% | 66% | -0.31 [-0.51, -0.11] | -0.50 | -0.05 | 2.24 / 2.33 | -0.24 | 0.940 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 1287 | 36% | 63% | -0.15 [-0.53, +0.19] | -0.37 | -0.03 | 2.40 / 2.33 | -0.23 | 0.234 | 0.00 |
| C2 MAJOR (shipped) | 474 | 37% | 62% | -0.15 [-0.61, +0.29] | -0.39 | -0.02 | 2.47 / 2.23 | -0.23 | 0.338 | 0.00 |
| C3 CONFIRMED | 813 | 35% | 64% | -0.15 [-0.52, +0.21] | -0.35 | -0.04 | 2.35 / 2.39 | -0.21 | 0.328 | 0.00 |
| C4 MAJOR + acceptance | 343 | 32% | 67% | -0.36 [-0.78, +0.09] | -0.52 | -0.08 | 2.18 / 2.34 | -0.22 | 0.751 | 0.00 |
| C5 with-HTF + acceptance | 999 | 35% | 65% | -0.25 [-0.65, +0.11] | -0.34 | -0.05 | 2.30 / 2.32 | -0.23 | 0.572 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 1788 | 32% | 67% | -0.30 [-0.51, -0.08] | -0.48 | -0.04 | 2.21 / 2.27 | -0.26 | 0.682 | 0.00 |
| B1 EMA 20/50 cross | 1509 | 30% | 68% | -0.32 [-0.55, -0.08] | -0.48 | -0.04 | 2.09 / 2.32 | -0.26 | 0.672 | 0.00 |
| B2 Supertrend flip | 2154 | 31% | 67% | -0.21 [-0.43, -0.00] | -0.41 | -0.03 | 2.17 / 2.20 | -0.23 | 0.403 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.17 [-0.07, +0.39]; realignment only -0.00 [-0.18, +0.18]; acceptance on MAJOR -0.21 [-0.50, +0.11]; acceptance on with-HTF -0.10 [-0.25, +0.03]; suppressed reversals vs MAJOR -0.15 [-0.59, +0.27]
PBO across C0–C6: **0.06** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.57.
Purged CPCV, event-weighted (post-hoc): picks {'C2': 9, 'C3': 5, 'C1': 1}; mean OOS rank of the pick 0.29.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 9, 'C2': 6}; mean OOS r_h of the pick -0.35; mean OOS rank of the pick 0.31 (0 = best, 1 = worst); path means [-0.39, -0.17, -0.25, -0.47, -0.47].

### bearish · all

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 52275 | 33% | 66% | -0.29 [-0.43, -0.16] | -0.47 | -7.10 | 2.12 / 2.13 | -0.27 | 0.920 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 18050 | 33% | 65% | -0.21 [-0.37, -0.05] | -0.56 | -19.61 | 2.21 / 2.20 | -0.26 | 0.045 | 0.00 |
| C2 MAJOR (shipped) | 6393 | 33% | 65% | -0.18 [-0.37, +0.00] | -0.47 | -0.18 | 2.23 / 2.10 | -0.26 | 0.045 | 0.00 |
| C3 CONFIRMED | 11657 | 34% | 65% | -0.23 [-0.42, -0.03] | -0.62 | -30.26 | 2.20 / 2.26 | -0.25 | 0.244 | 0.00 |
| C4 MAJOR + acceptance | 4561 | 34% | 64% | -0.18 [-0.39, +0.03] | -0.45 | -0.20 | 2.18 / 2.08 | -0.26 | 0.075 | 0.00 |
| C5 with-HTF + acceptance | 13738 | 33% | 65% | -0.22 [-0.40, -0.05] | -0.56 | -173.66 | 2.17 / 2.16 | -0.25 | 0.179 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 18050 | 32% | 66% | -0.31 [-0.46, -0.16] | -0.33 | -0.46 | 2.05 / 2.02 | -0.28 | 0.841 | 0.00 |
| B1 EMA 20/50 cross | 16877 | 33% | 64% | -0.26 [-0.41, -0.11] | -0.31 | -0.34 | 2.07 / 1.98 | -0.28 | 0.343 | 0.00 |
| B2 Supertrend flip | 21204 | 31% | 66% | -0.32 [-0.47, -0.17] | -0.39 | -0.47 | 2.04 / 2.09 | -0.28 | 0.935 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.08 [+0.01, +0.16]; realignment only +0.03 [-0.09, +0.15]; acceptance on MAJOR +0.00 [-0.08, +0.08]; acceptance on with-HTF -0.01 [-0.06, +0.04]; suppressed reversals vs MAJOR -0.13 [-0.28, +0.01]
PBO across C0–C6: **0.00** (352 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.49.
Purged CPCV, event-weighted (post-hoc): picks {'C4': 12, 'C2': 3}; mean OOS rank of the pick 0.11.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 15}; mean OOS r_h of the pick -0.16; mean OOS rank of the pick 0.00 (0 = best, 1 = worst); path means [-0.16, -0.16, -0.16, -0.16, -0.16].

### Regime at entry (all groups)

| set | volatile | range | trend_up | trend_down | transition |
|---|---:|---:|---:|---:|---:|
| C2|bullish | +0.30 (n=1035) | +0.14 (n=2805) | +0.21 (n=1668) | +0.06 (n=1) | -0.13 (n=247) |
| C0|bullish | +0.06 (n=10095) | -0.11 (n=18382) | -0.01 (n=14504) | -0.48 (n=6567) | -0.09 (n=5457) |
| C2|bearish | +0.10 (n=1174) | -0.30 (n=3001) | – | -0.07 (n=1916) | -0.67 (n=302) |
| C0|bearish | -0.36 (n=13374) | -0.17 (n=16248) | -0.46 (n=4820) | -0.26 (n=13076) | -0.43 (n=4757) |

## 4H  (70 symbols, 2020-01-01 → 2026-10-28)

### Bearish representation

| group | breaks bull / bear | MAJOR bull / bear | suppressed counter-HTF reversals bull / bear |
|---|---:|---:|---:|
| crypto | 10635 / 10427 | 983 / 1605 | 3877 / 3247 |
| equities | 1352 / 1040 | 229 / 64 | 304 / 485 |
| commodities | 392 / 306 | 48 / 23 | 98 / 126 |
| rates_fx | 1421 / 1254 | 197 / 109 | 391 / 481 |
| all | 13800 / 13027 | 1457 / 1801 | 4670 / 4339 |

### bullish · crypto

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 10635 | 34% | 66% | +0.55 [+0.11, +0.99] | -0.21 | +1.39 | 2.66 / 2.45 | +0.21 | 0.005 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 3305 | 35% | 65% | +1.21 [+0.66, +1.76] | +0.16 | +3.72 | 3.07 / 2.51 | +0.25 | 0.005 | 0.02 |
| C2 MAJOR (shipped) | 983 | 36% | 64% | +0.84 [+0.23, +1.48] | -0.01 | +2.60 | 2.74 / 2.39 | +0.26 | 0.005 | 0.18 |
| C3 CONFIRMED | 2322 | 35% | 65% | +1.37 [+0.74, +1.95] | +0.28 | +4.20 | 3.31 / 2.56 | +0.24 | 0.005 | 0.02 |
| C4 MAJOR + acceptance | 725 | 35% | 64% | +0.72 [+0.10, +1.36] | +0.06 | +2.12 | 2.66 / 2.38 | +0.25 | 0.015 | 0.30 |
| C5 with-HTF + acceptance | 2465 | 36% | 64% | +1.21 [+0.62, +1.80] | +0.11 | +3.70 | 3.10 / 2.49 | +0.25 | 0.005 | 0.01 |
| C6 counter-HTF reversals (suppressed) | 3877 | 35% | 64% | +0.13 [-0.30, +0.59] | -0.29 | +0.26 | 2.46 / 2.29 | +0.20 | 0.866 | 0.00 |
| B1 EMA 20/50 cross | 3436 | 34% | 65% | +0.30 [-0.14, +0.74] | -0.30 | +0.36 | 2.58 / 2.38 | +0.20 | 0.090 | 0.00 |
| B2 Supertrend flip | 3972 | 33% | 66% | +0.24 [-0.23, +0.72] | -0.36 | +0.38 | 2.48 / 2.33 | +0.21 | 0.348 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.67 [+0.34, +1.01]; realignment only -0.38 [-0.71, +0.03]; acceptance on MAJOR -0.11 [-0.37, +0.12]; acceptance on with-HTF -0.00 [-0.12, +0.11]; suppressed reversals vs MAJOR -0.70 [-1.28, -0.14]
PBO across C0–C6: **0.32** (352 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.02.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 15}; mean OOS rank of the pick 0.13.
Purged CPCV, best-in-train config chosen per split: picks {'C4': 10, 'C2': 5}; mean OOS r_h of the pick +0.28; mean OOS rank of the pick 0.24 (0 = best, 1 = worst); path means [0.35, 0.25, 0.25, 0.32, 0.22].

### bullish · equities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 1352 | 37% | 63% | +0.45 [-0.24, +1.11] | +0.47 | +0.47 | 2.93 / 2.65 | +0.70 | 0.990 | 0.55 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 870 | 36% | 64% | +0.41 [-0.29, +1.04] | +0.46 | +0.26 | 2.90 / 2.76 | +0.82 | 0.995 | 0.23 |
| C2 MAJOR (shipped) | 229 | 37% | 63% | +0.38 [-0.53, +1.18] | +0.39 | +0.17 | 2.74 / 2.63 | +0.85 | 0.915 | 0.39 |
| C3 CONFIRMED | 641 | 35% | 64% | +0.42 [-0.27, +1.09] | +0.49 | +0.29 | 3.00 / 2.79 | +0.80 | 0.995 | 0.30 |
| C4 MAJOR + acceptance | 191 | 36% | 64% | +0.21 [-0.76, +1.01] | +0.34 | +0.05 | 2.65 / 2.77 | +0.88 | 0.975 | 0.43 |
| C5 with-HTF + acceptance | 717 | 34% | 66% | +0.33 [-0.48, +1.04] | +0.49 | +0.16 | 2.89 / 2.88 | +0.83 | 1.000 | 0.14 |
| C6 counter-HTF reversals (suppressed) | 304 | 39% | 61% | +0.70 [-0.18, +1.51] | +0.40 | +1.13 | 3.14 / 2.30 | +0.52 | 0.229 | 0.45 |
| B1 EMA 20/50 cross | 326 | 37% | 63% | +0.79 [+0.07, +1.49] | +0.45 | +1.07 | 3.00 / 2.28 | +0.61 | 0.259 | 0.83 |
| B2 Supertrend flip | 630 | 36% | 64% | +0.65 [+0.01, +1.25] | +0.61 | +0.78 | 3.00 / 2.39 | +0.71 | 0.637 | 0.57 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate -0.04 [-0.24, +0.16]; realignment only -0.03 [-0.51, +0.45]; acceptance on MAJOR -0.18 [-0.39, +0.01]; acceptance on with-HTF -0.09 [-0.24, +0.06]; suppressed reversals vs MAJOR +0.32 [-0.43, +1.06]
PBO across C0–C6: **0.75** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.79.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 13, 'C6': 1, 'C3': 1}; mean OOS rank of the pick 0.20.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 5, 'C2': 5, 'C4': 3, 'C0': 2}; mean OOS r_h of the pick -0.13; mean OOS rank of the pick 0.81 (0 = best, 1 = worst); path means [-0.2, -0.05, -0.33, -0.01, -0.07].

### bullish · commodities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 392 | 44% | 56% | +1.12 [+0.20, +2.01] | +0.83 | +0.80 | 3.97 / 2.74 | +1.10 | 0.498 | 0.89 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 224 | 44% | 56% | +1.46 [+0.24, +2.70] | +0.89 | +1.32 | 4.21 / 2.76 | +1.37 | 0.433 | 0.89 |
| C2 MAJOR (shipped) | 48 | 46% | 54% | +1.51 [-0.27, +3.35] | +2.50 | +1.58 | 5.03 / 2.15 | +1.46 | 0.468 | 0.77 |
| C3 CONFIRMED | 176 | 43% | 57% | +1.44 [-0.08, +3.04] | +0.26 | +1.25 | 4.02 / 2.96 | +1.35 | 0.373 | 0.88 |
| C4 MAJOR + acceptance | 43 | 42% | 58% | +1.18 [-0.70, +2.96] | +2.13 | +1.33 | 5.27 / 1.91 | +1.43 | 0.637 | 0.63 |
| C5 with-HTF + acceptance | 198 | 39% | 61% | +1.62 [+0.38, +2.91] | +0.63 | +1.51 | 4.10 / 3.11 | +1.37 | 0.239 | 0.92 |
| C6 counter-HTF reversals (suppressed) | 98 | 49% | 51% | +0.84 [-0.26, +1.89] | +0.46 | +0.36 | 4.02 / 2.28 | +0.78 | 0.453 | 0.47 |
| B1 EMA 20/50 cross | 99 | 37% | 63% | +0.31 [-1.05, +1.63] | +0.34 | -0.61 | 3.32 / 2.72 | +0.96 | 0.886 | 0.34 |
| B2 Supertrend flip | 212 | 35% | 65% | +0.45 [-0.39, +1.26] | +0.05 | +0.32 | 3.05 / 2.56 | +1.01 | 0.950 | 0.27 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.34 [-0.08, +0.80]; realignment only +0.06 [-1.88, +1.68]; acceptance on MAJOR -0.34 [-0.81, +0.23]; acceptance on with-HTF +0.17 [-0.12, +0.46]; suppressed reversals vs MAJOR -0.67 [-2.03, +0.74]
PBO across C0–C6: **0.77** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.53.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 15}; mean OOS rank of the pick 0.11.
Purged CPCV, best-in-train config chosen per split: picks {'C5': 12, 'C2': 2, 'C0': 1}; mean OOS r_h of the pick +0.67; mean OOS rank of the pick 0.33 (0 = best, 1 = worst); path means [0.59, 0.77, 0.96, 0.08, 0.96].

### bullish · rates_fx

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 1421 | 32% | 67% | -0.31 [-0.60, -0.05] | +0.02 | -0.11 | 2.46 / 2.48 | -0.13 | 0.970 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 639 | 33% | 67% | -0.67 [-1.13, -0.25] | -0.53 | -0.21 | 2.33 / 2.95 | -0.16 | 1.000 | 0.00 |
| C2 MAJOR (shipped) | 197 | 38% | 61% | -0.66 [-1.33, -0.01] | -0.57 | -0.18 | 2.53 / 2.95 | -0.20 | 0.950 | 0.00 |
| C3 CONFIRMED | 442 | 31% | 69% | -0.67 [-1.19, -0.24] | -0.51 | -0.22 | 2.22 / 2.96 | -0.16 | 0.995 | 0.00 |
| C4 MAJOR + acceptance | 154 | 34% | 66% | -0.54 [-1.29, +0.15] | -0.51 | -0.14 | 2.43 / 2.73 | -0.18 | 0.871 | 0.00 |
| C5 with-HTF + acceptance | 504 | 31% | 69% | -0.57 [-1.04, -0.12] | -0.45 | -0.19 | 2.40 / 2.82 | -0.14 | 0.985 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 391 | 37% | 62% | +0.17 [-0.29, +0.63] | +0.55 | +0.03 | 2.77 / 2.00 | -0.14 | 0.100 | 0.01 |
| B1 EMA 20/50 cross | 409 | 33% | 67% | -0.42 [-0.91, +0.09] | -0.46 | -0.12 | 2.47 / 2.64 | -0.14 | 0.915 | 0.00 |
| B2 Supertrend flip | 581 | 34% | 65% | -0.11 [-0.48, +0.28] | +0.24 | -0.06 | 2.61 / 2.20 | -0.19 | 0.308 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate -0.36 [-0.64, -0.10]; realignment only +0.01 [-0.38, +0.43]; acceptance on MAJOR +0.12 [-0.21, +0.51]; acceptance on with-HTF +0.10 [-0.06, +0.29]; suppressed reversals vs MAJOR +0.83 [+0.03, +1.62]
PBO across C0–C6: **0.06** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.01.
Purged CPCV, event-weighted (post-hoc): picks {'C6': 14, 'C2': 1}; mean OOS rank of the pick 0.09.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 12, 'C4': 2, 'C2': 1}; mean OOS r_h of the pick -0.13; mean OOS rank of the pick 0.23 (0 = best, 1 = worst); path means [-0.27, 0.06, -0.14, -0.16, -0.14].

### bullish · all

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 13800 | 34% | 65% | +0.47 [+0.12, +0.82] | -0.10 | +1.13 | 2.69 / 2.48 | +0.25 | 0.005 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 5038 | 35% | 64% | +0.85 [+0.41, +1.29] | +0.16 | +2.52 | 2.93 / 2.61 | +0.34 | 0.005 | 0.11 |
| C2 MAJOR (shipped) | 1457 | 36% | 63% | +0.59 [+0.12, +1.11] | +0.08 | +1.81 | 2.73 / 2.46 | +0.35 | 0.040 | 0.37 |
| C3 CONFIRMED | 3581 | 35% | 65% | +0.95 [+0.47, +1.44] | +0.22 | +2.81 | 3.05 / 2.67 | +0.34 | 0.005 | 0.17 |
| C4 MAJOR + acceptance | 1113 | 36% | 64% | +0.48 [+0.04, +0.94] | +0.06 | +1.42 | 2.66 / 2.49 | +0.35 | 0.184 | 0.50 |
| C5 with-HTF + acceptance | 3884 | 35% | 65% | +0.84 [+0.39, +1.29] | +0.11 | +2.43 | 2.98 / 2.61 | +0.36 | 0.005 | 0.09 |
| C6 counter-HTF reversals (suppressed) | 4670 | 36% | 64% | +0.19 [-0.17, +0.59] | -0.17 | +0.30 | 2.56 / 2.28 | +0.21 | 0.617 | 0.05 |
| B1 EMA 20/50 cross | 4270 | 34% | 65% | +0.27 [-0.09, +0.64] | -0.23 | +0.35 | 2.61 / 2.42 | +0.22 | 0.264 | 0.02 |
| B2 Supertrend flip | 5395 | 34% | 66% | +0.26 [-0.09, +0.62] | -0.18 | +0.37 | 2.60 / 2.35 | +0.26 | 0.522 | 0.01 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.38 [+0.14, +0.62]; realignment only -0.26 [-0.51, +0.03]; acceptance on MAJOR -0.11 [-0.29, +0.05]; acceptance on with-HTF -0.01 [-0.10, +0.08]; suppressed reversals vs MAJOR -0.40 [-0.82, +0.03]
PBO across C0–C6: **0.40** (352 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.06.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 15}; mean OOS rank of the pick 0.12.
Purged CPCV, best-in-train config chosen per split: picks {'C4': 11, 'C2': 3, 'C6': 1}; mean OOS r_h of the pick +0.21; mean OOS rank of the pick 0.31 (0 = best, 1 = worst); path means [0.29, 0.16, 0.23, 0.19, 0.16].

### bearish · crypto

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 10427 | 35% | 63% | -0.12 [-0.48, +0.22] | -0.12 | -0.68 | 2.22 / 2.14 | -0.37 | 0.005 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 4567 | 36% | 63% | -0.03 [-0.50, +0.41] | -0.12 | -0.33 | 2.30 / 2.23 | -0.34 | 0.005 | 0.00 |
| C2 MAJOR (shipped) | 1605 | 36% | 62% | +0.01 [-0.50, +0.55] | -0.17 | -0.08 | 2.15 / 2.19 | -0.34 | 0.005 | 0.00 |
| C3 CONFIRMED | 2962 | 36% | 63% | -0.06 [-0.56, +0.43] | -0.09 | -0.47 | 2.39 / 2.26 | -0.33 | 0.005 | 0.00 |
| C4 MAJOR + acceptance | 1192 | 33% | 65% | +0.03 [-0.60, +0.63] | -0.24 | -0.05 | 2.07 / 2.27 | -0.33 | 0.005 | 0.00 |
| C5 with-HTF + acceptance | 3402 | 34% | 65% | -0.08 [-0.55, +0.38] | -0.18 | -0.51 | 2.22 / 2.27 | -0.34 | 0.005 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 3247 | 34% | 63% | -0.14 [-0.52, +0.26] | +0.02 | -0.94 | 2.14 / 1.97 | -0.40 | 0.005 | 0.00 |
| B1 EMA 20/50 cross | 3441 | 35% | 62% | +0.02 [-0.39, +0.41] | +0.09 | +0.05 | 2.18 / 1.95 | -0.39 | 0.005 | 0.00 |
| B2 Supertrend flip | 3961 | 33% | 64% | -0.02 [-0.43, +0.35] | -0.00 | -0.66 | 2.02 / 1.98 | -0.38 | 0.005 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.09 [-0.11, +0.27]; realignment only +0.05 [-0.20, +0.28]; acceptance on MAJOR +0.02 [-0.13, +0.17]; acceptance on with-HTF -0.05 [-0.14, +0.05]; suppressed reversals vs MAJOR -0.15 [-0.57, +0.27]
PBO across C0–C6: **0.18** (352 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.89.
Purged CPCV, event-weighted (post-hoc): picks {'C2': 5, 'C4': 5, 'C6': 3, 'C0': 1, 'C1': 1}; mean OOS rank of the pick 0.72.
Purged CPCV, best-in-train config chosen per split: picks {'C4': 7, 'C6': 4, 'C2': 4}; mean OOS r_h of the pick -0.51; mean OOS rank of the pick 0.29 (0 = best, 1 = worst); path means [-0.4, -0.52, -0.54, -0.55, -0.55].

### bearish · equities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 1040 | 31% | 68% | -0.83 [-1.43, -0.26] | -0.78 | -0.99 | 2.46 / 3.15 | -0.69 | 0.861 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 270 | 31% | 69% | -0.48 [-1.25, +0.31] | -0.39 | -0.64 | 2.37 / 3.00 | -0.34 | 0.682 | 0.00 |
| C2 MAJOR (shipped) | 64 | 31% | 69% | +0.05 [-1.20, +1.43] | -0.15 | -0.18 | 2.86 / 3.26 | -0.20 | 0.333 | 0.05 |
| C3 CONFIRMED | 206 | 31% | 68% | -0.64 [-1.36, +0.13] | -0.46 | -0.79 | 2.34 / 2.79 | -0.32 | 0.821 | 0.00 |
| C4 MAJOR + acceptance | 56 | 30% | 70% | -0.22 [-1.71, +1.33] | -0.10 | -0.70 | 2.81 / 3.44 | -0.18 | 0.488 | 0.01 |
| C5 with-HTF + acceptance | 219 | 29% | 70% | -0.83 [-1.73, +0.07] | -0.94 | -1.22 | 2.31 / 3.36 | -0.35 | 0.896 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 485 | 31% | 68% | -0.88 [-1.50, -0.24] | -0.69 | -0.88 | 2.50 / 3.26 | -0.84 | 0.582 | 0.00 |
| B1 EMA 20/50 cross | 335 | 28% | 71% | -1.07 [-1.76, -0.31] | -0.89 | -1.62 | 2.52 / 3.00 | -0.69 | 0.955 | 0.00 |
| B2 Supertrend flip | 625 | 31% | 68% | -0.85 [-1.50, -0.16] | -0.79 | -0.84 | 2.44 / 3.24 | -0.80 | 0.662 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.36 [-0.07, +0.82]; realignment only +0.53 [-0.20, +1.24]; acceptance on MAJOR -0.27 [-0.61, +0.10]; acceptance on with-HTF -0.35 [-0.55, -0.12]; suppressed reversals vs MAJOR -0.93 [-2.00, +0.22]
PBO across C0–C6: **0.49** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.20.
Purged CPCV, event-weighted (post-hoc): picks {'C2': 13, 'C4': 1, 'C1': 1}; mean OOS rank of the pick 0.24.
Purged CPCV, best-in-train config chosen per split: picks {'C2': 9, 'C3': 3, 'C1': 2, 'C4': 1}; mean OOS r_h of the pick -0.28; mean OOS rank of the pick 0.40 (0 = best, 1 = worst); path means [-0.42, -0.43, -0.11, -0.42, -0.04].

### bearish · commodities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 306 | 30% | 69% | -1.31 [-2.15, -0.56] | -0.98 | -1.37 | 2.03 / 3.20 | -1.03 | 0.831 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 110 | 24% | 75% | -1.68 [-2.63, -0.82] | -1.42 | -2.63 | 1.50 / 4.22 | -0.65 | 0.990 | 0.00 |
| C2 MAJOR (shipped) | 23 | 26% | 70% | -0.87 [-2.70, +0.75] | -0.32 | -0.55 | 1.64 / 3.44 | -0.52 | 0.642 | 0.03 |
| C3 CONFIRMED | 87 | 23% | 76% | -1.90 [-2.76, -1.07] | -2.02 | -3.18 | 1.48 / 4.33 | -0.67 | 0.995 | 0.00 |
| C4 MAJOR + acceptance | 20 | 35% | 60% | -1.25 [-3.39, +0.62] | -0.92 | -0.63 | 1.81 / 4.76 | -0.37 | 0.796 | 0.03 |
| C5 with-HTF + acceptance | 98 | 30% | 68% | -1.79 [-2.89, -0.73] | -1.75 | -2.65 | 1.75 / 4.17 | -0.63 | 0.985 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 126 | 34% | 66% | -1.29 [-2.43, -0.25] | -0.79 | -1.04 | 2.27 / 3.03 | -1.28 | 0.493 | 0.00 |
| B1 EMA 20/50 cross | 100 | 36% | 63% | -0.50 [-1.80, +0.76] | -0.28 | +0.34 | 2.53 / 2.57 | -1.09 | 0.104 | 0.00 |
| B2 Supertrend flip | 212 | 35% | 65% | -1.03 [-1.90, -0.25] | -0.83 | -1.36 | 2.35 / 3.06 | -1.17 | 0.338 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate -0.37 [-0.96, +0.13]; realignment only +0.81 [-0.37, +1.82]; acceptance on MAJOR -0.38 [-0.77, -0.03]; acceptance on with-HTF -0.11 [-0.35, +0.15]; suppressed reversals vs MAJOR -0.42 [-1.90, +1.09]
PBO across C0–C6: **0.06** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.04.
Purged CPCV, event-weighted (post-hoc): picks {'C2': 15}; mean OOS rank of the pick 0.01.
Purged CPCV, best-in-train config chosen per split: picks {'C2': 15}; mean OOS r_h of the pick -0.14; mean OOS rank of the pick 0.01 (0 = best, 1 = worst); path means [-0.14, -0.14, -0.14, -0.14, -0.14].

### bearish · rates_fx

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 1254 | 32% | 68% | -0.32 [-0.80, +0.18] | -0.40 | -0.13 | 2.47 / 2.61 | -0.08 | 0.980 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 356 | 30% | 69% | -0.27 [-1.06, +0.52] | -0.28 | -0.10 | 2.46 / 2.60 | -0.01 | 0.896 | 0.00 |
| C2 MAJOR (shipped) | 109 | 27% | 72% | +0.27 [-0.81, +1.46] | +0.16 | +0.14 | 2.67 / 2.45 | -0.05 | 0.174 | 0.00 |
| C3 CONFIRMED | 247 | 31% | 68% | -0.51 [-1.51, +0.46] | -0.61 | -0.20 | 2.35 / 2.67 | -0.02 | 0.970 | 0.00 |
| C4 MAJOR + acceptance | 81 | 30% | 69% | +0.53 [-0.58, +1.70] | +0.72 | +0.22 | 2.94 / 2.54 | -0.20 | 0.070 | 0.00 |
| C5 with-HTF + acceptance | 256 | 33% | 66% | -0.14 [-1.03, +0.74] | -0.07 | -0.06 | 2.40 / 2.44 | -0.03 | 0.682 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 481 | 32% | 68% | -0.24 [-0.82, +0.33] | -0.46 | -0.09 | 2.50 / 2.68 | -0.07 | 0.811 | 0.00 |
| B1 EMA 20/50 cross | 412 | 33% | 66% | -0.09 [-0.62, +0.49] | -0.40 | -0.06 | 2.57 / 2.61 | -0.11 | 0.463 | 0.00 |
| B2 Supertrend flip | 577 | 35% | 65% | -0.07 [-0.52, +0.41] | -0.20 | +0.00 | 2.54 / 2.31 | -0.07 | 0.507 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.05 [-0.44, +0.47]; realignment only +0.55 [-0.15, +1.40]; acceptance on MAJOR +0.25 [-0.12, +0.67]; acceptance on with-HTF +0.13 [-0.11, +0.39]; suppressed reversals vs MAJOR -0.52 [-1.65, +0.54]
PBO across C0–C6: **0.14** (144 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.34.
Purged CPCV, event-weighted (post-hoc): picks {'C4': 9, 'C2': 3, 'C0': 1, 'C5': 1, 'C6': 1}; mean OOS rank of the pick 0.47.
Purged CPCV, best-in-train config chosen per split: picks {'C2': 9, 'C4': 6}; mean OOS r_h of the pick +0.02; mean OOS rank of the pick 0.26 (0 = best, 1 = worst); path means [0.07, -0.02, 0.03, 0.02, -0.02].

### bearish · all

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 13027 | 35% | 64% | -0.22 [-0.52, +0.07] | -0.20 | -0.66 | 2.25 / 2.27 | -0.38 | 0.005 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 5303 | 35% | 64% | -0.10 [-0.49, +0.29] | -0.17 | -0.38 | 2.31 / 2.32 | -0.32 | 0.005 | 0.00 |
| C2 MAJOR (shipped) | 1801 | 35% | 63% | +0.02 [-0.46, +0.52] | -0.16 | -0.08 | 2.19 / 2.25 | -0.33 | 0.005 | 0.00 |
| C3 CONFIRMED | 3502 | 35% | 64% | -0.17 [-0.59, +0.25] | -0.18 | -0.54 | 2.37 / 2.35 | -0.32 | 0.020 | 0.00 |
| C4 MAJOR + acceptance | 1349 | 33% | 65% | +0.03 [-0.51, +0.56] | -0.20 | -0.07 | 2.11 / 2.34 | -0.31 | 0.005 | 0.00 |
| C5 with-HTF + acceptance | 3975 | 33% | 65% | -0.16 [-0.58, +0.26] | -0.23 | -0.57 | 2.22 / 2.37 | -0.33 | 0.025 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 4339 | 33% | 65% | -0.26 [-0.57, +0.06] | -0.10 | -0.84 | 2.20 / 2.19 | -0.44 | 0.010 | 0.00 |
| B1 EMA 20/50 cross | 4288 | 34% | 63% | -0.09 [-0.46, +0.26] | +0.01 | -0.09 | 2.23 / 2.09 | -0.39 | 0.005 | 0.00 |
| B2 Supertrend flip | 5375 | 33% | 65% | -0.16 [-0.48, +0.17] | -0.10 | -0.64 | 2.13 / 2.18 | -0.43 | 0.005 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.12 [-0.06, +0.29]; realignment only +0.12 [-0.09, +0.34]; acceptance on MAJOR +0.01 [-0.12, +0.16]; acceptance on with-HTF -0.06 [-0.15, +0.02]; suppressed reversals vs MAJOR -0.28 [-0.65, +0.10]
PBO across C0–C6: **0.15** (352 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.38.
Purged CPCV, event-weighted (post-hoc): picks {'C4': 7, 'C2': 7, 'C0': 1}; mean OOS rank of the pick 0.38.
Purged CPCV, best-in-train config chosen per split: picks {'C2': 9, 'C4': 4, 'C6': 2}; mean OOS r_h of the pick -0.52; mean OOS rank of the pick 0.27 (0 = best, 1 = worst); path means [-0.51, -0.48, -0.55, -0.6, -0.46].

### Regime at entry (all groups)

| set | volatile | range | trend_up | trend_down | transition |
|---|---:|---:|---:|---:|---:|
| C2|bullish | +0.28 (n=229) | +0.71 (n=767) | +0.22 (n=373) | -0.76 (n=4) | +2.01 (n=84) |
| C0|bullish | +0.60 (n=2166) | +0.38 (n=4883) | +0.79 (n=3532) | -0.20 (n=1832) | +0.61 (n=1387) |
| C2|bearish | +0.07 (n=243) | +0.18 (n=928) | – | -0.28 (n=520) | -0.04 (n=110) |
| C0|bearish | -0.30 (n=3236) | -0.10 (n=4380) | -0.34 (n=1020) | -0.28 (n=3307) | -0.21 (n=1084) |

## 1D  (70 symbols, 2010-01-01 → 2026-10-27)

### Bearish representation

| group | breaks bull / bear | MAJOR bull / bear | suppressed counter-HTF reversals bull / bear |
|---|---:|---:|---:|
| crypto | 2301 / 2376 | 177 / 389 | 740 / 519 |
| equities | 5252 / 3495 | 849 / 230 | 951 / 1577 |
| commodities | 1241 / 1174 | 125 / 160 | 364 / 328 |
| rates_fx | 2288 / 2009 | 313 / 194 | 574 / 694 |
| all | 11082 / 9054 | 1464 / 973 | 2629 / 3118 |

### bullish · crypto

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 2301 | 36% | 64% | +1.30 [+0.52, +2.12] | -0.02 | +7.81 | 2.65 / 2.04 | +0.55 | 0.005 | 0.19 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 747 | 35% | 65% | +1.71 [+0.50, +2.78] | +0.16 | +12.37 | 2.93 / 2.18 | +0.63 | 0.005 | 0.43 |
| C2 MAJOR (shipped) | 177 | 31% | 68% | +0.14 [-0.74, +0.99] | -0.55 | +0.19 | 2.10 / 2.39 | +0.64 | 0.940 | 0.17 |
| C3 CONFIRMED | 570 | 36% | 64% | +2.20 [+0.87, +3.50] | +0.41 | +16.16 | 3.24 / 2.17 | +0.63 | 0.005 | 0.57 |
| C4 MAJOR + acceptance | 115 | 35% | 63% | +0.55 [-0.52, +1.72] | -0.54 | +2.62 | 2.39 / 2.39 | +0.60 | 0.527 | 0.29 |
| C5 with-HTF + acceptance | 542 | 40% | 58% | +1.84 [+0.62, +2.90] | +0.30 | +13.14 | 3.17 / 2.14 | +0.63 | 0.005 | 0.50 |
| C6 counter-HTF reversals (suppressed) | 740 | 34% | 64% | +0.98 [-0.04, +2.24] | -0.41 | +4.36 | 2.22 / 1.94 | +0.50 | 0.010 | 0.18 |
| B1 EMA 20/50 cross | 561 | 34% | 65% | +1.37 [+0.14, +2.88] | -0.11 | +6.62 | 2.58 / 1.89 | +0.56 | 0.005 | 0.44 |
| B2 Supertrend flip | 745 | 36% | 63% | +1.19 [+0.04, +2.43] | -0.03 | +5.27 | 2.76 / 1.99 | +0.55 | 0.005 | 0.49 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.41 [-0.29, +1.10]; realignment only -1.57 [-2.33, -0.66]; acceptance on MAJOR +0.41 [-0.01, +0.90]; acceptance on with-HTF +0.13 [-0.20, +0.43]; suppressed reversals vs MAJOR +0.85 [-0.16, +2.00]
PBO across C0–C6: **0.71** (96 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.41.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 14, 'C3': 1}; mean OOS rank of the pick 0.16.
Purged CPCV, best-in-train config chosen per split: picks {'C3': 7, 'C5': 3, 'C6': 2, 'C4': 2, 'C0': 1}; mean OOS r_h of the pick +0.01; mean OOS rank of the pick 0.62 (0 = best, 1 = worst); path means [0.05, 0.07, 0.06, 0.0, -0.13].

### bullish · equities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 5252 | 36% | 61% | +0.37 [+0.09, +0.64] | +0.57 | +0.61 | 2.23 / 1.85 | +0.48 | 0.980 | 0.17 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 3272 | 36% | 61% | +0.40 [+0.06, +0.70] | +0.66 | +0.54 | 2.26 / 1.92 | +0.52 | 0.980 | 0.19 |
| C2 MAJOR (shipped) | 849 | 38% | 58% | +0.56 [+0.11, +0.97] | +0.80 | +0.94 | 2.14 / 1.74 | +0.51 | 0.313 | 0.40 |
| C3 CONFIRMED | 2423 | 36% | 62% | +0.34 [-0.00, +0.66] | +0.59 | +0.40 | 2.31 / 1.99 | +0.52 | 0.990 | 0.13 |
| C4 MAJOR + acceptance | 632 | 38% | 58% | +0.70 [+0.34, +1.05] | +0.74 | +1.16 | 2.28 / 1.63 | +0.53 | 0.104 | 0.73 |
| C5 with-HTF + acceptance | 2488 | 38% | 59% | +0.53 [+0.22, +0.81] | +0.74 | +0.71 | 2.38 / 1.80 | +0.54 | 0.602 | 0.31 |
| C6 counter-HTF reversals (suppressed) | 951 | 36% | 60% | +0.35 [-0.01, +0.71] | +0.40 | +0.93 | 2.15 / 1.61 | +0.40 | 0.597 | 0.07 |
| B1 EMA 20/50 cross | 1021 | 39% | 59% | +0.27 [-0.08, +0.61] | +0.54 | +0.45 | 2.13 / 1.77 | +0.46 | 0.945 | 0.09 |
| B2 Supertrend flip | 1713 | 37% | 59% | +0.46 [+0.07, +0.76] | +0.66 | +0.95 | 2.23 / 1.70 | +0.45 | 0.458 | 0.20 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.02 [-0.07, +0.12]; realignment only +0.16 [-0.09, +0.40]; acceptance on MAJOR +0.14 [-0.08, +0.40]; acceptance on with-HTF +0.13 [+0.04, +0.23]; suppressed reversals vs MAJOR -0.21 [-0.55, +0.22]
PBO across C0–C6: **0.33** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.42.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 15}; mean OOS rank of the pick 0.08.
Purged CPCV, best-in-train config chosen per split: picks {'C4': 8, 'C5': 4, 'C2': 3}; mean OOS r_h of the pick +0.16; mean OOS rank of the pick 0.44 (0 = best, 1 = worst); path means [0.11, 0.11, 0.04, 0.15, 0.4].

### bullish · commodities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 1241 | 34% | 66% | +0.12 [-0.25, +0.49] | -0.15 | +0.06 | 2.17 / 2.25 | +0.08 | 0.383 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 452 | 35% | 65% | +0.45 [-0.21, +1.10] | +0.05 | +0.72 | 2.46 / 2.32 | +0.20 | 0.104 | 0.04 |
| C2 MAJOR (shipped) | 125 | 34% | 66% | -0.15 [-1.00, +0.69] | +0.05 | -0.30 | 2.11 / 2.28 | +0.20 | 0.831 | 0.06 |
| C3 CONFIRMED | 327 | 36% | 64% | +0.68 [-0.04, +1.35] | +0.04 | +1.11 | 2.54 / 2.37 | +0.17 | 0.015 | 0.42 |
| C4 MAJOR + acceptance | 85 | 39% | 60% | +0.04 [-1.24, +1.14] | +0.21 | -0.07 | 2.30 / 1.82 | +0.25 | 0.662 | 0.09 |
| C5 with-HTF + acceptance | 341 | 40% | 59% | +0.67 [-0.15, +1.50] | +0.35 | +1.18 | 2.79 / 2.12 | +0.20 | 0.010 | 0.16 |
| C6 counter-HTF reversals (suppressed) | 364 | 32% | 66% | -0.04 [-0.51, +0.41] | -0.15 | -0.12 | 2.19 / 2.10 | +0.02 | 0.637 | 0.05 |
| B1 EMA 20/50 cross | 289 | 36% | 63% | -0.06 [-0.54, +0.45] | -0.29 | -0.53 | 2.20 / 2.23 | +0.06 | 0.711 | 0.04 |
| B2 Supertrend flip | 529 | 35% | 64% | -0.04 [-0.51, +0.42] | -0.00 | -0.42 | 2.24 / 2.15 | +0.07 | 0.756 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.34 [-0.01, +0.69]; realignment only -0.60 [-1.22, -0.02]; acceptance on MAJOR +0.19 [-0.31, +0.69]; acceptance on with-HTF +0.22 [-0.07, +0.50]; suppressed reversals vs MAJOR +0.11 [-0.61, +0.88]
PBO across C0–C6: **0.45** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.30.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 6, 'C3': 5, 'C5': 4}; mean OOS rank of the pick 0.62.
Purged CPCV, best-in-train config chosen per split: picks {'C3': 11, 'C5': 3, 'C6': 1}; mean OOS r_h of the pick +0.08; mean OOS rank of the pick 0.37 (0 = best, 1 = worst); path means [0.09, 0.09, -0.02, 0.01, 0.26].

### bullish · rates_fx

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 2288 | 33% | 61% | +0.13 [-0.06, +0.31] | +0.18 | +0.06 | 1.87 / 1.69 | +0.11 | 0.413 | 0.02 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 1104 | 35% | 61% | +0.21 [-0.03, +0.45] | +0.21 | +0.08 | 1.99 / 1.70 | +0.20 | 0.468 | 0.00 |
| C2 MAJOR (shipped) | 313 | 34% | 60% | +0.39 [+0.03, +0.77] | +0.48 | +0.23 | 1.86 / 1.53 | +0.17 | 0.119 | 0.45 |
| C3 CONFIRMED | 791 | 35% | 61% | +0.14 [-0.16, +0.43] | +0.14 | +0.02 | 2.01 / 1.80 | +0.19 | 0.701 | 0.00 |
| C4 MAJOR + acceptance | 225 | 32% | 64% | +0.27 [-0.10, +0.66] | +0.44 | +0.16 | 2.03 / 1.67 | +0.18 | 0.343 | 0.24 |
| C5 with-HTF + acceptance | 800 | 34% | 63% | +0.11 [-0.15, +0.37] | +0.24 | +0.02 | 2.02 / 1.76 | +0.21 | 0.806 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 574 | 31% | 62% | -0.06 [-0.34, +0.22] | +0.19 | -0.03 | 1.77 / 1.68 | +0.02 | 0.741 | 0.00 |
| B1 EMA 20/50 cross | 484 | 32% | 63% | +0.20 [-0.11, +0.50] | +0.23 | +0.11 | 1.90 / 1.59 | +0.09 | 0.224 | 0.14 |
| B2 Supertrend flip | 711 | 32% | 61% | +0.15 [-0.11, +0.39] | +0.17 | +0.12 | 1.78 / 1.66 | +0.11 | 0.393 | 0.03 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.08 [-0.06, +0.23]; realignment only +0.18 [-0.09, +0.46]; acceptance on MAJOR -0.13 [-0.37, +0.09]; acceptance on with-HTF -0.10 [-0.24, +0.06]; suppressed reversals vs MAJOR -0.45 [-0.84, -0.05]
PBO across C0–C6: **0.16** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.54.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 11, 'C1': 3, 'C2': 1}; mean OOS rank of the pick 0.34.
Purged CPCV, best-in-train config chosen per split: picks {'C2': 15}; mean OOS r_h of the pick +0.38; mean OOS rank of the pick 0.06 (0 = best, 1 = worst); path means [0.37, 0.37, 0.37, 0.37, 0.37].

### bullish · all

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 11082 | 35% | 62% | +0.49 [+0.23, +0.75] | +0.29 | +1.93 | 2.20 / 1.91 | +0.37 | 0.005 | 0.72 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 5575 | 36% | 62% | +0.54 [+0.24, +0.84] | +0.45 | +2.05 | 2.26 / 1.94 | +0.44 | 0.020 | 0.67 |
| C2 MAJOR (shipped) | 1464 | 36% | 61% | +0.41 [+0.06, +0.71] | +0.51 | +0.59 | 2.09 / 1.82 | +0.43 | 0.607 | 0.49 |
| C3 CONFIRMED | 4111 | 36% | 62% | +0.59 [+0.25, +0.92] | +0.43 | +2.57 | 2.32 / 2.00 | +0.45 | 0.005 | 0.66 |
| C4 MAJOR + acceptance | 1057 | 37% | 60% | +0.54 [+0.25, +0.81] | +0.55 | +1.01 | 2.23 / 1.70 | +0.43 | 0.169 | 0.75 |
| C5 with-HTF + acceptance | 4171 | 38% | 60% | +0.63 [+0.33, +0.91] | +0.54 | +2.23 | 2.39 / 1.87 | +0.45 | 0.005 | 0.83 |
| C6 counter-HTF reversals (suppressed) | 2629 | 34% | 62% | +0.39 [+0.04, +0.78] | +0.10 | +1.54 | 2.07 / 1.79 | +0.31 | 0.179 | 0.19 |
| B1 EMA 20/50 cross | 2355 | 36% | 61% | +0.48 [+0.10, +0.90] | +0.18 | +1.73 | 2.15 / 1.83 | +0.35 | 0.050 | 0.64 |
| B2 Supertrend flip | 3698 | 36% | 61% | +0.47 [+0.15, +0.81] | +0.33 | +1.47 | 2.20 / 1.81 | +0.36 | 0.055 | 0.80 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.05 [-0.10, +0.18]; realignment only -0.13 [-0.35, +0.07]; acceptance on MAJOR +0.13 [-0.02, +0.28]; acceptance on with-HTF +0.09 [+0.01, +0.18]; suppressed reversals vs MAJOR -0.03 [-0.34, +0.32]
PBO across C0–C6: **0.54** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.42.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 15}; mean OOS rank of the pick 0.01.
Purged CPCV, best-in-train config chosen per split: picks {'C5': 8, 'C4': 7}; mean OOS r_h of the pick +0.25; mean OOS rank of the pick 0.39 (0 = best, 1 = worst); path means [0.24, 0.24, 0.21, 0.24, 0.34].

### bearish · crypto

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 2376 | 32% | 60% | -0.19 [-0.72, +0.34] | +0.18 | -1.19 | 1.68 / 1.52 | -0.57 | 0.005 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 1209 | 32% | 60% | -0.33 [-1.14, +0.33] | +0.14 | -1.62 | 1.60 / 1.59 | -0.53 | 0.095 | 0.00 |
| C2 MAJOR (shipped) | 389 | 33% | 57% | -0.20 [-1.09, +0.57] | +0.19 | -0.77 | 1.52 / 1.44 | -0.51 | 0.109 | 0.00 |
| C3 CONFIRMED | 820 | 31% | 62% | -0.39 [-1.22, +0.27] | +0.10 | -2.03 | 1.64 / 1.65 | -0.52 | 0.194 | 0.00 |
| C4 MAJOR + acceptance | 297 | 31% | 57% | -0.51 [-1.54, +0.38] | -0.04 | -2.55 | 1.38 / 1.48 | -0.50 | 0.577 | 0.00 |
| C5 with-HTF + acceptance | 915 | 32% | 59% | -0.49 [-1.46, +0.23] | +0.02 | -2.14 | 1.51 / 1.62 | -0.51 | 0.468 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 519 | 33% | 59% | -0.24 [-0.91, +0.32] | +0.23 | -2.04 | 1.70 / 1.43 | -0.64 | 0.025 | 0.00 |
| B1 EMA 20/50 cross | 547 | 31% | 54% | +0.13 [-0.56, +0.70] | +0.33 | +1.59 | 1.68 / 1.23 | -0.62 | 0.005 | 0.07 |
| B2 Supertrend flip | 723 | 28% | 61% | -0.12 [-0.66, +0.38] | +0.16 | -0.74 | 1.52 / 1.54 | -0.60 | 0.005 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate -0.14 [-0.42, +0.12]; realignment only +0.13 [-0.24, +0.47]; acceptance on MAJOR -0.31 [-0.55, -0.08]; acceptance on with-HTF -0.16 [-0.34, -0.01]; suppressed reversals vs MAJOR -0.04 [-0.74, +0.71]
PBO across C0–C6: **0.50** (96 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.68.
Purged CPCV, event-weighted (post-hoc): picks {'C6': 7, 'C2': 5, 'C0': 2, 'C5': 1}; mean OOS rank of the pick 0.69.
Purged CPCV, best-in-train config chosen per split: picks {'C2': 9, 'C6': 4, 'C3': 1, 'C4': 1}; mean OOS r_h of the pick -0.78; mean OOS rank of the pick 0.41 (0 = best, 1 = worst); path means [-0.78, -0.52, -0.58, -1.15, -0.85].

### bearish · equities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 3495 | 30% | 69% | -0.70 [-1.04, -0.28] | -0.83 | -1.48 | 1.87 / 2.52 | -0.50 | 0.995 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 707 | 31% | 67% | -0.59 [-1.16, -0.01] | -0.82 | -2.00 | 1.89 / 2.45 | -0.39 | 0.940 | 0.00 |
| C2 MAJOR (shipped) | 230 | 29% | 70% | -0.43 [-1.06, +0.19] | -0.70 | -1.13 | 1.92 / 2.29 | -0.43 | 0.522 | 0.00 |
| C3 CONFIRMED | 477 | 32% | 66% | -0.66 [-1.32, +0.03] | -0.87 | -2.41 | 1.89 / 2.58 | -0.41 | 0.940 | 0.00 |
| C4 MAJOR + acceptance | 166 | 29% | 70% | -0.22 [-0.84, +0.40] | -0.20 | -0.52 | 1.93 / 2.28 | -0.41 | 0.249 | 0.00 |
| C5 with-HTF + acceptance | 530 | 31% | 68% | -0.43 [-0.98, +0.11] | -0.51 | -1.31 | 1.88 / 2.32 | -0.41 | 0.572 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 1577 | 30% | 68% | -0.64 [-1.01, -0.25] | -0.73 | -1.06 | 1.97 / 2.50 | -0.54 | 0.841 | 0.00 |
| B1 EMA 20/50 cross | 1025 | 31% | 67% | -0.48 [-0.90, -0.03] | -0.50 | -0.94 | 1.87 / 2.27 | -0.51 | 0.388 | 0.00 |
| B2 Supertrend flip | 1720 | 31% | 67% | -0.47 [-0.91, +0.06] | -0.59 | -0.86 | 1.93 / 2.38 | -0.52 | 0.299 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.11 [-0.21, +0.41]; realignment only +0.15 [-0.25, +0.55]; acceptance on MAJOR +0.22 [-0.08, +0.50]; acceptance on with-HTF +0.16 [-0.02, +0.32]; suppressed reversals vs MAJOR -0.20 [-0.73, +0.33]
PBO across C0–C6: **0.05** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.43.
Purged CPCV, event-weighted (post-hoc): picks {'C4': 12, 'C2': 2, 'C3': 1}; mean OOS rank of the pick 0.17.
Purged CPCV, best-in-train config chosen per split: picks {'C4': 13, 'C2': 2}; mean OOS r_h of the pick -0.20; mean OOS rank of the pick 0.13 (0 = best, 1 = worst); path means [-0.16, -0.23, -0.29, -0.16, -0.16].

### bearish · commodities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 1174 | 33% | 65% | -0.26 [-0.57, +0.04] | -0.20 | -0.43 | 1.98 / 2.07 | -0.15 | 0.831 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 562 | 33% | 65% | -0.14 [-0.51, +0.22] | -0.17 | -0.23 | 1.95 / 2.20 | -0.06 | 0.672 | 0.00 |
| C2 MAJOR (shipped) | 160 | 28% | 70% | -0.39 [-0.92, +0.14] | -0.32 | -1.24 | 1.70 / 2.45 | -0.03 | 0.905 | 0.00 |
| C3 CONFIRMED | 402 | 35% | 62% | -0.04 [-0.44, +0.36] | -0.13 | +0.17 | 2.07 / 2.03 | -0.09 | 0.383 | 0.00 |
| C4 MAJOR + acceptance | 114 | 25% | 74% | -0.28 [-0.85, +0.31] | -0.62 | -1.00 | 1.97 / 2.38 | -0.05 | 0.731 | 0.01 |
| C5 with-HTF + acceptance | 415 | 32% | 66% | +0.02 [-0.36, +0.39] | -0.11 | -0.02 | 2.08 / 2.08 | -0.09 | 0.279 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 328 | 34% | 63% | -0.29 [-0.80, +0.19] | -0.16 | -0.35 | 2.12 / 1.89 | -0.24 | 0.612 | 0.00 |
| B1 EMA 20/50 cross | 286 | 33% | 65% | -0.07 [-0.50, +0.34] | -0.15 | -0.25 | 2.11 / 1.87 | -0.14 | 0.378 | 0.02 |
| B2 Supertrend flip | 529 | 35% | 63% | -0.15 [-0.53, +0.21] | -0.03 | -0.18 | 2.10 / 1.91 | -0.17 | 0.438 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.12 [-0.08, +0.32]; realignment only -0.25 [-0.58, +0.10]; acceptance on MAJOR +0.11 [-0.19, +0.42]; acceptance on with-HTF +0.16 [-0.03, +0.33]; suppressed reversals vs MAJOR +0.10 [-0.42, +0.63]
PBO across C0–C6: **0.83** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.56.
Purged CPCV, event-weighted (post-hoc): picks {'C5': 7, 'C4': 5, 'C3': 3}; mean OOS rank of the pick 0.51.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 7, 'C4': 6, 'C5': 2}; mean OOS r_h of the pick -0.51; mean OOS rank of the pick 0.69 (0 = best, 1 = worst); path means [-0.56, -0.19, -0.6, -0.6, -0.6].

### bearish · rates_fx

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 2009 | 31% | 65% | -0.21 [-0.43, +0.02] | -0.29 | -0.18 | 1.73 / 1.91 | -0.16 | 0.776 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 700 | 30% | 65% | -0.07 [-0.42, +0.29] | -0.19 | -0.05 | 1.69 / 1.82 | -0.08 | 0.483 | 0.00 |
| C2 MAJOR (shipped) | 194 | 30% | 64% | -0.04 [-0.52, +0.44] | -0.03 | -0.01 | 1.87 / 1.81 | -0.08 | 0.423 | 0.02 |
| C3 CONFIRMED | 506 | 30% | 66% | -0.07 [-0.45, +0.32] | -0.25 | -0.07 | 1.61 / 1.82 | -0.08 | 0.478 | 0.00 |
| C4 MAJOR + acceptance | 145 | 27% | 69% | -0.30 [-0.77, +0.17] | -0.52 | -0.22 | 1.50 / 1.87 | -0.10 | 0.831 | 0.00 |
| C5 with-HTF + acceptance | 512 | 29% | 67% | -0.19 [-0.57, +0.16] | -0.35 | -0.20 | 1.51 / 1.89 | -0.09 | 0.791 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 694 | 31% | 66% | -0.36 [-0.65, -0.09] | -0.47 | -0.27 | 1.69 / 1.93 | -0.22 | 0.896 | 0.00 |
| B1 EMA 20/50 cross | 485 | 34% | 64% | -0.07 [-0.42, +0.26] | -0.09 | -0.09 | 1.88 / 1.88 | -0.17 | 0.234 | 0.01 |
| B2 Supertrend flip | 712 | 33% | 63% | -0.23 [-0.56, +0.15] | -0.39 | -0.18 | 1.78 / 1.91 | -0.22 | 0.562 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.14 [-0.09, +0.36]; realignment only +0.02 [-0.24, +0.31]; acceptance on MAJOR -0.26 [-0.51, -0.01]; acceptance on with-HTF -0.13 [-0.28, +0.00]; suppressed reversals vs MAJOR -0.32 [-0.73, +0.13]
PBO across C0–C6: **0.44** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.58.
Purged CPCV, event-weighted (post-hoc): picks {'C2': 8, 'C1': 4, 'C3': 3}; mean OOS rank of the pick 0.53.
Purged CPCV, best-in-train config chosen per split: picks {'C2': 9, 'C3': 4, 'C4': 2}; mean OOS r_h of the pick -0.24; mean OOS rank of the pick 0.42 (0 = best, 1 = worst); path means [-0.29, -0.22, -0.25, -0.22, -0.22].

### bearish · all

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 9054 | 31% | 65% | -0.40 [-0.65, -0.12] | -0.29 | -0.98 | 1.81 / 2.01 | -0.40 | 0.443 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 3178 | 32% | 64% | -0.29 [-0.66, +0.05] | -0.16 | -1.11 | 1.75 / 1.87 | -0.31 | 0.403 | 0.00 |
| C2 MAJOR (shipped) | 973 | 31% | 63% | -0.26 [-0.68, +0.17] | -0.11 | -0.78 | 1.71 / 1.79 | -0.32 | 0.318 | 0.00 |
| C3 CONFIRMED | 2205 | 32% | 64% | -0.31 [-0.67, +0.04] | -0.17 | -1.26 | 1.77 / 1.92 | -0.32 | 0.478 | 0.00 |
| C4 MAJOR + acceptance | 722 | 29% | 65% | -0.36 [-0.86, +0.07] | -0.22 | -1.37 | 1.60 / 1.88 | -0.34 | 0.537 | 0.00 |
| C5 with-HTF + acceptance | 2372 | 31% | 64% | -0.32 [-0.74, +0.05] | -0.19 | -1.16 | 1.67 / 1.90 | -0.33 | 0.463 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 3118 | 31% | 66% | -0.47 [-0.75, -0.17] | -0.37 | -0.97 | 1.88 / 2.08 | -0.45 | 0.637 | 0.00 |
| B1 EMA 20/50 cross | 2343 | 32% | 63% | -0.20 [-0.50, +0.10] | -0.11 | -0.09 | 1.84 / 1.86 | -0.42 | 0.005 | 0.00 |
| B2 Supertrend flip | 3684 | 32% | 65% | -0.31 [-0.63, +0.07] | -0.26 | -0.61 | 1.85 / 2.00 | -0.43 | 0.055 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.10 [-0.08, +0.27]; realignment only +0.04 [-0.16, +0.25]; acceptance on MAJOR -0.11 [-0.26, +0.03]; acceptance on with-HTF -0.03 [-0.13, +0.07]; suppressed reversals vs MAJOR -0.22 [-0.57, +0.16]
PBO across C0–C6: **0.55** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.73.
Purged CPCV, event-weighted (post-hoc): picks {'C2': 8, 'C4': 5, 'C3': 2}; mean OOS rank of the pick 0.29.
Purged CPCV, best-in-train config chosen per split: picks {'C3': 8, 'C4': 5, 'C5': 1, 'C2': 1}; mean OOS r_h of the pick -0.54; mean OOS rank of the pick 0.58 (0 = best, 1 = worst); path means [-0.52, -0.53, -0.49, -0.54, -0.62].

### Regime at entry (all groups)

| set | volatile | range | trend_up | trend_down | transition |
|---|---:|---:|---:|---:|---:|
| C2|bullish | +0.34 (n=211) | +0.46 (n=921) | +0.29 (n=297) | – | +0.48 (n=35) |
| C0|bullish | +0.06 (n=1421) | +0.57 (n=4631) | +0.61 (n=3431) | +0.23 (n=881) | +0.53 (n=718) |
| C2|bearish | -0.09 (n=195) | -0.49 (n=517) | -2.35 (n=1) | +0.05 (n=228) | +0.40 (n=32) |
| C0|bearish | -0.35 (n=2447) | -0.42 (n=3383) | -0.67 (n=899) | -0.25 (n=1706) | -0.46 (n=619) |

## 1W  (67 symbols, 2010-01-01 → 2026-10-20)

### Bearish representation

| group | breaks bull / bear | MAJOR bull / bear | suppressed counter-HTF reversals bull / bear |
|---|---:|---:|---:|
| crypto | 294 / 309 | 16 / 49 | 83 / 58 |
| equities | 1151 / 630 | 196 / 22 | 163 / 345 |
| commodities | 241 / 261 | 23 / 56 | 92 / 61 |
| rates_fx | 475 / 390 | 67 / 43 | 117 / 141 |
| all | 2161 / 1590 | 302 / 170 | 455 / 605 |

### bullish · crypto

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 294 | 37% | 61% | +2.52 [+0.62, +4.86] | -0.29 | +33.14 | 3.04 / 1.91 | +1.40 | 0.040 | 0.86 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 97 | 30% | 69% | +2.91 [+0.04, +6.29] | -0.25 | +34.91 | 3.16 / 2.18 | +1.32 | 0.035 | 0.83 |
| C2 MAJOR (shipped) | 16 | 38% | 62% | +1.00 [-1.70, +4.09] | -0.25 | +18.87 | 2.44 / 1.86 | +1.83 | 0.627 | 0.39 |
| C3 CONFIRMED | 81 | 28% | 70% | +3.29 [-0.02, +7.21] | -0.25 | +38.07 | 3.47 / 2.22 | +1.46 | 0.035 | 0.86 |
| C4 MAJOR + acceptance | 12 | 25% | 75% | +1.11 [-2.13, +4.57] | -1.32 | +17.33 | 1.26 / 2.36 | +1.61 | 0.493 | 0.45 |
| C5 with-HTF + acceptance | 79 | 25% | 75% | +3.08 [-0.31, +7.67] | -0.83 | +35.44 | 3.51 / 2.49 | +1.50 | 0.050 | 0.89 |
| C6 counter-HTF reversals (suppressed) | 83 | 40% | 58% | +0.93 [-0.20, +2.14] | -0.54 | +8.92 | 2.15 / 1.82 | +1.21 | 0.517 | 0.67 |
| B1 EMA 20/50 cross | 72 | 26% | 71% | +0.89 [-0.49, +2.74] | -0.59 | +11.85 | 2.02 / 2.12 | +1.15 | 0.582 | 0.91 |
| B2 Supertrend flip | 114 | 38% | 62% | +2.89 [-0.01, +8.25] | -0.83 | +41.92 | 2.66 / 1.99 | +1.47 | 0.104 | 0.68 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.39 [-0.95, +1.76]; acceptance on with-HTF +0.17 [-2.89, +3.70]
PBO across C0–C6: **0.49** (96 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.23.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 11, 'C6': 4}; mean OOS rank of the pick 0.21.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 7, 'C0': 6, 'C5': 2}; mean OOS r_h of the pick +0.27; mean OOS rank of the pick 0.57 (0 = best, 1 = worst); path means [0.15, 0.13, 0.21, 0.23, 0.65].

### bullish · equities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 1151 | 38% | 54% | +0.67 [+0.40, +0.93] | +0.76 | +2.65 | 2.02 / 1.30 | +0.71 | 0.756 | 0.85 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 877 | 39% | 54% | +0.70 [+0.37, +1.00] | +0.76 | +2.59 | 2.08 / 1.40 | +0.77 | 0.831 | 0.96 |
| C2 MAJOR (shipped) | 196 | 42% | 49% | +0.77 [+0.27, +1.24] | +1.18 | +2.95 | 2.05 / 1.17 | +0.75 | 0.438 | 0.95 |
| C3 CONFIRMED | 681 | 38% | 56% | +0.68 [+0.34, +1.01] | +0.71 | +2.49 | 2.09 / 1.44 | +0.78 | 0.836 | 0.89 |
| C4 MAJOR + acceptance | 148 | 46% | 46% | +0.99 [+0.52, +1.42] | +1.22 | +3.52 | 2.22 / 0.93 | +0.75 | 0.109 | 0.98 |
| C5 with-HTF + acceptance | 655 | 39% | 54% | +0.73 [+0.29, +1.12] | +0.89 | +2.53 | 2.11 / 1.36 | +0.77 | 0.687 | 0.99 |
| C6 counter-HTF reversals (suppressed) | 163 | 33% | 52% | +0.51 [+0.18, +0.83] | +0.69 | +2.40 | 1.81 / 1.10 | +0.53 | 0.488 | 0.59 |
| B1 EMA 20/50 cross | 182 | 32% | 55% | +0.39 [-0.06, +0.78] | +0.52 | +1.81 | 1.68 / 1.27 | +0.61 | 0.871 | 0.36 |
| B2 Supertrend flip | 332 | 40% | 48% | +0.57 [+0.20, +0.89] | +0.64 | +2.41 | 1.88 / 1.04 | +0.68 | 0.811 | 0.59 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.03 [-0.04, +0.10]; realignment only +0.08 [-0.26, +0.41]; acceptance on MAJOR +0.22 [-0.08, +0.50]; acceptance on with-HTF +0.03 [-0.16, +0.22]; suppressed reversals vs MAJOR -0.26 [-0.69, +0.18]
PBO across C0–C6: **0.60** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.39.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 15}; mean OOS rank of the pick 0.00.
Purged CPCV, best-in-train config chosen per split: picks {'C5': 12, 'C1': 3}; mean OOS r_h of the pick +0.59; mean OOS rank of the pick 0.21 (0 = best, 1 = worst); path means [0.65, 0.5, 0.5, 0.65, 0.65].

### bullish · commodities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 241 | 37% | 58% | +0.28 [-0.23, +0.77] | +0.12 | +0.92 | 1.72 / 1.77 | +0.20 | 0.289 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 84 | 49% | 46% | +1.41 [+0.69, +2.14] | +0.93 | +5.07 | 2.71 / 1.35 | +0.43 | 0.005 | 0.11 |
| C2 MAJOR (shipped) | 23 | 35% | 57% | +0.33 [-0.65, +1.33] | +0.29 | -0.43 | 1.76 / 1.76 | +0.51 | 0.617 | 0.04 |
| C3 CONFIRMED | 61 | 54% | 43% | +1.81 [+0.88, +2.67] | +1.22 | +7.15 | 3.02 / 0.93 | +0.38 | 0.005 | 0.28 |
| C4 MAJOR + acceptance | 13 | 23% | 62% | +0.96 [-0.56, +2.23] | +0.63 | +1.72 | 1.81 / 1.36 | +0.49 | 0.254 | 0.24 |
| C5 with-HTF + acceptance | 57 | 51% | 46% | +1.69 [+0.86, +2.53] | +1.63 | +6.12 | 2.88 / 1.08 | +0.41 | 0.005 | 0.32 |
| C6 counter-HTF reversals (suppressed) | 92 | 24% | 71% | -0.64 [-1.30, +0.06] | -1.43 | -2.18 | 0.99 / 2.13 | +0.06 | 1.000 | 0.00 |
| B1 EMA 20/50 cross | 49 | 33% | 63% | +0.66 [-0.53, +1.94] | +0.12 | +2.18 | 1.46 / 1.70 | +0.22 | 0.159 | 0.00 |
| B2 Supertrend flip | 94 | 26% | 73% | -0.29 [-0.89, +0.34] | -0.61 | -1.98 | 1.31 / 1.94 | +0.15 | 0.945 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +1.13 [+0.61, +1.64]; realignment only -1.08 [-1.94, -0.24]; acceptance on with-HTF +0.29 [-0.37, +1.04]; suppressed reversals vs MAJOR -0.98 [-1.99, +0.01]
PBO across C0–C6: **0.20** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.14.
Purged CPCV, event-weighted (post-hoc): picks {'C1': 6, 'C3': 5, 'C0': 3, 'C5': 1}; mean OOS rank of the pick 0.37.
Purged CPCV, best-in-train config chosen per split: picks {'C1': 8, 'C3': 4, 'C5': 3}; mean OOS r_h of the pick +0.35; mean OOS rank of the pick 0.29 (0 = best, 1 = worst); path means [0.41, 0.36, 0.36, 0.32, 0.29].

### bullish · rates_fx

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 475 | 33% | 57% | +0.29 [-0.02, +0.61] | +0.27 | +0.35 | 1.60 / 1.38 | +0.28 | 0.458 | 0.12 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 270 | 39% | 51% | +0.60 [+0.17, +1.03] | +0.78 | +0.79 | 1.86 / 1.17 | +0.46 | 0.204 | 0.53 |
| C2 MAJOR (shipped) | 67 | 40% | 48% | +0.35 [-0.49, +1.07] | +0.74 | +0.60 | 1.87 / 1.14 | +0.37 | 0.522 | 0.31 |
| C3 CONFIRMED | 203 | 38% | 52% | +0.68 [+0.23, +1.14] | +0.80 | +0.85 | 1.85 / 1.22 | +0.47 | 0.139 | 0.58 |
| C4 MAJOR + acceptance | 48 | 40% | 50% | +0.19 [-0.85, +1.27] | +0.70 | +0.28 | 2.07 / 1.07 | +0.41 | 0.731 | 0.49 |
| C5 with-HTF + acceptance | 195 | 39% | 50% | +0.68 [+0.18, +1.25] | +0.76 | +0.89 | 1.95 / 1.15 | +0.46 | 0.095 | 0.76 |
| C6 counter-HTF reversals (suppressed) | 117 | 26% | 64% | -0.05 [-0.55, +0.49] | -0.15 | -0.04 | 1.44 / 1.39 | +0.06 | 0.706 | 0.02 |
| B1 EMA 20/50 cross | 101 | 21% | 65% | +0.11 [-0.30, +0.52] | -0.26 | -0.04 | 1.31 / 1.41 | +0.13 | 0.532 | 0.06 |
| B2 Supertrend flip | 136 | 26% | 60% | +0.13 [-0.38, +0.63] | +0.09 | +0.05 | 1.31 / 1.42 | +0.20 | 0.667 | 0.02 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.31 [+0.11, +0.53]; realignment only -0.25 [-0.77, +0.25]; acceptance on MAJOR -0.15 [-0.74, +0.52]; acceptance on with-HTF +0.09 [-0.22, +0.41]; suppressed reversals vs MAJOR -0.39 [-1.13, +0.36]
PBO across C0–C6: **0.57** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.42.
Purged CPCV, event-weighted (post-hoc): picks {'C1': 9, 'C0': 4, 'C5': 2}; mean OOS rank of the pick 0.32.
Purged CPCV, best-in-train config chosen per split: picks {'C5': 13, 'C1': 2}; mean OOS r_h of the pick +0.39; mean OOS rank of the pick 0.18 (0 = best, 1 = worst); path means [0.38, 0.36, 0.43, 0.43, 0.36].

### bullish · all

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 2161 | 37% | 56% | +0.79 [+0.43, +1.21] | +0.50 | +6.10 | 1.96 / 1.44 | +0.65 | 0.075 | 0.60 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 1328 | 39% | 54% | +0.88 [+0.55, +1.23] | +0.74 | +4.74 | 2.09 / 1.40 | +0.73 | 0.040 | 0.92 |
| C2 MAJOR (shipped) | 302 | 41% | 50% | +0.66 [+0.25, +1.05] | +0.87 | +3.01 | 1.99 / 1.19 | +0.70 | 0.552 | 0.46 |
| C3 CONFIRMED | 1026 | 38% | 55% | +0.95 [+0.52, +1.39] | +0.71 | +5.25 | 2.11 / 1.43 | +0.75 | 0.020 | 0.86 |
| C4 MAJOR + acceptance | 221 | 42% | 49% | +0.82 [+0.36, +1.27] | +1.02 | +3.46 | 2.17 / 1.06 | +0.72 | 0.294 | 0.72 |
| C5 with-HTF + acceptance | 986 | 39% | 54% | +0.96 [+0.50, +1.46] | +0.82 | +5.05 | 2.13 / 1.37 | +0.76 | 0.040 | 0.94 |
| C6 counter-HTF reversals (suppressed) | 455 | 31% | 60% | +0.21 [-0.16, +0.56] | -0.06 | +2.04 | 1.61 / 1.47 | +0.44 | 0.896 | 0.00 |
| B1 EMA 20/50 cross | 404 | 28% | 61% | +0.44 [+0.02, +0.87] | +0.12 | +3.18 | 1.59 / 1.43 | +0.55 | 0.682 | 0.09 |
| B2 Supertrend flip | 676 | 35% | 57% | +0.75 [+0.13, +1.64] | +0.14 | +7.99 | 1.76 / 1.41 | +0.64 | 0.204 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.09 [-0.05, +0.23]; realignment only -0.23 [-0.62, +0.14]; acceptance on MAJOR +0.16 [-0.11, +0.42]; acceptance on with-HTF +0.08 [-0.20, +0.40]; suppressed reversals vs MAJOR -0.45 [-0.83, -0.01]
PBO across C0–C6: **0.22** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.23.
Purged CPCV, event-weighted (post-hoc): picks {'C0': 15}; mean OOS rank of the pick 0.00.
Purged CPCV, best-in-train config chosen per split: picks {'C5': 15}; mean OOS r_h of the pick +0.93; mean OOS rank of the pick 0.01 (0 = best, 1 = worst); path means [0.93, 0.93, 0.93, 0.93, 0.93].

### bearish · crypto

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 309 | 5% | 46% | -0.39 [-0.85, -0.00] | +0.04 | -16.06 | 0.72 / 0.89 | -1.26 | 0.010 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 166 | 4% | 49% | -0.50 [-1.29, -0.03] | -0.01 | -14.91 | 0.59 / 0.95 | -1.36 | 0.104 | 0.00 |
| C2 MAJOR (shipped) | 49 | 8% | 41% | -0.96 [-3.48, +0.26] | +0.14 | -24.33 | 0.63 / 0.76 | -1.29 | 0.542 | 0.00 |
| C3 CONFIRMED | 117 | 2% | 52% | -0.31 [-0.65, +0.05] | -0.04 | -10.97 | 0.52 / 1.01 | -1.25 | 0.075 | 0.00 |
| C4 MAJOR + acceptance | 39 | 10% | 33% | -0.01 [-0.69, +0.51] | +0.11 | -2.77 | 0.75 / 0.54 | -1.12 | 0.179 | 0.23 |
| C5 with-HTF + acceptance | 126 | 4% | 46% | -0.23 [-0.61, +0.17] | +0.04 | -10.54 | 0.59 / 0.93 | -1.26 | 0.060 | 0.04 |
| C6 counter-HTF reversals (suppressed) | 58 | 9% | 41% | +0.05 [-0.47, +0.52] | +0.21 | -4.48 | 1.16 / 0.83 | -1.40 | 0.015 | 0.01 |
| B1 EMA 20/50 cross | 77 | 14% | 36% | -0.09 [-1.01, +0.54] | +0.39 | +1.23 | 1.08 / 0.75 | -1.45 | 0.020 | 0.01 |
| B2 Supertrend flip | 111 | 6% | 55% | -0.47 [-1.04, +0.09] | -0.15 | -21.94 | 0.72 / 1.12 | -1.37 | 0.100 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate -0.11 [-0.43, +0.13]; realignment only -0.46 [-2.05, +0.37]; acceptance on MAJOR +0.95 [-0.08, +2.75]; acceptance on with-HTF +0.26 [-0.13, +0.84]; suppressed reversals vs MAJOR +1.01 [-0.24, +3.06]
PBO across C0–C6: **0.68** (96 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.33.
Purged CPCV, event-weighted (post-hoc): picks {'C6': 12, 'C4': 2, 'C2': 1}; mean OOS rank of the pick 0.22.
Purged CPCV, best-in-train config chosen per split: picks {'C4': 7, 'C0': 2, 'C6': 2, 'C2': 2, 'C3': 1, 'C5': 1}; mean OOS r_h of the pick -0.24; mean OOS rank of the pick 0.55 (0 = best, 1 = worst); path means [-0.15, -0.19, -0.19, -0.57, -0.11].

### bearish · equities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 630 | 19% | 76% | -1.07 [-1.44, -0.67] | -1.01 | -5.16 | 1.21 / 2.10 | -0.66 | 1.000 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 85 | 24% | 68% | -0.44 [-1.00, +0.23] | -0.57 | -4.25 | 1.40 / 1.65 | -0.45 | 0.468 | 0.00 |
| C2 MAJOR (shipped) | 22 | 27% | 59% | -0.23 [-1.18, +0.75] | +0.09 | -3.13 | 1.68 / 1.37 | -0.41 | 0.318 | 0.02 |
| C3 CONFIRMED | 63 | 22% | 71% | -0.51 [-1.19, +0.23] | -0.61 | -4.64 | 1.28 / 1.88 | -0.43 | 0.607 | 0.00 |
| C4 MAJOR + acceptance | 19 | 16% | 84% | -0.66 [-1.73, +0.78] | -1.32 | -7.45 | 1.57 / 2.25 | -0.45 | 0.607 | 0.02 |
| C5 with-HTF + acceptance | 61 | 26% | 74% | -0.53 [-1.33, +0.42] | -1.10 | -5.26 | 1.53 / 1.98 | -0.41 | 0.662 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 345 | 17% | 78% | -1.23 [-1.59, -0.80] | -1.34 | -5.43 | 1.15 / 2.19 | -0.70 | 1.000 | 0.00 |
| B1 EMA 20/50 cross | 185 | 26% | 70% | -0.89 [-1.39, -0.38] | -1.04 | -5.03 | 1.29 / 2.03 | -0.63 | 0.891 | 0.00 |
| B2 Supertrend flip | 341 | 16% | 79% | -1.13 [-1.54, -0.72] | -1.19 | -4.80 | 1.17 / 2.27 | -0.70 | 1.000 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.63 [+0.21, +1.08]; realignment only +0.21 [-0.48, +0.90]; acceptance on with-HTF -0.09 [-0.57, +0.46]; suppressed reversals vs MAJOR -0.99 [-1.80, -0.20]
PBO across C0–C6: **0.70** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.61.
Purged CPCV, event-weighted (post-hoc): picks {'C2': 11, 'C5': 2, 'C4': 1, 'C1': 1}; mean OOS rank of the pick 0.30.
Purged CPCV, best-in-train config chosen per split: picks {'C1': 7, 'C2': 4, 'C5': 3, 'C3': 1}; mean OOS r_h of the pick -0.06; mean OOS rank of the pick 0.49 (0 = best, 1 = worst); path means [-0.06, -0.1, -0.07, -0.03, -0.03].

### bearish · commodities

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 261 | 24% | 62% | -0.11 [-0.51, +0.30] | -0.11 | -0.28 | 1.40 / 1.53 | -0.16 | 0.418 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 154 | 23% | 59% | -0.17 [-0.65, +0.34] | -0.05 | -0.65 | 1.38 / 1.51 | -0.01 | 0.736 | 0.01 |
| C2 MAJOR (shipped) | 56 | 29% | 57% | -0.05 [-0.95, +0.86] | +0.11 | +0.63 | 1.40 / 1.42 | -0.05 | 0.493 | 0.06 |
| C3 CONFIRMED | 98 | 20% | 60% | -0.24 [-0.77, +0.33] | -0.13 | -1.38 | 1.38 / 1.53 | +0.04 | 0.846 | 0.02 |
| C4 MAJOR + acceptance | 40 | 18% | 60% | -0.53 [-1.55, +0.20] | -0.01 | -0.44 | 1.23 / 1.52 | -0.07 | 0.861 | 0.01 |
| C5 with-HTF + acceptance | 110 | 20% | 60% | -0.33 [-0.82, +0.13] | -0.20 | -0.75 | 1.24 / 1.54 | -0.01 | 0.920 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 61 | 23% | 69% | -0.24 [-0.87, +0.40] | -0.22 | -0.48 | 1.48 / 1.53 | -0.41 | 0.294 | 0.13 |
| B1 EMA 20/50 cross | 47 | 30% | 62% | +0.10 [-1.03, +1.13] | -0.02 | +1.54 | 1.52 / 1.62 | -0.24 | 0.259 | 0.25 |
| B2 Supertrend flip | 93 | 22% | 69% | -0.25 [-0.77, +0.28] | -0.37 | -1.82 | 1.11 / 1.62 | -0.24 | 0.512 | 0.09 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate -0.06 [-0.30, +0.19]; realignment only +0.12 [-0.42, +0.69]; acceptance on MAJOR -0.49 [-1.22, +0.22]; acceptance on with-HTF -0.16 [-0.58, +0.21]; suppressed reversals vs MAJOR -0.19 [-1.09, +0.70]
PBO across C0–C6: **0.54** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.89.
Purged CPCV, event-weighted (post-hoc): picks {'C2': 7, 'C0': 6, 'C6': 2}; mean OOS rank of the pick 0.69.
Purged CPCV, best-in-train config chosen per split: picks {'C6': 8, 'C2': 6, 'C0': 1}; mean OOS r_h of the pick -0.15; mean OOS rank of the pick 0.49 (0 = best, 1 = worst); path means [-0.14, -0.08, -0.12, -0.12, -0.28].

### bearish · rates_fx

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 390 | 26% | 65% | -0.28 [-0.62, +0.10] | -0.38 | -0.58 | 1.33 / 1.76 | -0.20 | 0.751 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 164 | 26% | 63% | -0.29 [-0.72, +0.18] | -0.32 | -0.61 | 1.34 / 1.76 | -0.03 | 0.955 | 0.00 |
| C2 MAJOR (shipped) | 43 | 28% | 58% | -0.27 [-0.87, +0.32] | -0.33 | -0.52 | 1.53 / 1.52 | -0.06 | 0.736 | 0.03 |
| C3 CONFIRMED | 121 | 26% | 65% | -0.30 [-0.81, +0.23] | -0.31 | -0.64 | 1.25 / 1.76 | -0.05 | 0.881 | 0.01 |
| C4 MAJOR + acceptance | 30 | 33% | 63% | -0.43 [-1.15, +0.26] | -0.58 | -1.04 | 1.29 / 1.33 | +0.02 | 0.876 | 0.01 |
| C5 with-HTF + acceptance | 116 | 25% | 70% | -0.36 [-0.80, +0.14] | -0.36 | -0.90 | 1.31 / 1.75 | -0.02 | 0.950 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 141 | 26% | 67% | -0.39 [-0.95, +0.16] | -0.44 | -0.86 | 1.41 / 1.81 | -0.29 | 0.672 | 0.00 |
| B1 EMA 20/50 cross | 98 | 28% | 66% | -0.16 [-0.65, +0.29] | -0.39 | -0.28 | 1.33 / 1.66 | -0.16 | 0.483 | 0.00 |
| B2 Supertrend flip | 137 | 26% | 66% | -0.07 [-0.62, +0.48] | -0.24 | -0.11 | 1.76 / 1.65 | -0.25 | 0.194 | 0.07 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate -0.02 [-0.28, +0.25]; realignment only +0.02 [-0.45, +0.52]; acceptance on MAJOR -0.16 [-0.64, +0.26]; acceptance on with-HTF -0.06 [-0.32, +0.21]; suppressed reversals vs MAJOR -0.12 [-0.79, +0.53]
PBO across C0–C6: **0.84** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.92.
Purged CPCV, event-weighted (post-hoc): picks {'C2': 5, 'C3': 4, 'C4': 2, 'C0': 2, 'C6': 1, 'C5': 1}; mean OOS rank of the pick 0.69.
Purged CPCV, best-in-train config chosen per split: picks {'C2': 5, 'C3': 5, 'C1': 3, 'C0': 2}; mean OOS r_h of the pick -0.21; mean OOS rank of the pick 0.72 (0 = best, 1 = worst); path means [-0.14, -0.09, -0.25, -0.25, -0.31].

### bearish · all

| config | n | precision | false pos | mean r_h [95% CI] | median r_h | fwd ret % | MFE / MAE | random r_h | p | DSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 every structure break | 1590 | 19% | 65% | -0.58 [-0.83, -0.32] | -0.42 | -5.36 | 1.10 / 1.67 | -0.59 | 0.532 | 0.00 |
| C1 with-HTF breaks (MAJOR+CONFIRMED) | 569 | 18% | 59% | -0.34 [-0.63, -0.06] | -0.06 | -5.34 | 1.03 / 1.47 | -0.45 | 0.333 | 0.00 |
| C2 MAJOR (shipped) | 170 | 22% | 53% | -0.39 [-1.07, +0.21] | +0.10 | -7.34 | 1.18 / 1.16 | -0.43 | 0.587 | 0.00 |
| C3 CONFIRMED | 399 | 17% | 61% | -0.32 [-0.60, -0.03] | -0.23 | -4.48 | 1.00 / 1.52 | -0.44 | 0.343 | 0.00 |
| C4 MAJOR + acceptance | 128 | 19% | 56% | -0.37 [-0.81, +0.02] | -0.05 | -2.33 | 1.10 / 1.20 | -0.57 | 0.448 | 0.00 |
| C5 with-HTF + acceptance | 413 | 17% | 61% | -0.34 [-0.60, -0.06] | -0.15 | -4.45 | 1.03 / 1.46 | -0.45 | 0.418 | 0.00 |
| C6 counter-HTF reversals (suppressed) | 605 | 19% | 71% | -0.81 [-1.13, -0.48] | -0.78 | -3.78 | 1.20 / 1.88 | -0.63 | 0.900 | 0.00 |
| B1 EMA 20/50 cross | 407 | 25% | 62% | -0.45 [-0.84, -0.09] | -0.38 | -1.94 | 1.26 / 1.66 | -0.61 | 0.199 | 0.00 |
| B2 Supertrend flip | 682 | 17% | 71% | -0.69 [-1.00, -0.36] | -0.58 | -6.24 | 1.13 / 1.85 | -0.68 | 0.542 | 0.00 |

Incremental value (difference in mean r_h, 90% month-cluster CI): HTF gate +0.24 [+0.05, +0.43]; realignment only -0.05 [-0.50, +0.32]; acceptance on MAJOR +0.02 [-0.41, +0.62]; acceptance on with-HTF +0.01 [-0.19, +0.23]; suppressed reversals vs MAJOR -0.42 [-0.95, +0.26]
PBO across C0–C6: **0.58** (192 buckets).
PBO, event-weighted buckets (post-hoc sensitivity): 0.55.
Purged CPCV, event-weighted (post-hoc): picks {'C4': 10, 'C2': 4, 'C3': 1}; mean OOS rank of the pick 0.29.
Purged CPCV, best-in-train config chosen per split: picks {'C4': 12, 'C3': 2, 'C2': 1}; mean OOS r_h of the pick -0.17; mean OOS rank of the pick 0.30 (0 = best, 1 = worst); path means [-0.16, -0.07, -0.07, -0.16, -0.41].

### Regime at entry (all groups)

| set | volatile | range | trend_up | trend_down | transition |
|---|---:|---:|---:|---:|---:|
| C2|bullish | +0.41 (n=29) | +0.76 (n=185) | +0.49 (n=80) | – | +0.90 (n=8) |
| C0|bullish | +0.73 (n=153) | +0.52 (n=887) | +0.95 (n=774) | +0.04 (n=139) | +1.92 (n=208) |
| C2|bearish | -0.34 (n=28) | -0.53 (n=96) | – | -0.10 (n=41) | -0.29 (n=5) |
| C0|bearish | -0.75 (n=368) | -0.50 (n=659) | -0.62 (n=189) | -0.39 (n=208) | -0.74 (n=166) |
