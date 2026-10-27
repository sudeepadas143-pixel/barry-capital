# BTC audit

python scripts/audit_btc.py      → reports/BTC_AUDIT.md, reports/btc_audit.json

Data: BTCUSDT (Binance, from 2017-08) for every timeframe, plus BTC-USD (Yahoo, from
2014-09) for 1D/1W, closer to the long BTC history TradingView loads for BTCUSD charts.
Periods: "design" = before each timeframe's holdout start (the v2 design used these
dates); "recent" = holdout start to the end of the data (not used for any v2 design
decision; BTC is a development symbol, so this is the out-of-sample check for BTC).

Per row: signals, signals per year, precision (+2 ATR before -1 ATR), false positives
(-1 ATR first), invalidated (a close back through the broken level within 3 candles),
mean r_h in ATR with 95% month-cluster CI, mean forward return % over H candles after
costs, median MFE/MAE, and the same-count random-entry baseline (same direction).

## BTCUSDT 1H  (2017-08-17 → 2026-10-27)

| variant | tier | side | period | n | per yr | precision | false pos | invalidated ≤3 | mean r_h [95% CI] | fwd ret % | MFE / MAE | random r_h | p |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| default | MAJOR (shown) | bullish | design | 241 | 30.6 | 33% | 64% | 44% | -0.02 [-0.61, +0.57] | +0.13 | 2.21 / 2.00 | -0.08 | 0.41 |
| default | MAJOR (shown) | bullish | recent | 32 | 24.1 | 28% | 69% | 28% | -0.15 [-1.09, +0.98] | -0.04 | 2.65 / 2.37 | -0.41 | 0.35 |
| default | MAJOR (shown) | bearish | design | 214 | 27.2 | 39% | 59% | 49% | -0.43 [-1.00, +0.13] | -0.13 | 2.51 / 2.23 | -0.49 | 0.45 |
| default | MAJOR (shown) | bearish | recent | 44 | 33.2 | 30% | 68% | 52% | -0.64 [-2.04, +0.93] | -0.23 | 2.13 / 2.85 | -0.43 | 0.64 |
| default | MAJOR+CONFIRMED | bullish | design | 782 | 99.4 | 33% | 65% | 44% | +0.39 [-0.03, +0.76] | +0.27 | 2.20 / 2.12 | -0.08 | 0.00 |
| default | MAJOR+CONFIRMED | bullish | recent | 111 | 83.8 | 35% | 64% | 38% | +0.07 [-0.67, +0.89] | +0.06 | 2.82 / 2.42 | -0.40 | 0.11 |
| default | MAJOR+CONFIRMED | bearish | design | 597 | 75.9 | 32% | 67% | 49% | -0.29 [-0.63, +0.03] | -0.46 | 2.14 / 2.39 | -0.47 | 0.14 |
| default | MAJOR+CONFIRMED | bearish | recent | 116 | 87.5 | 34% | 65% | 53% | -0.27 [-1.28, +0.57] | -0.07 | 2.49 / 2.17 | -0.47 | 0.29 |
| acceptance | MAJOR (shown) | bullish | design | 183 | 23.3 | 30% | 67% | 31% | +0.36 [-0.32, +1.07] | +0.31 | 2.16 / 2.02 | -0.08 | 0.08 |
| acceptance | MAJOR (shown) | bullish | recent | 28 | 21.1 | 29% | 68% | 36% | -0.68 [-1.95, +0.68] | -0.26 | 2.23 / 2.99 | -0.37 | 0.67 |
| acceptance | MAJOR (shown) | bearish | design | 151 | 19.2 | 42% | 56% | 32% | -0.12 [-0.86, +0.60] | -0.16 | 2.63 / 1.97 | -0.42 | 0.19 |
| acceptance | MAJOR (shown) | bearish | recent | 30 | 22.6 | 23% | 77% | 40% | -0.05 [-1.64, +1.72] | +0.12 | 2.07 / 2.11 | -0.44 | 0.31 |
| acceptance | MAJOR+CONFIRMED | bullish | design | 611 | 77.7 | 33% | 65% | 31% | +0.57 [+0.16, +0.98] | +0.32 | 2.20 / 2.04 | -0.07 | 0.00 |
| acceptance | MAJOR+CONFIRMED | bullish | recent | 93 | 70.2 | 29% | 69% | 34% | -0.41 [-1.07, +0.29] | -0.12 | 2.30 / 2.82 | -0.37 | 0.53 |
| acceptance | MAJOR+CONFIRMED | bearish | design | 435 | 55.3 | 35% | 64% | 33% | -0.15 [-0.53, +0.23] | -0.44 | 2.30 / 2.19 | -0.46 | 0.09 |
| acceptance | MAJOR+CONFIRMED | bearish | recent | 82 | 61.9 | 27% | 71% | 37% | -0.10 [-1.31, +0.94] | +0.15 | 2.20 / 1.95 | -0.41 | 0.27 |

## BTCUSDT 4H  (2017-08-17 → 2026-10-27)

| variant | tier | side | period | n | per yr | precision | false pos | invalidated ≤3 | mean r_h [95% CI] | fwd ret % | MFE / MAE | random r_h | p |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| default | MAJOR (shown) | bullish | design | 57 | 7.2 | 35% | 63% | 25% | +0.26 [-0.81, +1.41] | +0.66 | 1.95 / 2.20 | +0.34 | 0.52 |
| default | MAJOR (shown) | bullish | recent | 6 | 4.5 | 17% | 83% | 83% | -0.92 [-1.76, -0.20] | -0.96 | 1.26 / 3.06 | -0.01 | 0.66 |
| default | MAJOR (shown) | bearish | design | 58 | 7.4 | 34% | 64% | 43% | -0.25 [-1.60, +1.30] | -0.28 | 1.92 / 2.19 | -0.66 | 0.24 |
| default | MAJOR (shown) | bearish | recent | 15 | 11.3 | 47% | 53% | 47% | +0.16 [-1.46, +2.92] | -0.07 | 2.63 / 1.79 | -0.28 | 0.41 |
| default | MAJOR+CONFIRMED | bullish | design | 243 | 30.9 | 33% | 66% | 39% | +0.99 [+0.07, +1.78] | +1.57 | 2.75 / 2.52 | +0.39 | 0.04 |
| default | MAJOR+CONFIRMED | bullish | recent | 26 | 19.6 | 23% | 77% | 65% | -0.85 [-2.08, +0.22] | -0.95 | 1.58 / 2.73 | -0.10 | 0.76 |
| default | MAJOR+CONFIRMED | bearish | design | 151 | 19.2 | 31% | 68% | 48% | -0.16 [-1.06, +0.87] | -0.92 | 1.94 / 2.75 | -0.61 | 0.14 |
| default | MAJOR+CONFIRMED | bearish | recent | 38 | 28.7 | 37% | 63% | 34% | +0.69 [-0.83, +2.51] | +0.70 | 2.38 / 2.22 | -0.27 | 0.13 |
| acceptance | MAJOR (shown) | bullish | design | 50 | 6.4 | 32% | 66% | 28% | +0.17 [-0.92, +1.26] | +0.41 | 1.90 / 2.48 | +0.41 | 0.64 |
| acceptance | MAJOR (shown) | bullish | recent | 4 | 3.0 | 25% | 75% | 75% | -0.14 [-2.68, +2.40] | -0.02 | 3.03 / 2.92 | +0.11 | 0.50 |
| acceptance | MAJOR (shown) | bearish | design | 43 | 5.5 | 42% | 58% | 26% | -0.17 [-1.90, +1.66] | -0.22 | 1.71 / 2.06 | -0.59 | 0.30 |
| acceptance | MAJOR (shown) | bearish | recent | 10 | 7.5 | 50% | 50% | 30% | +0.34 [-1.79, +5.27] | +0.28 | 3.45 / 1.65 | -0.19 | 0.37 |
| acceptance | MAJOR+CONFIRMED | bullish | design | 186 | 23.6 | 38% | 61% | 25% | +1.01 [+0.02, +1.95] | +1.56 | 2.48 / 2.44 | +0.40 | 0.04 |
| acceptance | MAJOR+CONFIRMED | bullish | recent | 16 | 12.1 | 38% | 62% | 50% | -0.33 [-2.58, +1.53] | -0.50 | 2.33 / 2.76 | +0.02 | 0.54 |
| acceptance | MAJOR+CONFIRMED | bearish | design | 109 | 13.9 | 36% | 64% | 35% | -0.35 [-1.35, +0.65] | -1.55 | 1.85 / 2.73 | -0.60 | 0.31 |
| acceptance | MAJOR+CONFIRMED | bearish | recent | 31 | 23.4 | 39% | 61% | 26% | +0.88 [-0.88, +3.14] | +1.17 | 2.27 / 2.15 | -0.26 | 0.11 |

## BTCUSDT 1D  (2017-08-17 → 2026-10-25)

| variant | tier | side | period | n | per yr | precision | false pos | invalidated ≤3 | mean r_h [95% CI] | fwd ret % | MFE / MAE | random r_h | p |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| default | MAJOR (shown) | bullish | design | 6 | 0.9 | 33% | 67% | 50% | +0.43 [-2.58, +3.99] | +0.75 | 0.48 / 3.20 | +0.84 | 0.60 |
| default | MAJOR (shown) | bullish | recent | 6 | 2.1 | 33% | 67% | 50% | +1.41 [-1.62, +5.02] | +4.95 | 1.73 / 1.58 | +0.54 | 0.27 |
| default | MAJOR (shown) | bearish | design | 8 | 1.3 | 50% | 38% | 38% | +1.19 [-1.79, +4.59] | +4.25 | 2.08 / 0.87 | -0.89 | 0.07 |
| default | MAJOR (shown) | bearish | recent | 2 | 0.7 | 0% | 100% | 50% | +1.43 [-3.02, +5.88] | +1.10 | 4.34 / 2.27 | -0.53 | 0.20 |
| default | MAJOR+CONFIRMED | bullish | design | 39 | 6.1 | 44% | 56% | 38% | +2.75 [+0.61, +4.63] | +9.85 | 2.34 / 1.65 | +0.85 | 0.01 |
| default | MAJOR+CONFIRMED | bullish | recent | 27 | 9.6 | 30% | 70% | 52% | +1.00 [-0.73, +2.73] | +2.85 | 2.31 / 2.24 | +0.46 | 0.23 |
| default | MAJOR+CONFIRMED | bearish | design | 26 | 4.1 | 31% | 65% | 50% | +0.66 [-0.85, +2.33] | +2.57 | 1.38 / 1.65 | -0.93 | 0.05 |
| default | MAJOR+CONFIRMED | bearish | recent | 5 | 1.8 | 20% | 80% | 40% | +0.59 [-2.82, +4.08] | -1.03 | 1.44 / 1.77 | -0.60 | 0.25 |
| acceptance | MAJOR (shown) | bullish | design | 5 | 0.8 | 40% | 60% | 60% | +0.62 [-2.98, +4.47] | +1.48 | 0.72 / 3.42 | +0.81 | 0.53 |
| acceptance | MAJOR (shown) | bullish | recent | 3 | 1.1 | 33% | 67% | 0% | +3.86 [-1.85, +12.38] | +11.63 | 1.17 / 2.38 | +0.43 | 0.08 |
| acceptance | MAJOR (shown) | bearish | design | 5 | 0.8 | 60% | 40% | 20% | +1.97 [-0.53, +6.12] | +6.99 | 2.47 / 0.71 | -0.89 | 0.05 |
| acceptance | MAJOR (shown) | bearish | recent | 1 | 0.4 | 0% | 100% | 100% | -3.83 [-3.83, -3.83] | -16.31 | 0.49 / 4.23 | -0.41 | 0.90 |
| acceptance | MAJOR+CONFIRMED | bullish | design | 29 | 4.5 | 55% | 45% | 28% | +3.14 [+0.59, +5.13] | +11.64 | 4.59 / 1.04 | +0.78 | 0.00 |
| acceptance | MAJOR+CONFIRMED | bullish | recent | 18 | 6.4 | 39% | 61% | 44% | +1.32 [-1.07, +3.60] | +3.93 | 2.17 / 2.29 | +0.47 | 0.17 |
| acceptance | MAJOR+CONFIRMED | bearish | design | 16 | 2.5 | 44% | 56% | 25% | +1.43 [-0.32, +3.22] | +6.61 | 2.01 / 1.52 | -0.85 | 0.02 |
| acceptance | MAJOR+CONFIRMED | bearish | recent | 4 | 1.4 | 25% | 75% | 50% | -1.07 [-3.67, +3.02] | -6.95 | 0.66 / 2.96 | -0.47 | 0.66 |

## BTC-USD 1D  (2014-09-17 → 2026-10-26)

| variant | tier | side | period | n | per yr | precision | false pos | invalidated ≤3 | mean r_h [95% CI] | fwd ret % | MFE / MAE | random r_h | p |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| default | MAJOR (shown) | bullish | design | 16 | 1.7 | 62% | 38% | 19% | +2.05 [+0.10, +4.06] | +7.46 | 3.36 / 0.54 | +1.34 | 0.28 |
| default | MAJOR (shown) | bullish | recent | 6 | 2.1 | 33% | 67% | 50% | +1.50 [-1.66, +5.27] | +4.96 | 1.76 / 1.59 | +0.57 | 0.25 |
| default | MAJOR (shown) | bearish | design | 9 | 1.0 | 22% | 67% | 56% | -0.00 [-1.39, +1.35] | +1.08 | 0.53 / 1.50 | -1.58 | 0.22 |
| default | MAJOR (shown) | bearish | recent | 2 | 0.7 | 0% | 100% | 50% | +1.46 [-3.08, +6.00] | +1.06 | 4.41 / 2.31 | -0.54 | 0.20 |
| default | MAJOR+CONFIRMED | bullish | design | 84 | 9.0 | 61% | 39% | 25% | +4.08 [+2.39, +5.86] | +12.35 | 5.50 / 1.12 | +1.41 | 0.00 |
| default | MAJOR+CONFIRMED | bullish | recent | 26 | 9.2 | 31% | 69% | 50% | +1.23 [-0.53, +3.08] | +3.46 | 2.56 / 2.10 | +0.44 | 0.15 |
| default | MAJOR+CONFIRMED | bearish | design | 23 | 2.5 | 26% | 70% | 61% | -0.56 [-1.58, +0.48] | -1.71 | 0.96 / 2.14 | -1.59 | 0.21 |
| default | MAJOR+CONFIRMED | bearish | recent | 5 | 1.8 | 20% | 80% | 40% | +0.60 [-2.89, +4.16] | -1.05 | 1.45 / 1.82 | -0.61 | 0.27 |
| acceptance | MAJOR (shown) | bullish | design | 15 | 1.6 | 67% | 33% | 27% | +2.01 [-0.23, +4.34] | +7.49 | 3.45 / 0.79 | +1.52 | 0.35 |
| acceptance | MAJOR (shown) | bullish | recent | 3 | 1.1 | 33% | 67% | 0% | +4.09 [-1.90, +13.06] | +11.66 | 1.18 / 2.42 | +0.46 | 0.08 |
| acceptance | MAJOR (shown) | bearish | design | 5 | 0.5 | 20% | 80% | 60% | +0.01 [-0.99, +1.24] | +0.72 | 1.85 / 1.77 | -1.46 | 0.27 |
| acceptance | MAJOR (shown) | bearish | recent | 1 | 0.4 | 0% | 100% | 100% | -3.92 [-3.92, -3.92] | -16.50 | 0.48 / 4.30 | -0.38 | 0.90 |
| acceptance | MAJOR+CONFIRMED | bullish | design | 75 | 8.1 | 59% | 41% | 23% | +3.87 [+2.29, +5.38] | +11.68 | 5.37 / 1.33 | +1.48 | 0.00 |
| acceptance | MAJOR+CONFIRMED | bullish | recent | 17 | 6.0 | 41% | 59% | 35% | +1.72 [-0.74, +4.10] | +4.99 | 2.22 / 2.19 | +0.44 | 0.09 |
| acceptance | MAJOR+CONFIRMED | bearish | design | 14 | 1.5 | 21% | 79% | 43% | -0.36 [-1.81, +1.24] | -1.08 | 1.06 / 2.78 | -1.54 | 0.23 |
| acceptance | MAJOR+CONFIRMED | bearish | recent | 4 | 1.4 | 25% | 75% | 50% | -1.09 [-3.75, +3.10] | -7.01 | 0.66 / 3.02 | -0.46 | 0.67 |

## BTCUSDT 1W  (2017-08-14 → 2026-10-19)

| variant | tier | side | period | n | per yr | precision | false pos | invalidated ≤3 | mean r_h [95% CI] | fwd ret % | MFE / MAE | random r_h | p |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| default | MAJOR (shown) | bullish | design | 3 | 0.5 | 0% | 100% | 33% | -1.10 [-3.86, +2.32] | -18.26 | 1.97 / 1.94 | +1.52 | 0.85 |
| default | MAJOR (shown) | bullish | recent | 2 | 0.7 | 50% | 50% | 0% | +2.18 [-0.49, +4.85] | +21.46 | 3.37 / 1.24 | +0.50 | 0.18 |
| default | MAJOR (shown) | bearish | design | 1 | 0.2 | 100% | 0% | 0% | +1.15 [+1.15, +1.15] | +22.22 | 2.27 / 0.18 | -1.58 | 0.26 |
| default | MAJOR (shown) | bearish | recent | 0 | | | | | | | | | |
| default | MAJOR+CONFIRMED | bullish | design | 6 | 0.9 | 17% | 83% | 33% | +1.84 [-2.59, +8.41] | +8.99 | 2.30 / 1.51 | +1.65 | 0.39 |
| default | MAJOR+CONFIRMED | bullish | recent | 3 | 1.1 | 67% | 33% | 0% | +2.74 [-0.49, +4.85] | +23.28 | 5.93 / 0.57 | +0.65 | 0.13 |
| default | MAJOR+CONFIRMED | bearish | design | 3 | 0.5 | 33% | 33% | 0% | +0.10 [-1.73, +1.15] | +2.10 | 1.66 / 0.18 | -1.55 | 0.32 |
| default | MAJOR+CONFIRMED | bearish | recent | 0 | | | | | | | | | |
| acceptance | MAJOR (shown) | bullish | design | 3 | 0.5 | 0% | 100% | 33% | -1.12 [-4.17, +3.32] | -18.83 | 1.01 / 2.95 | +1.52 | 0.86 |
| acceptance | MAJOR (shown) | bullish | recent | 2 | 0.7 | 50% | 50% | 0% | +2.17 [-1.01, +5.34] | +21.56 | 3.73 / 0.96 | +0.50 | 0.18 |
| acceptance | MAJOR (shown) | bearish | design | 1 | 0.2 | 100% | 0% | 0% | +1.51 [+1.51, +1.51] | +28.78 | 2.19 / 0.36 | -1.58 | 0.20 |
| acceptance | MAJOR (shown) | bearish | recent | 0 | | | | | | | | | |
| acceptance | MAJOR+CONFIRMED | bullish | design | 5 | 0.8 | 20% | 80% | 20% | +2.04 [-3.71, +10.27] | +8.79 | 1.26 / 2.95 | +1.60 | 0.31 |
| acceptance | MAJOR+CONFIRMED | bullish | recent | 3 | 1.1 | 67% | 33% | 0% | +3.01 [-1.01, +5.34] | +25.12 | 6.22 / 0.23 | +0.65 | 0.09 |
| acceptance | MAJOR+CONFIRMED | bearish | design | 3 | 0.5 | 33% | 33% | 0% | -0.31 [-2.64, +1.51] | -5.03 | 0.36 / 0.82 | -1.55 | 0.40 |
| acceptance | MAJOR+CONFIRMED | bearish | recent | 0 | | | | | | | | | |

## BTC-USD 1W  (2014-09-15 → 2026-10-19)

| variant | tier | side | period | n | per yr | precision | false pos | invalidated ≤3 | mean r_h [95% CI] | fwd ret % | MFE / MAE | random r_h | p |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| default | MAJOR (shown) | bullish | design | 3 | 0.3 | 0% | 100% | 33% | -1.08 [-4.04, +2.64] | -18.24 | 1.99 / 1.99 | +2.89 | 0.95 |
| default | MAJOR (shown) | bullish | recent | 2 | 0.7 | 50% | 50% | 0% | +2.20 [-0.47, +4.88] | +21.39 | 3.40 / 1.11 | +0.51 | 0.18 |
| default | MAJOR (shown) | bearish | design | 0 | | | | | | | | | |
| default | MAJOR (shown) | bearish | recent | 0 | | | | | | | | | |
| default | MAJOR+CONFIRMED | bullish | design | 11 | 1.2 | 45% | 55% | 27% | +6.01 [+1.64, +10.87] | +50.57 | 11.20 / 1.05 | +2.80 | 0.03 |
| default | MAJOR+CONFIRMED | bullish | recent | 3 | 1.1 | 67% | 33% | 0% | +2.79 [-0.47, +4.88] | +23.24 | 5.99 / 0.58 | +0.66 | 0.13 |
| default | MAJOR+CONFIRMED | bearish | design | 1 | 0.1 | 0% | 100% | 0% | -1.83 [-1.83, -1.83] | -33.44 | 0.25 / 2.61 | -2.43 | 0.59 |
| default | MAJOR+CONFIRMED | bearish | recent | 0 | | | | | | | | | |
| acceptance | MAJOR (shown) | bullish | design | 3 | 0.3 | 0% | 100% | 33% | -1.07 [-4.38, +3.78] | -18.76 | 1.01 / 3.04 | +2.89 | 0.95 |
| acceptance | MAJOR (shown) | bullish | recent | 2 | 0.7 | 50% | 50% | 0% | +2.20 [-1.02, +5.42] | +21.71 | 3.73 / 0.87 | +0.51 | 0.18 |
| acceptance | MAJOR (shown) | bearish | design | 0 | | | | | | | | | |
| acceptance | MAJOR (shown) | bearish | recent | 0 | | | | | | | | | |
| acceptance | MAJOR+CONFIRMED | bullish | design | 10 | 1.1 | 50% | 50% | 20% | +6.13 [+1.23, +11.22] | +46.74 | 10.92 / 2.15 | +2.79 | 0.05 |
| acceptance | MAJOR+CONFIRMED | bullish | recent | 3 | 1.1 | 67% | 33% | 0% | +3.07 [-1.02, +5.42] | +25.22 | 6.36 / 0.23 | +0.66 | 0.09 |
| acceptance | MAJOR+CONFIRMED | bearish | design | 1 | 0.1 | 0% | 100% | 0% | -2.82 [-2.82, -2.82] | -49.53 | 0.24 / 3.09 | -2.43 | 0.68 |
| acceptance | MAJOR+CONFIRMED | bearish | recent | 0 | | | | | | | | | |

