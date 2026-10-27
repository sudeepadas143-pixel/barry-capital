"""V5 data roles (reports/V5_DATA_AUDIT.md, reports/V5_VALIDATION_PROTOCOL.md).

* EXPLORATION: every cached candle of the 109 previously examined instruments (70 seen, 38
  V4.1 holdout, BTC-USD audit) that OPENS at or before FREEZE. Already examined; never to be
  called untouched or independent.
* FORWARD: every candle opening after FREEZE, on any instrument. Reserved for confirmatory runs
  registered in advance. Shared with the frozen V4.1 H6/H7v forward test
  (reports/V4_1_PREREGISTRATION.md §9); V5 must not change that test or look at its outcomes.
* V5_RESERVE: instruments never downloaded, loaded or referenced before 2026-10-27, checked
  over the whole git history. Not to be fetched until a V5 confirmatory run is registered. Same
  calendar period as the exploration data, so they add cross-sectional (not temporal)
  independence.

Nothing here downloads anything.
"""

from __future__ import annotations

import pandas as pd

FREEZE = pd.Timestamp("2026-10-27 23:59:59", tz="UTC")

V5_RESERVE = {
    "crypto": ["FETUSDT", "INJUSDT", "RUNEUSDT", "ARUSDT", "GRTUSDT", "SANDUSDT", "MANAUSDT", "CRVUSDT",
               "KAVAUSDT", "IOTAUSDT", "DASHUSDT", "ONEUSDT"],
    "equities": ["JNJ", "LIN", "NEE", "AMT", "HON", "COST", "GS", "IBM", "WBA", "GE", "KHC", "CL",
                 "XLV", "XLI", "XLP", "XLY", "XLB", "EWA", "EWC", "EWW"],
    "commodities": ["DBC", "GSG", "BNO", "UGA", "SOYB", "CANE"],
    "rates_fx": ["IEI", "BND", "MBB", "AGG", "USDPLN=X", "USDHUF=X", "USDCZK=X", "USDTRY=X"],
}

# Frozen V4.1 forward-test files: V5 work must leave these byte-identical.
FROZEN_V41 = ["research/v41.py", "research/universe41.py", "scripts/v41_run.py", "scripts/v41_fetch.py",
              "reports/V4_1_PREREGISTRATION.md"]


def exploration_only(df: pd.DataFrame) -> pd.DataFrame:
    """Drop every candle that opens after FREEZE. Exploratory V5 code must call this on every frame."""
    return df[df.index <= FREEZE]
