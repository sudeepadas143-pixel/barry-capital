"""KX: outside-the-chart context for crypto and equity cycle turns (reports/KX_CONFIG.md).

Daily context series, each value at day d uses information available at d's close only:
  funding  (9 Binance perps, 2020+)  f7 = mean funding over the last 7 days; pf = its percentile over
                                     the previous 365 days
  open interest (2021-12+)           oi14 = OI(d) / OI(d - 14d) - 1, with price change p14
  alt breadth (crypto EVAL coins)    br = share of coins closing above their 200-day SMA
  VIX (Cboe, 1990+)                  spike-and-reversal: 10-day max >= max(30, 1-year 90th pct) and
                                     VIX <= 0.8 x that max
Loaders reuse the project guards: registered symbols only, cut at FREEZE.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from hcmtf import data as HD

from . import v5_data as DG
from .v5_reserve import FREEZE

ROOT = Path(__file__).resolve().parent.parent
VIX_FILE = ROOT / "data_ext" / "VIX_History.csv"
PERPS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "LINKUSDT", "LTCUSDT")


def load_oi(symbol: str) -> pd.DataFrame | None:
    DG.check_symbol(symbol)
    p = HD.DATA_DIR / f"{symbol}_oi.csv.gz"
    if not p.exists():
        return None
    f = pd.read_csv(p, index_col=0)
    f.index = pd.to_datetime(f.index, utc=True, format="ISO8601")
    return f[f.index <= FREEZE][["oi_usd"]].astype(float)


def load_vix() -> pd.Series:
    v = pd.read_csv(VIX_FILE, parse_dates=["DATE"])
    s = pd.Series(v["CLOSE"].to_numpy(float), index=pd.DatetimeIndex(v["DATE"]).tz_localize("UTC"))
    return s[s.index <= FREEZE]


def _asof(series: pd.Series, index: pd.DatetimeIndex, close_offset: pd.Timedelta) -> np.ndarray:
    """Value of `series` known at each candle's close (index = candle open; close = open + offset)."""
    s = series.dropna().sort_index()
    pos = s.index.searchsorted(index + close_offset, side="right") - 1
    out = np.full(len(index), np.nan)
    ok = pos >= 0
    out[ok] = s.to_numpy()[pos[ok]]
    return out


def crypto_context(sym: str, df: pd.DataFrame, breadth: pd.Series) -> dict:
    """Daily context aligned to df (1D candles of a perp-covered coin)."""
    day = pd.Timedelta(days=1)
    c = df["close"].to_numpy(float)
    out = {}
    f = DG.load_funding(sym)
    if f is not None:
        f7 = f["rate"].rolling("7D").mean()
        f7d = pd.Series(_asof(f7, df.index, day), index=df.index)
        out["f7"] = f7d.to_numpy()
        out["pf"] = f7d.rolling(365, min_periods=180).apply(lambda x: (x[:-1] <= x[-1]).mean() if np.isfinite(x[-1]) else np.nan, raw=True).to_numpy()
    else:
        out["f7"] = out["pf"] = np.full(len(c), np.nan)
    oi = load_oi(sym)
    if oi is not None:
        o = pd.Series(_asof(oi["oi_usd"], df.index, day), index=df.index)
        out["oi14"] = (o / o.shift(14) - 1).to_numpy()
    else:
        out["oi14"] = np.full(len(c), np.nan)
    out["p14"] = c / np.r_[np.full(14, np.nan), c[:-14]] - 1
    out["br"] = _asof(breadth, df.index, day)
    out["br20"] = np.r_[np.full(20, np.nan), out["br"][:-20]]
    return out


def alt_breadth(frames: dict[str, pd.DataFrame]) -> pd.Series:
    """Share of coins closing above their 200-day SMA, indexed by close time."""
    cols = {}
    for s, d in frames.items():
        sma = d["close"].rolling(200, min_periods=200).mean()
        above = (d["close"] > sma).astype(float).where(sma.notna())
        above.index = d.index + pd.Timedelta(days=1)
        cols[s] = above
    m = pd.DataFrame(cols)
    n = m.notna().sum(axis=1)
    return (m.sum(axis=1) / n).where(n >= 5)


def top_context(cx: dict) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        crowded = np.nan_to_num(cx["pf"]) >= 0.9
        build = (np.nan_to_num(cx["oi14"]) >= 0.15) & (np.nan_to_num(cx["p14"], nan=1) <= 0.05)
        narrowing = np.nan_to_num(cx["br20"] - cx["br"]) >= 0.10
    return crowded | build | narrowing


def bottom_context(cx: dict) -> dict:
    with np.errstate(invalid="ignore"):
        neg = (np.nan_to_num(cx["f7"], nan=1) < 0) | (np.nan_to_num(cx["pf"], nan=1) <= 0.1)
        flush = (np.nan_to_num(cx["oi14"]) <= -0.15) & (np.nan_to_num(cx["p14"]) <= -0.10)
        washed = np.nan_to_num(cx["br"], nan=1) <= 0.2
    n = len(neg)
    flush14 = np.convolve(flush.astype(float), np.ones(14), "full")[:n] > 0
    return {"neg": neg, "flush14": flush14, "washed": washed, "any": neg | flush14 | washed, "all": neg & flush14 & washed,
            "two": (neg.astype(int) + flush14.astype(int) + washed.astype(int)) >= 2}


def vix_reversal(index: pd.DatetimeIndex, close_offset: pd.Timedelta) -> np.ndarray:
    """VIX spike-and-reversal active in the last 10 trading days, as known at each candle close."""
    v = load_vix()
    mx10 = v.rolling(10).max()
    p90 = v.rolling(252, min_periods=200).quantile(0.9)
    flag = (mx10 >= np.maximum(30.0, p90)) & (v <= 0.8 * mx10)
    act = flag.astype(float).rolling(10, min_periods=1).max()
    act.index = act.index + pd.Timedelta(hours=21)                  # VIX close ~16:00 ET
    return np.nan_to_num(_asof(act, index, close_offset)) > 0
