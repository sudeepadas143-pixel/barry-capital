# KW-2: targeted weekly fixes (exploratory)

**Status: FROZEN** (2026-10-28), after KW-1 and before any KW-2 code ran on market data.

**Why a second trial.** KW-1 (`reports/KW_RESULTS.md`) adopted nothing. Its diagnostics showed two
defects in the current weekly engine (W0):

1. **SELL fires after crashes.** Confirmed weekly SELLs land near major lows, for example SPY
   2020-03-02 and 2025-04-07, and QQQ 2020-03 and 2025-04. In 2018+ the median 26-week return
   after a SELL is +5.2%: price rose.
2. **BUY never fires on BTC or ETH.** An absolute threshold of 3 ATR below EMA26 is not reached on
   high-volatility weekly charts.

KW-2 tests only fixes for these two defects. KW-1's cluster variants are **not** repeated.

**Scope and data.** Weekly only; daily and lower timeframes are unchanged. The data, guards,
universe, split (tuning before 2018, 2018+ reported separately but not unseen), metrics and
adoption rule are those of `reports/KW_CONFIG.md`.

## Variants (`research/kenny_weekly.py`)

All variants drop the cooldown, so repeats of a qualifying state are allowed.

| id | rule | grid (tuned on < 2018) |
|---|---|---|
| X1 (SELL) | current Confirmed SELL, dropped while the drawdown from the 52-week high ≥ g ATR14 | g ∈ {2, 4, 6} |
| X2 (SELL) | GBZ High Conviction onset (earlier than Confirmed), same guard | g ∈ {2, 4, 6} |
| Y1 (BUY) | current BUY **or** an onset of ext_c's own 156-week percentile ≤ q (with ext_c < 0) | q ∈ {0.02, 0.05} |
| Y2 (BUY) | the percentile rule alone | q ∈ {0.02, 0.05} |

The guard and the percentile rule are asset-agnostic: both are in units of the instrument's own
volatility or own history.

**Tuning objective.** The pre-2018 median 26-week forward return in the signal direction, subject
to:
* ≥ 25 signals;
* ≥ 0.05 signals per asset-year.

**Adoption rule** (per side, as in KW):
* the 2018+ median 26-week return is better than W0's;
* the major-turn hit rate is ≥ W0's − 0.05;
* ≥ 0.05 signals per asset-year.

**Ledger trial:** `kw2-1W` (hypothesis KW-2).
