"""Cumulative signal clusters for Kenny's Divergence Indicator (reports/KC_CONFIG.md).

Python reference of the Pine cluster layer. Per direction (BUY = bottom, SELL = top), every closed
candle can add evidence from separate families:
  ext - Kenny's model crossing a tier threshold: warning 0.4, standard 0.7, high 1.0 (onsets)
  cnf - Kenny's Confirmed rule (close beyond EMA21 after a D/4 ATR retreat; structure/trend)
  div - regular RSI14 / MACD-histogram divergence at a confirmed pivot (0.5 per oscillator)
  pa  - price-action reversal at the L-range extreme (failed breakout, engulfing, pin bar)
  vv  - volatility/volume burst (relvol >= 1 or log(ATR5/ATR_L) >= 0.5) with a reversal-side wick
Each family keeps a decaying trace. With redundancy control a firing adds only its NOVEL part
(w * e * (1 - trace / w)), so a persistent condition saturates while new families add fully.
Opposite-direction evidence shrinks the traces. The completed higher-timeframe trend multiplies
the score (context). A candle QUALIFIES when the model zone is active (ext > 0), the new evidence
on that candle is >= DELTA, and the cluster score >= theta. The zone is active while the model
score was at or above its warning threshold within the last c candles, or within m = L/2
candles after a standard onset (the Confirmed window). Every qualifying candle is a signal
(no cooldown); when BUY and SELL qualify together the larger score wins and a tie shows neither.
All inputs use closed candles <= i; the HTF trend is the previous completed HTF candle.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hcmtf import ta
from hcmtf.htf import align

from .cycle_features import SCALE, highest, lowest, q_of

FAMS = ("ext", "cnf", "div", "pa", "vv")
WEIGHTS = {"ext": 1.0, "cnf": 0.75, "div": 1.0, "pa": 0.75, "vv": 0.75}
TIER_E = {"K_W": 0.4, "K_S": 0.7, "K_H": 1.0}
KAPPA = 0.5          # opposite-evidence shrink
CTX = 1.2            # multiplier when the completed HTF trend agrees with the signal's continuation side
DELTA = 0.15         # minimum new evidence on a qualifying candle
PIV_L, PIV_R, GAP_MIN, GAP_MAX = 5, 5, 5, 60
HTF_OF = {"1W": "1M", "1D": "1W", "4H": "1D", "1H": "4H"}


def _lag(x, k=1):
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


def divergence(h, l, c):
    """Per direction, 0 / 0.5 / 1: share of {RSI14, MACD hist} with regular divergence against the
    nearest previous confirmed pivot 5..60 candles back; reported on the confirming candle."""
    n = len(c)
    osc = [ta.rsi(c, 14), ta.macd(c, 12, 26, 9)[2]]
    ph, pl = ta.pivots(h, l, PIV_L, PIV_R)
    out = {"top": np.zeros(n), "bot": np.zeros(n)}
    for d, conf, px in (("top", np.flatnonzero(np.isfinite(ph)), h), ("bot", np.flatnonzero(np.isfinite(pl)), l)):
        piv = conf - PIV_R
        for j in range(len(piv)):
            p, at = piv[j], conf[j]
            q = next((q for q in piv[:j][::-1] if GAP_MIN <= p - q <= GAP_MAX), None)
            if q is None:
                continue
            k = 0
            for x in osc:
                if np.isfinite(x[p]) and np.isfinite(x[q]):
                    if (d == "top" and px[p] > px[q] and x[p] < x[q]) or (d == "bot" and px[p] < px[q] and x[p] > x[q]):
                        k += 1
            out[d][at] = k / 2.0
    return out


def price_action(o, h, l, c, L):
    hh, ll = _lag(highest(h, L), 1), _lag(lowest(l, L), 1)
    rg = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        pos_prev = _lag((c - lowest(l, L)) / (highest(h, L) - lowest(l, L)), 1)
        wu = np.where(rg > 0, (h - np.maximum(o, c)) / rg, 0.0)
        wd = np.where(rg > 0, (np.minimum(o, c) - l) / rg, 0.0)
        o1, c1 = _lag(o), _lag(c)
        top = ((h > hh) & (c < hh)) | ((c < o) & (c1 > o1) & (o >= c1) & (c <= o1) & (pos_prev >= 0.9)) | ((wu >= 0.6) & (h >= hh))
        bot = ((l < ll) & (c > ll)) | ((c > o) & (c1 < o1) & (o <= c1) & (c >= o1) & (pos_prev <= 0.1)) | ((wd >= 0.6) & (l <= ll))
    return {"top": top.astype(float), "bot": bot.astype(float)}


def vol_burst(o, h, l, c, relvol, L):
    rg = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        vr = np.log(ta.atr(h, l, c, 5) / ta.atr(h, l, c, L))
        wu = np.where(rg > 0, (h - np.maximum(o, c)) / rg, 0.0)
        wd = np.where(rg > 0, (np.minimum(o, c) - l) / rg, 0.0)
        burst = (np.nan_to_num(relvol, nan=-9.0) >= 1.0) | (np.nan_to_num(vr, nan=-9.0) >= 0.5)
    return {"top": (burst & (wu >= 0.4)).astype(float), "bot": (burst & (wd >= 0.4)).astype(float)}


def htf_trend(df: pd.DataFrame, htf: pd.DataFrame | None) -> np.ndarray:
    """+1 / -1 of the previous completed HTF candle (close vs EMA21); 0 when unavailable."""
    if htf is None or not len(htf):
        return np.zeros(len(df))
    hc = htf["close"].to_numpy(float)
    e = ta.ema(hc, 21)
    with np.errstate(invalid="ignore"):
        v = np.where(hc > e, 1.0, -1.0)
    out = align(df.index, htf.index, v)
    return np.nan_to_num(out, nan=0.0)


def evidence(df: pd.DataFrame, tf: str, st: dict, htf: pd.DataFrame | None = None) -> dict:
    """Family strengths per direction from Kenny's states (kenny_sim.states) and the chart."""
    L = SCALE[tf]["L"]
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    F = st["F"]
    dv, pa = divergence(h, l, c), price_action(o, h, l, c, L)
    vb = vol_burst(o, h, l, c, F["relvol"].to_numpy(float), L)
    ev = {"trend": htf_trend(df, htf)}
    n = len(c)
    cc, m = q_of(L), L // 2
    for d in ("top", "bot"):
        p, th = st[d]["p"], st[d]["theta"]
        ext = np.zeros(n)
        for k, e in TIER_E.items():
            ext[st[d][k]] = np.maximum(ext[st[d][k]], e)
        cnf = np.zeros(n)
        cnf[st[d]["K_CONF"]] = 1.0
        with np.errstate(invalid="ignore"):
            warm = pd.Series(np.nan_to_num(p, nan=-np.inf) >= th["warning"]).astype(float).rolling(cc, min_periods=1).max().to_numpy() > 0
        win = np.zeros(n, bool)
        for s0 in st[d]["K_S"]:
            win[s0:min(n, s0 + m + 1)] = True
        ev[d] = {"ext": ext, "cnf": cnf, "div": dv[d], "pa": pa[d], "vv": vb[d], "active": warm | win}
    return ev


def run_clusters(ev: dict, tf: str, hl_frac: float = 1 / 8, theta: float = 1.0, novelty: bool = True):
    """Cluster scores and final signals. Returns (buy_idx, sell_idx, scores {top, bot})."""
    L = SCALE[tf]["L"]
    lam = 0.5 ** (1.0 / max(1.0, L * hl_frac))
    n = len(ev["trend"])
    T = {d: {f: 0.0 for f in FAMS} for d in ("top", "bot")}
    score = {d: np.zeros(n) for d in ("top", "bot")}
    qual = {d: np.zeros(n, bool) for d in ("top", "bot")}
    E = {d: np.column_stack([ev[d][f] for f in FAMS]) for d in ("top", "bot")}
    A = {d: ev[d]["active"] for d in ("top", "bot")}
    W = np.array([WEIGHTS[f] for f in FAMS])
    for i in range(n):
        new = {}
        for d, od in (("top", "bot"), ("bot", "top")):
            opp = float(E[od][i].max())
            tr = T[d]
            add = 0.0
            for k, f in enumerate(FAMS):
                t = tr[f] * lam * (1.0 - KAPPA * opp)
                e = E[d][i, k]
                inc = W[k] * e * ((1.0 - t / W[k]) if novelty else 1.0)
                inc = max(0.0, inc)
                tr[f] = min(t + inc, W[k]) if novelty else t + inc
                add += inc
            new[d] = add
        tr_sign = ev["trend"][i]
        for d in ("top", "bot"):
            s = sum(T[d].values())
            if (d == "bot" and tr_sign > 0) or (d == "top" and tr_sign < 0):
                s *= CTX
            score[d][i] = s
            qual[d][i] = A[d][i] and new[d] >= DELTA and s >= theta
    both = qual["top"] & qual["bot"]
    buy = qual["bot"] & ~(both & (score["top"] >= score["bot"]))
    sell = qual["top"] & ~(both & (score["bot"] >= score["top"]))
    return np.flatnonzero(buy), np.flatnonzero(sell), score
