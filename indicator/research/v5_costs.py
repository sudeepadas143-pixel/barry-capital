"""V5 trading costs, exactly as pre-registered in reports/V5_VALIDATION_PROTOCOL.md §4.

Round trip (unchanged since v3): hcmtf.universe.COST_BPS per class.

Holding costs, SHORT positions only (long positions are modelled as spot holdings: no holding
cost; this is stated, not measured):
* equities, index/sector/country ETFs, bond ETFs, commodity ETFs ("equity", "equity_index",
  "bond", "commodity"): general-collateral borrow 1.0% a year, accrued over CALENDAR time from the
  entry fill to the exit fill (actual/365.25). Hard-to-borrow fees are not modelled.
  source = "estimated_gc_borrow_1pct".
* crypto: the actual perp funding paid or received while short, where a cached funding series
  covers the whole holding period (source = "observed_funding"). Shorts RECEIVE funding when the
  rate is positive, so cost = -sum(rate) over funding timestamps in (entry, exit]. Otherwise a
  conservative 10% a year accrued as above (source = "estimated_crypto_10pct").
  "Covers" means: first funding print <= entry, last print >= exit - 9h, and no gap between
  consecutive prints within (entry - 9h, exit] longer than 2 days.
* FX: carry is not modelled: cost 0 with source = "unavailable_fx_carry" so it cannot be mistaken
  for an observed zero.

All costs are fractions of notional (0.01 = 1%). Every trade carries its source label, so
estimated and observed costs stay distinguishable in every report.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hcmtf.universe import COST_BPS

YEAR_SECONDS = 365.25 * 86400.0
BORROW_GC_ANNUAL = 0.01
CRYPTO_SHORT_FALLBACK_ANNUAL = 0.10
BORROW_CLASSES = ("equity", "equity_index", "bond", "commodity")
FUNDING_STALE = pd.Timedelta(days=2)
FUNDING_EDGE = pd.Timedelta(hours=9)


def round_trip(asset_cls: str) -> float:
    """Round-trip transaction cost as a fraction of notional."""
    return COST_BPS[asset_cls] / 1e4


def years_between(entry: pd.Timestamp, exit_: pd.Timestamp) -> float:
    if exit_ < entry:
        raise ValueError("exit before entry")
    return (exit_ - entry).total_seconds() / YEAR_SECONDS


def _funding_covers(f: pd.DataFrame, entry, exit_) -> bool:
    if f is None or len(f) == 0:
        return False
    idx = f.index
    if idx[0] > entry or idx[-1] < exit_ - FUNDING_EDGE:
        return False
    w = idx[(idx > entry - FUNDING_EDGE) & (idx <= exit_)]
    if len(w) == 0:
        return (exit_ - entry) < FUNDING_EDGE          # too short to span a print
    pts = w.insert(0, max(entry - FUNDING_EDGE, idx[0]))
    return bool((pd.Series(pts[1:] - pts[:-1]) <= FUNDING_STALE).all())


def short_holding_cost(asset_cls: str, entry: pd.Timestamp, exit_: pd.Timestamp,
                       funding: pd.DataFrame | None = None) -> tuple[float, str]:
    """(cost as a fraction of notional, source label) for a SHORT held from entry to exit."""
    yrs = years_between(entry, exit_)
    if asset_cls in BORROW_CLASSES:
        return BORROW_GC_ANNUAL * yrs, "estimated_gc_borrow_1pct"
    if asset_cls == "crypto":
        if _funding_covers(funding, entry, exit_):
            r = funding["rate"]
            paid = r[(r.index > entry) & (r.index <= exit_)].to_numpy(float)
            return float(-np.sum(paid)), "observed_funding"
        return CRYPTO_SHORT_FALLBACK_ANNUAL * yrs, "estimated_crypto_10pct"
    if asset_cls == "fx":
        return 0.0, "unavailable_fx_carry"
    raise ValueError(f"no cost rule for class {asset_cls!r}")


def holding_cost(side: int, asset_cls: str, entry, exit_, funding=None) -> tuple[float, str]:
    """Holding cost for either side; longs carry none (spot), shorts as above."""
    if side > 0:
        return 0.0, "none_long_spot"
    return short_holding_cost(asset_cls, entry, exit_, funding)
