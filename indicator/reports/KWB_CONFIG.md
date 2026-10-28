# KWB: weekly BUY for cycle bottoms on high-volatility assets (exploratory)

**Status: FROZEN** (2026-10-28), before any KWB code ran on market data.

**Why.** The shipped weekly BUY (High Conviction, B_ext ×1.1) measures extension in ATR14 units.
During crashes ATR14 inflates, so high-volatility assets never reach the threshold. BTCUSDT has no
weekly BUY at all.

## Variants (`research/kenny_wbuy.py`)

* **V1(k):** an onset of (close − EMA26)/ATR52 ≤ −k, i.e. extension against slow (52-week)
  volatility;
* **V2(k):** shipped BUY OR V1(k);
* k ∈ {2.5, 3.0, 3.5}, plus the shipped cooldown.

## Tuning and check

**Tuning.** On weekly candles before 2018 (EVAL universe; little crypto exists then), choose the
(variant, k) with the most arrows per instrument-year among those with:
* KR right-rate ≥ shipped's − 0.03 (KR rule: lowest 25% of the ±13-week range, and higher 6 weeks
  later);
* KF excess ≥ shipped's − 0.02 (higher 13 weeks later vs the instrument's base rate);
* ≥ 30 arrows.

**Check (2018+, previously studied).** Adopt only if **all** hold:
* right-rate ≥ shipped's − 0.03;
* excess ≥ shipped's − 0.02;
* coverage of meaningful swing lows ≥ shipped's;
* crypto coverage > shipped's.

**Reported, not used for tuning:** BTCUSDT, ETHUSDT and SOLUSDT weekly BUY dates, before and
after.

**Ledger trial:** `kwb-1W` (hypothesis KWB-1).
