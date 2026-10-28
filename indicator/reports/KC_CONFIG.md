# KC: cumulative signal clusters for Kenny's Divergence Indicator (exploratory)

**Status: FROZEN** (2026-10-28), before any KC code ran on market data.

**Scope.** A bounded check of a cluster-scoring layer against the current behaviour. There are no
new model families and no new benchmark.

**Data and guards.**
* Same as CY-2 and KB: guarded loader, the EVAL universe, no reserved instruments, no post-freeze
  candles.
* All data was examined before, so the results are **exploratory**.
* Kenny's scores and thresholds are the shipped CY-2 spec, which was fitted on these data, for
  every setting including the reference. Comparisons are therefore like-for-like, and absolute
  levels are in-sample.

## Settings compared (all else fixed, per `research/kenny_cluster.py`)

| id | layer | decay half-life | theta | redundancy control |
|---|---|---|---|---|
| S0 | current: BUY = High Conviction onsets, SELL = Confirmed, cooldown Q | – | – | – |
| S1 | cluster | L/8 candles | 1.5 | on |
| S2 | cluster | L/8 | 2.0 | on |
| S3 | cluster | L/4 | 1.5 | on |
| S4 | cluster | L/4 | 2.0 | on |
| S5 | cluster | L/8 | 1.5 | **off** (plain decayed sum) |

The theta grid was scaled on **synthetic** data only, so that cluster signal counts are of the
same order as S0. No market outcomes were seen.

**Evidence families** (`research/kenny_cluster.py`):
* **ext:** Kenny tier onsets — warning 0.4, standard 0.7, high 1.0;
* **cnf:** Kenny's Confirmed rule;
* **div:** RSI/MACD-histogram regular divergence;
* **pa:** price-action reversal;
* **vv:** volatility/volume burst with a reversal-side wick.

A candle can qualify only while Kenny's zone is active: score ≥ warning within the last c candles,
or within L/2 candles after a standard onset.

**Fixed layer parameters** (set before any run):
* weights: ext 1.0, cnf 0.75, div 1.0, pa 0.75, vv 0.75;
* opposite-evidence shrink κ = 0.5;
* HTF-context multiplier 1.2;
* minimum new evidence δ = 0.15.

L (and so the half-life) scales with the timeframe:

| TF | L candles | half-life L/8 | half-life L/4 |
|---|---|---|---|
| 1W | 26 | 3.25 | 6.5 |
| 1D | 63 | 7.9 | 15.8 |
| 4H | 126 | 15.8 | 31.5 |
| 1H | 168 | 21 | 42 |

## Metrics

Per TF × direction and setting:
* signals per asset-year;
* episodes (signals more than c candles apart);
* barrier win rate (+D/2 ATR before −D/4 ATR within L/2);
* MFE and MAE medians in ATR;
* net return at L/2 after `COST_BPS`: mean, median and per-instrument median;
* the same by early/late half (the CY-2 test-year midpoint).

## Decision rule

**Candidates.** S1–S4 are candidates; S5 is the no-redundancy control.

**Usability constraints.** A candidate qualifies only if, against S0:
* its signals per asset-year are ≤ 4× S0's in every cell;
* its median MAE is not worse by more than 10% in ≥ 6 of the 8 cells.

**Choice.** The qualifying candidate with the best mean rank across the 8 cells of win rate,
median net and per-instrument median net is chosen.

**Reporting.** The impact is reported as measured, whether better or worse than S0.

**Ledger trial:** `kc-all` (hypothesis KC-1).
