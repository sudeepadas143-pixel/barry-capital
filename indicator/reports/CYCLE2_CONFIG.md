# Cycle engine CY-2: nonlinear, trade-aware turning-point models (exploratory)

**Status: FROZEN** (2026-10-28), before any CY-2 code ran.

**Data.** All data was examined by CY-1 (including its test periods), so every CY-2 result is
**exploratory**. Reserved instruments and post-freeze candles are not read.

**Reused from CY-1:**
* universe (108), loader, frozen labels, zone target, CY-1 features, B_ext/B_rsi baselines;
* alert mechanics (onset with cooldown c = L/4);
* the ledger.

**Not repeated:** CY-1's single-split linear/context selection.

## Changes vs CY-1

1. **New causal features** (`research/cycle2_features.py`; Pine-portable), with L, q as in CY-1:
   * `bbz` = (c − SMA_L)/stdev_L;
   * `roc` = (c − c[q])/ATR, and `roc_acc` = roc − roc[q];
   * `wick_up` / `wick_dn` = 3-bar mean of upper / lower wick share of the range;
   * `td_up` / `td_dn` = consecutive closes above / below the close 4 bars earlier, capped at 13,
     divided by 13;
   * `vratio` = log(ATR5/ATR_L);
   * `dd_hh` = (HH_L − c)/ATR, `du_ll` = (c − LL_L)/ATR;
   * `above` = 1 if c > EMA_L, else 0;
   * `climax` = relvol × sign(c − o) (volume assets; NaN otherwise).
2. **Two targets** per TF × direction:
   * **zone:** the CY-1 label-proximity target;
   * **barrier:** a reversal entry at open[s+1] reaches +U·ATR[s] in the reversal direction before
     −S·ATR[s] against, within H = L/2 candles. U = D/2 and S = D/4. If both are hit on the same
     candle, the stop counts.
3. **Models:**
   * **B_ext** (baseline);
   * **LR**: the CY-1 L_mom logistic, C = 0.1;
   * **GBZ / GBB**: HistGradientBoosting on CY-1 + CY-2 features, for the zone and the barrier
     target respectively. Primary hyperparameters: depth 3, 60 trees, learning rate 0.1, min
     leaf 200, L2 1.0. NaN is routed natively, so there is one model for volume and non-volume
     feeds.
4. **Walk-forward.** Expanding window, refit per test year. Training candles whose label or
   barrier window reaches the test year are purged. Training rows are subsampled with a stride,
   to at most 300k.

   | TF | test years |
   |---|---|
   | 1W | 2008–2026, refit every 2 years |
   | 1D | 2010–2026 |
   | 4H, 1H | 2021–2026 (crypto history before 2021 only) |

   Thresholds use only training data:
   * **warning:** onset rate = 3× the event rate;
   * **standard:** 2× (as CY-1);
   * **high-conviction:** 0.75×.
5. **Confirmations**, for the standard tier:
   * (a) the CY-1 rule;
   * (b) the first EMA20/EMA50 cross against the prior move within m = L/2 candles after an onset.
6. **Metrics per TF × direction × model × tier,** on walk-forward out-of-time alerts:
   * events, recall, precision excluding duplicates, false alarms per asset-year, lead;
   * lift (calendar-cluster wild bootstrap);
   * barrier win rate;
   * MFE/MAE in ATR;
   * net return at H after `COST_BPS` (and 2×).
7. **Promotion** of a model over B_ext for a TF × direction (reported with uncertainty, no
   significance gate). All of:
   * at matched standard rate: lift higher and net return per alert higher;
   * the near-rate difference CI lower bound > −0.01;
   * the same sign of both improvements in each half of the test years;
   * the same sign in ≥ 3 of 4 robustness variants: depth 2/4, trees 30/120.
8. **Pine.** Promoted GBMs are exported as generated nested conditions, with a parity test of
   the Python tree evaluation against sklearn. Non-promoted cells ship B_ext. The production
   indicator is unchanged.

**Ledger trials:** `cy2-1W`, `cy2-1D`, `cy2-4H`, `cy2-1H`.
