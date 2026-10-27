"""Family C (major tops) detectors, exactly as frozen in reports/V5_C_EXPLORATION_CONFIG.md
(§3 and freezing clarifications F1-F6, commit 74d5ae5). Written after the freeze.

All detectors are bearish, read closed chart candles up to i only, and return sorted unique
candle indices. They never import the retrospective label module (test P1).

  C1a  extension crosses up through 3 ATR in a bullish HTF state                (warning)
  C1b  extension percentile (previous 500) >= 95 in a bullish state, onset only  (warning)
  C2   bearish RSI14 divergence between consecutive confirmed pivot highs        (warning)
  C3   failed breakout: close back below a just-broken pivot-high level within 5 (warning + confirmation)
  C4   ATR% percentile jump >= 33.3 in 5 candles on a down candle after extension (warning)
  C5a  bearish change of character in a bull/neutral state after a C1-C4 warning (confirmation)
  C5b  the same change of character without the warning precondition (ablation)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hcmtf import engine as G, ta
from hcmtf.engine import percentrank

DETECTORS = ("C1a", "C1b", "C2", "C3", "C4", "C5a", "C5b")
WARNINGS = ("C1a", "C1b", "C2", "C3", "C4")
CONFIRMATIONS = ("C3", "C5a", "C5b")
PIV_L, PIV_R = 5, 3
C5_WINDOW = 50


def c1a(state: pd.DataFrame) -> np.ndarray:
    ext = state["extension_atr"].to_numpy(float)
    bull = state["direction_label"].to_numpy(object) == "bull"
    prev = np.r_[np.nan, ext[:-1]]
    with np.errstate(invalid="ignore"):
        fire = (ext >= 3.0) & (prev < 3.0) & bull & ~np.isnan(ext) & ~np.isnan(prev)
    return np.flatnonzero(fire)


def c1b(state: pd.DataFrame) -> np.ndarray:
    ext = state["extension_atr"].to_numpy(float)
    bull = state["direction_label"].to_numpy(object) == "bull"
    pct = percentrank(ext, 500)                       # F1: % of the previous 500 values <= current
    with np.errstate(invalid="ignore"):
        cond = bull & (pct >= 95.0) & ~np.isnan(pct)
    prev = np.r_[False, cond[:-1]]
    return np.flatnonzero(cond & ~prev)


def c2(df: pd.DataFrame, state: pd.DataFrame) -> np.ndarray:
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    ph, _ = ta.pivots(h, l, PIV_L, PIV_R)
    rsi = ta.rsi(c, 14)
    lab = state["direction_label"].to_numpy(object)
    out, prev = [], None
    for i in np.flatnonzero(~np.isnan(ph)):
        p = i - PIV_R
        if prev is not None and p - prev <= 100:
            if (h[p] > h[prev] and not np.isnan(rsi[p]) and not np.isnan(rsi[prev]) and rsi[p] < rsi[prev]
                    and lab[i] in ("bull", "neutral")):
                out.append(i)
        prev = p
    return np.array(out, int)


def c3(df: pd.DataFrame) -> np.ndarray:
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    ph, _ = ta.pivots(h, l, PIV_L, PIV_R)
    levels: list[float] = []            # unbroken pivot-high levels known so far
    pending: list[tuple[int, float]] = []
    out = []
    for i in range(len(c)):
        if np.isnan(c[i]):
            pending = [(b, s) for b, s in pending if i <= b + 5]
            continue
        fired = False
        keep = []
        for b, s in pending:                         # failures of earlier breakouts
            if i <= b + 5:
                if c[i] < s:
                    fired = True
                else:
                    keep.append((b, s))
        pending = keep
        broken = [s for s in levels if c[i] > s]      # breakouts of levels known before i
        if broken:
            levels = [s for s in levels if not c[i] > s]
            pending += [(i, s) for s in broken]
        if not np.isnan(ph[i]):                       # a level confirmed at i is known from i on
            levels.append(float(ph[i]))
        if fired:
            out.append(i)
    return np.array(out, int)


def c4(df: pd.DataFrame, state: pd.DataFrame) -> np.ndarray:
    o, c = df["open"].to_numpy(float), df["close"].to_numpy(float)
    ext = state["extension_atr"].to_numpy(float)
    vp = state["vol_pct"].to_numpy(float)
    ext_prev = np.r_[np.nan, ext[:-1]]
    vp5 = np.r_[np.full(5, np.nan), vp[:-5]] if len(vp) > 5 else np.full(len(vp), np.nan)
    with np.errstate(invalid="ignore"):
        fire = (ext_prev >= 1.0) & (c < o) & ((vp - vp5) >= 33.3)
    fire &= ~np.isnan(ext_prev) & ~np.isnan(vp) & ~np.isnan(vp5)
    return np.flatnonzero(fire)


def bearish_choch(df: pd.DataFrame, htf1: pd.DataFrame, htf2: pd.DataFrame | None, tf: str, asset,
                  state: pd.DataFrame) -> np.ndarray:
    ctx = G.Ctx(df, htf1, htf2, None, asset.volume, asset.cls == "crypto")
    p = G.DEFAULTS[tf]
    f = G.features(ctx, p)
    t = G.breaks(f, p)
    if len(t) == 0:
        return np.array([], int)
    t = t[(t["dir"] == -1) & t["choch"].astype(bool) & t["warm"].astype(bool)]
    i = t["i"].to_numpy(int)
    lab = state["direction_label"].to_numpy(object)
    return np.unique(i[np.isin(lab[i], ["bull", "neutral"])])


def eligible(alerts, state: pd.DataFrame, start: pd.Timestamp) -> np.ndarray:
    """F6: keep alerts on warm candles opening at or after the window start."""
    a = np.unique(np.asarray(alerts, int))
    if len(a) == 0:
        return a
    warm = state["warm"].to_numpy(bool)
    after = np.asarray(state.index >= start)
    return a[warm[a] & after[a]]


def detect_all(df: pd.DataFrame, htf1: pd.DataFrame, htf2: pd.DataFrame | None, state: pd.DataFrame,
               tf: str, asset, start: pd.Timestamp) -> dict[str, np.ndarray]:
    """Eligible alerts of every frozen variant for one instrument and timeframe."""
    raw = {"C1a": c1a(state), "C1b": c1b(state), "C2": c2(df, state), "C3": c3(df), "C4": c4(df, state)}
    out = {k: eligible(v, state, start) for k, v in raw.items()}
    ch = eligible(bearish_choch(df, htf1, htf2, tf, asset, state), state, start)
    out["C5b"] = ch
    warn = np.unique(np.concatenate([out[k] for k in WARNINGS])) if any(len(out[k]) for k in WARNINGS) else np.array([], int)
    if len(ch) and len(warn):
        lo = np.searchsorted(warn, ch - C5_WINDOW, "left")
        hi = np.searchsorted(warn, ch - 1, "right")
        out["C5a"] = ch[hi > lo]
    else:
        out["C5a"] = np.array([], int)
    return out
