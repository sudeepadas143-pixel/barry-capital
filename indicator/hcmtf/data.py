"""Download, cache and resample OHLCV bars.

Every frame returned here is indexed by the bar's OPEN time in UTC and has the columns
open, high, low, close, volume. Bars are only ever built from bars that are complete,
so a 4H bar never contains an hour that had not closed yet.

Sources: Yahoo Finance (via yfinance) for stocks, ETFs and FX, and Binance's public
market-data mirror for crypto. Yahoo serves hourly bars for the last ~730 days only,
which limits the 1H/4H sample for non-crypto assets; the report states the spans used.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .universe import BY_SYMBOL, Asset

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
COLS = ["open", "high", "low", "close", "volume"]
BINANCE = "https://data-api.binance.vision/api/v3/klines"
BINANCE_START = pd.Timestamp("2017-08-01", tz="UTC")


def _cache_path(symbol: str, kind: str) -> Path:
    safe = symbol.replace("=", "_").replace("^", "_")
    return DATA_DIR / f"{safe}_{kind}.csv.gz"


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    return df[COLS].astype(float)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df[COLS].astype(float)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df.dropna(subset=["open", "high", "low", "close"])
    # Yahoo occasionally returns a bar whose high/low do not bracket open/close.
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    df["volume"] = df["volume"].fillna(0.0)
    return df


# --------------------------------------------------------------------------- yahoo


def _yahoo(symbol: str, interval: str) -> pd.DataFrame:
    import yfinance as yf

    period = "730d" if interval == "1h" else "max"
    for attempt in range(5):
        try:
            raw = yf.download(symbol, period=period, interval=interval, progress=False,
                              auto_adjust=True, threads=False)
            if len(raw):
                break
        except Exception:  # network hiccup or rate limit
            pass
        time.sleep(2 ** (attempt + 1))
    else:
        raise RuntimeError(f"yahoo returned nothing for {symbol} {interval}")
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw = raw.rename(columns=str.lower)
    idx = raw.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    raw.index = idx.tz_convert("UTC")
    return _clean(raw)


# ------------------------------------------------------------------------- binance


def _binance(symbol: str, interval: str) -> pd.DataFrame:
    import requests

    rows: list[list] = []
    start = int(BINANCE_START.timestamp() * 1000)
    while True:
        for attempt in range(5):
            try:
                r = requests.get(BINANCE, params={"symbol": symbol, "interval": interval,
                                                  "startTime": start, "limit": 1000}, timeout=30)
                r.raise_for_status()
                batch = r.json()
                break
            except Exception:
                time.sleep(2 ** (attempt + 1))
        else:
            raise RuntimeError(f"binance failed for {symbol} {interval}")
        if not batch:
            break
        rows.extend(batch)
        start = batch[-1][0] + 1
        if len(batch) < 1000:
            break
    df = pd.DataFrame(rows, columns=["t", "open", "high", "low", "close", "volume", "ct",
                                     "qv", "n", "tb", "tq", "ig"])
    df.index = pd.to_datetime(df["t"], unit="ms", utc=True)
    df = _clean(df)
    # Drop the bar that is still forming: its close time is in the future.
    step = {"1h": pd.Timedelta(hours=1), "1d": pd.Timedelta(days=1)}[interval]
    return df[df.index + step <= pd.Timestamp.now(tz="UTC")]


# --------------------------------------------------------------------------- public


def load_native(symbol: str, interval: str, refresh: bool = False) -> pd.DataFrame:
    """Native bars: interval is "1h" or "1d"."""
    path = _cache_path(symbol, interval)
    if path.exists() and not refresh:
        return _drop_forming(_read(path), interval)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = BY_SYMBOL[symbol]
    df = _binance(symbol, interval) if asset.source == "binance" else _yahoo(symbol, interval)
    df.to_csv(path, compression="gzip")
    return _drop_forming(df, interval)


def _drop_forming(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    """Drop the newest bar: it may have been live (still forming) at download time.

    Yahoo returns the current day's and hour's bar before they close. Dropping the last
    bar of every series costs one bar and removes the question entirely.
    """
    return df.iloc[:-1]


def _resample(df: pd.DataFrame, rule: str, **kw) -> pd.DataFrame:
    g = df.resample(rule, **kw)
    out = pd.DataFrame({
        "open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
        "close": g["close"].last(), "volume": g["volume"].sum(),
        "n": g["close"].count(),
    })
    return out[out["n"] > 0].drop(columns="n")


def to_4h(h1: pd.DataFrame, asset: Asset) -> pd.DataFrame:
    """4H bars from 1H bars, anchored like TradingView.

    24h markets: UTC 00/04/08/... buckets. Exchange-hours markets: buckets of four hourly
    bars counted from each session's first bar (09:30-13:30 and 13:30-16:00 for US equities).
    """
    if asset.session == "24h":
        out = _resample(h1, "4h", label="left", closed="left")
        # A trailing bucket with fewer hours than expected is a forming bar: drop it.
        last = h1.index[-1]
        if last.floor("4h") == out.index[-1] and (last + pd.Timedelta(hours=1)) < out.index[-1] + pd.Timedelta(hours=4):
            out = out.iloc[:-1]
        return out
    local = h1.index.tz_convert("America/New_York")
    day = local.normalize()
    pos = pd.Series(1, index=h1.index).groupby(day).cumsum().values - 1
    key = pd.Series(day.astype("int64") // 10**9 * 10 + pos // 4, index=h1.index)
    g = h1.groupby(key.values)
    out = pd.DataFrame({
        "open": g["open"].first().values, "high": g["high"].max().values,
        "low": g["low"].min().values, "close": g["close"].last().values,
        "volume": g["volume"].sum().values,
    }, index=pd.DatetimeIndex(h1.index.to_series().groupby(key.values).first().values))
    out.index = out.index.tz_convert("UTC") if out.index.tz else out.index.tz_localize("UTC")
    return out


def to_weekly(d1: pd.DataFrame) -> pd.DataFrame:
    """Weeks starting Monday, labelled by the Monday (TradingView convention)."""
    out = _resample(d1, "W-MON", label="left", closed="left")
    return out


def to_monthly(d1: pd.DataFrame) -> pd.DataFrame:
    return _resample(d1, "MS")


def load(symbol: str, tf: str) -> pd.DataFrame:
    """Bars for one of 1H, 4H, 1D, 1W, 1M, 3M, with forming bars removed."""
    asset = BY_SYMBOL[symbol]
    if tf == "1H":
        return load_native(symbol, "1h")
    if tf == "4H":
        return to_4h(load_native(symbol, "1h"), asset)
    d1 = load_native(symbol, "1d")
    if asset.source == "yahoo":
        # Yahoo daily bars are stamped at local midnight; normalise to the UTC date.
        d1 = d1.copy()
        d1.index = d1.index.normalize()
    if tf == "1D":
        return d1
    # A week/month/quarter counts as closed only if the data runs to its last day.
    # (Weekends: a week whose Friday is in the data is complete for exchange assets.)
    end = d1.index[-1] + pd.Timedelta(days=1)
    if asset.session == "rth":
        end = end + pd.Timedelta(days=2) if d1.index[-1].dayofweek == 4 else end
    if tf == "1W":
        w = to_weekly(d1)
        return w[w.index + pd.Timedelta(days=7) <= end]
    if tf == "1M":
        m = to_monthly(d1)
        return m[m.index + pd.offsets.MonthBegin(1) <= end]
    if tf == "3M":
        q = _resample(d1, "QS")
        return q[q.index + pd.offsets.QuarterBegin(1, startingMonth=1) <= end]
    raise ValueError(tf)


def manifest() -> dict:
    """SHA-256 and span of every cached file, so a run can be tied to its exact data."""
    out = {}
    for p in sorted(DATA_DIR.glob("*.csv.gz")):
        df = _read(p)
        out[p.name] = {
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "rows": len(df), "first": str(df.index[0]), "last": str(df.index[-1]),
        }
    return out


def write_manifest(path: Path) -> None:
    path.write_text(json.dumps(manifest(), indent=1))


def has_volume(df: pd.DataFrame) -> bool:
    v = df["volume"].to_numpy()
    return bool(np.mean(v > 0) > 0.9)
