# V5 family C (major tops), 1H/4H exploration: summary report

> **EXPLORATORY ONLY.** Every candle used here was already examined in earlier studies (V3, V4, V4.1).
> Review mode is `self_audited_exploration_only`: no external review took place
> ([`V5_REVIEW_WAIVER.md`](V5_REVIEW_WAIVER.md)). Nothing here is independent confirmation, and nothing
> here shows a predictive edge or profitability.

Inputs:
* frozen configuration [`V5_C_EXPLORATION_CONFIG.md`](V5_C_EXPLORATION_CONFIG.md) (commit `74d5ae5`, unchanged);
* run at commit `b3be192`;
* data manifest `57e107b0…`;
* raw output [`v5_c_x1_results.json`](v5_c_x1_results.json);
* full tables in [`V5_C_EXPLORATION_RESULTS.md`](V5_C_EXPLORATION_RESULTS.md).

Tables are produced by `python scripts/v5_c_summary.py <part>`, which reads the stored json only and
recomputes nothing.

## 1. Run integrity

| check | result |
|---|---|
| trials recorded | 18 of 18: `c-x1-{C1a,C1b,C2,C3,C4}-W-{1H,4H}`, `c-x1-{C3,C5a,C5b}-C-{1H,4H}`, `c-x1-baselines-{1H,4H}` |
| recorded before computation | yes: each TF's 9 records were committed (one commit each) before that TF's worker pool started (log order) |
| ledger hash chain | valid; `verify_against_git` passes; committed ledger = working ledger; head `e8aefcb2…` |
| code state at record time | clean and committed; one config sha256 across all 18 records |
| completion | 1H: 96/96 instruments computed; 4H: 96/96; exit status 0 |
| execution failures | none (no worker exception, no instrument skipped) |
| changes after seeing results | none to the config, detectors, baselines, evaluation or selection code; this report adds only a read-only table script (`scripts/v5_c_summary.py`) |

## 2. Mechanical outcome (frozen §8 selection, §9 rejection)

| detector | kind | best TF (frozen: highest score) | score | p wild < 0.05 | lead > 0 (W) | remain ≥ 0.5 (C) | prec* ≥ best matched baseline (C) | qualifies | §9 |
|---|---|---|---:|---|---|---|---|---|---|
| C1a | warning | 1H | -0.0628 | **no** (0.8668) | yes | n/a | n/a | no | not dropped |
| C1b | warning | 1H | -0.0735 | **no** (0.9539) | yes | n/a | n/a | no | not dropped |
| C2 | warning | 1H | -0.0658 | **no** (0.9930) | yes | n/a | n/a | no | not dropped |
| C3 | warning | 1H | -0.0576 | **no** (0.9940) | yes | n/a | n/a | no | not dropped |
| C4 | warning | 4H | -0.0254 | **no** (0.1196) | yes | n/a | n/a | no | not dropped |
| C3 | confirmation | 1H | -0.0666 | **no** (1.0000) | n/a | yes | **no** (0.068 vs 0.217 ema_cross) | no | not dropped |
| C5a | confirmation | 1H | +0.0500 | yes (0.0001) | n/a | yes | **no** (0.205 vs 0.239 ema_cross) | no | not dropped |
| C5b | confirmation | 1H | +0.0498 | yes (0.0001) | n/a | yes | **no** (0.201 vs 0.237 ema_cross) | no | not dropped |

**Selected for G2: none. Family C at configuration x1: REJECTED at exploration or REDESIGN** (frozen §8.5).

How the variants failed:
* **No warning variant** reaches p < 0.05 in its best TF.
* **C3 confirmation** has a pooled lift CI entirely below 0 at both TFs.
* **C5a and C5b** pass the lift and move-remaining requirements but fail the matched-baseline test: their
  duplicate-free precision is lower than the EMA-cross baseline's at matched frequency (1H). At 4H the same
  holds in every cell, against the HTF-flip baseline.

Under §9, no variant is **dropped**. The rule needs the lift CI below 0 (or lead ≤ 0) in *every* evaluable
cell. Rates (8 instruments) and, for some variants, commodities have CIs wide enough to cross 0. So,
mechanically, the non-selected variants are **inconclusive**, not dropped.

## 3. What the numbers say (exploratory)

**Warnings (C1a, C1b, C2, C3, C4).**
* All five fire well before tops: median lead is 23 to 65 candles at 1H and 8 to 42 at 4H, and recall is high.
* They do so no more often than an arbitrary warm candle in the same HTF state. Pooled lift is ≤ 1 in every
  1H cell; at 4H only C4 has a pooled point estimate above 0.
* The pooled excess CI lies entirely below 0 for C2 and C3 at 1H.
* High recall here reflects how common these conditions are in bull markets, not tops specifically.
  Duplicate-free precision is 0.09 to 0.22.
* C4 at 4H is the best warning cell: excess +0.044 [−0.025, +0.112], p = 0.12, median lead 8 candles. It
  does not qualify, and it is 1 of 10 warning cells.

**Confirmations.**
* **C3** (failed breakout) fires about 135 times per instrument-year at 1H, with precision* 0.07. It is the
  noisiest variant and is below every baseline.
* **C5a/C5b** (engine bearish CHoCH, with or without a prior warning) have real lift: pooled excess about
  +0.07, p ≤ 0.0004 at both TFs. But matched-frequency baselines do as well or better:
  * **C5b is the `counter_reversal` baseline in practice.** At 1H the thinned counter-reversal kept 22,448
    of its 22,834 alerts, against C5b's 22,448, with zero shortfall blocks, and precision* is identical
    (0.201 vs 0.201).
  * **C5a's prior-warning filter adds nothing**: precision* 0.205 vs 0.201 for C5b, with the same recall
    and timing.
  * The CHoCH lift belongs to the existing engine signal, not to a new family-C detector.
* All confirmations arrive after the top: median −15 candles for C5, −2 for C3. On average, 68 to 72% of
  the subsequent decline remains at C5 alerts.

**Trading view (secondary; not part of selection).**
* Net mean after round-trip costs is negative in every pooled confirmation cell (−0.002 to −0.010 ATR).
* r_h minus the causal benchmark is positive at 4H for C5a/C5b: +0.44 [+0.08, +0.80] (C5a) and +0.47 [+0.10, +0.83] (C5b), p ≈ 0.008.
  This is one of six secondary cells, it was not a selection criterion, and the data had already been
  examined. It is not evidence of an edge.

## 4. Confirmations vs the four baselines at matched frequency

* prec* = precision excluding duplicates.
* Baseline values are the mean of 50 thinned replicates.
* `<` marks a detector below the best baseline.

### 1H

| detector | group | inst | alerts | recall | prec* | FA /inst-yr | lead | remain | lift excess [t-CI] | p wild | htf_flip prec* · recall | ema_cross prec* · recall | supertrend_flip prec* · recall | counter_reversal prec* · recall | best baseline prec* |
|---|---|---:|---:|---|---:|---:|---|---:|---|---:|---|---|---|---|---|
| C3 | crypto | 36 | 58971 | 0.990 [0.987, 0.993] | 0.066 **<** | 206.6 | -2 [-2, -2] | 0.84 | -0.0568 [-0.0707, -0.0429] | 1.0000 | 0.159 · 0.789 | 0.212 · 0.999 | 0.179 · 0.999 | 0.201 · 0.982 | 0.212 (ema_cross) |
| C3 | equities | 41 | 5089 | 0.959 [0.932, 0.983] | 0.086 **<** | 35.1 | -20 [-33, -4] | 0.83 | -0.0319 [-0.0634, -0.0005] | 0.9776 | 0.243 · 0.942 | 0.273 · 0.945 | 0.178 · 0.973 | 0.215 · 0.951 | 0.273 (ema_cross) |
| C3 | commodities | 11 | 1157 | 0.967 [0.928, 1.000] | 0.092 **<** | 29.7 | -29 [-53, -4] | 0.70 | -0.0093 [-0.0714, +0.0528] | 0.6231 | 0.210 · 0.972 | 0.249 · 0.968 | 0.142 · 0.989 | 0.200 · 0.964 | 0.249 (ema_cross) |
| C3 | rates | 8 | 922 | 0.969 [0.918, 1.000] | 0.081 **<** | 33.5 | -3 [-39, -2] | 0.91 | -0.0096 [-0.0833, +0.0640] | 0.6013 | 0.214 · 0.883 | 0.213 · 0.922 | 0.143 · 0.963 | 0.170 · 0.938 | 0.214 (htf_flip) |
| C3 | pooled | 96 | 66139 | 0.986 [0.981, 0.991] | 0.068 **<** | 135.0 | -2 [-2, -2] | 0.84 | -0.0534 [-0.0666, -0.0402] | 1.0000 | 0.168 · 0.810 | 0.217 · 0.991 | 0.177 · 0.996 | 0.201 · 0.978 | 0.217 (ema_cross) |
| C5a | crypto | 36 | 18690 | 0.978 [0.971, 0.984] | 0.205 **<** | 55.4 | -15 [-16, -15] | 0.72 | +0.0640 [+0.0433, +0.0847] | 0.0001 | 0.200 · 0.694 | 0.233 · 0.948 | 0.208 · 0.937 | 0.204 · 0.971 | 0.233 (ema_cross) |
| C5a | equities | 41 | 2049 | 0.978 [0.960, 0.994] | 0.214 **<** | 12.3 | -13 [-14, -11] | 0.76 | +0.1112 [+0.0594, +0.1629] | 0.0001 | 0.310 · 0.886 | 0.301 · 0.912 | 0.228 · 0.949 | 0.214 · 0.977 | 0.310 (htf_flip) |
| C5a | commodities | 11 | 551 | 0.989 [0.959, 1.000] | 0.192 **<** | 13.0 | -13 [-14, -11] | 0.68 | +0.0983 [+0.0194, +0.1772] | 0.0100 | 0.270 · 0.890 | 0.288 · 0.968 | 0.191 · 0.952 | 0.192 · 0.989 | 0.288 (ema_cross) |
| C5a | rates | 8 | 437 | 0.953 [0.857, 1.000] | 0.164 **<** | 14.8 | -13 [-14, -9] | 0.82 | +0.0800 [-0.0043, +0.1642] | 0.0277 | 0.259 · 0.883 | 0.220 · 0.906 | 0.178 · 0.960 | 0.164 · 0.953 | 0.259 (htf_flip) |
| C5a | pooled | 96 | 21727 | 0.977 [0.971, 0.984] | 0.205 **<** | 37.7 | -15 [-15, -14] | 0.72 | +0.0696 [+0.0500, +0.0893] | 0.0001 | 0.212 · 0.721 | 0.239 · 0.944 | 0.209 · 0.939 | 0.204 · 0.972 | 0.239 (ema_cross) |
| C5b | crypto | 36 | 19334 | 0.982 [0.976, 0.988] | 0.201 **<** | 57.3 | -15 [-16, -15] | 0.72 | +0.0633 [+0.0428, +0.0838] | 0.0001 | 0.198 · 0.703 | 0.231 · 0.956 | 0.205 · 0.946 | 0.201 · 0.982 | 0.231 (ema_cross) |
| C5b | equities | 41 | 2088 | 0.981 [0.962, 0.995] | 0.212 **<** | 12.5 | -13 [-14, -11] | 0.76 | +0.1135 [+0.0601, +0.1668] | 0.0002 | 0.308 · 0.892 | 0.301 · 0.917 | 0.226 · 0.952 | 0.212 · 0.981 | 0.308 (htf_flip) |
| C5b | commodities | 11 | 572 | 0.989 [0.959, 1.000] | 0.188 **<** | 13.3 | -13 [-14, -11] | 0.68 | +0.1045 [+0.0237, +0.1853] | 0.0079 | 0.262 · 0.890 | 0.282 · 0.971 | 0.187 · 0.958 | 0.188 · 0.989 | 0.282 (ema_cross) |
| C5b | rates | 8 | 454 | 0.953 [0.857, 1.000] | 0.159 **<** | 15.3 | -13 [-14, -9] | 0.82 | +0.0776 [-0.0050, +0.1602] | 0.0283 | 0.250 · 0.900 | 0.218 · 0.922 | 0.172 · 0.959 | 0.159 · 0.953 | 0.250 (htf_flip) |
| C5b | pooled | 96 | 22448 | 0.982 [0.976, 0.988] | 0.201 **<** | 38.9 | -15 [-15, -14] | 0.72 | +0.0693 [+0.0498, +0.0888] | 0.0001 | 0.209 · 0.729 | 0.237 · 0.952 | 0.206 · 0.947 | 0.201 · 0.982 | 0.237 (ema_cross) |

### 4H

| detector | group | inst | alerts | recall | prec* | FA /inst-yr | lead | remain | lift excess [t-CI] | p wild | htf_flip prec* · recall | ema_cross prec* · recall | supertrend_flip prec* · recall | counter_reversal prec* · recall | best baseline prec* |
|---|---|---:|---:|---|---:|---:|---|---:|---|---:|---|---|---|---|---|
| C3 | crypto | 36 | 13928 | 0.946 [0.931, 0.961] | 0.062 **<** | 53.4 | -2 [-3, -2] | 0.81 | -0.0618 [-0.0864, -0.0371] | 1.0000 | 0.207 · 0.675 | 0.201 · 0.997 | 0.176 · 0.998 | 0.209 · 0.956 | 0.209 (counter_reversal) |
| C3 | equities | 41 | 1174 | 0.903 [0.807, 0.974] | 0.095 **<** | 10.0 | -4 [-47, -2] | 0.79 | +0.0102 [-0.0305, +0.0509] | 0.3180 | 0.279 · 0.739 | 0.307 · 0.831 | 0.199 · 0.886 | 0.224 · 0.830 | 0.307 (ema_cross) |
| C3 | commodities | 11 | 314 | 0.939 [0.840, 1.000] | 0.124 **<** | 9.3 | -30 [-52, -2] | 0.71 | +0.0017 [-0.0877, +0.0910] | 0.4842 | 0.287 · 0.879 | 0.380 · 0.909 | 0.219 · 0.984 | 0.298 · 0.909 | 0.380 (ema_cross) |
| C3 | rates (not eval.) | 8 | 275 | 1.000 [1.000, 1.000] | 0.120 **<** | 11.0 | -2 [-54, -1] | 0.81 | -0.0109 [-0.1918, +0.1701] | 0.5556 | 0.441 · 0.577 | 0.439 · 0.962 | 0.241 · 0.978 | 0.256 · 0.905 | 0.441 (htf_flip) |
| C3 | pooled | 96 | 15691 | 0.943 [0.930, 0.957] | 0.066 **<** | 37.2 | -2 [-3, -2] | 0.80 | -0.0542 [-0.0773, -0.0311] | 1.0000 | 0.219 · 0.686 | 0.213 · 0.976 | 0.180 · 0.985 | 0.214 · 0.939 | 0.219 (htf_flip) |
| C5a | crypto | 36 | 4091 | 0.952 [0.932, 0.970] | 0.213 **<** | 13.1 | -15 [-17, -14] | 0.68 | +0.0649 [+0.0230, +0.1068] | 0.0022 | 0.249 · 0.567 | 0.234 · 0.871 | 0.210 · 0.846 | 0.212 · 0.945 | 0.249 (htf_flip) |
| C5a | equities | 41 | 513 | 0.903 [0.747, 1.000] | 0.215 **<** | 3.8 | -12 [-14, -10] | 0.70 | +0.0769 [-0.0159, +0.1697] | 0.0513 | 0.375 · 0.676 | 0.325 · 0.848 | 0.241 · 0.900 | 0.214 · 0.900 | 0.375 (htf_flip) |
| C5a | commodities | 11 | 132 | 0.970 [0.885, 1.000] | 0.296 **<** | 3.2 | -10 [-14, -8] | 0.59 | +0.1172 [-0.0374, +0.2719] | 0.0627 | 0.495 · 0.866 | 0.445 · 0.939 | 0.282 · 0.875 | 0.295 · 0.970 | 0.495 (htf_flip) |
| C5a | rates (not eval.) | 8 | 124 | 0.962 [0.812, 1.000] | 0.260 **<** | 4.1 | -9 [-14, -5] | 0.78 | +0.0769 [-0.1314, +0.2852] | 0.2125 | 0.512 · 0.538 | 0.490 · 0.962 | 0.285 · 0.987 | 0.260 · 0.962 | 0.512 (htf_flip) |
| C5a | pooled | 96 | 4860 | 0.948 [0.925, 0.969] | 0.217 **<** | 9.6 | -15 [-16, -13] | 0.68 | +0.0679 [+0.0333, +0.1025] | 0.0004 | 0.270 · 0.588 | 0.249 · 0.873 | 0.217 · 0.856 | 0.216 · 0.942 | 0.270 (htf_flip) |
| C5b | crypto | 36 | 4222 | 0.957 [0.940, 0.973] | 0.209 **<** | 13.5 | -15 [-17, -14] | 0.68 | +0.0650 [+0.0230, +0.1070] | 0.0022 | 0.246 · 0.573 | 0.233 · 0.882 | 0.209 · 0.859 | 0.209 · 0.957 | 0.246 (htf_flip) |
| C5b | equities | 41 | 521 | 0.903 [0.747, 1.000] | 0.213 **<** | 3.9 | -12 [-14, -10] | 0.70 | +0.0782 [-0.0139, +0.1702] | 0.0454 | 0.372 · 0.684 | 0.324 · 0.852 | 0.241 · 0.908 | 0.213 · 0.903 | 0.372 (htf_flip) |
| C5b | commodities | 11 | 136 | 0.970 [0.885, 1.000] | 0.291 **<** | 3.3 | -10 [-14, -8] | 0.59 | +0.1169 [-0.0373, +0.2711] | 0.0659 | 0.495 · 0.896 | 0.439 · 0.939 | 0.280 · 0.882 | 0.291 · 0.970 | 0.495 (htf_flip) |
| C5b | rates (not eval.) | 8 | 126 | 0.962 [0.812, 1.000] | 0.258 **<** | 4.2 | -9 [-14, -5] | 0.78 | +0.0797 [-0.1306, +0.2900] | 0.2042 | 0.494 · 0.538 | 0.480 · 0.962 | 0.282 · 0.987 | 0.258 · 0.962 | 0.494 (htf_flip) |
| C5b | pooled | 96 | 5005 | 0.952 [0.930, 0.972] | 0.213 **<** | 9.9 | -15 [-16, -13] | 0.68 | +0.0681 [+0.0333, +0.1029] | 0.0003 | 0.267 · 0.595 | 0.248 · 0.883 | 0.216 · 0.868 | 0.213 · 0.952 | 0.267 (htf_flip) |

**Matched frequency is approximate.** Thinning never pads. In a calendar block where a baseline fired less
often than the detector, the baseline keeps all its alerts (a "shortfall block"):
* **C3** has 67k alerts at 1H. Every baseline was far sparser, so those comparisons are effectively at the
  baselines' natural frequency.
* **C5a/C5b** have moderate shortfall against htf_flip and ema_cross, and none against counter_reversal.

| TF | detector | baseline | kept / target alerts (available) | shortfall blocks |
|---|---|---|---|---:|
| 1H | C3 | htf_flip | 21892 / 67353 (22923) | 4152 |
| 1H | C3 | ema_cross | 20976 / 67353 (21546) | 4358 |
| 1H | C3 | supertrend_flip | 25931 / 67353 (27189) | 3971 |
| 1H | C3 | counter_reversal | 22255 / 67353 (22834) | 4295 |
| 1H | C5a | htf_flip | 14750 / 22101 (22923) | 1907 |
| 1H | C5a | ema_cross | 17776 / 22101 (21546) | 1928 |
| 1H | C5a | supertrend_flip | 20012 / 22101 (27189) | 906 |
| 1H | C5a | counter_reversal | 21725 / 22101 (22834) | 0 |
| 1H | C5b | htf_flip | 15165 / 22834 (22923) | 1953 |
| 1H | C5b | ema_cross | 18145 / 22834 (21546) | 2049 |
| 1H | C5b | supertrend_flip | 20529 / 22834 (27189) | 983 |
| 1H | C5b | counter_reversal | 22448 / 22834 (22834) | 0 |
| 4H | C3 | htf_flip | 3463 / 16568 (4053) | 1888 |
| 4H | C3 | ema_cross | 5007 / 16568 (5380) | 1963 |
| 4H | C3 | supertrend_flip | 6052 / 16568 (6741) | 1812 |
| 4H | C3 | counter_reversal | 4898 / 16568 (5395) | 1928 |
| 4H | C5a | htf_flip | 2298 / 5237 (4053) | 1083 |
| 4H | C5a | ema_cross | 3772 / 5237 (5380) | 790 |
| 4H | C5a | supertrend_flip | 4267 / 5237 (6741) | 423 |
| 4H | C5a | counter_reversal | 4858 / 5237 (5395) | 0 |
| 4H | C5b | htf_flip | 2361 / 5395 (4053) | 1099 |
| 4H | C5b | ema_cross | 3843 / 5395 (5380) | 833 |
| 4H | C5b | supertrend_flip | 4365 / 5395 (6741) | 456 |
| 4H | C5b | counter_reversal | 5005 / 5395 (5395) | 0 |

**Warnings were not compared against matched baselines.** The frozen configuration (§4, "Baselines
(confirmations only)") defines that comparison for confirmations only. Adding it for warnings now would be
a new, post-hoc analysis, so it was not run. The warnings' pre-registered comparator is lift against warm
candles in the same instrument and HTF state.

## 5. Warnings by timeframe and group

* lift excess = event-in-window rate of the alerts minus the same-state warm-candle rate.
* t-CI with G − 1 df; wild-bootstrap p is one-sided.
* "(not eval.)" marks a cell that fails the frozen evaluability rule.

### 1H

| detector | group | inst | events | alerts | recall [CI] | precision [CI] | prec* | FA /inst-yr | lead [CI] | remain | lift excess [t-CI] | p wild |
|---|---|---:|---:|---:|---|---|---:|---:|---|---:|---|---:|
| C1a | crypto | 36 | 3246 | 26751 | 0.772 [0.726, 0.819] | 0.094 [0.083, 0.106] | 0.146 | 66.3 | 44 [38, 49] | 0.69 | -0.0264 [-0.0729, +0.0200] | 0.8606 |
| C1a | equities | 41 | 369 | 3641 | 0.954 [0.903, 0.987] | 0.097 [0.081, 0.115] | 0.148 | 18.9 | 51 [47, 57] | 0.68 | -0.0055 [-0.0597, +0.0487] | 0.5786 |
| C1a | commodities | 11 | 90 | 957 | 0.956 [0.912, 0.990] | 0.090 [0.068, 0.116] | 0.135 | 19.1 | 58 [51, 63] | 0.58 | -0.0312 [-0.1316, +0.0693] | 0.7359 |
| C1a | rates | 8 | 64 | 759 | 0.984 [0.940, 1.000] | 0.083 [0.051, 0.118] | 0.129 | 20.3 | 63 [53, 69] | 0.73 | +0.0270 [-0.1039, +0.1579] | 0.3429 |
| C1a | pooled | 96 | 3769 | 32108 | 0.798 [0.757, 0.838] | 0.094 [0.085, 0.103] | 0.145 | 46.7 | 47 [42, 50] | 0.68 | -0.0229 [-0.0628, +0.0170] | 0.8668 |
| C1b | crypto | 36 | 3246 | 17359 | 0.683 [0.644, 0.720] | 0.128 [0.115, 0.142] | 0.187 | 43.4 | 34 [29, 39] | 0.73 | -0.0316 [-0.0780, +0.0147] | 0.9066 |
| C1b | equities | 41 | 369 | 1836 | 0.645 [0.554, 0.728] | 0.130 [0.109, 0.157] | 0.175 | 10.4 | 34 [26, 42] | 0.76 | -0.0716 [-0.1353, -0.0079] | 0.9823 |
| C1b | commodities | 11 | 90 | 582 | 0.856 [0.775, 0.924] | 0.132 [0.105, 0.164] | 0.193 | 11.2 | 35 [28, 58] | 0.72 | -0.0168 [-0.1259, +0.0922] | 0.6253 |
| C1b | rates | 8 | 64 | 395 | 0.812 [0.684, 0.906] | 0.132 [0.085, 0.193] | 0.184 | 11.0 | 37 [20, 54] | 0.83 | +0.0101 [-0.1482, +0.1684] | 0.4506 |
| C1b | pooled | 96 | 3769 | 20172 | 0.686 [0.651, 0.719] | 0.128 [0.116, 0.141] | 0.186 | 29.8 | 35 [30, 38] | 0.74 | -0.0340 [-0.0735, +0.0055] | 0.9539 |
| C2 | crypto | 36 | 3246 | 18107 | 0.913 [0.899, 0.926] | 0.164 [0.151, 0.176] | 0.223 | 46.6 | 40 [36, 43] | 0.65 | -0.0414 [-0.0738, -0.0090] | 0.9936 |
| C2 | equities | 41 | 369 | 2249 | 0.919 [0.867, 0.956] | 0.151 [0.132, 0.172] | 0.212 | 11.7 | 42 [33, 48] | 0.69 | -0.0120 [-0.0654, +0.0414] | 0.6754 |
| C2 | commodities | 11 | 90 | 527 | 0.878 [0.795, 0.942] | 0.150 [0.113, 0.189] | 0.209 | 10.4 | 49 [44, 56] | 0.63 | -0.0162 [-0.1275, +0.0950] | 0.6161 |
| C2 | rates | 8 | 64 | 409 | 0.969 [0.918, 1.000] | 0.152 [0.098, 0.217] | 0.209 | 11.2 | 38 [24, 53] | 0.75 | +0.0086 [-0.1292, +0.1464] | 0.4518 |
| C2 | pooled | 96 | 3769 | 21292 | 0.913 [0.900, 0.926] | 0.162 [0.151, 0.173] | 0.221 | 32.0 | 40 [37, 43] | 0.66 | -0.0367 [-0.0658, -0.0077] | 0.9930 |
| C3 | crypto | 36 | 3246 | 58890 | 0.999 [0.997, 1.000] | 0.055 [0.052, 0.059] | 0.086 | 156.3 | 65 [64, 66] | 0.58 | -0.0352 [-0.0626, -0.0077] | 0.9927 |
| C3 | equities | 41 | 369 | 4990 | 0.981 [0.949, 1.000] | 0.073 [0.063, 0.083] | 0.119 | 24.9 | 63 [60, 67] | 0.61 | -0.0165 [-0.0600, +0.0270] | 0.7739 |
| C3 | commodities | 11 | 90 | 1132 | 0.989 [0.959, 1.000] | 0.079 [0.059, 0.100] | 0.125 | 21.7 | 59 [55, 67] | 0.59 | -0.0143 [-0.0970, +0.0684] | 0.6382 |
| C3 | rates | 8 | 64 | 905 | 0.984 [0.940, 1.000] | 0.070 [0.043, 0.101] | 0.115 | 23.2 | 62 [52, 68] | 0.68 | +0.0243 [-0.0918, +0.1405] | 0.3324 |
| C3 | pooled | 96 | 3769 | 65917 | 0.997 [0.993, 1.000] | 0.057 [0.054, 0.060] | 0.089 | 101.4 | 65 [63, 66] | 0.58 | -0.0326 [-0.0576, -0.0076] | 0.9940 |
| C4 | crypto | 36 | 3246 | 14718 | 0.751 [0.723, 0.776] | 0.166 [0.152, 0.181] | 0.233 | 36.1 | 20 [16, 24] | 0.70 | -0.0093 [-0.0492, +0.0306] | 0.6776 |
| C4 | equities | 41 | 369 | 2377 | 0.840 [0.786, 0.890] | 0.130 [0.114, 0.151] | 0.193 | 12.0 | 36 [27, 45] | 0.69 | -0.0179 [-0.0698, +0.0341] | 0.7585 |
| C4 | commodities | 11 | 90 | 772 | 0.911 [0.841, 0.968] | 0.106 [0.078, 0.136] | 0.154 | 15.6 | 50 [35, 61] | 0.64 | -0.0297 [-0.1346, +0.0752] | 0.7155 |
| C4 | rates | 8 | 64 | 450 | 0.859 [0.701, 0.974] | 0.122 [0.078, 0.171] | 0.177 | 12.2 | 45 [23, 52] | 0.73 | +0.0202 [-0.1448, +0.1853] | 0.4046 |
| C4 | pooled | 96 | 3769 | 18317 | 0.765 [0.739, 0.789] | 0.157 [0.146, 0.170] | 0.224 | 26.4 | 23 [19, 26] | 0.70 | -0.0105 [-0.0446, +0.0235] | 0.7291 |

### 4H

| detector | group | inst | events | alerts | recall [CI] | precision [CI] | prec* | FA /inst-yr | lead [CI] | remain | lift excess [t-CI] | p wild |
|---|---|---:|---:|---:|---|---|---:|---:|---|---:|---|---:|
| C1a | crypto | 36 | 816 | 5263 | 0.545 [0.433, 0.656] | 0.085 [0.067, 0.107] | 0.114 | 15.8 | 30 [24, 35] | 0.65 | -0.0280 [-0.1117, +0.0556] | 0.7480 |
| C1a | equities | 41 | 103 | 887 | 0.864 [0.711, 0.968] | 0.100 [0.069, 0.131] | 0.140 | 6.2 | 33 [22, 42] | 0.69 | +0.0063 [-0.0828, +0.0953] | 0.4313 |
| C1a | commodities | 11 | 33 | 226 | 0.818 [0.639, 0.976] | 0.119 [0.066, 0.171] | 0.190 | 4.8 | 31 [-24, 48] | 0.59 | +0.0257 [-0.1506, +0.2021] | 0.3790 |
| C1a | rates (not eval.) | 8 | 26 | 212 | 0.962 [0.812, 1.000] | 0.118 [0.061, 0.172] | 0.205 | 5.6 | 50 [26, 56] | 0.73 | -0.0416 [-0.2523, +0.1692] | 0.6614 |
| C1a | pooled | 96 | 978 | 6588 | 0.599 [0.507, 0.690] | 0.089 [0.073, 0.108] | 0.122 | 12.1 | 31 [27, 34] | 0.66 | -0.0220 [-0.0916, +0.0475] | 0.7365 |
| C1b | crypto | 36 | 816 | 3614 | 0.429 [0.335, 0.518] | 0.097 [0.073, 0.129] | 0.128 | 10.9 | 24 [14, 32] | 0.69 | -0.0284 [-0.1171, +0.0604] | 0.7382 |
| C1b | equities (not eval.) | 41 | 103 | 330 | 0.466 [0.202, 0.702] | 0.145 [0.096, 0.220] | 0.189 | 2.3 | 28 [3, 42] | 0.78 | +0.0026 [-0.1822, +0.1875] | 0.4800 |
| C1b | commodities (not eval.) | 11 | 33 | 113 | 0.515 [0.227, 0.879] | 0.150 [0.039, 0.265] | 0.191 | 3.0 | 30 [14, 44] | 0.61 | -0.1119 [-0.3395, +0.1157] | 0.8473 |
| C1b | rates (not eval.) | 8 | 26 | 65 | 0.500 [0.125, 0.828] | 0.200 [0.133, 0.300] | 0.289 | 1.9 | 20 [13, 56] | 0.83 | -0.0854 [-0.2973, +0.1265] | 0.8374 |
| C1b | pooled | 96 | 978 | 4122 | 0.438 [0.360, 0.520] | 0.104 [0.080, 0.135] | 0.137 | 7.7 | 25 [15, 32] | 0.70 | -0.0291 [-0.1077, +0.0495] | 0.7677 |
| C2 | crypto | 36 | 816 | 3929 | 0.804 [0.765, 0.841] | 0.167 [0.138, 0.197] | 0.203 | 11.8 | 20 [15, 24] | 0.68 | -0.0403 [-0.1075, +0.0269] | 0.8839 |
| C2 | equities | 41 | 103 | 515 | 0.786 [0.609, 0.920] | 0.157 [0.119, 0.197] | 0.212 | 3.4 | 26 [8, 36] | 0.74 | +0.0041 [-0.0929, +0.1012] | 0.4663 |
| C2 | commodities | 11 | 33 | 118 | 0.727 [0.556, 0.947] | 0.203 [0.108, 0.302] | 0.276 | 2.7 | 10 [-65, 42] | 0.43 | -0.0184 [-0.1546, +0.1178] | 0.6135 |
| C2 | rates (not eval.) | 8 | 26 | 93 | 0.962 [0.889, 1.000] | 0.269 [0.145, 0.371] | 0.410 | 2.1 | 38 [5, 44] | 0.76 | +0.0241 [-0.2152, +0.2633] | 0.4121 |
| C2 | pooled | 96 | 978 | 4655 | 0.804 [0.766, 0.841] | 0.169 [0.142, 0.197] | 0.209 | 8.6 | 21 [16, 25] | 0.68 | -0.0336 [-0.0940, +0.0268] | 0.8688 |
| C3 | crypto | 36 | 816 | 13848 | 0.994 [0.987, 0.999] | 0.059 [0.050, 0.067] | 0.079 | 43.5 | 42 [39, 44] | 0.58 | -0.0319 [-0.0810, +0.0172] | 0.9037 |
| C3 | equities | 41 | 103 | 1096 | 0.951 [0.909, 0.989] | 0.089 [0.059, 0.126] | 0.130 | 7.4 | 40 [22, 51] | 0.60 | -0.0087 [-0.0849, +0.0675] | 0.6015 |
| C3 | commodities | 11 | 33 | 291 | 0.939 [0.840, 1.000] | 0.107 [0.059, 0.166] | 0.172 | 6.3 | 40 [-26, 50] | 0.49 | -0.0228 [-0.1500, +0.1043] | 0.6540 |
| C3 | rates (not eval.) | 8 | 26 | 257 | 1.000 [1.000, 1.000] | 0.101 [0.051, 0.147] | 0.187 | 6.5 | 50 [38, 56] | 0.69 | -0.0223 [-0.2088, +0.1643] | 0.6092 |
| C3 | pooled | 96 | 978 | 15492 | 0.988 [0.981, 0.995] | 0.062 [0.053, 0.072] | 0.085 | 29.9 | 42 [39, 44] | 0.59 | -0.0300 [-0.0749, +0.0150] | 0.9078 |
| C4 | crypto | 36 | 816 | 3715 | 0.702 [0.642, 0.759] | 0.154 [0.124, 0.187] | 0.211 | 9.8 | 6 [0, 12] | 0.68 | +0.0496 [-0.0327, +0.1319] | 0.1309 |
| C4 | equities | 41 | 103 | 422 | 0.748 [0.597, 0.873] | 0.182 [0.144, 0.226] | 0.248 | 2.6 | 11 [2, 26] | 0.73 | +0.0193 [-0.0578, +0.0964] | 0.2953 |
| C4 | commodities | 11 | 33 | 125 | 0.636 [0.428, 0.871] | 0.168 [0.094, 0.231] | 0.250 | 2.7 | 24 [-1, 43] | 0.62 | +0.0056 [-0.2258, +0.2369] | 0.4868 |
| C4 | rates (not eval.) | 8 | 26 | 90 | 0.769 [0.545, 0.950] | 0.222 [0.130, 0.344] | 0.345 | 2.2 | 32 [-2, 59] | 0.74 | -0.0422 [-0.2765, +0.1920] | 0.6420 |
| C4 | pooled | 96 | 978 | 4352 | 0.707 [0.650, 0.761] | 0.159 [0.131, 0.187] | 0.218 | 7.1 | 8 [2, 13] | 0.68 | +0.0435 [-0.0254, +0.1123] | 0.1196 |

## 6. Eligible instruments and clusters per cell

Each entry reads n · G · eval:
* n = instruments with data;
* G = calendar-block clusters carrying lift units;
* eval = meets the frozen F8 rule (detection evaluable, ≥ 30 lift units, G ≥ 10).

| TF | kind | detector | crypto n·G·eval | equities n·G·eval | commodities n·G·eval | rates n·G·eval | groups evaluable |
|---|---|---|---|---|---|---|---|
| 1H | warning | C1a | 36·82·yes | 41·30·yes | 11·30·yes | 8·30·yes | 4/4 |
| 1H | warning | C1b | 36·82·yes | 41·29·yes | 11·29·yes | 8·26·yes | 4/4 |
| 1H | warning | C2 | 36·82·yes | 41·30·yes | 11·30·yes | 8·30·yes | 4/4 |
| 1H | warning | C3 | 36·82·yes | 41·30·yes | 11·30·yes | 8·30·yes | 4/4 |
| 1H | warning | C4 | 36·82·yes | 41·30·yes | 11·30·yes | 8·29·yes | 4/4 |
| 1H | confirmation | C3 | 36·82·yes | 41·31·yes | 11·31·yes | 8·31·yes | 4/4 |
| 1H | confirmation | C5a | 36·82·yes | 41·31·yes | 11·31·yes | 8·31·yes | 4/4 |
| 1H | confirmation | C5b | 36·82·yes | 41·31·yes | 11·31·yes | 8·31·yes | 4/4 |
| 4H | warning | C1a | 36·41·yes | 41·12·yes | 11·12·yes | 8·11·**no** | 3/4 |
| 4H | warning | C1b | 36·41·yes | 41·9·**no** | 11·9·**no** | 8·6·**no** | 1/4 |
| 4H | warning | C2 | 36·41·yes | 41·12·yes | 11·12·yes | 8·11·**no** | 3/4 |
| 4H | warning | C3 | 36·41·yes | 41·12·yes | 11·12·yes | 8·12·**no** | 3/4 |
| 4H | warning | C4 | 36·41·yes | 41·12·yes | 11·12·yes | 8·11·**no** | 3/4 |
| 4H | confirmation | C3 | 36·41·yes | 41·12·yes | 11·12·yes | 8·12·**no** | 3/4 |
| 4H | confirmation | C5a | 36·41·yes | 41·12·yes | 11·12·yes | 8·12·**no** | 3/4 |
| 4H | confirmation | C5b | 36·41·yes | 41·12·yes | 11·12·yes | 8·12·**no** | 3/4 |

Pooled cells: 96 instruments, G = 82 at 1H and 41 at 4H.

## 7. Disclosures and limitations

* **Already-examined data.** Every instrument and period was used in earlier studies. Multiplicity: 18
  trials, 16 detector cells × 5 groups. Holm-adjusted p is shown for information in the full tables.
* **No independent review.** Self-audited exploration mode; the confirmatory gate stays closed
  (`v5_gate.confirmatory_blockers()`).
* **No per-instrument results.** The frozen runner stores results per asset group (crypto, equities,
  commodities, rates, pooled), not per instrument. So results "by instrument" appear here as instrument
  counts per group cell (§6). Extracting per-instrument numbers would mean a new computation on examined
  data, and was not done.
* **Insufficient samples.**
  * At 4H, rates (8 instruments, 26 labelled tops) is not evaluable for any variant.
  * C1b at 4H is evaluable in crypto only (equities and commodities have G = 9).
  * Every 1H cell is evaluable.
  * Commodities (11) and rates (8) have wide CIs everywhere.
  * Crypto dominates the pooled numbers: 3,246 of 3,769 tops at 1H and 816 of 978 at 4H.
* **Censoring.** Tops too close to the data edges cannot be scored and are excluded: 450 at 1H and 170 at
  4H.
* **Missing data.**
  * FX (12 pairs) is excluded by design: causal daily alignment is not demonstrably safe, and carry data is
    missing.
  * BTC-USD is excluded from pooling.
  * Equity 4H candles outside regular trading hours are dropped.
  * Candles after the freeze (2026-10-27) are never loaded.
* **Costs.**
  * Detection metrics are cost-free by definition.
  * The trading view uses round-trip costs per asset class plus a short holding cost.
  * Holding cost is observed perpetual funding for only about 27–30% of crypto confirmation trades; the rest
    use an assumed 10%/yr.
  * Equities and ETFs use an assumed 1%/yr general-collateral borrow, with no hard-to-borrow fees.
  * There is no slippage beyond `COST_BPS` and no market-impact model.
* **Excluded trades.** Trades whose exit falls beyond the data are counted as `no_exit_in_data` and
  excluded (see the table below).

| TF | detector | trades | net mean (ATR) | r_h − causal benchmark [CI] (p wild) | holding-cost sources |
|---|---|---:|---:|---|---|
| 1H | C3 | 67353 | -0.0023 | +0.089 [-0.044, +0.222] (0.0971) | {'estimated_crypto_10pct': 43625, 'observed_funding': 15799, 'estimated_gc_borrow_1pct': 7825, 'no_exit_in_data': 104} |
| 1H | C5a | 22101 | -0.0042 | +0.091 [-0.058, +0.240] (0.1126) | {'estimated_crypto_10pct': 13618, 'observed_funding': 5181, 'estimated_gc_borrow_1pct': 3261, 'no_exit_in_data': 41} |
| 1H | C5b | 22834 | -0.0042 | +0.094 [-0.054, +0.242] (0.1036) | {'estimated_crypto_10pct': 14064, 'observed_funding': 5383, 'estimated_gc_borrow_1pct': 3346, 'no_exit_in_data': 41} |
| 4H | C3 | 16568 | -0.0070 | -0.031 [-0.404, +0.343] (0.5629) | {'estimated_crypto_10pct': 10459, 'observed_funding': 3825, 'estimated_gc_borrow_1pct': 2157, 'no_exit_in_data': 127} |
| 4H | C5a | 5237 | -0.0104 | +0.444 [+0.084, +0.804] (0.0085) | {'estimated_crypto_10pct': 2953, 'observed_funding': 1254, 'estimated_gc_borrow_1pct': 978, 'no_exit_in_data': 52} |
| 4H | C5b | 5395 | -0.0099 | +0.465 [+0.099, +0.831] (0.0071) | {'estimated_crypto_10pct': 3057, 'observed_funding': 1284, 'estimated_gc_borrow_1pct': 1001, 'no_exit_in_data': 53} |

## 8. Recommendation

**Reject family C at configuration x1. Nominate no variant for an untouched-data test.**

| variant | recommendation | reason |
|---|---|---|
| C1a warning | **reject** | lift ≤ 1 at both TFs (pooled 1H excess −0.023, p 0.87) |
| C1b warning | **reject** | lift < 1; at 4H mostly not evaluable |
| C2 warning | **reject** | pooled 1H lift CI entirely below 0 |
| C3 warning | **reject** | pooled 1H lift CI entirely below 0; about 100 alerts per instrument-year |
| C3 confirmation | **reject** | lift CI below 0 at both TFs; precision* about ⅓ of every baseline's |
| C4 warning | **reject at x1** (note for any redesign) | only warning with a positive pooled point estimate (4H +0.044, p 0.12); not significant, and 1 of 10 warning cells |
| C5a confirmation | **reject as a family-C detector** | the lift is real but no better than the EMA-cross / HTF-flip baselines; the warning filter adds nothing over C5b |
| C5b confirmation | **reject as a family-C detector** | the same alerts as the existing `counter_reversal` baseline (engine CHoCH); no new information |

* **Mechanical status.** §9 drops none of these variants, so formally they are *inconclusive*. The frozen
  family outcome is "REJECTED at exploration or REDESIGN".
* **Why reject rather than redesign.** On this evidence, none of the detectors separates major tops from
  ordinary bull-state candles beyond what the existing CHoCH already does.
* **If a redesign is wanted anyway.** It would need a new configuration version (x2) with new trial ids, and
  these 18 trials count against it.

**Not done, pending review of this report:**
* no new experiment and no redesign;
* no change to production Pine scripts;
* no change to the frozen configuration or the H6/H7v files.
