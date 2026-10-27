"""V5 guarded data access for EXPLORATION (reports/V5_DATA_AUDIT.md, V5_VALIDATION_PROTOCOL.md §2).

Every V5 exploratory loader goes through this module. It is stricter than hcmtf.data:

* only instruments in the exploration set (70 seen + 38 V4.1 holdout + BTC-USD audit) load;
  a V5 reserve instrument or an unknown symbol raises ReservedDataError;
* the cache is read, never extended: if a needed file is missing this raises instead of letting
  hcmtf.data / hcmtf.derivs download (they fetch on a cache miss);
* every frame is cut at FREEZE (research.v5_reserve.exploration_only) after loading, including
  higher-timeframe frames, so no post-freeze candle can reach an exploratory computation even if
  one is later added to the cache;
* the V4.1 Amendment 1 integrity rule (token swap / relisting: > 20x daily open jump) is applied,
  computed on exploration-window data only.

There is deliberately no confirmatory loader yet: reserved instruments and forward candles become
readable only through a loader added together with a family's G2 pre-registration.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hcmtf import data
from hcmtf.universe import AUDIT

from .universe41 import HOLDOUT, SEEN
from .v41 import JUMP
from .v5_reserve import FREEZE, V5_RESERVE, exploration_only

EXPLORATION = {a.symbol: a for a in SEEN + HOLDOUT + AUDIT}
RESERVED = {s for g in V5_RESERVE.values() for s in g}
NATIVE = {"1H": "1h", "4H": "1h", "1D": "1d", "1W": "1d", "1M": "1d", "3M": "1d"}


class ReservedDataError(RuntimeError):
    """Raised when exploratory code asks for reserved, unknown or uncached data."""


def check_symbol(symbol: str):
    if symbol in RESERVED:
        raise ReservedDataError(f"{symbol} is a V5 reserve instrument: not readable in exploration")
    if symbol not in EXPLORATION:
        raise ReservedDataError(f"{symbol} is not in the exploration set")
    return EXPLORATION[symbol]


def _require_cache(symbol: str, interval: str):
    p = data._cache_path(symbol, interval)
    if not p.exists():
        raise ReservedDataError(f"{p.name} is not cached; exploration never downloads")


def integrity_cut(symbol: str):
    """V4.1 Amendment 1 on exploration-window daily data; first day of a >20x open jump, or None."""
    _require_cache(symbol, "1d")
    d1 = exploration_only(data.load(symbol, "1D"))
    o = d1["open"].to_numpy(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        jump = np.abs(np.log(o[1:] / o[:-1])) > np.log(JUMP)
    k = np.flatnonzero(jump)
    return d1.index[k[0]] if len(k) else None


def load(symbol: str, tf: str) -> pd.DataFrame:
    """Exploration frame: registered symbol, cache only, cut at FREEZE and at an integrity jump."""
    check_symbol(symbol)
    _require_cache(symbol, NATIVE[tf])
    df = exploration_only(data.load(symbol, tf))
    cut = integrity_cut(symbol)
    if cut is not None:
        df = df[df.index < cut]
    assert df.index.max() <= FREEZE
    return df


def load_funding(symbol: str) -> pd.DataFrame | None:
    """Cached perp funding (rate per funding event) cut at FREEZE, or None if never cached."""
    check_symbol(symbol)
    p = data.DATA_DIR / f"{symbol}_funding.csv.gz"
    if not p.exists():
        return None
    f = pd.read_csv(p, index_col=0)
    f.index = pd.to_datetime(f.index, utc=True, format="ISO8601")
    return exploration_only(f[["rate"]].astype(float))
