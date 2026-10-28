# KX: outside-the-chart context for cycle tops and bottoms (exploratory)

**Status: FROZEN** (2026-10-28), before any KX code ran on market data. The user approved the
plan.

## Data

All through the project guards: registered symbols only, nothing after FREEZE.
* **Funding:** cached Binance funding (2020+) and open interest (2021-12+) for 9 perps: BTC, ETH,
  SOL, BNB, XRP, ADA, DOGE, LINK, LTC.
* **Alt breadth:** computed from the EVAL crypto daily candles. These are surviving coins, so
  survivorship bias is disclosed.
* **VIX:** the Cboe free daily CSV (`data_ext/VIX_History.csv`, cut at 2026-10-27; sha256
  122ea1f2…d036).

**No liquidations.** No free market-wide history exists.

## Context (`research/kenny_context.py`)

Known at each daily close.
* **Top context**, any of:
  * funding 7-day mean in the top 10% of its prior year (crowded longs);
  * open interest +15% in 14 days while price is ≤ +5% (leverage building);
  * alt breadth down ≥ 10 points in 20 days (narrowing).
* **Bottom context.** Three parts:
  * **neg:** negative funding, or funding in the bottom 10% of its prior year;
  * **flush:** an open-interest flush (−15% in 14 days with price −10%) within the last 14 days;
  * **washed:** alt breadth ≤ 20%.
* **VIX reversal:** within the last 10 days, the 10-day max VIX was ≥ max(30, its 1-year 90th
  percentile), and VIX has since fallen ≥ 20% from that max.

## Tests (daily candles; "right" = KR rule, "excess" = KF rule at L/2 = 31 days)

**A. Crypto SELL filter.** Shipped 1D SELL arrows on the 9 perps, kept only with top context. Vs
all SELL arrows.

**B. Crypto bottoms.**
* B1: shipped 1D BUY arrows, kept only with bottom context (≥ 2 of 3 parts);
* B2: standalone BUY = an onset of all three bottom parts, 15-day cooldown.
* Both vs the shipped 1D BUY.

**C. Equity BUY filter.** Shipped 1D and 1W BUY arrows on equities and indices, kept only with a
VIX reversal. Vs all BUY arrows.

**Splits:**
* crypto: tuning before 2023-01-01 (2020–2022: the 2021 top and the 2022 bottom), check 2023+;
* equities: tuning before 2018, check 2018+;
* both check periods were studied before.

**No parameter is tuned.** The context thresholds above are fixed.

## Adoption

**A filter (A, B1, C)** is adopted only if, in both periods:
* its right-rate is ≥ unfiltered + 0.05;
* its excess is ≥ unfiltered + 0.03;
* n ≥ 15 per period.

The samples are small, and this is disclosed.

**B2** is adopted only if, in both periods:
* excess ≥ +0.05;
* right-rate ≥ shipped BUY's − 0.03;
* n ≥ 10.

**Pine.** Anything adopted must be available live in TradingView. VIX (CBOE:VIX) is. Funding and
open-interest symbol availability must be verified before shipping.

**Ledger trial:** `kx-all` (hypothesis KX-1).
