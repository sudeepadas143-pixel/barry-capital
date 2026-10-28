# KWB-2: weekly BUY from cycle-sized drawdowns (exploratory)

**Status: FROZEN** (2026-10-28), after KWB-1 and before any KWB-2 code ran on market data.

**Why.** KWB-1 (slow-volatility extension) still produced no weekly BUY on BTC, ETH or SOL. Crypto
cycle lows follow long declines, so by the low price is no longer far below its 26-week average.

## Variants (`research/kenny_wbuy.py`)

* **D1(k):** an onset of dd_sigma ≥ k, where dd_sigma = −log(close / 104-week high) / (104-week
  stdev of weekly log returns × √52). That is the drawdown from the 2-year high in units of the
  asset's own annual volatility.
* **D2(k):** shipped BUY OR D1(k);
* k ∈ {1.0, 1.25, 1.5}, plus the shipped cooldown.

**Tuning, check and adoption.** Identical to `reports/KWB_CONFIG.md`, unchanged:
* tuning before 2018: right-rate ≥ shipped's − 0.03, excess ≥ shipped's − 0.02, ≥ 30 arrows,
  then the most frequent;
* check on 2018+ (previously studied): right-rate, excess and coverage tests as before, and
  crypto coverage > shipped's.

**Reported only:** BTC, ETH and SOL dates.

**Ledger trial:** `kwb2-1W` (hypothesis KWB-2).
