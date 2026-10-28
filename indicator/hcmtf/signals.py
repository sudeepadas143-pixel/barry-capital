"""The signal engine. pine/HighConvictionMTF.pine implements the same rules.

Pipeline, per closed bar:

1. Market structure. Swing highs/lows are confirmed ``right`` bars after they form and
   only then become levels. A close beyond the latest unbroken swing level is a
   structure break (the trigger). A break in the direction of the prevailing structure
   is a CONTINUATION (BOS); a break against it is a REVERSAL (CHoCH).
2. Evidence. On the trigger bar six yes/no conditions are checked, each a different kind
   of evidence:
     htf_near  near higher timeframe trend agrees (4H for a 1H chart, D for 4H, W for D, M for W)
     htf_anchor anchor higher timeframe trend agrees (D for 1H, W for 4H, M for D, 3M for W)
     momentum  RSI(14) on the right side of 50 and MACD histogram on the same side of 0
     strength  ADX(14) >= 20 with the directional index of the signal side on top
     displacement  the break bar's body is at least 0.5 ATR(14) in the signal direction
     volume    volume >= 1.3x its 20-bar average (skipped where the feed has no real volume)
   The score is the fraction of available conditions that hold. The weights are equal on
   purpose: with a few hundred events per fold, fitted weights would chase noise.
   Whether the score means anything is a question for the walk-forward test, not for
   the weights.
3. Tiers. A trigger with score >= ``confirm`` is a CONFIRMED signal; one that also has
   score >= ``major`` and an agreeing anchor timeframe is MAJOR. Everything else is not a
   signal. The thresholds are chosen per timeframe by walk-forward (see walkforward.py).
4. Early warning. While structure points one way, the first closed bar where price
   closes back across EMA(21) with RSI and MACD flipped too is an early WARNING of a
   possible reversal. It precedes the structural break, is marked differently, and is
   evaluated separately.
5. De-duplication. Each swing level can trigger once. A signal in the same direction as
   the previous signal needs ``cooldown`` bars since it; an opposite signal is always
   allowed. Warnings fire at most once per structure leg.

Everything at bar i uses data at or before bar i plus higher-timeframe values from
completed HTF bars, so signals never move once printed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

from . import ta
from .htf import CONTEXT, align, trend_state

COMPONENTS = ["htf_near", "htf_anchor", "momentum", "strength", "displacement", "volume"]
SHORT = {"htf_near": "N", "htf_anchor": "A", "momentum": "M", "strength": "S",
         "displacement": "D", "volume": "V"}


@dataclass(frozen=True)
class Params:
    pivot_left: int = 5
    pivot_right: int = 3
    confirm: float = 0.6
    major: float = 0.8
    cooldown: int = 10
    ema_len: int = 21
    rsi_len: int = 14
    atr_len: int = 14
    adx_len: int = 14
    adx_min: float = 20.0
    disp_atr: float = 0.5
    vol_len: int = 20
    vol_mult: float = 1.3
    htf_ema: int = 21


# Starting values per timeframe before any data was seen. Pivot spans and cooldowns are
# fixed by reasoning about bar duration, not tuned: roughly a trading day of bars on 1H,
# a few days on 4H, a week-plus on 1D, a month on 1W. walkforward.py only tunes the
# two score thresholds.
DEFAULTS = {
    "1H": Params(pivot_left=5, pivot_right=3, cooldown=12),
    "4H": Params(pivot_left=5, pivot_right=3, cooldown=6),
    "1D": Params(pivot_left=5, pivot_right=2, cooldown=5),
    "1W": Params(pivot_left=4, pivot_right=2, cooldown=4),
}


@dataclass
class Features:
    index: pd.DatetimeIndex
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    v: np.ndarray
    atr: np.ndarray
    ema: np.ndarray
    rsi: np.ndarray
    hist: np.ndarray
    pdi: np.ndarray
    mdi: np.ndarray
    adx: np.ndarray
    vol_ok: bool
    rvol: np.ndarray
    near: np.ndarray
    anchor: np.ndarray
    extra: dict = field(default_factory=dict)


def features(df: pd.DataFrame, near_df: pd.DataFrame | None, anchor_df: pd.DataFrame | None,
             p: Params, vol_ok: bool) -> Features:
    o, h, l, c, v = (df[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    pdi, mdi, adx = ta.dmi(h, l, c, p.adx_len, p.adx_len)
    _, _, hist = ta.macd(c, 12, 26, 9)
    with np.errstate(divide="ignore", invalid="ignore"):
        rvol = v / ta.sma(v, p.vol_len)
    nan = np.full(len(c), np.nan)
    near = nan if near_df is None else align(df.index, near_df.index, trend_state(near_df, p.htf_ema))
    anchor = nan if anchor_df is None else align(df.index, anchor_df.index, trend_state(anchor_df, p.htf_ema))
    return Features(df.index, o, h, l, c, v, ta.atr(h, l, c, p.atr_len), ta.ema(c, p.ema_len),
                    ta.rsi(c, p.rsi_len), hist, pdi, mdi, adx, vol_ok, rvol, near, anchor)


def structure(f: Features, p: Params) -> pd.DataFrame:
    """Every structure break, with its direction, kind and evidence. One row per trigger."""
    ph, pl = ta.pivots(f.h, f.l, p.pivot_left, p.pivot_right)
    sh = sl = np.nan
    sh_used = sl_used = True
    trend = 0                      # +1 after a bullish break, -1 after a bearish one
    rows = []
    n = len(f.c)
    struct = np.zeros(n)
    for i in range(n):
        if not np.isnan(ph[i]):
            sh, sh_used = ph[i], False
        if not np.isnan(pl[i]):
            sl, sl_used = pl[i], False
        up = (not sh_used) and f.c[i] > sh
        dn = (not sl_used) and f.c[i] < sl
        if up and dn:              # one bar through both levels: let the body decide
            up, dn = f.c[i] >= f.o[i], f.c[i] < f.o[i]
        if up or dn:
            d = 1 if up else -1
            kind = "reversal" if trend == -d else "continuation"
            level = sh if up else sl
            rows.append((i, d, kind, level))
            trend = d
            if up:
                sh_used = True
            else:
                sl_used = True
        struct[i] = trend
    f.extra["struct"] = struct
    out = pd.DataFrame(rows, columns=["i", "dir", "kind", "level"])
    return _evidence(out, f, p)


def _evidence(t: pd.DataFrame, f: Features, p: Params) -> pd.DataFrame:
    i = t["i"].to_numpy(int)
    d = t["dir"].to_numpy(int)
    t["htf_near"] = f.near[i] == d
    t["htf_anchor"] = f.anchor[i] == d
    t["momentum"] = np.where(d > 0, (f.rsi[i] > 50) & (f.hist[i] > 0), (f.rsi[i] < 50) & (f.hist[i] < 0))
    t["strength"] = (f.adx[i] >= p.adx_min) & np.where(d > 0, f.pdi[i] > f.mdi[i], f.mdi[i] > f.pdi[i])
    t["displacement"] = d * (f.c[i] - f.o[i]) >= p.disp_atr * f.atr[i]
    t["volume"] = (f.rvol[i] >= p.vol_mult) if f.vol_ok else False
    avail = np.full(len(t), 6.0 if f.vol_ok else 5.0)
    # Context that does not exist yet (warm-up) counts as unavailable, not as a "no".
    avail -= np.isnan(f.near[i]).astype(float) + np.isnan(f.anchor[i]).astype(float)
    t["available"] = avail
    t["score"] = t[COMPONENTS].sum(axis=1).astype(float)
    t["frac"] = t["score"] / t["available"]
    t["atr"] = f.atr[i]
    t["near"] = f.near[i]
    t["anchor"] = f.anchor[i]
    t["warm"] = ~np.isnan(f.atr[i]) & ~np.isnan(f.rsi[i]) & ~np.isnan(f.hist[i]) & ~np.isnan(f.adx[i])
    return t


def classify(trig: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Apply tiers and the de-duplication state machine. Returns signals only."""
    t = trig[trig["warm"]]
    keep = []
    last_dir, last_i = 0, -10**9
    frac = t["frac"].to_numpy()
    anchor_ok = t["htf_anchor"].to_numpy()
    anchor_missing = np.isnan(t["anchor"].to_numpy())
    for k, (i, d) in enumerate(zip(t["i"].to_numpy(), t["dir"].to_numpy())):
        if frac[k] < p.confirm - 1e-9:
            continue
        if d == last_dir and i - last_i < p.cooldown:
            continue
        major = frac[k] >= p.major - 1e-9 and (anchor_ok[k] or anchor_missing[k])
        keep.append((t.index[k], "major" if major else "confirmed"))
        last_dir, last_i = d, i
    if not keep:
        return t.iloc[:0].assign(tier=pd.Series(dtype=str))
    idx, tiers = zip(*keep)
    out = t.loc[list(idx)].copy()
    out["tier"] = list(tiers)
    return out


def warnings(f: Features) -> pd.DataFrame:
    """Early reversal warnings: momentum turns against the prevailing structure.

    Needs ``structure`` to have run first (it stores the structure series). Fires on the
    first bar of a leg where close crosses EMA(21) against structure with RSI past 50
    and the MACD histogram past 0 in the same direction. At most one per leg.
    """
    s = f.extra["struct"]
    rows = []
    armed_leg = None
    leg = 0
    for i in range(1, len(f.c)):
        if s[i] != s[i - 1]:
            leg += 1
        if s[i] == 0 or np.isnan(f.ema[i]) or np.isnan(f.rsi[i]) or np.isnan(f.hist[i]):
            continue
        d = -int(s[i])                     # the direction a reversal would take
        cross = d * (f.c[i] - f.ema[i]) > 0 and d * (f.c[i - 1] - f.ema[i - 1]) <= 0
        if cross and d * (f.rsi[i] - 50) > 0 and d * f.hist[i] > 0 and armed_leg != leg:
            rows.append((i, d))
            armed_leg = leg
    return pd.DataFrame(rows, columns=["i", "dir"])


def run(df: pd.DataFrame, near_df, anchor_df, p: Params, vol_ok: bool):
    """Convenience: features, triggers, signals and warnings for one series."""
    f = features(df, near_df, anchor_df, p, vol_ok)
    trig = structure(f, p)
    sig = classify(trig, p)
    warn = warnings(f)
    return f, trig, sig, warn


def label_text(row) -> str:
    """The text the Pine label shows, e.g. 'MAJOR BULL REVERSAL 5/6 N A M S D -'."""
    side = "BULL" if row["dir"] > 0 else "BEAR"
    marks = " ".join(SHORT[k] if row[k] else "-" for k in COMPONENTS)
    return f"{row['tier'].upper()} {side} {row['kind'].upper()} {int(row['score'])}/{int(row['available'])} {marks}"


def with_thresholds(p: Params, confirm: float, major: float) -> Params:
    return replace(p, confirm=confirm, major=major)


__all__ = ["Params", "DEFAULTS", "CONTEXT", "COMPONENTS", "run", "features", "structure",
           "classify", "warnings", "label_text", "with_thresholds"]
