# KLB: better-placed BUY arrows on 4H and 1H (exploratory)

**Status: FROZEN** (2026-10-28), before any KLB code ran on market data.

**Why.** The user reports that 4H/1H BUYs are:
* too early (price keeps falling after the arrow);
* in the middle of nowhere;
* missing real lows.

The current shipped BUY there is H|0.8 (`reports/KBAL_CONFIG.md`).

## Candidates

Definitions are in `research/kenny_ltfbuy.py`. Each is tried at scale s ∈ {0.8, 1.0}; H also at 1.1.
* **H|s:** the current family.
* **LOC|s:** H|s plus the close in the lowest 25% of the trailing L range.
* **TRIG|s:** a Kenny warning setup, then a turn up from a fresh L-low within L/4 candles.
* **PIV|s:** a confirmed half-cycle swing low with Kenny's score at warning or above, drawn on the
  confirmation candle.

## Measures

All candidates are scored against all EVAL_SYMBOLS on 4H and 1H:
* KR right-rate and its zone / follow parts;
* KR coverage: the share of meaningful swing lows that have a right BUY within ±L/4 ("missing real
  lows");
* KF excess at L/2;
* invalidation: a new low below the signal candle within L/4 ("too early");
* median further drop in ATR within L/4;
* rate per instrument-year.

**Split.** Tuning before 2024, check from 2024 on. The check period has been studied before.

## Rule

**Choose on tuning data only.** Eligible candidates have:
* n ≥ 30;
* a rate ≥ 0.6 × the current H|0.8 rate (BUYs stay frequent);
* coverage ≥ the current coverage − 0.03;
* excess ≥ +0.02.

Among those, take the highest tuning right-rate.

**Adopt** the chosen candidate if, in the check period:
* its right-rate ≥ the current + 0.03;
* its coverage ≥ the current − 0.03;
* its excess ≥ +0.02.

Otherwise H|0.8 stays.

**Ledger trial:** `klb-all` (hypothesis KLB-1).
