"""Chronological walk-forward validation with a final untouched holdout.

For each chart timeframe the calendar is cut into consecutive TEST windows. For each
window the two tunable numbers (the score thresholds for CONFIRMED and MAJOR) are chosen
using only events that finished before the window starts (expanding training set, with a
purge gap so no training outcome overlaps the test window). The chosen thresholds are then
applied, unchanged, to the test window. Stitching the test windows together gives an
out-of-sample record in which no event was ever used to pick the parameters that scored it.

The last stretch of data (HOLDOUT) is not touched by any of that. Its thresholds are
picked once from everything before it, it is evaluated once, and those thresholds are
what the Pine script ships with.

Nothing else is tuned. Indicator lengths, pivot spans, cooldowns, the ATR barrier and the
horizons are fixed in code and were not changed after looking at test results.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import data, evaluate as E, signals as S
from .htf import CONTEXT
from .universe import COST_BPS, UNIVERSE, Asset

TS = pd.Timestamp

FOLDS = {
    # test windows [start, end), then holdout start. Daily/weekly have decades of
    # history for most assets; intraday has ~9 years for crypto and ~3 for the rest.
    "1D": dict(windows=[("2010-01-01", "2013-01-01"), ("2013-01-01", "2016-01-01"),
                        ("2016-01-01", "2019-01-01"), ("2019-01-01", "2022-01-01"),
                        ("2022-01-01", "2024-01-01")], holdout="2024-01-01",
               purge=pd.Timedelta(days=35)),
    "1W": dict(windows=[("2010-01-01", "2013-01-01"), ("2013-01-01", "2016-01-01"),
                        ("2016-01-01", "2019-01-01"), ("2019-01-01", "2022-01-01"),
                        ("2022-01-01", "2024-01-01")], holdout="2024-01-01",
               purge=pd.Timedelta(days=100)),
    "4H": dict(windows=[("2020-01-01", "2021-01-01"), ("2021-01-01", "2022-01-01"),
                        ("2022-01-01", "2023-01-01"), ("2023-01-01", "2024-01-01"),
                        ("2024-01-01", "2025-07-01")], holdout="2025-07-01",
               purge=pd.Timedelta(days=8)),
    "1H": dict(windows=[("2020-01-01", "2021-01-01"), ("2021-01-01", "2022-01-01"),
                        ("2022-01-01", "2023-01-01"), ("2023-01-01", "2024-01-01"),
                        ("2024-01-01", "2025-07-01")], holdout="2025-07-01",
               purge=pd.Timedelta(days=2)),
}
GRID_CONFIRM = [0.5, 0.6, 0.67, 0.8]
GRID_MAJOR = [0.8, 1.0]
MAX_HOLD = {"1H": 72, "4H": 60, "1D": 60, "1W": 26}
MIN_N_CONFIRM, MIN_N_MAJOR = 50, 20


@dataclass
class Series:
    symbol: str
    cls: str
    tf: str
    cost: float
    f: S.Features
    trig: pd.DataFrame
    warn: pd.DataFrame
    table: dict
    base: dict = field(default_factory=dict)

    @property
    def index(self) -> pd.DatetimeIndex:
        return self.f.index


def prepare_one(args) -> Series | None:
    asset, tf = args
    try:
        df = data.load(asset.symbol, tf)
        near_tf, anchor_tf = CONTEXT[tf]
        near = data.load(asset.symbol, near_tf)
        anchor = data.load(asset.symbol, anchor_tf)
    except Exception:
        return None
    if len(df) < 300:
        return None
    p = S.DEFAULTS[tf]
    vol_ok = asset.volume and data.has_volume(df)
    f, trig, _, warn = S.run(df, near, anchor, p, vol_ok)
    cost = COST_BPS[asset.cls]
    s = Series(asset.symbol, asset.cls, tf, cost, f, trig, warn, E.bar_outcomes(f, E.HORIZON[tf], cost))
    s.base = {
        "raw_breaks": E.raw_breaks(trig),
        "ema_cross": E.ema_cross(f),
        "supertrend": E.supertrend_flip(f),
    }
    return s


def prepare(tf: str, assets: list[Asset] = UNIVERSE, workers: int = 8) -> list[Series]:
    with ProcessPoolExecutor(workers) as ex:
        out = list(ex.map(prepare_one, [(a, tf) for a in assets]))
    return [s for s in out if s is not None]


# --------------------------------------------------------------------------- helpers


def in_window(s: Series, ev: pd.DataFrame, start, end) -> pd.DataFrame:
    t = s.index[ev["i"].to_numpy(int)]
    m = (t >= start) & (t < end)
    return ev[m]


def tag(s: Series, ev: pd.DataFrame) -> pd.DataFrame:
    ev = E.lookup(ev, s.table)
    ev["symbol"] = s.symbol
    ev["cls"] = s.cls
    ev["time"] = s.index[ev["i"].to_numpy(int)]
    return ev


def signals_for(s: Series, confirm: float, major: float) -> pd.DataFrame:
    return S.classify(s.trig, S.with_thresholds(S.DEFAULTS[s.tf], confirm, major))


def _tstat(x: np.ndarray) -> float:
    x = x[~np.isnan(x)]
    if len(x) < 2 or x.std(ddof=1) == 0:
        return -np.inf
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def select(series: list[Series], train_end) -> tuple[float, float, dict]:
    """Pick (confirm, major) using events whose whole outcome window ended before train_end.

    confirm: maximise the t-statistic of mean r_h over all signals (n >= 50).
    major:   given confirm, maximise the t-statistic over MAJOR signals (n >= 20).
             MAJOR must be strictly stricter than CONFIRMED, or the tiers would merge.
    Ties go to the stricter threshold. Falls back to the timeframe default when no
    candidate has enough events.
    """
    tf = series[0].tf
    p0 = S.DEFAULTS[tf]
    best_c, best_tc, log = p0.confirm, -np.inf, {}
    cache = {}
    for c in GRID_CONFIRM:
        for m in GRID_MAJOR:
            if m <= c:
                continue
            evs = []
            for s in series:
                ev = signals_for(s, c, m)
                ev = ev[s.index[ev["i"].to_numpy(int)] < train_end]
                evs.append(E.lookup(ev, s.table))
            cache[(c, m)] = pd.concat(evs) if evs else pd.DataFrame()
    for c in GRID_CONFIRM:
        ev = cache.get((c, GRID_MAJOR[-1]))
        if ev is None or len(ev) < MIN_N_CONFIRM:
            continue
        t = _tstat(ev["r_h"].to_numpy())
        log[f"confirm={c}"] = (len(ev), round(float(t), 2))
        if t >= best_tc:
            best_c, best_tc = c, t
    best_m, best_tm = max(p0.major, min(g for g in GRID_MAJOR if g > best_c)), -np.inf
    for m in GRID_MAJOR:
        if m <= best_c:
            continue
        ev = cache[(best_c, m)]
        ev = ev[ev["tier"] == "major"]
        if len(ev) < MIN_N_MAJOR:
            continue
        t = _tstat(ev["r_h"].to_numpy())
        log[f"major={m}"] = (len(ev), round(float(t), 2))
        if t >= best_tm:
            best_m, best_tm = m, t
    return best_c, best_m, log


# ----------------------------------------------------------------------------- run


@dataclass
class Result:
    tf: str
    folds: list            # (start, end, confirm, major, selection log)
    holdout: tuple         # (start, confirm, major, selection log)
    oos: dict              # name -> events in walk-forward test windows
    hold: dict             # name -> events in the holdout
    trig_oos: pd.DataFrame # every trigger in test windows (score-monotonicity check)
    series: list
    windows_oos: list
    window_hold: tuple
    sig_by_series_oos: dict
    sig_by_series_hold: dict


def run(tf: str, series: list[Series] | None = None) -> Result:
    series = series or prepare(tf)
    cfg = FOLDS[tf]
    end_all = max(s.index[-1] for s in series) + pd.Timedelta(days=1)
    windows = [(TS(a, tz="UTC"), TS(b, tz="UTC")) for a, b in cfg["windows"]]
    hstart = TS(cfg["holdout"], tz="UTC")
    folds = []
    oos: dict[str, list] = {}
    sig_oos: dict[str, list] = {s.symbol: [] for s in series}
    trig_oos = []

    def collect(store, s, start, end, sig):
        sig = in_window(s, sig, start, end)
        store.setdefault("signals", []).append(tag(s, sig))
        store.setdefault("warnings", []).append(tag(s, in_window(s, s.warn, start, end)))
        for k, b in s.base.items():
            store.setdefault(k, []).append(tag(s, in_window(s, b, start, end)))
        return sig

    for start, end in windows:
        c, m, log = select(series, start - cfg["purge"])
        folds.append((start, end, c, m, log))
        for s in series:
            sig = collect(oos, s, start, end, signals_for(s, c, m))
            sig_oos[s.symbol].append(sig)
            tr = in_window(s, s.trig[s.trig["warm"]], start, end)
            trig_oos.append(tag(s, tr))

    c, m, log = select(series, hstart - cfg["purge"])
    hold: dict[str, list] = {}
    sig_hold = {}
    for s in series:
        sig_hold[s.symbol] = collect(hold, s, hstart, end_all, signals_for(s, c, m))

    cat = lambda d: {k: pd.concat(v, ignore_index=True) for k, v in d.items()}
    return Result(tf, folds, (hstart, c, m, log), cat(oos), cat(hold),
                  pd.concat(trig_oos, ignore_index=True), series, windows, (hstart, end_all),
                  {k: pd.concat(v) for k, v in sig_oos.items()}, sig_hold)
