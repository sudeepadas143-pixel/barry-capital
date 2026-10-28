# KW-4: Candidate A variants for the weekly SELL (exploratory)

**Status: FROZEN** (2026-10-28), before any KW-4 code ran on market data.

**Scope.** A diagnostic refinement of KW-3 candidate A, for the weekly SELL only.
* No production indicator change.
* Weekly BUY and all other timeframes are untouched.
* The data, guards, evaluator, metrics and **adoption rule are those of `reports/KW3_CONFIG.md`,
  unchanged**. Comparison is against W0, with A and the RSI-70 recross shown alongside.

**Tuning and robustness check.**
* Parameters are chosen walk-forward per year on earlier signals: development before 2018,
  outcome windows purged.
* 2018+ is a robustness check on data already examined in earlier research.
* Nothing is re-tuned after 2018+ is seen. KW-4 stops after these three variants.

## Variants (`research/kenny_weekly_sell.py`)

Each variant adds one hypothesis to A's arm: extended advance, RSI ≥ 65 within 8 weeks, near the
52-week high, RSI ≥ 5 off its 8-week max.

| id | hypothesis for A's premature signals | rule | grid |
|---|---|---|---|
| A1 | they come on modest advances | A + extension ≥ x40 ATR above SMA40 within 8 weeks + falling 13-week momentum | x40 ∈ {2, 3} |
| A2 | one reversal candle is weak evidence | A's arm + failed new 52-week high, then a weekly close below that week's low within w weeks | w ∈ {2, 4} |
| A3 | they come inside persistent, still-accelerating trends | A, suppressed while TSMOM > cap and the SMA40 slope is still rising (≥ its value 8 weeks ago) | cap ∈ {1.5, 2.5} |

**Additional report: breadth.** The share of instruments (each with ≥ 3 signals) where the
variant's useful rate beats W0, and beats A.

**Ledger trial:** `kw4-eval` (hypothesis KW-4).
