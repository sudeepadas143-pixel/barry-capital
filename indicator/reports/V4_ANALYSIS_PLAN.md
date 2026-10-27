# V4 Phase 1: diagnostic analysis plan (written and committed before any V4 number was computed)

Status of the data: every symbol and date used here was already examined in v1–v3. V3_RESULTS.md
and V3_SUMMARY.md were known when this plan was written. Everything below is therefore
**diagnostic, not confirmatory**: it can explain why the engine fails and decide which hypotheses
deserve a fresh test, but it cannot demonstrate an edge. No production file is changed.

## Events

Every warm MTF structure break from `hcmtf.engine.breaks` with the shipped parameters
(`engine.DEFAULTS`, `reports/active_config.json`: no evidence gates, no filters), on the 70 v3
symbols (`universe.UNIVERSE + universe.FRESH`), from the v3 start (1H/4H 2020-01-01, 1D/1W
2010-01-01; Yahoo intraday only exists from 2023-11-28) to the end of the cached data.
Groups: crypto; equities (stocks + index ETFs); commodities; rates & FX. Sides: bullish and bearish
always separately. Classes (from the engine's own `cls`, plus one split it leaves implicit):

| class | engine meaning | user's taxonomy |
|---|---|---|
| continuation | break with MTF structure, HTFs with it (= CONFIRMED) | continuation |
| realignment | MTF change of character back into the HTF direction (= MAJOR) | MTF reversal, HTF continuation (pullback end) |
| counter_reversal | MTF change of character against the HTFs (WATCH) | early reversal |
| counter_continuation | break with MTF structure, against the HTFs | continuation against the HTFs |
| neutral | HTFs flat (neither with nor against) | — |

## Outcomes (unchanged from v3)

Entry at the next open; r_h = direction-adjusted move to the close of candle H in ATR(14) at the
signal, after the v3 round-trip costs. Primary H: 1H 24, 4H 30, 1D 20, 1W 13. Secondary
horizons, reported but not used for decisions: short H/4 (6, 8, 5, 3) and long 2H.
Also: median, 5% trimmed mean, mean without the top 1% of events, share of the cell's total
r_h from its top 5% of events, MFE/MAE, triple-barrier (+2/−1 ATR) hit rate.

## Controls (per event, same symbol, same direction, same cost table)

* **R0 unconditional**: mean r_h over every eligible candle of the symbol in the window (what the
  v3 random baseline estimates).
* **R1 local-time matched**: mean r_h over candles within ±2H of the event. Removes drift and
  regime; leaves timing.
* **R2 HTF-state matched**: mean r_h over candles of the same calendar year whose HTF relation
  for that direction (with / against / neutral) equals the event's. Asks whether the break adds
  anything beyond being in that HTF state.
* **R3 volatility matched**: same calendar year and same ATR%-percentile tercile.

Excess = r_h − control. Inference: mean excess with a 95% month-cluster bootstrap (calendar
months pooled across symbols; 1W also with quarter clusters because its horizon spans ~3 months),
plus the median excess.

## Pre-declared reading rules

* A cell **shows information** only if mean excess vs R1 and vs R2 both have 95% CI lower bound
  > 0, the median excess vs R1 is > 0, and the mean excess vs R1 stays > 0 without the top 1% of
  events.
* A cell is **adequately sampled** if it has ≥ 100 events in ≥ 24 distinct months; otherwise it is
  reported as insufficient and not interpreted.
* Minimum detectable effect (80% power, two-sided 5%) ≈ 1.43 × the CI half-width; a null result is
  only "no effect" down to that size.
* **Decision rule.** If raw structure breaks (all classes) show information vs R1 and R2 in no
  TF × side for at least two asset groups, and the MAJOR class shows none either, the
  structure-break hypothesis is judged to have no measurable predictive value after controls →
  **REPLACE HYPOTHESIS**. If some adequately sampled cells show information but it would not
  survive correction for the number of cells read here → **RESEARCH FURTHER** with those cells
  as pre-registered targets on new data. **GO** requires information that survives correction
  in adequately sampled cells and is consistent across groups, which this already-seen data
  cannot establish on its own.

## Other measurements

* **Detection and lag**: ex-post zigzag legs (reversal ≥ 4 ATR, `evaluate.zigzag`, future data,
  used only for scoring) as eligible moves; share detected by a same-direction break / MAJOR
  signal inside the leg; bars from the extreme to the first signal; share of the leg left; entry
  distance from the leg extreme in ATR.
* **Visually convincing**: share of events with MFE ≥ 2 ATR within H ("looks right on a chart")
  vs the same share for R1-local random candles; share of those that still end with r_h ≤ 0.
* **Research audit**: V3-style iid random p-value vs the cluster-bootstrap CI of the excess for the
  same cells; overlap of outcome windows (effective sample size); HTF state durations and the
  share of candles where a with-HTF bearish signal is even possible; how often the Pine strategy
  twin would receive a same-direction signal while a trade is open (a code path that differs from
  `evaluate.simulate`).
