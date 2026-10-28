# KF: balance arrow frequency against accuracy (exploratory)

**Status: FROZEN** (2026-10-28), before any KF code ran on market data.

**User's choices:**
* An arrow "works out" if price is higher (BUY) or lower (SELL, breakdown) **half a cycle later**:
  H = L/2 candles (13 weeks on 1W, about 3 months on 1D, about 10 days on 4H, about 3.5 days on 1H).
* Frequency matters. Pick the **most frequent setting that still beats a random entry by ≥ 5
  points**.

## Excess and options

**Excess** of an arrow = its 0/1 outcome − the instrument's own base rate in the same period (the
share of all candles that were higher or lower H candles later).

**Options** (`research/kenny_freq.py`), per timeframe × side:
* Kenny states: warning, standard, high, confirmed;
* thresholds scaled by {0.7, 0.8, 0.9, 1.0, 1.1};
* the shipped same-side cooldown;
* weekly SELL also: Candidate A.

**Breakdown ✕ variants** (4H and below), scored with the SELL outcome:
* current;
* re-armed after L/4;
* SMA_L instead of SMA_1.5L;
* both changes.

**Split.** As in KR: tuning before 2018 (1W, 1D) or before 2024 (4H, 1H). The check period has
been studied before.

## Selection (per timeframe × side, and for ✕)

**Tuning period.** Eligible = ≥ 30 arrows and mean excess ≥ +0.05. Choose the eligible option
with the **most arrows per instrument-year**.

**Check period.** Adopt it if ≥ 30 arrows and mean excess ≥ +0.03. Otherwise keep the current
choice.

**Reported per cell:** arrows per year, mean excess, hit rate, base rate, median return at H, and
equities vs crypto. The current choices are included for comparison.

**Ledger trial:** `kf-all` (hypothesis KF-1).
