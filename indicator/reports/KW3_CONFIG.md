# KW-3 stage 2: weekly SELL candidates (exploratory)

**Status: FROZEN** (2026-10-28), after the pre-2018 diagnosis (`reports/KW3_DIAG.md`) and before
any candidate was scored.

**Scope.** Weekly SELL only. Weekly BUY, daily, 4H, 1H and production HC-MTF are unchanged; the
current weekly SELL (W0) is the baseline and the rollback.

**What the diagnosis showed** (pre-2018 W0 SELLs, outcome windows ending before 2018):
* **Late:** 50% of signals fired when price was already ≥ 3 ATR below its 26-week high.
* **Premature:** 24% saw price rise 3 ATR first.
* **Useful:** only 9%.
* **Missed tops** (380) sat near the 52-week high:
  * median 0.75 ATR from that high, 3.4 ATR above SMA40;
  * RSI 68 and still-positive 13-week momentum;
  * a failed new high or reversal candle in the prior 4 weeks.
* Divergence was rare at both.

## Candidates (`research/kenny_weekly_sell.py`, at most three)

| id | purpose | rule | parameter grid |
|---|---|---|---|
| A | major-top warning | extended advance (rally from 52w low ≥ R ATR, TSMOM ≥ 0.5, RSI max 8w ≥ 65) + RSI ≥ 5 below its 8w max + shooting star / bearish engulfing / failed new 52w high, within 2 ATR of the 52w high | R ∈ {6, 10} |
| B | downside confirmation | mature uptrend (TSMOM ≥ 0.5 and within 2 ATR of the 52w high in the last 13w) first closes below SMA40 (in 13w), MACD hist < 0, drawdown from 52w high < dlim ATR | dlim ∈ {4, 6} |
| C | two-stage | stage 1 (internal): extended advance with RSI ≥ 65, or Kenny's weekly top zone; stage 2 within 13w: close below the prior 4-week low while drawdown < dmax ATR | dmax ∈ {3, 5} |

**Baselines** at their natural frequency:
* W0 (current Confirmed SELL);
* SMA40x: first weekly close below SMA40 after ≥ 13 weeks above;
* RSI70: weekly RSI re-crossing 70 down.

## Evaluation (`scripts/kw3_eval.py eval`)

**Data.** EVAL weekly instruments from 2008.
* **Development:** < 2018. Each candidate's parameter is chosen **walk-forward per year**, on
  signals before that year, by useful rate.
* **Robustness check:** 2018+. This data was examined in earlier research, so it is not unseen.
* Results are reported for all instruments, equities (equity + index) and crypto separately.

**Measured separately by purpose:**
* **Warning:**
  * major tops caught: a labelled 1W top with a signal in [−13, +2] weeks;
  * median lag vs the ±26-week peak.
* **Confirmation:**
  * decline ≥ 3 ATR within 4, 13 and 26 weeks;
  * the class shares;
  * median forward returns;
  * MFE/MAE;
  * net 13-week short return after `COST_BPS`;
  * signals per instrument-year;
  * the strong-uptrend (TSMOM ≥ 1) share of signals, and the premature rate there.

## Adoption rule (per candidate, walk-forward parameters)

A candidate passes only if all of these hold.

In **both** periods (< 2018 and 2018+):
* useful rate ≥ W0's + 0.05;
* median 26-week SELL-direction return ≥ W0's + 1 percentage point.

In 2018+:
* major-top catch ≥ W0's − 0.05;
* signals per instrument-year ≤ 2× W0's (not merely more alerts);
* median lag vs the peak ≤ W0's + 2 weeks (not merely later);
* for equities and for crypto, wherever both have ≥ 20 signals: useful rate > W0's.

**Choice.** If several pass, the one with the higher pre-2018 useful rate is adopted. If none
passes, W0 stays and the remaining limitation is documented.

**Ledger trial:** `kw3-eval` (hypothesis KW-3).
