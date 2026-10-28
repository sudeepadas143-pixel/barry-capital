"""Binance public-archive data beyond spot hourly/daily bars.

* 15-minute spot bars (the lower timeframe for 1H charts)
* USD-M perpetual 1-hour bars (spot/perp basis)
* funding rates (8-hourly, some symbols later 4-hourly)
* open interest (5-minute "metrics" files, kept as hourly last value)

All from https://data.binance.vision (monthly zips; open interest only exists as daily
zips, from late 2021). Monthly archives lag by up to a month, so these series end a few
weeks before the spot data does. None of this exists for non-crypto symbols, and in
TradingView it is only reachable on symbols whose exchange publishes perp/OI tickers,
so every feature built on it is optional and degrades to "unavailable".
"""

from __future__ import annotations

import io
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import requests

from .data import COLS, DATA_DIR, _clean

BASE = "https://data.binance.vision/data"


def _get(url: str) -> bytes | None:
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except Exception:
            time.sleep(2 ** attempt)
    return None


def _csv(blob: bytes) -> pd.DataFrame:
    z = zipfile.ZipFile(io.BytesIO(blob))
    raw = z.read(z.namelist()[0]).decode()
    first = raw.split("\n", 1)[0]
    header = 0 if any(c.isalpha() for c in first.split(",")[0]) else None
    return pd.read_csv(io.StringIO(raw), header=header)


def _months(start: str, end: pd.Timestamp | None = None) -> list[str]:
    end = end or pd.Timestamp.now(tz="UTC")
    return [p.strftime("%Y-%m") for p in pd.period_range(start, end.tz_localize(None), freq="M")]


def _ms_index(x: pd.Series) -> pd.DatetimeIndex:
    x = x.astype("int64")
    unit = np.where(x > 10**14, "us", "ms")
    if (unit == "us").all():
        return pd.to_datetime(x, unit="us", utc=True)
    if (unit == "ms").all():
        return pd.to_datetime(x, unit="ms", utc=True)
    return pd.DatetimeIndex([pd.Timestamp(v, unit=u, tz="UTC") for v, u in zip(x, unit)])


def _klines(kind: str, symbol: str, interval: str, start: str) -> pd.DataFrame:
    urls = [f"{BASE}/{kind}/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{m}.zip" for m in _months(start)]
    with ThreadPoolExecutor(12) as ex:
        blobs = list(ex.map(_get, urls))
    frames = []
    for b in blobs:
        if b is None:
            continue
        df = _csv(b)
        df = df.iloc[:, :6]
        df.columns = ["t", "open", "high", "low", "close", "volume"]
        df.index = _ms_index(df["t"])
        frames.append(df[COLS])
    if not frames:
        return pd.DataFrame(columns=COLS)
    return _clean(pd.concat(frames))


def _cached(name: str, build) -> pd.DataFrame:
    path = DATA_DIR / f"{name}.csv.gz"
    if path.exists():
        df = pd.read_csv(path, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True, format="ISO8601")
        return df
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = build()
    df.to_csv(path, compression="gzip")
    return df


def spot_15m(symbol: str, start: str = "2017-08") -> pd.DataFrame:
    def build():
        df = _klines("spot", symbol, "15m", start)
        # Top up the weeks the monthly archive has not published yet from the REST mirror.
        rows, t0 = [], int((df.index[-1] + pd.Timedelta(minutes=15)).timestamp() * 1000) if len(df) else None
        while t0 is not None:
            r = requests.get("https://data-api.binance.vision/api/v3/klines",
                             params={"symbol": symbol, "interval": "15m", "startTime": t0, "limit": 1000}, timeout=30)
            batch = r.json() if r.ok else []
            if not batch:
                break
            rows += batch
            t0 = batch[-1][0] + 1
            if len(batch) < 1000:
                break
        if rows:
            top = pd.DataFrame([r[:6] for r in rows], columns=["t", *COLS])
            top.index = pd.to_datetime(top["t"], unit="ms", utc=True)
            df = _clean(pd.concat([df, top[COLS]]))
        return df[df.index + pd.Timedelta(minutes=15) <= pd.Timestamp.now(tz="UTC")]
    return _cached(f"{symbol}_15m", build)


def perp_1h(symbol: str, start: str = "2019-09") -> pd.DataFrame:
    return _cached(f"{symbol}_perp1h", lambda: _klines("futures/um", symbol, "1h", start))


def funding(symbol: str, start: str = "2019-09") -> pd.DataFrame:
    def build():
        urls = [f"{BASE}/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{m}.zip" for m in _months(start)]
        with ThreadPoolExecutor(12) as ex:
            blobs = list(ex.map(_get, urls))
        frames = []
        for b in blobs:
            if b is None:
                continue
            df = _csv(b)
            df.columns = [str(c) for c in df.columns]
            tcol = df.columns[0]
            rcol = df.columns[-1]
            out = pd.DataFrame({"rate": df[rcol].astype(float).to_numpy()}, index=_ms_index(df[tcol]))
            frames.append(out)
        if not frames:
            return pd.DataFrame(columns=["rate"])
        f = pd.concat(frames).sort_index()
        return f[~f.index.duplicated()]
    return _cached(f"{symbol}_funding", build)


def open_interest(symbol: str, start: str = "2021-12-01") -> pd.DataFrame:
    """Hourly open interest (contracts and USD), last 5-minute reading in each hour."""
    def build():
        days = pd.date_range(start, pd.Timestamp.now().normalize() - pd.Timedelta(days=2), freq="D")
        urls = [f"{BASE}/futures/um/daily/metrics/{symbol}/{symbol}-metrics-{d.date()}.zip" for d in days]
        with ThreadPoolExecutor(16) as ex:
            blobs = list(ex.map(_get, urls))
        frames = []
        for b in blobs:
            if b is None:
                continue
            df = _csv(b)
            idx = pd.to_datetime(df["create_time"], utc=True)
            frames.append(pd.DataFrame({"oi": df["sum_open_interest"].astype(float).to_numpy(),
                                        "oi_usd": df["sum_open_interest_value"].astype(float).to_numpy()},
                                       index=idx))
        if not frames:
            return pd.DataFrame(columns=["oi", "oi_usd"])
        oi = pd.concat(frames).sort_index()
        oi = oi[~oi.index.duplicated()]
        # The reading stamped hh:55 is the last one inside hour hh; label the hour by its
        # OPEN time like every other bar here, so it is used only from that bar's close on.
        return oi.resample("1h", label="left", closed="left").last().dropna()
    return _cached(f"{symbol}_oi", build)
