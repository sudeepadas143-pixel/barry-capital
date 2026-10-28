"""v2 study plumbing: build contexts, run the engine over symbols and windows.

Three data roles, kept apart:

* DEV symbols (universe.UNIVERSE), before the holdout start: used to screen components
  and to make the design decisions in reports/DESIGN_CHECK.md. Everything learned comes
  from here. (v2 has no fitted thresholds left.)
* DEV symbols in the holdout window: seen once during v1, so reported but no longer
  "untouched". Labelled as such everywhere.
* FRESH symbols (universe.FRESH), all dates: never used for any design decision. This
  is the primary out-of-sample test for v2.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import data, derivs, engine as G, evaluate as E
from .universe import COST_BPS, FRESH, UNIVERSE, Asset

TS = pd.Timestamp
HOLDOUT = {"1H": "2025-07-01", "4H": "2025-07-01", "1D": "2024-01-01", "1W": "2024-01-01"}
WINDOWS = {
    "1D": [("2010-01-01", "2013-01-01"), ("2013-01-01", "2016-01-01"), ("2016-01-01", "2019-01-01"),
           ("2019-01-01", "2022-01-01"), ("2022-01-01", "2024-01-01")],
    "1W": [("2010-01-01", "2013-01-01"), ("2013-01-01", "2016-01-01"), ("2016-01-01", "2019-01-01"),
           ("2019-01-01", "2022-01-01"), ("2022-01-01", "2024-01-01")],
    "4H": [("2020-01-01", "2021-01-01"), ("2021-01-01", "2022-01-01"), ("2022-01-01", "2023-01-01"),
           ("2023-01-01", "2024-01-01"), ("2024-01-01", "2025-07-01")],
    "1H": [("2020-01-01", "2021-01-01"), ("2021-01-01", "2022-01-01"), ("2022-01-01", "2023-01-01"),
           ("2023-01-01", "2024-01-01"), ("2024-01-01", "2025-07-01")],
}
PURGE = {"1H": pd.Timedelta(days=2), "4H": pd.Timedelta(days=8), "1D": pd.Timedelta(days=35),
         "1W": pd.Timedelta(days=100)}
MAX_HOLD = {"1H": 72, "4H": 60, "1D": 60, "1W": 26}



def _ltf_frame(symbol: str, tf: str, asset: Asset):
    if tf == "15m":
        if asset.source != "binance" or not (data.DATA_DIR / f"{symbol}_15m.csv.gz").exists():
            return None
        m = derivs.spot_15m(symbol)
        # the archive has a few stray records off the 15-minute grid: drop them
        ok = (m.index.second == 0) & (m.index.minute % 15 == 0)
        return m[ok]
    return data.load(symbol, tf)


def build_ctx(asset: Asset, tf: str) -> G.Ctx | None:
    try:
        df = data.load(asset.symbol, tf)
    except Exception:
        return None
    if len(df) < 300:
        return None
    ltf_tf, h1, h2 = G.LADDER[tf]
    ctx = G.Ctx(df, data.load(asset.symbol, h1), data.load(asset.symbol, h2),
                _ltf_frame(asset.symbol, ltf_tf, asset),
                asset.volume, asset.cls == "crypto")  # instrument property, as in Pine (syminfo.type)
    if asset.cls == "crypto":
        # Perp data is optional context (screening kept no perp feature): use it when it is
        # already cached, never download it here.
        cached = lambda kind: (data.DATA_DIR / f"{asset.symbol}_{kind}.csv.gz").exists()
        try:
            ctx.funding = derivs.funding(asset.symbol) if cached("funding") else None
            ctx.perp = derivs.perp_1h(asset.symbol) if cached("perp1h") else None
            ctx.spot1h = data.load(asset.symbol, "1H") if ctx.perp is not None else None
            ctx.oi = derivs.open_interest(asset.symbol) if cached("oi") else None
        except Exception:
            pass
    return ctx


@dataclass
class Series:
    symbol: str
    cls: str
    tier_cls: str
    tf: str
    cost: float
    f: G.Feat
    trig: pd.DataFrame
    warn: pd.DataFrame
    table: dict
    base: dict = field(default_factory=dict)

    @property
    def index(self):
        return self.f.index


def prepare_one(args) -> Series | None:
    asset, tf = args
    ctx = build_ctx(asset, tf)
    if ctx is None:
        return None
    p = G.DEFAULTS[tf]
    f = G.features(ctx, p)
    t = G.breaks(f, p)
    if len(t) == 0:
        return None
    w = G.warnings(f)
    cost = COST_BPS[asset.cls]
    s = Series(asset.symbol, asset.cls, asset.tier or asset.cls, tf, cost, f, t, w,
               E.bar_outcomes(f, E.HORIZON[tf], cost))
    s.base = {"raw_breaks": t[t["warm"]][["i", "dir"]].reset_index(drop=True),
              "ema_cross": E.ema_cross(f), "supertrend": E.supertrend_flip(f)}
    return s


def prepare(tf: str, assets: list[Asset], workers: int = 8) -> list[Series]:
    with ProcessPoolExecutor(workers) as ex:
        out = list(ex.map(prepare_one, [(a, tf) for a in assets]))
    return [s for s in out if s is not None]


def signals_for(s: Series, p: G.Params) -> pd.DataFrame:
    return G.classify(G.score(s.trig, s.f, p), p)


def tag(s: Series, ev: pd.DataFrame) -> pd.DataFrame:
    ev = E.lookup(ev, s.table)
    ev["symbol"] = s.symbol
    ev["cls_asset"] = s.cls
    ev["tier_cls"] = s.tier_cls
    ev["time"] = s.index[ev["i"].to_numpy(int)]
    return ev


def in_window(s: Series, ev: pd.DataFrame, a, b) -> pd.DataFrame:
    t = s.index[ev["i"].to_numpy(int)]
    return ev[(t >= a) & (t < b)]
