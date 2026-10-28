# KF: frequency vs accuracy (EXPLORATORY)

Works out = price higher (BUY) / lower (SELL, ✕) L/2 candles later. Excess = hit − the instrument's own base rate. Most frequent option with tuning excess >= +0.05, kept if check excess >= +0.03. Check period previously studied.

## 1W BUY — current H|1.1, chosen None, **adopted H|1.1**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| H|1.1 ←adopted | 210, 0.12/yr, hit 0.61 vs base 0.59 (excess +0.02), med +3.0% | 98, 0.13/yr, hit 0.76 vs base 0.57 (excess +0.19), med +7.6% | 50, 0.07/yr, hit 0.82 vs base 0.58 (excess +0.24), med +12.0% | 1, 0.00/yr, hit 1.00 vs base 0.44 (excess +0.56), med +10.3% |
| H|1.1 ←adopted | 210, 0.12/yr, hit 0.61 vs base 0.59 (excess +0.02), med +3.0% | 98, 0.13/yr, hit 0.76 vs base 0.57 (excess +0.19), med +7.6% | 50, 0.07/yr, hit 0.82 vs base 0.58 (excess +0.24), med +12.0% | 1, 0.00/yr, hit 1.00 vs base 0.44 (excess +0.56), med +10.3% |
| W|0.7 | 1714, 0.94/yr, hit 0.61 vs base 0.61 (excess +0.01), med +2.8% | 826, 1.10/yr, hit 0.59 vs base 0.55 (excess +0.04), med +1.7% | 391, 0.52/yr, hit 0.64 vs base 0.60 (excess +0.04), med +4.2% | 129, 0.17/yr, hit 0.53 vs base 0.46 (excess +0.07), med +1.7% |
| W|0.8 | 1604, 0.88/yr, hit 0.61 vs base 0.60 (excess +0.00), med +2.6% | 770, 1.02/yr, hit 0.60 vs base 0.55 (excess +0.05), med +1.9% | 358, 0.48/yr, hit 0.65 vs base 0.60 (excess +0.05), med +4.2% | 125, 0.17/yr, hit 0.54 vs base 0.46 (excess +0.09), med +3.7% |
| W|0.9 | 1486, 0.82/yr, hit 0.60 vs base 0.60 (excess -0.00), med +2.2% | 712, 0.95/yr, hit 0.60 vs base 0.55 (excess +0.05), med +1.8% | 329, 0.44/yr, hit 0.64 vs base 0.60 (excess +0.04), med +4.2% | 117, 0.16/yr, hit 0.56 vs base 0.46 (excess +0.11), med +3.1% |
| S|0.7 | 1402, 0.77/yr, hit 0.60 vs base 0.60 (excess -0.00), med +2.2% | 691, 0.92/yr, hit 0.61 vs base 0.55 (excess +0.06), med +2.2% | 319, 0.42/yr, hit 0.66 vs base 0.59 (excess +0.06), med +4.4% | 115, 0.15/yr, hit 0.58 vs base 0.46 (excess +0.13), med +5.2% |
| W|1.0 | 1333, 0.73/yr, hit 0.59 vs base 0.60 (excess -0.01), med +2.1% | 668, 0.89/yr, hit 0.61 vs base 0.55 (excess +0.06), med +2.1% | 314, 0.42/yr, hit 0.66 vs base 0.59 (excess +0.07), med +4.8% | 105, 0.14/yr, hit 0.56 vs base 0.46 (excess +0.11), med +2.7% |
| S|0.8 | 1204, 0.66/yr, hit 0.59 vs base 0.60 (excess -0.01), med +2.1% | 618, 0.82/yr, hit 0.62 vs base 0.55 (excess +0.07), med +2.4% | 292, 0.39/yr, hit 0.69 vs base 0.59 (excess +0.10), med +6.2% | 92, 0.12/yr, hit 0.52 vs base 0.45 (excess +0.07), med +1.6% |

## 1W SELL — current A, chosen None, **adopted A**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| A ←adopted | 2165, 1.19/yr, hit 0.34 vs base 0.37 (excess -0.02), med -3.3% | 646, 0.86/yr, hit 0.40 vs base 0.38 (excess +0.02), med -1.2% | 435, 0.58/yr, hit 0.40 vs base 0.37 (excess +0.03), med -2.7% | 25, 0.03/yr, hit 0.64 vs base 0.46 (excess +0.18), med +8.6% |
| A ←adopted | 2165, 1.19/yr, hit 0.34 vs base 0.37 (excess -0.02), med -3.3% | 646, 0.86/yr, hit 0.40 vs base 0.38 (excess +0.02), med -1.2% | 435, 0.58/yr, hit 0.40 vs base 0.37 (excess +0.03), med -2.7% | 25, 0.03/yr, hit 0.64 vs base 0.46 (excess +0.18), med +8.6% |
| W|0.9 | 1876, 1.03/yr, hit 0.34 vs base 0.37 (excess -0.03), med -3.0% | 737, 0.98/yr, hit 0.43 vs base 0.41 (excess +0.02), med -1.4% | 422, 0.56/yr, hit 0.42 vs base 0.38 (excess +0.04), med -2.0% | 70, 0.09/yr, hit 0.46 vs base 0.52 (excess -0.06), med -6.7% |
| S|0.8 | 1816, 1.00/yr, hit 0.34 vs base 0.37 (excess -0.03), med -3.1% | 706, 0.94/yr, hit 0.42 vs base 0.41 (excess +0.01), med -1.5% | 400, 0.53/yr, hit 0.41 vs base 0.38 (excess +0.03), med -2.4% | 69, 0.09/yr, hit 0.45 vs base 0.52 (excess -0.07), med -8.9% |
| S|0.7 | 1758, 0.97/yr, hit 0.34 vs base 0.37 (excess -0.03), med -2.8% | 730, 0.97/yr, hit 0.44 vs base 0.41 (excess +0.03), med -1.1% | 411, 0.55/yr, hit 0.44 vs base 0.38 (excess +0.06), med -1.9% | 71, 0.09/yr, hit 0.45 vs base 0.52 (excess -0.07), med -7.0% |
| W|0.8 | 1671, 0.92/yr, hit 0.35 vs base 0.37 (excess -0.02), med -2.8% | 708, 0.94/yr, hit 0.44 vs base 0.41 (excess +0.03), med -1.3% | 390, 0.52/yr, hit 0.41 vs base 0.38 (excess +0.03), med -2.4% | 72, 0.10/yr, hit 0.49 vs base 0.52 (excess -0.03), med -4.1% |
| W|0.7 | 1626, 0.90/yr, hit 0.37 vs base 0.38 (excess -0.01), med -2.4% | 712, 0.95/yr, hit 0.44 vs base 0.42 (excess +0.02), med -1.2% | 373, 0.50/yr, hit 0.38 vs base 0.38 (excess -0.01), med -2.9% | 79, 0.11/yr, hit 0.48 vs base 0.52 (excess -0.04), med -1.9% |
| W|1.0 | 1578, 0.87/yr, hit 0.35 vs base 0.37 (excess -0.02), med -3.2% | 635, 0.85/yr, hit 0.40 vs base 0.41 (excess -0.01), med -1.8% | 366, 0.49/yr, hit 0.40 vs base 0.38 (excess +0.02), med -2.7% | 64, 0.09/yr, hit 0.41 vs base 0.52 (excess -0.12), med -13.9% |

## 1D BUY — current H|1.0, chosen None, **adopted H|1.0**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| H|1.0 ←adopted | 758, 0.42/yr, hit 0.57 vs base 0.57 (excess +0.00), med +1.4% | 432, 0.49/yr, hit 0.60 vs base 0.52 (excess +0.08), med +2.2% | 151, 0.17/yr, hit 0.68 vs base 0.56 (excess +0.12), med +5.0% | 154, 0.17/yr, hit 0.55 vs base 0.46 (excess +0.09), med +2.6% |
| H|1.0 ←adopted | 758, 0.42/yr, hit 0.57 vs base 0.57 (excess +0.00), med +1.4% | 432, 0.49/yr, hit 0.60 vs base 0.52 (excess +0.08), med +2.2% | 151, 0.17/yr, hit 0.68 vs base 0.56 (excess +0.12), med +5.0% | 154, 0.17/yr, hit 0.55 vs base 0.46 (excess +0.09), med +2.6% |
| W|0.7 | 3691, 2.03/yr, hit 0.58 vs base 0.58 (excess -0.00), med +1.3% | 2168, 2.44/yr, hit 0.51 vs base 0.52 (excess -0.01), med +0.2% | 814, 0.92/yr, hit 0.60 vs base 0.57 (excess +0.03), med +2.1% | 741, 0.83/yr, hit 0.38 vs base 0.46 (excess -0.09), med -6.4% |
| W|0.8 | 3434, 1.89/yr, hit 0.58 vs base 0.58 (excess -0.00), med +1.3% | 2096, 2.36/yr, hit 0.52 vs base 0.52 (excess -0.00), med +0.3% | 760, 0.86/yr, hit 0.61 vs base 0.57 (excess +0.04), med +2.6% | 750, 0.85/yr, hit 0.40 vs base 0.46 (excess -0.06), med -4.9% |
| W|0.9 | 3167, 1.75/yr, hit 0.57 vs base 0.58 (excess -0.01), med +1.3% | 1975, 2.23/yr, hit 0.53 vs base 0.52 (excess +0.01), med +0.5% | 708, 0.80/yr, hit 0.62 vs base 0.57 (excess +0.05), med +2.6% | 713, 0.80/yr, hit 0.43 vs base 0.46 (excess -0.03), med -3.7% |
| S|0.7 | 3102, 1.71/yr, hit 0.58 vs base 0.58 (excess -0.00), med +1.4% | 1932, 2.18/yr, hit 0.53 vs base 0.52 (excess +0.01), med +0.5% | 688, 0.78/yr, hit 0.62 vs base 0.57 (excess +0.05), med +2.5% | 705, 0.79/yr, hit 0.44 vs base 0.46 (excess -0.02), med -3.4% |
| W|1.0 | 2885, 1.59/yr, hit 0.58 vs base 0.58 (excess -0.00), med +1.4% | 1814, 2.04/yr, hit 0.53 vs base 0.52 (excess +0.01), med +0.5% | 644, 0.73/yr, hit 0.62 vs base 0.57 (excess +0.05), med +2.6% | 674, 0.76/yr, hit 0.45 vs base 0.46 (excess -0.02), med -2.4% |
| CONF|0.7 | 2767, 1.52/yr, hit 0.57 vs base 0.58 (excess -0.01), med +1.2% | 1622, 1.83/yr, hit 0.51 vs base 0.52 (excess -0.01), med +0.2% | 629, 0.71/yr, hit 0.57 vs base 0.57 (excess -0.00), med +1.7% | 541, 0.61/yr, hit 0.44 vs base 0.46 (excess -0.02), med -2.9% |

## 1D Breakdown ✕ — current BRK, chosen None, **adopted BRK**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| BRK ←adopted | 2070, 1.14/yr, hit 0.40 vs base 0.41 (excess -0.01), med -1.7% | 998, 1.12/yr, hit 0.44 vs base 0.45 (excess -0.01), med -0.7% | 473, 0.53/yr, hit 0.36 vs base 0.41 (excess -0.06), med -2.6% | 232, 0.26/yr, hit 0.64 vs base 0.53 (excess +0.12), med +5.8% |
| BRK ←adopted | 2070, 1.14/yr, hit 0.40 vs base 0.41 (excess -0.01), med -1.7% | 998, 1.12/yr, hit 0.44 vs base 0.45 (excess -0.01), med -0.7% | 473, 0.53/yr, hit 0.36 vs base 0.41 (excess -0.06), med -2.6% | 232, 0.26/yr, hit 0.64 vs base 0.53 (excess +0.12), med +5.8% |
| BRK_qL | 3338, 1.84/yr, hit 0.38 vs base 0.41 (excess -0.02), med -1.6% | 1542, 1.74/yr, hit 0.46 vs base 0.45 (excess +0.01), med -0.5% | 713, 0.80/yr, hit 0.39 vs base 0.41 (excess -0.03), med -2.1% | 364, 0.41/yr, hit 0.61 vs base 0.53 (excess +0.08), med +5.4% |
| BRK_q | 2670, 1.47/yr, hit 0.40 vs base 0.41 (excess -0.01), med -1.5% | 1258, 1.42/yr, hit 0.46 vs base 0.45 (excess +0.00), med -0.5% | 601, 0.68/yr, hit 0.38 vs base 0.41 (excess -0.03), med -2.3% | 285, 0.32/yr, hit 0.65 vs base 0.53 (excess +0.12), med +6.0% |
| BRK_L | 2498, 1.38/yr, hit 0.37 vs base 0.41 (excess -0.03), med -1.8% | 1184, 1.33/yr, hit 0.45 vs base 0.45 (excess +0.00), med -0.6% | 536, 0.60/yr, hit 0.40 vs base 0.41 (excess -0.02), med -1.8% | 291, 0.33/yr, hit 0.57 vs base 0.52 (excess +0.05), med +4.4% |

## 1D SELL — current H|0.9, chosen None, **adopted H|0.9**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| H|0.9 ←adopted | 1428, 0.79/yr, hit 0.41 vs base 0.40 (excess +0.01), med -1.1% | 637, 0.72/yr, hit 0.41 vs base 0.44 (excess -0.03), med -1.2% | 296, 0.33/yr, hit 0.42 vs base 0.41 (excess +0.01), med -1.2% | 158, 0.18/yr, hit 0.43 vs base 0.52 (excess -0.09), med -3.1% |
| H|0.9 ←adopted | 1428, 0.79/yr, hit 0.41 vs base 0.40 (excess +0.01), med -1.1% | 637, 0.72/yr, hit 0.41 vs base 0.44 (excess -0.03), med -1.2% | 296, 0.33/yr, hit 0.42 vs base 0.41 (excess +0.01), med -1.2% | 158, 0.18/yr, hit 0.43 vs base 0.52 (excess -0.09), med -3.1% |
| W|0.7 | 4218, 2.32/yr, hit 0.42 vs base 0.41 (excess +0.01), med -1.0% | 2152, 2.42/yr, hit 0.45 vs base 0.46 (excess -0.02), med -0.9% | 876, 0.99/yr, hit 0.42 vs base 0.42 (excess +0.01), med -1.5% | 696, 0.78/yr, hit 0.46 vs base 0.53 (excess -0.07), med -3.7% |
| W|0.8 | 4078, 2.25/yr, hit 0.42 vs base 0.41 (excess +0.01), med -1.2% | 2020, 2.28/yr, hit 0.45 vs base 0.46 (excess -0.01), med -0.7% | 833, 0.94/yr, hit 0.43 vs base 0.41 (excess +0.02), med -1.3% | 634, 0.71/yr, hit 0.45 vs base 0.53 (excess -0.07), med -3.5% |
| W|0.9 | 3807, 2.10/yr, hit 0.40 vs base 0.41 (excess -0.00), med -1.4% | 1843, 2.08/yr, hit 0.46 vs base 0.46 (excess -0.00), med -0.7% | 776, 0.87/yr, hit 0.44 vs base 0.41 (excess +0.03), med -1.3% | 566, 0.64/yr, hit 0.46 vs base 0.53 (excess -0.07), med -3.3% |
| S|0.7 | 3785, 2.09/yr, hit 0.41 vs base 0.41 (excess +0.00), med -1.4% | 1818, 2.05/yr, hit 0.46 vs base 0.46 (excess -0.00), med -0.6% | 771, 0.87/yr, hit 0.45 vs base 0.41 (excess +0.03), med -1.0% | 556, 0.63/yr, hit 0.45 vs base 0.53 (excess -0.07), med -3.5% |
| W|1.0 | 3551, 1.96/yr, hit 0.41 vs base 0.40 (excess +0.00), med -1.3% | 1640, 1.85/yr, hit 0.45 vs base 0.46 (excess -0.00), med -0.7% | 729, 0.82/yr, hit 0.44 vs base 0.41 (excess +0.03), med -0.9% | 474, 0.53/yr, hit 0.44 vs base 0.53 (excess -0.09), med -5.0% |
| S|0.8 | 3408, 1.88/yr, hit 0.40 vs base 0.40 (excess +0.00), med -1.3% | 1545, 1.74/yr, hit 0.45 vs base 0.45 (excess -0.01), med -0.8% | 700, 0.79/yr, hit 0.43 vs base 0.41 (excess +0.02), med -1.2% | 439, 0.49/yr, hit 0.44 vs base 0.53 (excess -0.09), med -3.9% |

## 4H BUY — current H|1.1, chosen None, **adopted H|1.1**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| H|1.1 ←adopted | 363, 2.13/yr, hit 0.53 vs base 0.49 (excess +0.04), med +2.1% | 297, 1.02/yr, hit 0.65 vs base 0.48 (excess +0.17), med +1.7% | 51, 0.17/yr, hit 0.67 vs base 0.48 (excess +0.18), med +4.3% | 155, 0.53/yr, hit 0.68 vs base 0.46 (excess +0.22), med +6.8% |
| H|1.1 ←adopted | 363, 2.13/yr, hit 0.53 vs base 0.49 (excess +0.04), med +2.1% | 297, 1.02/yr, hit 0.65 vs base 0.48 (excess +0.17), med +1.7% | 51, 0.17/yr, hit 0.67 vs base 0.48 (excess +0.18), med +4.3% | 155, 0.53/yr, hit 0.68 vs base 0.46 (excess +0.22), med +6.8% |
| W|1.0 | 1482, 8.71/yr, hit 0.50 vs base 0.50 (excess +0.00), med -0.1% | 1566, 5.35/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.1% | 282, 0.96/yr, hit 0.62 vs base 0.59 (excess +0.03), med +1.9% | 886, 3.03/yr, hit 0.46 vs base 0.46 (excess -0.00), med -1.5% |
| W|0.8 | 1479, 8.69/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.2% | 1523, 5.21/yr, hit 0.50 vs base 0.50 (excess +0.00), med +0.0% | 287, 0.98/yr, hit 0.62 vs base 0.59 (excess +0.03), med +1.9% | 855, 2.92/yr, hit 0.45 vs base 0.46 (excess -0.01), med -1.7% |
| W|0.7 | 1477, 8.68/yr, hit 0.50 vs base 0.50 (excess +0.01), med +0.2% | 1518, 5.19/yr, hit 0.50 vs base 0.50 (excess -0.00), med -0.0% | 288, 0.98/yr, hit 0.62 vs base 0.59 (excess +0.02), med +1.9% | 849, 2.90/yr, hit 0.43 vs base 0.46 (excess -0.03), med -1.9% |
| W|0.9 | 1477, 8.68/yr, hit 0.50 vs base 0.50 (excess +0.01), med +0.0% | 1545, 5.28/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.0% | 288, 0.98/yr, hit 0.62 vs base 0.60 (excess +0.02), med +1.8% | 870, 2.97/yr, hit 0.45 vs base 0.46 (excess -0.01), med -1.5% |
| W|1.1 | 1462, 8.59/yr, hit 0.49 vs base 0.50 (excess -0.01), med -0.5% | 1554, 5.31/yr, hit 0.50 vs base 0.50 (excess +0.01), med +0.0% | 273, 0.93/yr, hit 0.59 vs base 0.59 (excess +0.00), med +1.5% | 892, 3.05/yr, hit 0.46 vs base 0.46 (excess -0.00), med -1.3% |
| S|0.7 | 1431, 8.41/yr, hit 0.47 vs base 0.49 (excess -0.02), med -0.7% | 1497, 5.12/yr, hit 0.52 vs base 0.49 (excess +0.03), med +0.2% | 236, 0.81/yr, hit 0.56 vs base 0.57 (excess -0.00), med +1.7% | 894, 3.06/yr, hit 0.48 vs base 0.46 (excess +0.03), med -0.5% |

## 4H Breakdown ✕ — current BRK, chosen None, **adopted BRK**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| BRK ←adopted | 364, 2.14/yr, hit 0.46 vs base 0.50 (excess -0.03), med -0.6% | 342, 1.17/yr, hit 0.45 vs base 0.49 (excess -0.04), med -0.5% | 68, 0.23/yr, hit 0.26 vs base 0.36 (excess -0.10), med -4.1% | 192, 0.66/yr, hit 0.54 vs base 0.53 (excess +0.01), med +1.3% |
| BRK ←adopted | 364, 2.14/yr, hit 0.46 vs base 0.50 (excess -0.03), med -0.6% | 342, 1.17/yr, hit 0.45 vs base 0.49 (excess -0.04), med -0.5% | 68, 0.23/yr, hit 0.26 vs base 0.36 (excess -0.10), med -4.1% | 192, 0.66/yr, hit 0.54 vs base 0.53 (excess +0.01), med +1.3% |
| BRK_qL | 739, 4.34/yr, hit 0.48 vs base 0.50 (excess -0.02), med -0.6% | 685, 2.34/yr, hit 0.48 vs base 0.48 (excess -0.00), med -0.1% | 150, 0.51/yr, hit 0.34 vs base 0.37 (excess -0.03), med -3.0% | 368, 1.26/yr, hit 0.57 vs base 0.53 (excess +0.03), med +1.4% |
| BRK_L | 545, 3.20/yr, hit 0.46 vs base 0.50 (excess -0.04), med -1.1% | 505, 1.73/yr, hit 0.48 vs base 0.48 (excess -0.01), med -0.1% | 112, 0.38/yr, hit 0.32 vs base 0.38 (excess -0.06), med -3.2% | 277, 0.95/yr, hit 0.57 vs base 0.53 (excess +0.04), med +1.7% |
| BRK_q | 488, 2.87/yr, hit 0.48 vs base 0.50 (excess -0.01), med -0.3% | 466, 1.59/yr, hit 0.48 vs base 0.49 (excess -0.01), med -0.1% | 91, 0.31/yr, hit 0.32 vs base 0.37 (excess -0.05), med -3.6% | 255, 0.87/yr, hit 0.58 vs base 0.53 (excess +0.04), med +2.5% |

## 4H SELL — current W|0.9, chosen None, **adopted W|0.9**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| W|0.9 ←adopted | 1578, 9.28/yr, hit 0.49 vs base 0.50 (excess -0.01), med -0.3% | 1418, 4.85/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.1% | 267, 0.91/yr, hit 0.45 vs base 0.41 (excess +0.05), med -0.6% | 823, 2.81/yr, hit 0.54 vs base 0.54 (excess +0.00), med +1.0% |
| W|0.9 ←adopted | 1578, 9.28/yr, hit 0.49 vs base 0.50 (excess -0.01), med -0.3% | 1418, 4.85/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.1% | 267, 0.91/yr, hit 0.45 vs base 0.41 (excess +0.05), med -0.6% | 823, 2.81/yr, hit 0.54 vs base 0.54 (excess +0.00), med +1.0% |
| W|1.0 | 1766, 10.38/yr, hit 0.47 vs base 0.50 (excess -0.03), med -1.1% | 1680, 5.74/yr, hit 0.52 vs base 0.49 (excess +0.03), med +0.2% | 346, 1.18/yr, hit 0.41 vs base 0.40 (excess +0.02), med -1.2% | 922, 3.15/yr, hit 0.58 vs base 0.53 (excess +0.05), med +2.7% |
| S|0.9 | 1725, 10.14/yr, hit 0.47 vs base 0.50 (excess -0.03), med -0.8% | 1671, 5.71/yr, hit 0.52 vs base 0.49 (excess +0.03), med +0.2% | 352, 1.20/yr, hit 0.41 vs base 0.39 (excess +0.01), med -1.3% | 897, 3.07/yr, hit 0.59 vs base 0.53 (excess +0.06), med +2.6% |
| H|0.7 | 1704, 10.02/yr, hit 0.47 vs base 0.50 (excess -0.03), med -0.9% | 1528, 5.22/yr, hit 0.51 vs base 0.49 (excess +0.01), med +0.1% | 293, 1.00/yr, hit 0.44 vs base 0.40 (excess +0.04), med -0.8% | 878, 3.00/yr, hit 0.55 vs base 0.53 (excess +0.02), med +1.6% |
| CONF|0.9 | 1604, 9.43/yr, hit 0.49 vs base 0.50 (excess -0.01), med -0.5% | 1562, 5.34/yr, hit 0.52 vs base 0.49 (excess +0.03), med +0.2% | 327, 1.12/yr, hit 0.41 vs base 0.40 (excess +0.01), med -1.3% | 849, 2.90/yr, hit 0.58 vs base 0.53 (excess +0.05), med +2.4% |
| S|0.8 | 1584, 9.31/yr, hit 0.49 vs base 0.50 (excess -0.01), med -0.3% | 1416, 4.84/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.1% | 266, 0.91/yr, hit 0.45 vs base 0.41 (excess +0.04), med -0.6% | 822, 2.81/yr, hit 0.54 vs base 0.54 (excess +0.00), med +0.9% |
| CONF|0.8 | 1525, 8.96/yr, hit 0.49 vs base 0.50 (excess -0.01), med -0.2% | 1376, 4.70/yr, hit 0.50 vs base 0.50 (excess -0.00), med -0.0% | 256, 0.88/yr, hit 0.41 vs base 0.41 (excess +0.00), med -1.7% | 808, 2.76/yr, hit 0.54 vs base 0.54 (excess +0.01), med +1.3% |

## 1H BUY — current H|1.0, chosen None, **adopted H|1.0**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| H|1.0 ←adopted | 1557, 9.15/yr, hit 0.52 vs base 0.50 (excess +0.03), med +0.4% | 1783, 6.09/yr, hit 0.57 vs base 0.49 (excess +0.07), med +0.5% | 318, 1.09/yr, hit 0.61 vs base 0.53 (excess +0.08), med +1.5% | 992, 3.39/yr, hit 0.57 vs base 0.47 (excess +0.10), med +1.2% |
| H|1.0 ←adopted | 1557, 9.15/yr, hit 0.52 vs base 0.50 (excess +0.03), med +0.4% | 1783, 6.09/yr, hit 0.57 vs base 0.49 (excess +0.07), med +0.5% | 318, 1.09/yr, hit 0.61 vs base 0.53 (excess +0.08), med +1.5% | 992, 3.39/yr, hit 0.57 vs base 0.47 (excess +0.10), med +1.2% |
| W|1.0 | 4844, 28.47/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.1% | 4617, 15.78/yr, hit 0.48 vs base 0.50 (excess -0.02), med -0.1% | 753, 2.57/yr, hit 0.54 vs base 0.56 (excess -0.02), med +0.6% | 2785, 9.52/yr, hit 0.45 vs base 0.47 (excess -0.02), med -0.6% |
| W|1.1 | 4812, 28.29/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.1% | 4600, 15.72/yr, hit 0.48 vs base 0.49 (excess -0.01), med -0.1% | 742, 2.54/yr, hit 0.55 vs base 0.56 (excess -0.01), med +0.5% | 2788, 9.53/yr, hit 0.45 vs base 0.47 (excess -0.02), med -0.6% |
| W|0.8 | 4808, 28.26/yr, hit 0.52 vs base 0.50 (excess +0.02), med +0.3% | 4608, 15.75/yr, hit 0.48 vs base 0.50 (excess -0.01), med -0.1% | 771, 2.64/yr, hit 0.54 vs base 0.56 (excess -0.02), med +0.6% | 2730, 9.33/yr, hit 0.46 vs base 0.47 (excess -0.01), med -0.7% |
| W|0.9 | 4773, 28.06/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.2% | 4618, 15.78/yr, hit 0.49 vs base 0.50 (excess -0.01), med -0.1% | 762, 2.60/yr, hit 0.55 vs base 0.56 (excess -0.01), med +0.7% | 2760, 9.43/yr, hit 0.46 vs base 0.47 (excess -0.01), med -0.6% |
| W|0.7 | 4768, 28.03/yr, hit 0.52 vs base 0.50 (excess +0.02), med +0.3% | 4583, 15.67/yr, hit 0.48 vs base 0.50 (excess -0.01), med -0.1% | 775, 2.65/yr, hit 0.53 vs base 0.56 (excess -0.03), med +0.5% | 2698, 9.22/yr, hit 0.46 vs base 0.47 (excess -0.01), med -0.6% |
| S|1.1 | 4577, 26.90/yr, hit 0.52 vs base 0.50 (excess +0.02), med +0.3% | 4416, 15.09/yr, hit 0.49 vs base 0.50 (excess -0.01), med -0.1% | 775, 2.65/yr, hit 0.54 vs base 0.56 (excess -0.01), med +0.5% | 2564, 8.76/yr, hit 0.46 vs base 0.47 (excess -0.01), med -0.6% |

## 1H Breakdown ✕ — current BRK, chosen None, **adopted BRK**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| BRK ←adopted | 901, 5.30/yr, hit 0.42 vs base 0.50 (excess -0.08), med -1.2% | 733, 2.51/yr, hit 0.52 vs base 0.50 (excess +0.03), med +0.1% | 121, 0.41/yr, hit 0.40 vs base 0.42 (excess -0.03), med -1.2% | 418, 1.43/yr, hit 0.56 vs base 0.52 (excess +0.04), med +0.8% |
| BRK ←adopted | 901, 5.30/yr, hit 0.42 vs base 0.50 (excess -0.08), med -1.2% | 733, 2.51/yr, hit 0.52 vs base 0.50 (excess +0.03), med +0.1% | 121, 0.41/yr, hit 0.40 vs base 0.42 (excess -0.03), med -1.2% | 418, 1.43/yr, hit 0.56 vs base 0.52 (excess +0.04), med +0.8% |
| BRK_qL | 1903, 11.19/yr, hit 0.47 vs base 0.50 (excess -0.03), med -0.4% | 1713, 5.86/yr, hit 0.50 vs base 0.50 (excess +0.00), med -0.0% | 301, 1.03/yr, hit 0.45 vs base 0.42 (excess +0.02), med -0.7% | 995, 3.40/yr, hit 0.50 vs base 0.52 (excess -0.02), med +0.0% |
| BRK_L | 1474, 8.66/yr, hit 0.46 vs base 0.50 (excess -0.04), med -0.6% | 1233, 4.21/yr, hit 0.50 vs base 0.49 (excess +0.00), med -0.0% | 209, 0.71/yr, hit 0.45 vs base 0.42 (excess +0.03), med -0.6% | 712, 2.43/yr, hit 0.49 vs base 0.52 (excess -0.03), med -0.0% |
| BRK_q | 1187, 6.98/yr, hit 0.44 vs base 0.50 (excess -0.06), med -0.8% | 1063, 3.63/yr, hit 0.52 vs base 0.50 (excess +0.02), med +0.1% | 173, 0.59/yr, hit 0.42 vs base 0.42 (excess -0.01), med -0.8% | 612, 2.09/yr, hit 0.56 vs base 0.52 (excess +0.04), med +0.9% |

## 1H SELL — current W|1.0, chosen None, **adopted W|1.0**

| option | tune | check | check equities | check crypto |
|---|---|---|---|---|
| W|1.0 ←adopted | 5030, 29.57/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.3% | 4583, 15.67/yr, hit 0.52 vs base 0.50 (excess +0.02), med +0.1% | 689, 2.36/yr, hit 0.43 vs base 0.45 (excess -0.02), med -0.6% | 2826, 9.66/yr, hit 0.55 vs base 0.53 (excess +0.02), med +0.7% |
| W|1.0 ←adopted | 5030, 29.57/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.3% | 4583, 15.67/yr, hit 0.52 vs base 0.50 (excess +0.02), med +0.1% | 689, 2.36/yr, hit 0.43 vs base 0.45 (excess -0.02), med -0.6% | 2826, 9.66/yr, hit 0.55 vs base 0.53 (excess +0.02), med +0.7% |
| W|0.9 | 5008, 29.44/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.3% | 4557, 15.58/yr, hit 0.52 vs base 0.51 (excess +0.01), med +0.1% | 674, 2.30/yr, hit 0.43 vs base 0.45 (excess -0.02), med -0.7% | 2832, 9.68/yr, hit 0.54 vs base 0.53 (excess +0.02), med +0.7% |
| W|1.1 | 4971, 29.22/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.2% | 4575, 15.64/yr, hit 0.52 vs base 0.50 (excess +0.02), med +0.1% | 702, 2.40/yr, hit 0.43 vs base 0.45 (excess -0.01), med -0.6% | 2804, 9.58/yr, hit 0.54 vs base 0.53 (excess +0.02), med +0.7% |
| W|0.8 | 4956, 29.13/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.2% | 4544, 15.53/yr, hit 0.51 vs base 0.51 (excess +0.01), med +0.1% | 666, 2.28/yr, hit 0.43 vs base 0.45 (excess -0.02), med -0.6% | 2832, 9.68/yr, hit 0.54 vs base 0.53 (excess +0.01), med +0.7% |
| S|0.7 | 4952, 29.11/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.2% | 4572, 15.63/yr, hit 0.52 vs base 0.50 (excess +0.02), med +0.2% | 718, 2.45/yr, hit 0.45 vs base 0.45 (excess +0.00), med -0.5% | 2783, 9.51/yr, hit 0.54 vs base 0.53 (excess +0.02), med +0.8% |
| CONF|0.7 | 4935, 29.01/yr, hit 0.50 vs base 0.50 (excess +0.00), med +0.0% | 4541, 15.52/yr, hit 0.53 vs base 0.50 (excess +0.02), med +0.2% | 709, 2.42/yr, hit 0.44 vs base 0.45 (excess -0.01), med -0.5% | 2776, 9.49/yr, hit 0.57 vs base 0.53 (excess +0.04), med +1.0% |
| W|0.7 | 4907, 28.84/yr, hit 0.51 vs base 0.50 (excess +0.01), med +0.3% | 4512, 15.42/yr, hit 0.51 vs base 0.51 (excess +0.00), med +0.1% | 665, 2.27/yr, hit 0.43 vs base 0.45 (excess -0.02), med -0.6% | 2820, 9.64/yr, hit 0.53 vs base 0.53 (excess +0.00), med +0.5% |

