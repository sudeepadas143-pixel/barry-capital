# KW-6: Weekly Cycle Engine (WCE) — design and frozen evaluation plan (exploratory)

**Status: FROZEN** (2026-10-28), before any WCE code ran on market data.

**Scope.** Research only.
* Production Kenny's Divergence Indicator, its weekly BUY/SELL, daily, 4H and 1H logic, and
  production HC-MTF are unchanged.
* Any future production use would keep only the green BUY and red SELL triangles.

## 1. Source models reviewed (mechanisms only; no code copied)

| source | licence | mechanism used | not used / limitation |
|---|---|---|---|
| Deep momentum networks with market trend dynamics (PMC12404547) | article | weekly **fast vs 52-week slow momentum sign regime** (bull / correction / bear / rebound); turning points = regime transitions; 8–20-week fast windows | the XGBoost/LSTM stack, daily rebalancing; edge vanishes at 25 bps |
| Exhaustion Scanner (casoon pine-scripts) | MIT (site footer) | **role-separated** score: location (stretch), momentum exhaustion, reaction trigger; regime shifts thresholds rather than blocking | 0–100 weighted blend; confirmation/repaint behaviour undocumented |
| peterdmv/tradingview | MPL-2.0 | ATR distance from the 52-week high; PowerTrend trend start/end from an MA stack | no cycle or divergence logic |
| CHRD pine scripts | MIT | Trend Compass lifecycle (emerging → accelerating → mature → exhausting → reversing); bottom scorecard (RSI, %B, momentum turn, MA test, capitulation volume) | phase formulas not published on the page |

Earlier project findings reused:
* KW-3/KW-5: weekly confirmations arrive late; unconfirmed warnings are mostly premature.
* KW-1: absolute ATR thresholds miss high-volatility assets, so stretch here is a percentile of
  the instrument's own history.

## 2. Engine (`research/weekly_cycle.py`)

**Groups.** Each answers one question with one witness, so correlated oscillators (RSI, MACD)
are not counted twice.

**A. Phase.**
* Fast momentum fm = 13-week change / (ATR·√13); slow momentum sm = 52-week change / (ATR·√52).
* Regime by the signs of (sm, fm): bull, correction, bear, rebound.
* Stretch = percentile of (close − SMA40)/ATR within the instrument's own last 156 weeks.

**B. Exhaustion** (three roles, each counted once):
* **Location:** stretch ≥ 0.90 (top) or ≤ 0.10 (bottom).
* **Momentum:** fm ≥ 1.0 below its 8-week max (top), or ≥ 1.0 above its 8-week min (bottom).
* **Trigger** (top): failed new 26-week high, an upper-wick rejection (≥ 50% of the range, close
  in the lower half), or a bearish engulfing.
* **Trigger** (bottom): failed new 26-week low, a lower-wick rejection, a bullish engulfing, or a
  volatility burst (log ATR5/ATR26 ≥ 0.4) with a lower wick ≥ 40%. The bottom model is its own
  model, not a mirror of the top: it admits capitulation.

**C. Transition.**
* Persistent fast momentum: two consecutive weeks with fm < 0 (top) or fm ≥ 0 (bottom).
* A structure break: close below the prior 8-week low (top) or above the prior 8-week high
  (bottom) within the last 3 weeks.

**State machine** (top side; the bottom side mirrors the roles):
* **Exhausted:** the trigger fires while location and momentum were live within EVID = 8 weeks,
  in a bull or correction regime (bear or rebound for bottoms).
* **Transition:** C holds within LINK = 26 weeks after an Exhausted state. A correction without
  prior exhaustion is an ordinary pullback and raises nothing.

**Signals:**
* SELL **warning** = entry into Exhausted; SELL **confirmed** = entry into Transition.
* BUY **warning** and **confirmed** are the same for the bottom side.

**Repeats and decay:**
* Re-entry needs the state to have been off for REARM = 4 weeks, so one persistent condition
  cannot emit unlimited signals.
* Evidence older than EVID weeks (roles) or LINK weeks (exhaustion → transition) is stale and
  ignored.

**Parameters.** All are fixed in advance (13/52, 156, 0.90/0.10, 1.0, 8/26/4, 8). **None is
tuned on market data.** This is the simple, interpretable design; no search follows.

## 3. Evaluation (`scripts/kw6_eval.py`)

**Data.** EVAL weekly instruments from 2008, via the guarded loader. Development is before 2018.
2018+ has **already been studied** in KW-1…KW-5 and is a robustness check only. Results are given
for all instruments, equities (equity + index) and crypto (with sample sizes), and other groups.

**Compared, per side and purpose:**

| side | purpose | candidates |
|---|---|---|
| SELL | warning | WCE-warn, KW-3 Candidate A, RSI-70 recross |
| SELL | confirmed | WCE-conf, current weekly SELL (W0), SMA40 break, fast/slow regime transition |
| BUY | warning | WCE-warn, current weekly BUY (W0), RSI-30 recross |
| BUY | confirmed | WCE-conf, SMA40 reclaim, fast/slow regime transition |

**Metrics** (KW-3 definitions, mirrored for BUY):
* classes: useful / premature / late / false reversal / flat, with MOVE = 3 ATR;
* decline (or rally) within 4/13/26 weeks;
* forward 4/13/26-week returns in the signal direction;
* MFE/MAE;
* major-turn capture: a labelled 1W top (bottom) with a signal in [−13, +2] weeks;
* lag vs the ±26-week extreme;
* signals per instrument-year;
* net 13-week return after `COST_BPS`, as a strategy check;
* the share of instruments where WCE beats the side's W0.

**Ablations** (WCE-warn and WCE-conf, each with one group removed):
* no location role;
* no momentum role;
* no trigger role;
* transition without the exhaustion requirement;
* transition without the structure break.

A group "adds value" if removing it lowers the useful rate by ≥ 0.03 **or** the median 26-week
return by ≥ 1 pp, in **both** periods.

## 4. Decision rule (frozen)

* **SELL:** WCE-warn and WCE-conf are each scored with the **unchanged KW-3 adoption rule**
  against W0 SELL.
* **BUY:** the same rule mirrored against W0 BUY:
  * in both periods: useful ≥ W0's + 0.05, and median 26-week return ≥ W0's + 1 pp;
  * in 2018+: bottom capture ≥ W0's − 0.05, signals per instrument-year ≤ 2× W0's, lag ≤ W0's + 2
    weeks, and equities/crypto useful > W0's where both have n ≥ 20.

The WCE **merits further testing** only if at least one WCE signal passes its rule. Otherwise the
failure is documented and production stays unchanged. Sophistication alone is not a reason to
adopt.

**Ledger trial:** `kw6-eval` (hypothesis KW-6).
