# V5 workstream M, stages A/B: BTC-regime context on crypto 1H/4H (results)

**EXPLORATORY ONLY. Review mode: `self_audited_exploration_only`.** Every candle read was examined in earlier studies.
Nothing here is independent confirmation or evidence of a predictive edge.
Configuration `reports/V5_M_B_CONFIG.md` (frozen); run at commit `90086a8`; manifest `57e107b08c6912a0…`.
Survivorship: the 35 pairs were chosen with hindsight from coins that became large; coins liquid in 2020–2021 but not cached are absent. Eligibility rules E1–E4 remove hindsight only within the set.

## Hypothesis verdicts

| hypothesis | primary (Holm within hypothesis) | stricter sensitivity (Holm across all 36 cells) |
|---|---|---|
| M-B1 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B2 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B3 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B4 | **INCONCLUSIVE** | INCONCLUSIVE |

The primary column is the decision. The sensitivity column never replaces it.

The two correction scopes agree on every cell and hypothesis.

## Stage B cells

Δ = mean(K) − mean(S∖K) (`rh_x` in ATR for M-B1–B3; `near` for M-B4). p = one-sided wild cluster restricted bootstrap; decisive p = larger of calendar-block and BTC-episode clustering. Removal = matched random removal (no BTC information).

| cell | n K / S∖K | pairs | Δ [t-CI calendar] | eq-pair Δ | qual. pairs | median pair Δ | share > 0 | altcoin Δ | mean K vs removal p97.5 | G cal / ep | episodes gate / not | p cal / ep | Holm within | Holm all | verdict | verdict (all-cell Holm) |
|---|---|---:|---|---:|---:|---:|---:|---:|---|---|---|---|---:|---:|---|---|
| M-B1|S-eng|+1|1H | 8133 / 2569 | 35 | +0.0539 [-0.3187, +0.4265] | +0.0705 | 32 | +0.1613 | 0.59 | -0.0015 | -0.1447 vs -0.1098 | 82 / 652 | 257 / 395 | 0.3909 / 0.3840 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B1|S-htf|+1|1H | 6842 / 3881 | 35 | +0.0824 [-0.2554, +0.4201] | -0.2017 | 32 | +0.0839 | 0.62 | +0.0750 | -0.1858 vs -0.1708 | 82 / 703 | 258 / 445 | 0.3132 / 0.3065 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B1|S-ema|+1|1H | 4518 / 7636 | 35 | -0.0017 [-0.3303, +0.3268] | -0.1262 | 32 | +0.0206 | 0.56 | -0.0247 | -0.0136 vs +0.0096 | 82 / 746 | 255 / 491 | 0.5052 / 0.5032 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B1|S-st|+1|1H | 4625 / 9701 | 35 | +0.3005 [+0.0199, +0.5811] | +0.0249 | 32 | +0.4000 | 0.72 | +0.2851 | +0.1632 vs +0.0823 | 82 / 751 | 255 / 496 | 0.0172 / 0.0443 | 0.3544 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B2|S-eng|-1|1H | 7757 / 3873 | 35 | -0.0439 [-0.5055, +0.4177] | -0.1660 | 32 | -0.0199 | 0.47 | -0.0702 | -0.2542 vs -0.1891 | 82 / 599 | 239 / 360 | 0.5708 / 0.5727 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B2|S-htf|-1|1H | 6065 / 6346 | 35 | +0.0902 [-0.1995, +0.3799] | +0.0949 | 32 | +0.0534 | 0.53 | +0.1219 | -0.1608 vs -0.1473 | 82 / 707 | 242 / 465 | 0.2733 / 0.2998 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B2|S-ema|-1|1H | 3446 / 8759 | 35 | -0.2940 [-0.6161, +0.0282] | -0.5173 | 32 | -0.3557 | 0.12 | -0.3049 | -0.2238 vs -0.1132 | 82 / 744 | 237 / 507 | 0.9620 / 0.9583 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B2|S-st|-1|1H | 3361 / 11000 | 35 | -0.1216 [-0.4637, +0.2205] | -0.2785 | 31 | -0.1285 | 0.42 | -0.1121 | -0.0874 vs -0.0147 | 82 / 736 | 237 / 499 | 0.7560 / 0.7433 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-eng|+1|1H | 7801 / 2901 | 35 | -0.2639 [-0.7160, +0.1882] | -0.2720 | 31 | -0.2307 | 0.32 | -0.2646 | -0.2291 vs -0.1184 | 82 / 561 | 393 / 168 | 0.8734 / 0.8834 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-eng|-1|1H | 7092 / 4538 | 35 | +0.0217 [-0.4679, +0.5114] | +0.0118 | 33 | -0.0484 | 0.48 | +0.0403 | -0.2311 vs -0.1889 | 82 / 508 | 347 / 161 | 0.4675 / 0.4710 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B3|S-htf|+1|1H | 7473 / 3250 | 35 | -0.4130 [-0.7136, -0.1124] | -0.5648 | 32 | -0.3716 | 0.19 | -0.4278 | -0.3408 vs -0.1629 | 82 / 604 | 407 / 197 | 0.9965 / 0.9963 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-htf|-1|1H | 8706 / 3705 | 35 | +0.0145 [-0.3841, +0.4131] | +0.0642 | 32 | +0.0303 | 0.53 | +0.0631 | -0.2026 vs -0.1637 | 82 / 580 | 387 / 193 | 0.4717 / 0.4733 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B3|S-ema|+1|1H | 8654 / 3500 | 35 | -0.3755 [-0.7325, -0.0185] | -0.3387 | 33 | -0.4482 | 0.15 | -0.4083 | -0.1206 vs +0.0329 | 82 / 621 | 416 / 205 | 0.9771 / 0.9826 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-ema|-1|1H | 8608 / 3597 | 35 | +0.2441 [-0.0479, +0.5362] | +0.4435 | 32 | +0.2216 | 0.84 | +0.2621 | +0.0592 vs +0.0221 | 82 / 621 | 415 / 206 | 0.0517 / 0.0576 | 0.9216 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B3|S-st|+1|1H | 9435 / 4891 | 35 | -0.2036 [-0.5202, +0.1130] | -0.2486 | 33 | -0.1802 | 0.27 | -0.2396 | -0.1098 vs +0.0128 | 82 / 629 | 416 / 213 | 0.8918 / 0.8841 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-st|-1|1H | 9719 / 4642 | 35 | +0.1652 [-0.2044, +0.5349] | +0.2476 | 33 | +0.1891 | 0.82 | +0.1439 | +0.0592 vs +0.0446 | 82 / 621 | 412 / 209 | 0.1931 / 0.1805 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B4|R-cr|-1|1H | 5363 / 7337 | 35 | -0.0038 [-0.0447, +0.0371] | -0.0119 | 33 | -0.0076 | 0.39 | -0.0026 | +0.3535 vs +0.3511 | 82 / 734 | 473 / 261 | 0.5769 / 0.5777 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B4|R-cr|+1|1H | 7141 / 6524 | 35 | -0.0358 [-0.0741, +0.0025] | -0.0539 | 33 | -0.0354 | 0.30 | -0.0373 | +0.3022 vs +0.3166 | 82 / 733 | 494 / 239 | 0.9657 / 0.9493 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B1|S-eng|+1|4H | 1751 / 383 | 34 | +0.9116 [-0.1667, +1.9899] | +1.2089 | 3 | +0.6299 | 1.00 | +0.9163 | +0.6662 vs +0.6273 | 41 / 127 | 45 / 82 | 0.0522 / 0.0398 | 0.3654 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B1|S-htf|+1|4H | 1195 / 504 | 35 | -0.2609 [-1.3083, +0.7865] | -0.2027 | 8 | -0.5300 | 0.38 | -0.3463 | -0.7516 vs -0.5883 | 41 / 139 | 46 / 93 | 0.6850 / 0.7157 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B1|S-ema|+1|4H | 1263 / 1696 | 35 | -0.1242 [-0.9840, +0.7356] | +0.1539 | 26 | -0.3386 | 0.31 | -0.0766 | -0.0896 vs +0.0097 | 41 / 148 | 46 / 102 | 0.6075 / 0.6155 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B1|S-st|+1|4H | 1195 / 2262 | 35 | +0.0857 [-0.9280, +1.0995] | -0.0800 | 27 | -0.1398 | 0.44 | +0.1141 | -0.0587 vs -0.0337 | 41 / 148 | 46 / 102 | 0.4251 / 0.4293 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B2|S-eng|-1|4H | 1563 / 1160 | 33 | +0.0807 [-1.0915, +1.2530] | -0.0549 | 23 | -0.0080 | 0.48 | +0.0223 | +0.0369 vs +0.1563 | 40 / 124 | 37 / 87 | 0.4509 / 0.4474 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B2|S-htf|-1|4H | 661 / 1182 | 34 | -0.1228 [-1.0711, +0.8254] | -0.2411 | 17 | -0.5193 | 0.41 | -0.0322 | -0.3117 vs +0.0419 | 40 / 131 | 36 / 95 | 0.6017 / 0.6000 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B2|S-ema|-1|4H | 628 / 2396 | 35 | -0.6258 [-1.5578, +0.3063] | -0.4161 | 16 | -0.7460 | 0.31 | -0.5048 | -0.0456 vs +0.3966 | 41 / 148 | 37 / 111 | 0.8993 / 0.9039 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B2|S-st|-1|4H | 690 / 2802 | 35 | -0.4504 [-1.5674, +0.6667] | -0.0400 | 19 | -0.6029 | 0.21 | -0.3473 | +0.2114 vs +0.5910 | 41 / 147 | 37 / 110 | 0.7738 / 0.7803 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-eng|+1|4H | 1569 / 565 | 34 | -0.4365 [-1.4756, +0.6026] | -0.3066 | 10 | -0.2508 | 0.40 | -0.4853 | +0.3871 vs +0.6455 | 41 / 110 | 71 / 39 | 0.7859 / 0.8017 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-eng|-1|4H | 1719 / 1004 | 33 | -0.2554 [-1.0147, +0.5039] | -0.3413 | 26 | -0.5419 | 0.27 | -0.2398 | -0.0916 vs +0.1030 | 40 / 107 | 71 / 36 | 0.7457 / 0.7040 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-htf|+1|4H | 1180 / 519 | 35 | -0.1044 [-0.9603, +0.7515] | -0.1731 | 9 | +0.0112 | 0.56 | -0.1029 | -0.7061 vs -0.5428 | 41 / 124 | 80 / 44 | 0.5918 / 0.5848 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-htf|-1|4H | 1319 / 524 | 34 | -0.1544 [-0.9644, +0.6557] | -0.0742 | 12 | -0.1958 | 0.42 | -0.1301 | -0.2768 vs -0.1230 | 40 / 115 | 75 / 40 | 0.6516 / 0.6209 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-ema|+1|4H | 2319 / 640 | 35 | -0.4158 [-1.5871, +0.7555] | -0.5851 | 17 | -0.3496 | 0.47 | -0.4799 | -0.1084 vs +0.0759 | 41 / 129 | 83 / 46 | 0.7594 / 0.7683 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-ema|-1|4H | 2170 / 854 | 35 | -0.6584 [-1.3993, +0.0825] | -0.3210 | 24 | -0.8730 | 0.17 | -0.6056 | +0.2643 vs +0.4881 | 41 / 130 | 83 / 47 | 0.9562 / 0.9548 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-st|+1|4H | 2473 / 984 | 35 | -0.5032 [-1.2730, +0.2665] | -0.6291 | 25 | -0.4912 | 0.24 | -0.5997 | -0.2580 vs -0.0078 | 41 / 132 | 83 / 49 | 0.9039 / 0.8785 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |
| M-B3|S-st|-1|4H | 2359 / 1133 | 35 | +0.3532 [-0.3072, +1.0136] | +0.4156 | 27 | +0.3309 | 0.63 | +0.3777 | +0.6874 vs +0.6602 | 41 / 131 | 83 / 48 | 0.1384 / 0.1591 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B4|R-cr|-1|4H | 1117 / 1784 | 35 | +0.0119 [-0.0545, +0.0782] | -0.0000 | 25 | -0.0084 | 0.48 | +0.0128 | +0.3196 vs +0.3268 | 41 / 142 | 97 / 45 | 0.3584 / 0.3700 | 1.0000 | 1.0000 | **INCONCLUSIVE** | INCONCLUSIVE |
| M-B4|R-cr|+1|4H | 2019 / 1338 | 35 | -0.0622 [-0.1461, +0.0217] | -0.0534 | 27 | -0.0693 | 0.30 | -0.0654 | +0.2779 vs +0.2957 | 41 / 144 | 107 / 37 | 0.9247 / 0.8889 | 1.0000 | 1.0000 | **NO VALUE** | NO VALUE |

## BTC episodes (effective number of distinct market regimes)

| TF · field | episodes | raw runs | by value (count, median/min/max length in candles) |
|---|---:|---:|---|
| 1H|btc_dir | 767 | 2016 | bear: 243 (72/24/320); bull: 263 (72/24/372); neutral: 261 (48/24/168) |
| 1H|btc_unstable | 638 | 2519 | no: 421 (90/24/399); yes: 217 (62/24/203) |
| 4H|btc_dir | 149 | 307 | bear: 37 (96/30/294); bull: 46 (132/30/390); neutral: 66 (60/30/156) |
| 4H|btc_unstable | 133 | 613 | no: 84 (110/30/420); yes: 49 (79/34/226) |

## Stage A: price-only reference (non-BTC pairs; BTC separately)

| signal · side · TF | n | pairs | mean [t-CI] (rh_x or near) | p wild | median | pair median of means | BTC n | BTC mean |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| S-eng|+1|1H | 10702 | 35 | -0.1576 [-0.3836, +0.0684] | 0.9082 | -0.7551 | -0.2226 | 598 | -0.0903 |
| S-eng|-1|1H | 11630 | 35 | -0.2396 [-0.4788, -0.0004] | 0.9730 | -0.6495 | -0.2497 | 419 | -0.1186 |
| S-htf|+1|1H | 10723 | 35 | -0.2156 [-0.3823, -0.0489] | 0.9933 | -0.4084 | -0.1711 | 521 | -0.3803 |
| S-htf|-1|1H | 12411 | 35 | -0.2069 [-0.3814, -0.0325] | 0.9890 | -0.2142 | -0.1920 | 494 | -0.2605 |
| S-ema|+1|1H | 12154 | 35 | -0.0125 [-0.1723, +0.1472] | 0.5626 | -0.1833 | -0.0553 | 549 | +0.1802 |
| S-ema|-1|1H | 12205 | 35 | -0.0128 [-0.1829, +0.1574] | 0.5562 | -0.0054 | +0.0484 | 549 | -0.2263 |
| S-st|+1|1H | 14326 | 35 | -0.0403 [-0.2081, +0.1275] | 0.6882 | -0.1737 | -0.0440 | 646 | +0.0562 |
| S-st|-1|1H | 14361 | 35 | +0.0058 [-0.1666, +0.1781] | 0.4700 | -0.0187 | +0.0016 | 646 | +0.1324 |
| R-cr|+1|1H | 13665 | 35 | +0.3193 [+0.2933, +0.3452] | 0.0001 | +0.0000 | +0.3151 | 624 | +0.3077 |
| R-cr|-1|1H | 12700 | 35 | +0.3557 [+0.3324, +0.3790] | 0.0001 | +0.0000 | +0.3547 | 647 | +0.3292 |
| S-eng|+1|4H | 2134 | 34 | +0.5026 [-0.2043, +1.2096] | 0.0906 | -0.5576 | +0.3662 | 174 | +0.1151 |
| S-eng|-1|4H | 2723 | 33 | +0.0025 [-0.5092, +0.5143] | 0.4979 | -0.0273 | -0.0276 | 80 | +0.1494 |
| S-htf|+1|4H | 1699 | 35 | -0.6742 [-1.2045, -0.1439] | 0.9885 | -1.1051 | -0.9760 | 91 | -0.2600 |
| S-htf|-1|4H | 1843 | 34 | -0.2330 [-0.7055, +0.2396] | 0.8426 | +0.0260 | -0.1235 | 62 | -0.2294 |
| S-ema|+1|4H | 2959 | 35 | -0.0184 [-0.4529, +0.4161] | 0.5272 | -0.5091 | -0.0481 | 142 | +0.0996 |
| S-ema|-1|4H | 3024 | 35 | +0.4502 [+0.0248, +0.8757] | 0.0191 | +0.6169 | +0.4390 | 142 | +0.8558 |
| S-st|+1|4H | 3457 | 35 | -0.1148 [-0.5470, +0.3174] | 0.6970 | -0.5341 | -0.2306 | 170 | +0.0744 |
| S-st|-1|4H | 3492 | 35 | +0.5728 [+0.2082, +0.9375] | 0.0015 | +0.6354 | +0.5991 | 169 | +1.2062 |
| R-cr|+1|4H | 3357 | 35 | +0.3027 [+0.2589, +0.3464] | 0.0001 | +0.0000 | +0.2977 | 150 | +0.2533 |
| R-cr|-1|4H | 2901 | 35 | +0.3123 [+0.2703, +0.3543] | 0.0001 | +0.0000 | +0.2917 | 153 | +0.3399 |

## R-cr detection (major tops for side −1, bottoms for +1): S, K, S∖K and matched-frequency baselines

| side · TF | set | alerts | recall | precision* |
|---|---|---:|---|---:|
| R-cr|+1|1H | S | 13665 | 0.660 | 0.176 |
| R-cr|+1|1H | K | 7141 | 0.452 | 0.214 |
| R-cr|+1|1H | SK | 6524 | 0.457 | 0.241 |
| R-cr|+1|1H | htf_flip matched to K | 7141 target, 585 shortfall blocks | 0.334 | 0.195 |
| R-cr|+1|1H | ema_cross matched to K | 7141 target, 159 shortfall blocks | 0.497 | 0.245 |
| R-cr|+1|1H | supertrend_flip matched to K | 7141 target, 87 shortfall blocks | 0.487 | 0.236 |
| R-cr|-1|1H | S | 12700 | 0.689 | 0.210 |
| R-cr|-1|1H | K | 5363 | 0.410 | 0.271 |
| R-cr|-1|1H | SK | 7337 | 0.507 | 0.253 |
| R-cr|-1|1H | htf_flip matched to K | 5363 target, 304 shortfall blocks | 0.318 | 0.238 |
| R-cr|-1|1H | ema_cross matched to K | 5363 target, 90 shortfall blocks | 0.440 | 0.296 |
| R-cr|-1|1H | supertrend_flip matched to K | 5363 target, 33 shortfall blocks | 0.416 | 0.271 |
| R-cr|+1|4H | S | 3357 | 0.656 | 0.194 |
| R-cr|+1|4H | K | 2019 | 0.437 | 0.205 |
| R-cr|+1|4H | SK | 1338 | 0.350 | 0.254 |
| R-cr|+1|4H | htf_flip matched to K | 2019 target, 416 shortfall blocks | 0.205 | 0.185 |
| R-cr|+1|4H | ema_cross matched to K | 2019 target, 198 shortfall blocks | 0.476 | 0.263 |
| R-cr|+1|4H | supertrend_flip matched to K | 2019 target, 141 shortfall blocks | 0.459 | 0.237 |
| R-cr|-1|4H | S | 2901 | 0.700 | 0.216 |
| R-cr|-1|4H | K | 1117 | 0.338 | 0.259 |
| R-cr|-1|4H | SK | 1784 | 0.459 | 0.226 |
| R-cr|-1|4H | htf_flip matched to K | 1117 target, 237 shortfall blocks | 0.235 | 0.273 |
| R-cr|-1|4H | ema_cross matched to K | 1117 target, 75 shortfall blocks | 0.354 | 0.293 |
| R-cr|-1|4H | supertrend_flip matched to K | 1117 target, 34 shortfall blocks | 0.334 | 0.258 |

## Trading outcomes (separate from signal quality; never decisive)

Net = fraction of notional after 20 bp round trip and short holding cost; slippage not modelled (sensitivity: +10 bp for pairs ranked > 10).

| set | trades | net mean | net median | net mean +slippage | MAE p5/p50/p95 | cost sources |
|---|---:|---:|---:|---:|---|---|
| A|S-eng|+1|1H · targets | 10702 | +0.0025 | -0.0160 | +0.0020 | 0.004/0.039/0.126 | {'none_long_spot': 10702} |
| A|S-eng|-1|1H · targets | 11621 | -0.0041 | -0.0139 | -0.0047 | 0.003/0.033/0.119 | {'estimated_crypto_10pct': 7832, 'observed_funding': 3789, 'no_exit_in_data': 9} |
| A|S-htf|+1|1H · targets | 10723 | +0.0027 | -0.0144 | +0.0022 | 0.003/0.028/0.092 | {'none_long_spot': 10723} |
| A|S-htf|-1|1H · targets | 12405 | -0.0016 | -0.0121 | -0.0022 | 0.002/0.024/0.085 | {'estimated_crypto_10pct': 8120, 'observed_funding': 4285, 'no_exit_in_data': 6} |
| A|S-ema|+1|1H · targets | 12148 | +0.0023 | -0.0122 | +0.0017 | 0.003/0.029/0.092 | {'none_long_spot': 12148, 'no_exit_in_data': 6} |
| A|S-ema|-1|1H · targets | 12204 | -0.0014 | -0.0098 | -0.0019 | 0.003/0.029/0.098 | {'estimated_crypto_10pct': 7923, 'observed_funding': 4281, 'no_exit_in_data': 1} |
| A|S-st|+1|1H · targets | 14320 | +0.0018 | -0.0094 | +0.0012 | 0.003/0.033/0.099 | {'none_long_spot': 14320, 'no_exit_in_data': 6} |
| A|S-st|-1|1H · targets | 14355 | -0.0036 | -0.0101 | -0.0041 | 0.003/0.033/0.107 | {'estimated_crypto_10pct': 9389, 'observed_funding': 4966, 'no_exit_in_data': 6} |
| A|R-cr|+1|1H · targets | 13665 | -0.0006 | -0.0145 | -0.0012 | 0.003/0.031/0.092 | {'none_long_spot': 13665} |
| A|R-cr|-1|1H · targets | 12700 | -0.0029 | -0.0127 | -0.0035 | 0.003/0.031/0.104 | {'estimated_crypto_10pct': 8091, 'observed_funding': 4609} |
| B|M-B1|S-eng|+1|1H · S | 10702 | +0.0025 | -0.0160 | +0.0020 | 0.004/0.039/0.126 | {'none_long_spot': 10702} |
| B|M-B1|S-eng|+1|1H · K | 8133 | +0.0020 | -0.0171 | +0.0015 | 0.004/0.040/0.122 | {'none_long_spot': 8133} |
| B|M-B1|S-eng|+1|1H · S∖K | 2569 | +0.0042 | -0.0121 | +0.0037 | 0.003/0.038/0.137 | {'none_long_spot': 2569} |
| B|M-B1|S-htf|+1|1H · S | 10723 | +0.0027 | -0.0144 | +0.0022 | 0.003/0.028/0.092 | {'none_long_spot': 10723} |
| B|M-B1|S-htf|+1|1H · K | 6842 | +0.0025 | -0.0144 | +0.0019 | 0.003/0.028/0.085 | {'none_long_spot': 6842} |
| B|M-B1|S-htf|+1|1H · S∖K | 3881 | +0.0031 | -0.0143 | +0.0026 | 0.003/0.029/0.103 | {'none_long_spot': 3881} |
| B|M-B1|S-ema|+1|1H · S | 12148 | +0.0023 | -0.0122 | +0.0017 | 0.003/0.029/0.092 | {'none_long_spot': 12148, 'no_exit_in_data': 6} |
| B|M-B1|S-ema|+1|1H · K | 4518 | +0.0022 | -0.0137 | +0.0017 | 0.003/0.030/0.090 | {'none_long_spot': 4518} |
| B|M-B1|S-ema|+1|1H · S∖K | 7630 | +0.0023 | -0.0114 | +0.0017 | 0.003/0.029/0.095 | {'none_long_spot': 7630, 'no_exit_in_data': 6} |
| B|M-B1|S-st|+1|1H · S | 14320 | +0.0018 | -0.0094 | +0.0012 | 0.003/0.033/0.099 | {'none_long_spot': 14320, 'no_exit_in_data': 6} |
| B|M-B1|S-st|+1|1H · K | 4625 | +0.0043 | -0.0088 | +0.0037 | 0.003/0.032/0.095 | {'none_long_spot': 4625} |
| B|M-B1|S-st|+1|1H · S∖K | 9695 | +0.0006 | -0.0095 | +0.0000 | 0.003/0.033/0.101 | {'none_long_spot': 9695, 'no_exit_in_data': 6} |
| B|M-B2|S-eng|-1|1H · S | 11621 | -0.0041 | -0.0139 | -0.0047 | 0.003/0.033/0.119 | {'estimated_crypto_10pct': 7832, 'observed_funding': 3789, 'no_exit_in_data': 9} |
| B|M-B2|S-eng|-1|1H · K | 7749 | -0.0060 | -0.0158 | -0.0065 | 0.004/0.036/0.135 | {'estimated_crypto_10pct': 5031, 'observed_funding': 2718, 'no_exit_in_data': 8} |
| B|M-B2|S-eng|-1|1H · S∖K | 3872 | -0.0004 | -0.0104 | -0.0010 | 0.003/0.029/0.091 | {'estimated_crypto_10pct': 2801, 'observed_funding': 1071, 'no_exit_in_data': 1} |
| B|M-B2|S-htf|-1|1H · S | 12405 | -0.0016 | -0.0121 | -0.0022 | 0.002/0.024/0.085 | {'estimated_crypto_10pct': 8120, 'observed_funding': 4285, 'no_exit_in_data': 6} |
| B|M-B2|S-htf|-1|1H · K | 6059 | -0.0032 | -0.0124 | -0.0038 | 0.002/0.025/0.093 | {'estimated_crypto_10pct': 3842, 'observed_funding': 2217, 'no_exit_in_data': 6} |
| B|M-B2|S-htf|-1|1H · S∖K | 6346 | -0.0001 | -0.0117 | -0.0007 | 0.002/0.022/0.075 | {'estimated_crypto_10pct': 4278, 'observed_funding': 2068} |
| B|M-B2|S-ema|-1|1H · S | 12204 | -0.0014 | -0.0098 | -0.0019 | 0.003/0.029/0.098 | {'estimated_crypto_10pct': 7923, 'observed_funding': 4281, 'no_exit_in_data': 1} |
| B|M-B2|S-ema|-1|1H · K | 3445 | -0.0043 | -0.0120 | -0.0049 | 0.003/0.030/0.103 | {'estimated_crypto_10pct': 2254, 'observed_funding': 1191, 'no_exit_in_data': 1} |
| B|M-B2|S-ema|-1|1H · S∖K | 8759 | -0.0002 | -0.0083 | -0.0008 | 0.003/0.028/0.095 | {'estimated_crypto_10pct': 5669, 'observed_funding': 3090} |
| B|M-B2|S-st|-1|1H · S | 14355 | -0.0036 | -0.0101 | -0.0041 | 0.003/0.033/0.107 | {'estimated_crypto_10pct': 9389, 'observed_funding': 4966, 'no_exit_in_data': 6} |
| B|M-B2|S-st|-1|1H · K | 3355 | -0.0042 | -0.0133 | -0.0048 | 0.004/0.034/0.109 | {'estimated_crypto_10pct': 2264, 'observed_funding': 1091, 'no_exit_in_data': 6} |
| B|M-B2|S-st|-1|1H · S∖K | 11000 | -0.0034 | -0.0090 | -0.0039 | 0.003/0.033/0.106 | {'estimated_crypto_10pct': 7125, 'observed_funding': 3875} |
| B|M-B3|S-eng|+1|1H · S | 10702 | +0.0025 | -0.0160 | +0.0020 | 0.004/0.039/0.126 | {'none_long_spot': 10702} |
| B|M-B3|S-eng|+1|1H · K | 7801 | +0.0004 | -0.0178 | -0.0001 | 0.004/0.038/0.122 | {'none_long_spot': 7801} |
| B|M-B3|S-eng|+1|1H · S∖K | 2901 | +0.0083 | -0.0098 | +0.0078 | 0.004/0.042/0.134 | {'none_long_spot': 2901} |
| B|M-B3|S-eng|-1|1H · S | 11621 | -0.0041 | -0.0139 | -0.0047 | 0.003/0.033/0.119 | {'estimated_crypto_10pct': 7832, 'observed_funding': 3789, 'no_exit_in_data': 9} |
| B|M-B3|S-eng|-1|1H · K | 7084 | -0.0035 | -0.0148 | -0.0040 | 0.003/0.030/0.092 | {'estimated_crypto_10pct': 4831, 'observed_funding': 2253, 'no_exit_in_data': 8} |
| B|M-B3|S-eng|-1|1H · S∖K | 4537 | -0.0051 | -0.0117 | -0.0057 | 0.004/0.042/0.156 | {'estimated_crypto_10pct': 3001, 'observed_funding': 1536, 'no_exit_in_data': 1} |
| B|M-B3|S-htf|+1|1H · S | 10723 | +0.0027 | -0.0144 | +0.0022 | 0.003/0.028/0.092 | {'none_long_spot': 10723} |
| B|M-B3|S-htf|+1|1H · K | 7473 | -0.0001 | -0.0156 | -0.0006 | 0.003/0.027/0.087 | {'none_long_spot': 7473} |
| B|M-B3|S-htf|+1|1H · S∖K | 3250 | +0.0092 | -0.0085 | +0.0086 | 0.003/0.031/0.102 | {'none_long_spot': 3250} |
| B|M-B3|S-htf|-1|1H · S | 12405 | -0.0016 | -0.0121 | -0.0022 | 0.002/0.024/0.085 | {'estimated_crypto_10pct': 8120, 'observed_funding': 4285, 'no_exit_in_data': 6} |
| B|M-B3|S-htf|-1|1H · K | 8702 | -0.0009 | -0.0124 | -0.0015 | 0.002/0.022/0.076 | {'estimated_crypto_10pct': 5680, 'observed_funding': 3022, 'no_exit_in_data': 4} |
| B|M-B3|S-htf|-1|1H · S∖K | 3703 | -0.0032 | -0.0111 | -0.0038 | 0.003/0.027/0.108 | {'estimated_crypto_10pct': 2440, 'observed_funding': 1263, 'no_exit_in_data': 2} |
| B|M-B3|S-ema|+1|1H · S | 12148 | +0.0023 | -0.0122 | +0.0017 | 0.003/0.029/0.092 | {'none_long_spot': 12148, 'no_exit_in_data': 6} |
| B|M-B3|S-ema|+1|1H · K | 8648 | -0.0000 | -0.0149 | -0.0006 | 0.003/0.029/0.088 | {'none_long_spot': 8648, 'no_exit_in_data': 6} |
| B|M-B3|S-ema|+1|1H · S∖K | 3500 | +0.0080 | -0.0020 | +0.0074 | 0.003/0.031/0.101 | {'none_long_spot': 3500} |
| B|M-B3|S-ema|-1|1H · S | 12204 | -0.0014 | -0.0098 | -0.0019 | 0.003/0.029/0.098 | {'estimated_crypto_10pct': 7923, 'observed_funding': 4281, 'no_exit_in_data': 1} |
| B|M-B3|S-ema|-1|1H · K | 8607 | +0.0002 | -0.0101 | -0.0004 | 0.003/0.027/0.088 | {'estimated_crypto_10pct': 5583, 'observed_funding': 3024, 'no_exit_in_data': 1} |
| B|M-B3|S-ema|-1|1H · S∖K | 3597 | -0.0051 | -0.0090 | -0.0056 | 0.004/0.034/0.120 | {'estimated_crypto_10pct': 2340, 'observed_funding': 1257} |
| B|M-B3|S-st|+1|1H · S | 14320 | +0.0018 | -0.0094 | +0.0012 | 0.003/0.033/0.099 | {'none_long_spot': 14320, 'no_exit_in_data': 6} |
| B|M-B3|S-st|+1|1H · K | 9429 | -0.0002 | -0.0126 | -0.0008 | 0.003/0.032/0.093 | {'none_long_spot': 9429, 'no_exit_in_data': 6} |
| B|M-B3|S-st|+1|1H · S∖K | 4891 | +0.0057 | -0.0040 | +0.0051 | 0.003/0.035/0.112 | {'none_long_spot': 4891} |
| B|M-B3|S-st|-1|1H · S | 14355 | -0.0036 | -0.0101 | -0.0041 | 0.003/0.033/0.107 | {'estimated_crypto_10pct': 9389, 'observed_funding': 4966, 'no_exit_in_data': 6} |
| B|M-B3|S-st|-1|1H · K | 9713 | -0.0015 | -0.0089 | -0.0021 | 0.003/0.031/0.096 | {'estimated_crypto_10pct': 6374, 'observed_funding': 3339, 'no_exit_in_data': 6} |
| B|M-B3|S-st|-1|1H · S∖K | 4642 | -0.0080 | -0.0128 | -0.0085 | 0.004/0.039/0.124 | {'estimated_crypto_10pct': 3015, 'observed_funding': 1627} |
| B|M-B4|R-cr|-1|1H · S | 12700 | -0.0029 | -0.0127 | -0.0035 | 0.003/0.031/0.104 | {'estimated_crypto_10pct': 8091, 'observed_funding': 4609} |
| B|M-B4|R-cr|-1|1H · K | 5363 | -0.0018 | -0.0119 | -0.0023 | 0.003/0.030/0.111 | {'estimated_crypto_10pct': 3459, 'observed_funding': 1904} |
| B|M-B4|R-cr|-1|1H · S∖K | 7337 | -0.0038 | -0.0136 | -0.0043 | 0.003/0.031/0.099 | {'estimated_crypto_10pct': 4632, 'observed_funding': 2705} |
| B|M-B4|R-cr|+1|1H · S | 13665 | -0.0006 | -0.0145 | -0.0012 | 0.003/0.031/0.092 | {'none_long_spot': 13665} |
| B|M-B4|R-cr|+1|1H · K | 7141 | +0.0002 | -0.0133 | -0.0003 | 0.003/0.029/0.086 | {'none_long_spot': 7141} |
| B|M-B4|R-cr|+1|1H · S∖K | 6524 | -0.0016 | -0.0159 | -0.0021 | 0.004/0.033/0.096 | {'none_long_spot': 6524} |
| A|S-eng|+1|4H · targets | 2134 | +0.0489 | -0.0262 | +0.0484 | 0.008/0.087/0.267 | {'none_long_spot': 2134} |
| A|S-eng|-1|4H · targets | 2719 | -0.0095 | -0.0320 | -0.0102 | 0.007/0.069/0.207 | {'estimated_crypto_10pct': 1848, 'observed_funding': 871, 'no_exit_in_data': 4} |
| A|S-htf|+1|4H · targets | 1696 | +0.0067 | -0.0378 | +0.0062 | 0.008/0.069/0.200 | {'none_long_spot': 1696, 'no_exit_in_data': 3} |
| A|S-htf|-1|4H · targets | 1840 | -0.0014 | -0.0234 | -0.0020 | 0.006/0.054/0.176 | {'estimated_crypto_10pct': 1197, 'observed_funding': 643, 'no_exit_in_data': 3} |
| A|S-ema|+1|4H · targets | 2955 | +0.0054 | -0.0394 | +0.0049 | 0.007/0.069/0.191 | {'none_long_spot': 2955, 'no_exit_in_data': 4} |
| A|S-ema|-1|4H · targets | 3022 | +0.0026 | -0.0187 | +0.0021 | 0.007/0.065/0.202 | {'estimated_crypto_10pct': 1956, 'observed_funding': 1066, 'no_exit_in_data': 2} |
| A|S-st|+1|4H · targets | 3442 | +0.0036 | -0.0409 | +0.0031 | 0.008/0.077/0.194 | {'none_long_spot': 3442, 'no_exit_in_data': 15} |
| A|S-st|-1|4H · targets | 3489 | +0.0033 | -0.0059 | +0.0027 | 0.007/0.070/0.229 | {'estimated_crypto_10pct': 2261, 'observed_funding': 1228, 'no_exit_in_data': 3} |
| A|R-cr|+1|4H · targets | 3357 | -0.0024 | -0.0395 | -0.0030 | 0.008/0.068/0.166 | {'none_long_spot': 3357} |
| A|R-cr|-1|4H · targets | 2901 | -0.0060 | -0.0275 | -0.0065 | 0.007/0.069/0.220 | {'estimated_crypto_10pct': 1811, 'observed_funding': 1090} |
| B|M-B1|S-eng|+1|4H · S | 2134 | +0.0489 | -0.0262 | +0.0484 | 0.008/0.087/0.267 | {'none_long_spot': 2134} |
| B|M-B1|S-eng|+1|4H · K | 1751 | +0.0553 | -0.0251 | +0.0548 | 0.010/0.089/0.265 | {'none_long_spot': 1751} |
| B|M-B1|S-eng|+1|4H · S∖K | 383 | +0.0193 | -0.0303 | +0.0189 | 0.006/0.075/0.289 | {'none_long_spot': 383} |
| B|M-B1|S-htf|+1|4H · S | 1696 | +0.0067 | -0.0378 | +0.0062 | 0.008/0.069/0.200 | {'none_long_spot': 1696, 'no_exit_in_data': 3} |
| B|M-B1|S-htf|+1|4H · K | 1193 | +0.0056 | -0.0406 | +0.0051 | 0.010/0.071/0.197 | {'none_long_spot': 1193, 'no_exit_in_data': 2} |
| B|M-B1|S-htf|+1|4H · S∖K | 503 | +0.0090 | -0.0302 | +0.0086 | 0.005/0.066/0.219 | {'none_long_spot': 503, 'no_exit_in_data': 1} |
| B|M-B1|S-ema|+1|4H · S | 2955 | +0.0054 | -0.0394 | +0.0049 | 0.007/0.069/0.191 | {'none_long_spot': 2955, 'no_exit_in_data': 4} |
| B|M-B1|S-ema|+1|4H · K | 1259 | +0.0099 | -0.0404 | +0.0093 | 0.009/0.070/0.191 | {'none_long_spot': 1259, 'no_exit_in_data': 4} |
| B|M-B1|S-ema|+1|4H · S∖K | 1696 | +0.0020 | -0.0381 | +0.0015 | 0.007/0.068/0.190 | {'none_long_spot': 1696} |
| B|M-B1|S-st|+1|4H · S | 3442 | +0.0036 | -0.0409 | +0.0031 | 0.008/0.077/0.194 | {'none_long_spot': 3442, 'no_exit_in_data': 15} |
| B|M-B1|S-st|+1|4H · K | 1187 | +0.0100 | -0.0417 | +0.0094 | 0.006/0.081/0.206 | {'none_long_spot': 1187, 'no_exit_in_data': 8} |
| B|M-B1|S-st|+1|4H · S∖K | 2255 | +0.0003 | -0.0403 | -0.0002 | 0.008/0.075/0.187 | {'none_long_spot': 2255, 'no_exit_in_data': 7} |
| B|M-B2|S-eng|-1|4H · S | 2719 | -0.0095 | -0.0320 | -0.0102 | 0.007/0.069/0.207 | {'estimated_crypto_10pct': 1848, 'observed_funding': 871, 'no_exit_in_data': 4} |
| B|M-B2|S-eng|-1|4H · K | 1562 | -0.0091 | -0.0336 | -0.0097 | 0.007/0.075/0.231 | {'estimated_crypto_10pct': 1000, 'observed_funding': 562, 'no_exit_in_data': 1} |
| B|M-B2|S-eng|-1|4H · S∖K | 1157 | -0.0102 | -0.0308 | -0.0108 | 0.008/0.061/0.173 | {'estimated_crypto_10pct': 848, 'observed_funding': 309, 'no_exit_in_data': 3} |
| B|M-B2|S-htf|-1|4H · S | 1840 | -0.0014 | -0.0234 | -0.0020 | 0.006/0.054/0.176 | {'estimated_crypto_10pct': 1197, 'observed_funding': 643, 'no_exit_in_data': 3} |
| B|M-B2|S-htf|-1|4H · K | 661 | -0.0044 | -0.0203 | -0.0049 | 0.008/0.057/0.212 | {'estimated_crypto_10pct': 394, 'observed_funding': 267} |
| B|M-B2|S-htf|-1|4H · S∖K | 1179 | +0.0003 | -0.0257 | -0.0003 | 0.005/0.052/0.154 | {'estimated_crypto_10pct': 803, 'observed_funding': 376, 'no_exit_in_data': 3} |
| B|M-B2|S-ema|-1|4H · S | 3022 | +0.0026 | -0.0187 | +0.0021 | 0.007/0.065/0.202 | {'estimated_crypto_10pct': 1956, 'observed_funding': 1066, 'no_exit_in_data': 2} |
| B|M-B2|S-ema|-1|4H · K | 628 | +0.0083 | -0.0140 | +0.0078 | 0.007/0.065/0.200 | {'estimated_crypto_10pct': 404, 'observed_funding': 224} |
| B|M-B2|S-ema|-1|4H · S∖K | 2394 | +0.0012 | -0.0195 | +0.0006 | 0.007/0.065/0.204 | {'estimated_crypto_10pct': 1552, 'observed_funding': 842, 'no_exit_in_data': 2} |
| B|M-B2|S-st|-1|4H · S | 3489 | +0.0033 | -0.0059 | +0.0027 | 0.007/0.070/0.229 | {'estimated_crypto_10pct': 2261, 'observed_funding': 1228, 'no_exit_in_data': 3} |
| B|M-B2|S-st|-1|4H · K | 689 | +0.0073 | -0.0178 | +0.0068 | 0.007/0.075/0.229 | {'estimated_crypto_10pct': 458, 'observed_funding': 231, 'no_exit_in_data': 1} |
| B|M-B2|S-st|-1|4H · S∖K | 2800 | +0.0023 | -0.0023 | +0.0017 | 0.007/0.069/0.229 | {'estimated_crypto_10pct': 1803, 'observed_funding': 997, 'no_exit_in_data': 2} |
| B|M-B3|S-eng|+1|4H · S | 2134 | +0.0489 | -0.0262 | +0.0484 | 0.008/0.087/0.267 | {'none_long_spot': 2134} |
| B|M-B3|S-eng|+1|4H · K | 1569 | +0.0463 | -0.0326 | +0.0459 | 0.009/0.084/0.268 | {'none_long_spot': 1569} |
| B|M-B3|S-eng|+1|4H · S∖K | 565 | +0.0558 | -0.0081 | +0.0553 | 0.008/0.095/0.265 | {'none_long_spot': 565} |
| B|M-B3|S-eng|-1|4H · S | 2719 | -0.0095 | -0.0320 | -0.0102 | 0.007/0.069/0.207 | {'estimated_crypto_10pct': 1848, 'observed_funding': 871, 'no_exit_in_data': 4} |
| B|M-B3|S-eng|-1|4H · K | 1715 | -0.0131 | -0.0351 | -0.0137 | 0.007/0.066/0.184 | {'estimated_crypto_10pct': 1166, 'observed_funding': 549, 'no_exit_in_data': 4} |
| B|M-B3|S-eng|-1|4H · S∖K | 1004 | -0.0035 | -0.0205 | -0.0042 | 0.008/0.073/0.255 | {'estimated_crypto_10pct': 682, 'observed_funding': 322} |
| B|M-B3|S-htf|+1|4H · S | 1696 | +0.0067 | -0.0378 | +0.0062 | 0.008/0.069/0.200 | {'none_long_spot': 1696, 'no_exit_in_data': 3} |
| B|M-B3|S-htf|+1|4H · K | 1177 | +0.0037 | -0.0379 | +0.0032 | 0.008/0.066/0.198 | {'none_long_spot': 1177, 'no_exit_in_data': 3} |
| B|M-B3|S-htf|+1|4H · S∖K | 519 | +0.0134 | -0.0374 | +0.0129 | 0.009/0.076/0.205 | {'none_long_spot': 519} |
| B|M-B3|S-htf|-1|4H · S | 1840 | -0.0014 | -0.0234 | -0.0020 | 0.006/0.054/0.176 | {'estimated_crypto_10pct': 1197, 'observed_funding': 643, 'no_exit_in_data': 3} |
| B|M-B3|S-htf|-1|4H · K | 1316 | +0.0013 | -0.0234 | +0.0007 | 0.005/0.048/0.149 | {'estimated_crypto_10pct': 844, 'observed_funding': 472, 'no_exit_in_data': 3} |
| B|M-B3|S-htf|-1|4H · S∖K | 524 | -0.0082 | -0.0236 | -0.0088 | 0.008/0.070/0.232 | {'estimated_crypto_10pct': 353, 'observed_funding': 171} |
| B|M-B3|S-ema|+1|4H · S | 2955 | +0.0054 | -0.0394 | +0.0049 | 0.007/0.069/0.191 | {'none_long_spot': 2955, 'no_exit_in_data': 4} |
| B|M-B3|S-ema|+1|4H · K | 2315 | +0.0030 | -0.0399 | +0.0024 | 0.008/0.065/0.178 | {'none_long_spot': 2315, 'no_exit_in_data': 4} |
| B|M-B3|S-ema|+1|4H · S∖K | 640 | +0.0143 | -0.0385 | +0.0137 | 0.006/0.084/0.229 | {'none_long_spot': 640} |
| B|M-B3|S-ema|-1|4H · S | 3022 | +0.0026 | -0.0187 | +0.0021 | 0.007/0.065/0.202 | {'estimated_crypto_10pct': 1956, 'observed_funding': 1066, 'no_exit_in_data': 2} |
| B|M-B3|S-ema|-1|4H · K | 2168 | -0.0016 | -0.0291 | -0.0021 | 0.006/0.063/0.182 | {'estimated_crypto_10pct': 1404, 'observed_funding': 764, 'no_exit_in_data': 2} |
| B|M-B3|S-ema|-1|4H · S∖K | 854 | +0.0133 | +0.0113 | +0.0128 | 0.008/0.071/0.263 | {'estimated_crypto_10pct': 552, 'observed_funding': 302} |
| B|M-B3|S-st|+1|4H · S | 3442 | +0.0036 | -0.0409 | +0.0031 | 0.008/0.077/0.194 | {'none_long_spot': 3442, 'no_exit_in_data': 15} |
| B|M-B3|S-st|+1|4H · K | 2458 | +0.0010 | -0.0463 | +0.0004 | 0.007/0.074/0.186 | {'none_long_spot': 2458, 'no_exit_in_data': 15} |
| B|M-B3|S-st|+1|4H · S∖K | 984 | +0.0103 | -0.0228 | +0.0097 | 0.008/0.085/0.213 | {'none_long_spot': 984} |
| B|M-B3|S-st|-1|4H · S | 3489 | +0.0033 | -0.0059 | +0.0027 | 0.007/0.070/0.229 | {'estimated_crypto_10pct': 2261, 'observed_funding': 1228, 'no_exit_in_data': 3} |
| B|M-B3|S-st|-1|4H · K | 2357 | +0.0045 | -0.0122 | +0.0039 | 0.006/0.066/0.193 | {'estimated_crypto_10pct': 1538, 'observed_funding': 819, 'no_exit_in_data': 2} |
| B|M-B3|S-st|-1|4H · S∖K | 1132 | +0.0008 | +0.0064 | +0.0003 | 0.009/0.077/0.289 | {'estimated_crypto_10pct': 723, 'observed_funding': 409, 'no_exit_in_data': 1} |
| B|M-B4|R-cr|-1|4H · S | 2901 | -0.0060 | -0.0275 | -0.0065 | 0.007/0.069/0.220 | {'estimated_crypto_10pct': 1811, 'observed_funding': 1090} |
| B|M-B4|R-cr|-1|4H · K | 1117 | +0.0082 | -0.0101 | +0.0077 | 0.006/0.064/0.203 | {'estimated_crypto_10pct': 713, 'observed_funding': 404} |
| B|M-B4|R-cr|-1|4H · S∖K | 1784 | -0.0149 | -0.0378 | -0.0154 | 0.008/0.074/0.231 | {'estimated_crypto_10pct': 1098, 'observed_funding': 686} |
| B|M-B4|R-cr|+1|4H · S | 3357 | -0.0024 | -0.0395 | -0.0030 | 0.008/0.068/0.166 | {'none_long_spot': 3357} |
| B|M-B4|R-cr|+1|4H · K | 2019 | +0.0008 | -0.0390 | +0.0002 | 0.007/0.065/0.164 | {'none_long_spot': 2019} |
| B|M-B4|R-cr|+1|4H · S∖K | 1338 | -0.0072 | -0.0409 | -0.0077 | 0.010/0.072/0.169 | {'none_long_spot': 1338} |

## Exclusions (counted, never hidden)

```
{
 "1H": {
  "S-eng|+1": {
   "in_window": 15932,
   "first_fail": {
    "pass": 10702,
    "E2": 2567,
    "E1": 1423,
    "E3": 1217,
    "E6": 23
   },
   "no_exit": 0,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 10702
  },
  "S-eng|-1": {
   "in_window": 17600,
   "first_fail": {
    "pass": 11637,
    "E2": 3236,
    "E3": 1630,
    "E1": 1050,
    "E6": 47
   },
   "no_exit": 6,
   "gap": 1,
   "no_benchmark": 0,
   "in_S": 11630
  },
  "S-htf|+1": {
   "in_window": 16082,
   "first_fail": {
    "pass": 10723,
    "E2": 2618,
    "E1": 1438,
    "E3": 1289,
    "E6": 14
   },
   "no_exit": 0,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 10723
  },
  "S-htf|-1": {
   "in_window": 18904,
   "first_fail": {
    "pass": 12413,
    "E2": 3635,
    "E3": 1631,
    "E1": 1212,
    "E6": 13
   },
   "no_exit": 2,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 12411
  },
  "S-ema|+1": {
   "in_window": 18196,
   "first_fail": {
    "pass": 12157,
    "E2": 3223,
    "E3": 1505,
    "E1": 1302,
    "E6": 9
   },
   "no_exit": 3,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 12154
  },
  "S-ema|-1": {
   "in_window": 18195,
   "first_fail": {
    "pass": 12206,
    "E2": 3186,
    "E3": 1498,
    "E1": 1298,
    "E6": 7
   },
   "no_exit": 1,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 12205
  },
  "S-st|+1": {
   "in_window": 21560,
   "first_fail": {
    "pass": 14329,
    "E2": 3844,
    "E3": 1847,
    "E1": 1519,
    "E6": 21
   },
   "no_exit": 3,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 14326
  },
  "S-st|-1": {
   "in_window": 21553,
   "first_fail": {
    "pass": 14364,
    "E2": 3817,
    "E3": 1841,
    "E1": 1515,
    "E6": 16
   },
   "no_exit": 3,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 14361
  },
  "R-cr|+1": {
   "in_window": 20396,
   "first_fail": {
    "pass": 13770,
    "E2": 3509,
    "E3": 1717,
    "E1": 1388,
    "E6": 12
   },
   "no_exit": 11,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 13665
  },
  "R-cr|-1": {
   "in_window": 18805,
   "first_fail": {
    "pass": 12748,
    "E2": 3043,
    "E3": 1585,
    "E1": 1422,
    "E6": 6,
    "E7": 1
   },
   "no_exit": 2,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 12700
  }
 },
 "4H": {
  "S-eng|+1": {
   "in_window": 3102,
   "first_fail": {
    "pass": 2134,
    "E1": 363,
    "E2": 311,
    "E3": 270,
    "E6": 24
   },
   "no_exit": 0,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 2134
  },
  "S-eng|-1": {
   "in_window": 4396,
   "first_fail": {
    "pass": 2729,
    "E2": 1005,
    "E3": 414,
    "E1": 202,
    "E6": 46
   },
   "no_exit": 4,
   "gap": 2,
   "no_benchmark": 0,
   "in_S": 2723
  },
  "S-htf|+1": {
   "in_window": 2392,
   "first_fail": {
    "pass": 1699,
    "E1": 256,
    "E2": 243,
    "E3": 183,
    "E6": 11
   },
   "no_exit": 0,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 1699
  },
  "S-htf|-1": {
   "in_window": 2956,
   "first_fail": {
    "pass": 1845,
    "E2": 679,
    "E3": 234,
    "E1": 186,
    "E6": 12
   },
   "no_exit": 2,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 1843
  },
  "S-ema|+1": {
   "in_window": 4499,
   "first_fail": {
    "pass": 2961,
    "E2": 854,
    "E3": 358,
    "E1": 308,
    "E6": 18
   },
   "no_exit": 2,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 2959
  },
  "S-ema|-1": {
   "in_window": 4507,
   "first_fail": {
    "pass": 3028,
    "E2": 795,
    "E3": 367,
    "E1": 300,
    "E6": 17
   },
   "no_exit": 4,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 3024
  },
  "S-st|+1": {
   "in_window": 5195,
   "first_fail": {
    "pass": 3457,
    "E2": 932,
    "E3": 444,
    "E1": 338,
    "E6": 24
   },
   "no_exit": 0,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 3457
  },
  "S-st|-1": {
   "in_window": 5202,
   "first_fail": {
    "pass": 3507,
    "E2": 895,
    "E3": 450,
    "E1": 330,
    "E6": 20
   },
   "no_exit": 15,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 3492
  },
  "R-cr|+1": {
   "in_window": 5147,
   "first_fail": {
    "pass": 3422,
    "E2": 1018,
    "E3": 421,
    "E1": 275,
    "E6": 11
   },
   "no_exit": 3,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 3357
  },
  "R-cr|-1": {
   "in_window": 4213,
   "first_fail": {
    "pass": 2993,
    "E2": 586,
    "E3": 313,
    "E1": 312,
    "E6": 9
   },
   "no_exit": 11,
   "gap": 0,
   "no_benchmark": 0,
   "in_S": 2901
  }
 }
}
```
