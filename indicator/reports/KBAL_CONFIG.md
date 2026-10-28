# KBAL: more BUY arrows on 4H and 1H (balance BUY against SELL); arrow size by timeframe

**Status: decided 2026-10-28, EXPLORATORY.** The user saw far fewer BUYs than SELLs on 4H/1H (zero
BUYs on BTC 1H) and accepted a little less accuracy on lower timeframes to balance them.

## Rule (fixed before choosing; uses tuning-period numbers only)

For 4H and 1H, take the **lowest** High-Conviction threshold scale in {0.7, 0.8, 0.9, 1.0, 1.1}
whose **tuning-period** excess (KF rule: price higher L/2 later vs the base rate) is ≥ +0.02 with
n ≥ 30. Drop the strength cut-off there, so every such BUY is drawn. 1W and 1D are unchanged.

Source: `reports/kf_results.json` (already computed). **Caveat:** its check-period numbers were
already seen in KF, so this is not a clean out-of-sample choice.

## Outcome

| TF | BUY before | BUY now | Tuning excess · rate/yr | Check excess · rate/yr | SELL rate/yr (tune / check) |
|---|---|---|---|---|---|
| 4H | H × 1.1 | **H × 0.8** | +0.023 · 5.8 (was +0.043 · 2.1) | +0.129 · 3.3 (was +0.175 · 1.0) | 9.3 / 4.9 |
| 1H | H × 1.0, strength ≥ 1 | **H × 0.8, no strength cut** | +0.025 · 16.3 (was +0.029 · 9.2 before the cut) | +0.058 · 10.4 (was +0.073 · 6.1) | 29.6 / 15.7 |

Scale 0.7 failed the rule on both timeframes (4H tuning −0.004; 1H tuning +0.013).

**BTC, last 12 months, before the per-chart de-duplication:**
* 4H BUY: from 3 to 6. SELL: 7.
* 1H BUY: from 12 (0 shown after the strength cut) to 21. SELL: 33.

The research constants `KR_BUY_SCALE` / `KS_BUY_K` stay as the KR/KS record; the Pine uses
`BAL_BUY_SCALE` / `BAL_BUY_K`.

## Arrow size by timeframe (display only)

The weight of an arrow follows its timeframe:

| | 4H and below | 1D | 1W |
|---|---|---|---|
| BUY / SELL | small | normal | large |
| VIX-confirmed BUY | — | large | huge |
