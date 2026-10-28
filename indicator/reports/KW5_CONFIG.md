# KW-5: two-state weekly SELL architecture (exploratory)

**Status: FROZEN** (2026-10-28), before any KW-5 code ran on market data.

**Scope.** A structural study, not threshold tuning.
* No parameter is tuned.
* The production indicator is untouched until the evidence supports a replacement.
* Weekly BUY and all other timeframes are unchanged.

**Data and evaluator.** As in KW-3: weekly EVAL instruments from 2008, development before 2018,
and 2018+ as a robustness check on data already studied. The KW-3 evaluator and the **KW-3
adoption rule are reused unchanged**.

## States (`research/kenny_weekly_sell.py`)

* **EW (early warning):** Candidate A exactly as frozen by KW-3 (R = 6): an extended advance near
  the 52-week high with momentum off its high, plus a reversal candle or a failed new high.
* **CF (confirmed reversal):** the first week in (EW, EW + 13] with a close below the lowest low
  of the previous 4 weeks **and** the MACD histogram below 0. This is weekly structure plus
  momentum deterioration, reusing existing features.

## Reported

**Conditional outcomes** (classes, decline within 4/13/26 weeks, forward 4/13/26-week returns,
MFE/MAE), separately before 2018 and from 2018, for equities and crypto:
* all EWs, measured from the EW week;
* EWs that were later confirmed, from the EW week;
* EWs never confirmed, from the EW week;
* CFs, from the CF week.

Plus:
* the delay EW→CF in weeks;
* the price change from EW to CF (the cost of waiting);
* the drawdown from the 52-week high at CF;
* CF's late share.

**Systems compared with W0** (the current weekly SELL, the baseline), all with one SELL triangle
type:
* EW alone (= A);
* CF alone, a two-state system drawing only the confirmation;
* EW + CF, both drawn.

## Decisions

**Incremental value of confirmation** (reported, not a replacement criterion). CF adds value only
if, in **both** periods:
* CF's useful rate is ≥ EW's + 0.05;
* CF's median 26-week SELL-direction return is ≥ EW's;
* CF's late share is ≤ W0's.

**Replacement.** The CF and EW + CF systems are scored with the unchanged KW-3 adoption rule
against W0. Only a pass leads to a replacement. Otherwise W0 stays and the limitation is
documented.

**Ledger trial:** `kw5-eval` (hypothesis KW-5).
