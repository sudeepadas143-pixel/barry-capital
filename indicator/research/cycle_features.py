"""Cycle-engine features and alert mechanics (reports/CYCLE_CONFIG.md §3 and §5, FROZEN).

Pure, causal functions of one chart's OHLCV: every value at candle i uses candles <= i only
(closed at i's close). Pine-identical primitives (hcmtf.ta). No labels, no outcomes, no downloads.
The Pine indicator (pine/HC_CycleEngine.pine) computes the same quantities in the same way.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as win

from hcmtf import ta

# per-TF scale: label radius L (= the frozen label table; restated here so this module never imports
# the label module) and move size D used by the confirmation rule (D/4 ATR)
SCALE = {"1H": {"L": 168, "D": 8.0}, "4H": {"L": 126, "D": 8.0}, "1D": {"L": 63, "D": 8.0},
         "1W": {"L": 26, "D": 5.0}, "1M": {"L": 12, "D": 5.0}}
HTF_OF = {"1H": "4H", "4H": "1D", "1D": "1W", "1W": "1M"}

PRICE = ["ext_c", "ext_f", "rng", "slope", "since_hh", "since_ll", "atr_rank"]
MOM = ["rsi", "rsi_slope", "rsi_gap_hi", "rsi_gap_lo", "hist", "hist_acc"]
VOL = ["relvol", "vtrend", "effort", "vpress"]
INTER = ["i_rng_gaphi", "i_rng_gaplo", "i_ext_relvol"]


def q_of(L: int) -> int:
    return max(2, L // 4)


def _roll(x: np.ndarray, n: int, fn) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = fn(win(x, n), axis=1)
    return out


def highest(x, n):
    """ta.highest(x, n): max of the last n values including the current one."""
    return _roll(np.asarray(x, float), n, np.max)


def lowest(x, n):
    return _roll(np.asarray(x, float), n, np.min)


def bars_since_extreme(x, n, hi: bool) -> np.ndarray:
    """-ta.highestbars / -ta.lowestbars: bars back to the most recent extreme in the last n."""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        w = win(x, n)[:, ::-1]                          # column 0 = current bar
        k = np.argmax(w, axis=1) if hi else np.argmin(w, axis=1)
        bad = np.isnan(w).any(axis=1)
        out[n - 1:] = np.where(bad, np.nan, k)
    return out


def percentrank(x, n):
    """ta.percentrank: % of the previous n values <= the current value."""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) > n:
        prev = win(x, n)[:-1]                           # windows ending at i-1
        cur = x[n:]
        ok = ~np.isnan(prev).any(axis=1) & ~np.isnan(cur)
        out[n:] = np.where(ok, 100.0 * (prev <= cur[:, None]).sum(axis=1) / n, np.nan)
    return out


def _lag(x, k):
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


def range_position(h, l, c, L) -> np.ndarray:
    hh, ll = highest(h, L), lowest(l, L)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = (c - ll) / (hh - ll)
    r[~np.isfinite(r)] = np.nan
    return r


def features(df: pd.DataFrame, tf: str, has_volume: bool) -> pd.DataFrame:
    """All §3 features (except the context ones) for one chart. Volume features are NaN when the
    instrument has no usable volume: never zero."""
    L = SCALE[tf]["L"]
    q = q_of(L)
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    atr = ta.atr(h, l, c, 14)
    ema_l, ema_f = ta.ema(c, L), ta.ema(c, 21)
    rsi = ta.rsi(c, 14)
    _, _, hist = ta.macd(c, 12, 26, 9)
    with np.errstate(invalid="ignore", divide="ignore"):
        f = {
            "ext_c": (c - ema_l) / atr, "ext_f": (c - ema_f) / atr, "rng": range_position(h, l, c, L),
            "slope": (ema_l - _lag(ema_l, q)) / atr,
            "since_hh": bars_since_extreme(h, L, True) / L, "since_ll": bars_since_extreme(l, L, False) / L,
            "atr_rank": percentrank(atr / c, 100) / 100.0,
            "rsi": rsi / 100.0, "rsi_slope": (rsi - _lag(rsi, 3)) / 100.0,
            "rsi_gap_hi": (highest(rsi, L) - rsi) / 100.0, "rsi_gap_lo": (rsi - lowest(rsi, L)) / 100.0,
            "hist": hist / atr, "hist_acc": (hist - _lag(hist, 3)) / atr,
        }
        if has_volume and "volume" in df:
            v = df["volume"].to_numpy(float)
            v = np.where(v > 0, v, np.nan)
            relvol = np.clip(np.log(v / ta.sma(v, 20)), -3, 3)
            dv = np.sign(c - _lag(c, 1)) * v
            sv = pd.Series(v).rolling(10, min_periods=10).sum().to_numpy()
            f.update({"relvol": relvol, "vtrend": np.clip(np.log(ta.sma(v, 5) / ta.sma(v, L)), -3, 3),
                      "effort": np.clip(np.log(np.abs(c - o) / atr + 0.05) - relvol, -5, 5),
                      "vpress": pd.Series(dv).rolling(10, min_periods=10).sum().to_numpy() / sv})
        else:
            for k in VOL:
                f[k] = np.full(len(c), np.nan)
    out = pd.DataFrame(f, index=df.index)
    for k in out:
        x = out[k].to_numpy(float, copy=True)
        x[~np.isfinite(x)] = np.nan
        out[k] = x
    out["i_rng_gaphi"] = out["rng"] * out["rsi_gap_hi"]
    out["i_rng_gaplo"] = (1 - out["rng"]) * out["rsi_gap_lo"]
    out["i_ext_relvol"] = out["ext_c"] * out["relvol"]
    out["_atr"], out["_ema_f"], out["_rsi"], out["_hist"] = atr, ema_f, rsi, hist
    return out


# ----------------------------------------------------------------------------- alert mechanics (§5)

def zone_onsets(p: np.ndarray, theta: float, c: int) -> np.ndarray:
    """p >= theta and max(p[i-c .. i-1]) < theta (undefined p never fires; an undefined value in
    the look-back window counts as below theta, as Pine's ta.highest skips na)."""
    p = np.asarray(p, float)
    prev = pd.Series(p).shift(1).rolling(c, min_periods=1).max().to_numpy()
    with np.errstate(invalid="ignore"):
        on = (p >= theta) & ~(prev >= theta)
    return np.flatnonzero(on & np.isfinite(p))


def developing_and_confirmed(onsets, side: int, o, h, l, c, rsi, hist, ema_f, atr, L: int, D: float):
    """For each onset s: developing = first i in (s, s+c] with momentum turning against the prior
    move and a candle in the new direction; confirmed = first i in (s, s+m] with close beyond EMA21
    and an ATR-scaled retreat of D/4 from the extreme since s. Returns (developing, confirmed)."""
    n = len(c)
    cc, m = q_of(L), L // 2
    dev, conf = [], []
    for s in onsets:
        s = int(s)
        for i in range(s + 1, min(n, s + cc + 1)):
            if side < 0:                                   # top
                ok = rsi[i] < rsi[i - 1] and hist[i] < hist[i - 1] and c[i] < o[i]
            else:
                ok = rsi[i] > rsi[i - 1] and hist[i] > hist[i - 1] and c[i] > o[i]
            if ok:
                dev.append(i)
                break
        ext = h[s] if side < 0 else l[s]
        for i in range(s + 1, min(n, s + m + 1)):
            ext = max(ext, h[i]) if side < 0 else min(ext, l[i])
            if not (np.isfinite(atr[i]) and np.isfinite(ema_f[i])):
                continue
            if side < 0 and c[i] < ema_f[i] and ext - c[i] >= D / 4 * atr[i]:
                conf.append(i); break
            if side > 0 and c[i] > ema_f[i] and c[i] - ext >= D / 4 * atr[i]:
                conf.append(i); break
    return np.unique(np.array(dev, int)), np.unique(np.array(conf, int))
