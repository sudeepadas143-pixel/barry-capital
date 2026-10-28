"""CY-2 complementary features (reports/CYCLE2_CONFIG.md §1) and the barrier target (§2).

Features are causal, Pine-portable functions of one chart (closed candles <= i). The barrier
target uses FUTURE candles by construction and is used only to train and score, never as an input.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hcmtf import ta

from .cycle_features import SCALE, highest, lowest, q_of

NEW = ["bbz", "roc", "roc_acc", "wick_up", "wick_dn", "td_up", "td_dn", "vratio", "dd_hh", "du_ll", "above", "climax"]


def _lag(x, k):
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


def td_count(c: np.ndarray, up: bool) -> np.ndarray:
    """Consecutive closes above (below) the close 4 candles earlier, capped at 13, / 13."""
    out = np.zeros(len(c))
    n = 0
    for i in range(len(c)):
        if i < 4 or not (np.isfinite(c[i]) and np.isfinite(c[i - 4])):
            n = 0
            out[i] = np.nan if i < 4 else 0.0
            continue
        hit = c[i] > c[i - 4] if up else c[i] < c[i - 4]
        n = min(n + 1, 13) if hit else 0
        out[i] = n / 13.0
    return out


def features(df: pd.DataFrame, tf: str, relvol: np.ndarray | None) -> pd.DataFrame:
    L = SCALE[tf]["L"]
    q = q_of(L)
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    atr = ta.atr(h, l, c, 14)
    rng_ = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        sma = ta.sma(c, L)
        sd = pd.Series(c).rolling(L, min_periods=L).std(ddof=0).to_numpy()   # Pine ta.stdev (biased)
        roc = (c - _lag(c, q)) / atr
        wu = np.where(rng_ > 0, (h - np.maximum(o, c)) / rng_, 0.0)
        wd = np.where(rng_ > 0, (np.minimum(o, c) - l) / rng_, 0.0)
        f = {
            "bbz": (c - sma) / sd, "roc": roc, "roc_acc": roc - _lag(roc, q),
            "wick_up": ta.sma(wu, 3), "wick_dn": ta.sma(wd, 3),
            "td_up": td_count(c, True), "td_dn": td_count(c, False),
            "vratio": np.log(ta.atr(h, l, c, 5) / ta.atr(h, l, c, L)),
            "dd_hh": (highest(h, L) - c) / atr, "du_ll": (c - lowest(l, L)) / atr,
            "above": np.where(np.isnan(ta.ema(c, L)), np.nan, (c > ta.ema(c, L)).astype(float)),
            "climax": (relvol * np.sign(c - o)) if relvol is not None else np.full(len(c), np.nan),
        }
    out = pd.DataFrame(f, index=df.index)
    for k in out:
        x = out[k].to_numpy(float, copy=True)
        x[~np.isfinite(x)] = np.nan
        out[k] = x
    return out


def barrier_target(o, h, l, c, atr, side: int, H: int, U: float, S: float) -> np.ndarray:
    """1.0 if an entry at open[s+1] in direction `side` reaches +U*ATR[s] before -S*ATR[s]
    within s+1 .. s+H (stop first when both hit in one candle); 0.0 otherwise; NaN when the
    window runs past the data or ATR is undefined. USES FUTURE DATA (training/scoring only)."""
    n = len(c)
    out = np.full(n, np.nan)
    for s in range(n - H - 1):
        a = atr[s]
        if not np.isfinite(a) or a <= 0:
            continue
        px = o[s + 1]
        tgt, stp = px + side * U * a, px - side * S * a
        res = 0.0
        for k in range(s + 1, s + H + 1):
            if side > 0:
                if l[k] <= stp:
                    break
                if h[k] >= tgt:
                    res = 1.0
                    break
            else:
                if h[k] >= stp:
                    break
                if l[k] <= tgt:
                    res = 1.0
                    break
        out[s] = res
    return out
