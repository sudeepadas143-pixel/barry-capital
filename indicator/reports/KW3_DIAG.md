# KW-3 stage 1: why the weekly SELL fails (pre-2018 development data)

1040 W0 SELL signals (outcome window before 2018) plus missed labelled major tops. Classes per `reports/KW3_DIAG_CONFIG.md`.

| class | n | ext26 | ext40 | dd52 | rally52 | tsm | roc13 | roc13_acc | rsi | rsi_max8 | div8 | vratio | wick_up | rev4 | failed4 | slope40 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| false_reversal | 22 | -0.08 | 0.83 | 2.52 | 5.85 | 1.11 | -0.65 | -1.97 | 49.80 | 67.74 | 0.00 | 0.07 | 0.17 | 0.50 | 0.00 | 0.47 |
| flat | 88 | -0.01 | 0.82 | 2.59 | 4.93 | 0.97 | -0.24 | -2.48 | 50.25 | 68.83 | 0.00 | 0.17 | 0.16 | 1.00 | 0.00 | 0.39 |
| late | 332 | -0.54 | 0.34 | 3.48 | 4.48 | 0.83 | -0.88 | -2.97 | 46.50 | 71.00 | 0.00 | 0.20 | 0.11 | 1.00 | 0.00 | 0.37 |
| missed_top | 380 | 2.37 | 3.42 | 0.75 | 7.48 | 1.11 | 3.18 | 0.64 | 68.15 | 71.50 | 0.00 | 0.07 | 0.31 | 1.00 | 1.00 | 0.48 |
| premature | 159 | 0.02 | 0.91 | 2.57 | 5.34 | 1.11 | -0.32 | -2.52 | 50.56 | 70.14 | 0.00 | 0.19 | 0.16 | 1.00 | 0.00 | 0.43 |
| useful | 59 | 0.06 | 0.98 | 2.58 | 4.69 | 0.97 | -0.07 | -2.62 | 50.76 | 70.89 | 0.00 | 0.22 | 0.19 | 0.00 | 0.00 | 0.40 |

By asset group (counts):

| group | false_reversal | flat | late | missed_top | premature | useful |
|---|---:|---:|---:|---:|---:|---:|
| equities | 19 | 75 | 264 | 296 | 148 | 49 |
| other | 3 | 13 | 68 | 84 | 11 | 10 |
