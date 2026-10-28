"""HC-MTF 6.0 stage-1 continuation signals (reports/V6_CONT_CONFIG.md, FROZEN; section numbers
refer to it): EMA trend state, model A (trend + pullback + trigger) as a per-pair state machine,
and the filters B (RSI), C (MACD), D (extension) evaluated at A's signal candle.

Pure functions of chart OHLC: every condition at candle i reads candles <= i only (closed at i's
close); no higher timeframe, no labels, no outcomes, no downloads. Undefined (NaN) inputs satisfy
no condition and end an open pullback, as Pine's na does.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from hcmtf import ta

UP, DOWN, NONE, UNKNOWN = "up", "down", "none", "unknown"
SLOPE_M, SLOPE_S = 10, 50                       # §3.1 slope lags (rows)
GAP_FACTOR = 1.5                                # §2 gap: spacing > 1.5 nominal durations
NOMINAL = {"1H": pd.Timedelta(hours=1), "4H": pd.Timedelta(hours=4)}


@dataclass(frozen=True)
class Config:
    ema: tuple = (20, 50, 200)
    W: int = 10
    rsi_long: tuple = (45.0, 50.0)              # (dip <=, recover >=)
    rsi_short: tuple = (55.0, 50.0)             # (peak >=, fall <=)
    macd: str = "hist"                          # hist | line_signal | zero_cross
    ext: float = 3.0


P = Config()
CONFIGS = {                                     # §3.5: one setting changed per alternative
    "P": P,
    "E1": replace(P, ema=(10, 30, 100)), "E2": replace(P, ema=(30, 70, 200)),
    "W1": replace(P, W=6), "W2": replace(P, W=15),
    "R1": replace(P, rsi_long=(40.0, 50.0), rsi_short=(60.0, 50.0)),
    "R2": replace(P, rsi_long=(50.0, 55.0), rsi_short=(50.0, 45.0)),
    "M1": replace(P, macd="line_signal"), "M2": replace(P, macd="zero_cross"),
    "X1": replace(P, ext=2.0), "X2": replace(P, ext=4.0),
}
# which contrasts each config enters (§3.5, §8)
AFFECTS = {"P": "ABCD", "E1": "ABCD", "E2": "ABCD", "W1": "ABCD", "W2": "ABCD",
           "R1": "BC", "R2": "BC", "M1": "C", "M2": "C", "X1": "D", "X2": "D"}


def gaps(index: pd.DatetimeIndex, tf: str) -> np.ndarray:
    """gap[k]: a gap before candle k (open-time spacing > 1.5 nominal durations); gap[0] False."""
    g = np.zeros(len(index), bool)
    if len(index) > 1:
        g[1:] = (index[1:] - index[:-1]) > GAP_FACTOR * NOMINAL[tf]
    return g


def indicators(df: pd.DataFrame, ema: tuple) -> dict:
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    ef, em, es = (ta.ema(c, n) for n in ema)
    line, sig, hist = ta.macd(c, 12, 26, 9)
    return {"o": o, "h": h, "l": l, "c": c, "ef": ef, "em": em, "es": es, "rsi": ta.rsi(c, 14),
            "line": line, "sig": sig, "hist": hist, "atr": ta.atr(h, l, c, 14)}


def _lag(x: np.ndarray, k: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if k < len(x):
        out[k:] = x[:-k]
    return out


def trend_state(ind: dict) -> np.ndarray:
    """§3.1 per candle: up / down / none / unknown."""
    ef, em, es = ind["ef"], ind["em"], ind["es"]
    dm, ds = em - _lag(em, SLOPE_M), es - _lag(es, SLOPE_S)
    known = ~(np.isnan(ef) | np.isnan(em) | np.isnan(es) | np.isnan(dm) | np.isnan(ds) | np.isnan(ind["c"]))
    with np.errstate(invalid="ignore"):
        up = (ef > em) & (em > es) & (dm > 0) & (ds >= 0)
        dn = (ef < em) & (em < es) & (dm < 0) & (ds <= 0)
    out = np.where(up, UP, np.where(dn, DOWN, NONE)).astype(object)
    out[~known] = UNKNOWN
    return out


def model_a(ind: dict, trend: np.ndarray, gap: np.ndarray, side: int, W: int) -> pd.DataFrame:
    """§3.2/§3.3 state machine. Returns one row per model-A signal: i (signal candle), j
    (pullback start). Per candle: (a) end an open pullback (invalidation, trend change, window,
    gap, undefined input) BEFORE any trigger; (b) with none open: re-arm, then start; (c) trigger."""
    h, l, c, ef, em = ind["h"], ind["l"], ind["c"], ind["ef"], ind["em"]
    want = UP if side > 0 else DOWN
    n = len(c)
    armed, j = True, -1
    rows = []
    for k in range(n):
        defined = trend[k] != UNKNOWN and not np.isnan(h[k]) and not np.isnan(l[k])
        if j >= 0:                                                       # (a) end checks
            inval = (c[k] < em[k]) if side > 0 else (c[k] > em[k])
            if (not defined) or trend[k] != want or k - j > W or gap[k] or inval:
                j = -1
        if j < 0 and defined and trend[k] == want:                       # (b) arm, then start
            if (l[k] > ef[k]) if side > 0 else (h[k] < ef[k]):
                armed = True
            elif armed and not gap[k] and ((l[k] <= ef[k]) if side > 0 else (h[k] >= ef[k])):
                j, armed = k, False
        if j >= 0 and k >= 1 and not np.isnan(h[k - 1]) and not np.isnan(l[k - 1]):   # (c) trigger
            if side > 0:
                trig = c[k] > ef[k] and c[k] > h[k - 1]
            else:
                trig = c[k] < ef[k] and c[k] < l[k - 1]
            if trig:
                rows.append((k, j))
                j = -1
    return pd.DataFrame(rows, columns=["i", "j"], dtype=int)


def _window(x: np.ndarray, j: int, i: int) -> np.ndarray:
    return x[j:i + 1]


def filters(ind: dict, a: pd.DataFrame, side: int, cfg: Config) -> pd.DataFrame:
    """§3.4 filters at each A signal (same candle i, pullback rows j..i): B, C, D flags."""
    rsi, hist, line, sig, c, em, atr = (ind[k] for k in ("rsi", "hist", "line", "sig", "c", "em", "atr"))
    B, C, D = [], [], []
    for i, j in zip(a["i"].to_numpy(int), a["j"].to_numpy(int)):
        w = _window(rsi, j, i)
        r0 = rsi[i - 1] if i >= 1 else np.nan
        if np.isnan(w).any() or np.isnan(r0):
            b = False
        elif side > 0:
            b = w.min() <= cfg.rsi_long[0] and rsi[i] >= cfg.rsi_long[1] and rsi[i] > r0
        else:
            b = w.max() >= cfg.rsi_short[0] and rsi[i] <= cfg.rsi_short[1] and rsi[i] < r0
        if cfg.macd == "hist":
            m = i >= 1 and not np.isnan(hist[i]) and not np.isnan(hist[i - 1]) and \
                ((hist[i] > hist[i - 1]) if side > 0 else (hist[i] < hist[i - 1]))
        elif cfg.macd == "line_signal":
            m = not np.isnan(line[i]) and not np.isnan(sig[i]) and ((line[i] > sig[i]) if side > 0 else (line[i] < sig[i]))
        else:                                                             # zero_cross within i-4 .. i
            m = False
            for k in range(max(1, i - 4), i + 1):
                a0, a1 = line[k - 1], line[k]
                if np.isnan(a0) or np.isnan(a1):
                    continue
                if (a1 > 0 >= a0) if side > 0 else (a1 < 0 <= a0):
                    m = True
                    break
        with np.errstate(invalid="ignore", divide="ignore"):
            e = ((c[i] - em[i]) if side > 0 else (em[i] - c[i])) / atr[i]
        d = bool(np.isfinite(e) and e <= cfg.ext)
        B.append(bool(b)); C.append(bool(b and m)); D.append(d)
    out = a.copy()
    out["B"], out["C"], out["D"] = np.array(B, bool), np.array(C, bool), np.array(D, bool)
    return out


def signals(df: pd.DataFrame, tf: str, cfg: Config, side: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """Model A signals with B/C/D flags for one config and side, plus indicators and trend."""
    ind = indicators(df, cfg.ema)
    tr = trend_state(ind)
    a = model_a(ind, tr, gaps(df.index, tf), side, cfg.W)
    return filters(ind, a, side, cfg), ind, tr
