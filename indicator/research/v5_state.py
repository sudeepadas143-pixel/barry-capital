"""V5 shared market-state classifier (reports/V5_DEVELOPMENT_PLAN.md §4, register E1).

A research feature and benchmark stratum, NOT a predictor: nothing here claims that any state
forecasts returns. Output is one row per chart candle, decided at that candle's CLOSE.

Inputs: the chart frame (MTF) and two higher-timeframe frames (HTF1, HTF2 from engine.LADDER),
all indexed by candle OPEN time (UTC), as hcmtf.data returns them.

Timing and alignment rules
* Chart values at candle i use chart candles 0..i only (EMA/RMA/ATR/ADX are recursive; the
  volatility percentile compares with the PREVIOUS 200 values, as Pine ta.percentrank).
* HTF values use hcmtf.htf.align: the value of the HTF candle BEFORE the one containing the
  chart candle's open, i.e. the last HTF candle that was complete when the chart candle opened.
  This is Pine's request.security(..., f()[1], lookahead=barmerge.lookahead_on). It lags by one
  HTF candle on the chart candle that closes together with an HTF candle (conservative, and
  identical on history and realtime). A forming HTF candle is never read.
* No centred windows, no backward fills, no future values anywhere.

State definitions (fixed a priori, not tuned; the cut points are conventional values)
* direction: the HTF bias exactly as engine.breaks / V4.1 H6: +1 if with(+1) (HTF1+HTF2 >= 1 and
  neither HTF down), -1 if with(-1), 0 otherwise. HTF trend = close vs EMA21 with agreeing slope
  on the HTF candle (hcmtf.htf.trend_state). A missing HTF2 (warm-up) counts as 0, as in the engine.
* strength: chart ADX(14): weak < 20 <= moderate < 30 <= strong. Independent of direction.
* vol_regime: percentile of chart ATR%(14) = ATR/close against its previous 200 values:
  low < 33.3 <= mid < 66.7 <= high. Independent of direction and strength.
* extension_atr: (chart close - EMA21 of the last completed HTF1 candle) / chart ATR14, where the
  HTF1 closes are taken FROM THE CHART FEED (the last chart close inside each HTF1 period). Mixing
  feeds biased this on dividend-adjusted daily vs hourly Yahoo data (audit finding A2);
  ext_bucket: <= -3 "far_below", (-3,-1] "below", (-1,1) "near", [1,3) "above", >= 3 "far_above".
* warm: True only when every input above is defined. Any state field is "unknown" (or NaN) when
  its inputs are not available: HTF1 trend undefined, fewer than 200 prior ATR% values, ADX/ATR
  warm-up, or a candle with missing OHLC.

Missing candles: indicators run over the candles that exist, as TradingView does (no synthetic
filling). gap_steps reports the calendar gap before each candle in units of the median of the
PREVIOUS spacings minus 1 (0 = no gap; causal), for diagnostics; it does not change any state.
decided_at is timestamp metadata only (the next candle's open, capped at open + median spacing),
not an input to any computation. A candle with NaN
OHLC is "unknown" and its NaN propagates through the recursive indicators until they re-warm.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from hcmtf import ta
from hcmtf.engine import _bar_close_times, percentrank
from hcmtf.htf import align, trend_state

UNKNOWN = "unknown"


def _htf_close_from_chart(chart_index: pd.DatetimeIndex, c: np.ndarray, htf_index: pd.DatetimeIndex) -> np.ndarray:
    """Close of each HTF period as seen in the CHART feed: the last chart close whose candle opens
    before the next HTF period starts (NaN if the period has no chart candle). Only used through
    align(), which reads the PREVIOUS (completed) HTF period, so it never reads the future."""
    if len(htf_index) == 0:
        return np.full(0, np.nan)
    nxt = htf_index[1:].append(pd.DatetimeIndex([htf_index[-1] + pd.Timedelta(days=36500)]))
    pos = chart_index.searchsorted(nxt, side="left") - 1
    start = chart_index.searchsorted(htf_index, side="left")
    out = np.full(len(htf_index), np.nan)
    ok = (pos >= 0) & (pos >= start)
    out[ok] = c[pos[ok]]
    return out


@dataclass(frozen=True)
class StateConfig:
    ema_len: int = 21
    atr_len: int = 14
    adx_len: int = 14
    vol_rank_len: int = 200
    strength_cuts: tuple = (20.0, 30.0)
    vol_cuts: tuple = (100 / 3, 200 / 3)
    ext_cuts: tuple = (-3.0, -1.0, 1.0, 3.0)


def _direction(t1: np.ndarray, t2: np.ndarray) -> np.ndarray:
    out = np.zeros(len(t1))
    for d in (1, -1):
        a1, a2 = np.nan_to_num(t1 * d), np.nan_to_num(t2 * d)
        with_ = (a1 + a2 >= 1) & (a1 >= 0) & (a2 >= 0)
        out[with_] = d
    out[np.isnan(t1)] = np.nan
    return out


def classify(df: pd.DataFrame, htf1: pd.DataFrame, htf2: pd.DataFrame | None,
             cfg: StateConfig = StateConfig()) -> pd.DataFrame:
    """Market state per chart candle, known at the candle's close. Does not modify its inputs."""
    if not df.index.is_monotonic_increasing or df.index.has_duplicates:
        raise ValueError("chart index must be strictly increasing")
    o, h, l, c = (df[k].to_numpy(float).copy() for k in ("open", "high", "low", "close"))
    bad = np.isnan(o) | np.isnan(h) | np.isnan(l) | np.isnan(c)
    atr = ta.atr(h, l, c, cfg.atr_len)
    _, _, adx = ta.dmi(h, l, c, cfg.adx_len, cfg.adx_len)
    with np.errstate(divide="ignore", invalid="ignore"):
        atr_pct = atr / c
    vol_pct = percentrank(atr_pct, cfg.vol_rank_len)

    t1 = align(df.index, htf1.index, trend_state(htf1, cfg.ema_len))
    t2 = (align(df.index, htf2.index, trend_state(htf2, cfg.ema_len)) if htf2 is not None
          else np.full(len(df), np.nan))
    ema1 = align(df.index, htf1.index, ta.ema(_htf_close_from_chart(df.index, c, htf1.index), cfg.ema_len))
    direction = _direction(t1, t2)
    with np.errstate(divide="ignore", invalid="ignore"):
        ext = (c - ema1) / atr

    def cut(x, edges, labels):
        out = np.full(len(x), UNKNOWN, dtype=object)
        ok = ~np.isnan(x)
        out[ok] = np.array(labels, dtype=object)[np.searchsorted(np.asarray(edges), x[ok], side="right")]
        return out

    strength = cut(adx, cfg.strength_cuts, ["weak", "moderate", "strong"])
    vol_regime = cut(vol_pct, cfg.vol_cuts, ["low", "mid", "high"])
    e = cfg.ext_cuts
    ext_bucket = np.full(len(ext), UNKNOWN, dtype=object)
    ok = ~np.isnan(ext)
    x = ext[ok]
    ext_bucket[ok] = np.where(x <= e[0], "far_below", np.where(x <= e[1], "below", np.where(
        x < e[2], "near", np.where(x < e[3], "above", "far_above"))))
    dlabel = np.full(len(df), UNKNOWN, dtype=object)
    okd = ~np.isnan(direction)
    dlabel[okd] = np.where(direction[okd] > 0, "bull", np.where(direction[okd] < 0, "bear", "neutral"))

    # a candle with missing OHLC is unknown in every field
    for arr in (strength, vol_regime, ext_bucket, dlabel):
        arr[bad] = UNKNOWN
    for arr in (direction, adx, vol_pct, ext, atr):
        arr[bad] = np.nan

    gaps = np.zeros(len(df))
    if len(df) > 2:
        sp = pd.Series((df.index[1:] - df.index[:-1]).total_seconds().to_numpy(float))
        prior = sp.expanding().median().shift(1).to_numpy()          # median of PREVIOUS spacings only
        with np.errstate(invalid="ignore", divide="ignore"):
            g = sp.to_numpy() / prior - 1.0
        gaps[1:] = np.nan_to_num(g, nan=0.0)
    warm = (dlabel != UNKNOWN) & (strength != UNKNOWN) & (vol_regime != UNKNOWN) & (ext_bucket != UNKNOWN)
    return pd.DataFrame({
        "decided_at": _bar_close_times(df.index), "t1": t1, "t2": t2, "direction": direction, "direction_label": dlabel,
        "adx": adx, "strength": strength, "atr": atr, "vol_pct": vol_pct, "vol_regime": vol_regime,
        "extension_atr": ext, "ext_bucket": ext_bucket, "gap_steps": np.round(gaps, 3), "warm": warm,
    }, index=df.index)


STATE_KEYS = ("direction_label", "strength", "vol_regime", "ext_bucket")   # causal stratum columns
