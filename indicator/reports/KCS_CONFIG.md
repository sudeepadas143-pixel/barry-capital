# KCS: Close Short, and BUY + Close Short confluence (exploratory)

**Status: FROZEN** (2026-10-28), before any KCS code ran on market data. The user asked for a Close
Short marker and for BUY + Close Short confluence to carry more weight.

## Definitions (`research/kenny_closeshort.py`)

These are our own transparent rules; TBO's code is not public.
* **Close Short (CS):** in a downtrend (EMA20 < EMA50), the first close back above EMA20 after ≥ 5
  consecutive closes below it.
* **Confluence (BUY+CS):** a CS within Q = L/4 candles after a shipped (Optimized-profile) BUY
  arrow. It is placed on the CS candle.

## Measures

* **Excess:** the KF rule, price higher L/2 candles later minus the instrument's base rate.
* **Right:** the KR rule, near the low and higher L/4 later.
* **Invalidation:** a new low below the signal candle within L/4.

**Split.** As in KR: tuning before 2018 (1W, 1D) or before 2024 (4H, 1H). The check period has
been studied before. The user accepts frequent invalidations.

## Adoption (per timeframe)

**CS marker shown** if, in **both** periods:
* excess ≥ +0.03;
* n ≥ 30.

**Confluence emphasis** (BUY drawn as confirmed) if, in **both** periods:
* its excess is ≥ all BUYs' excess + 0.03;
* its right-rate is ≥ all BUYs' right-rate − 0.05;
* n ≥ 20.

**Ledger trial:** `kcs-all` (hypothesis KCS-1).
