"""Weekly-only engine for Kenny's Divergence Indicator (reports/KW_CONFIG.md).

Separate, asymmetric BUY (major bottom) and SELL (major top) cluster logic on closed weekly
candles. Reuses the shipped weekly scores (kenny_sim: B_ext bottoms, GBZ tops) and the KC cluster
mechanics (decaying per-family traces, novelty-limited repeats, opposite-evidence shrink), and adds
weekly families drawn from the references:
  dd    - drawdown from the 52-week high, in ATR (long-term correction depth)       [BUY]
  rally - advance from the 52-week low, in ATR                                        [SELL]
  tsm   - sign-based 52-week time-series momentum, sum(sign(r))/sqrt(52)              [regime gate]
  div   - RSI14 / MACD-histogram regular divergence at 5/2 pivots (earlier on weekly)
  rev   - hammer / shooting star (wick >= 2x body, >= 50% of range) at the 26-week extreme
  turn  - momentum turn: RSI14 re-crossing 35 up (BUY) / 65 down (SELL)
  cap   - capitulation: relvol >= 1 or log(ATR5/ATR26) >= 0.4, with a lower wick       [BUY]
Every value at candle i uses candles <= i.
"""

from __future__ import annotations

import numpy as np

from hcmtf import ta

from .cycle_features import highest, lowest, q_of

L = 26
PIV_L, PIV_R, GAP_MIN, GAP_MAX = 5, 2, 4, 52


def _lag(x, k=1):
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


def tsmom(c, n=52):
    r = np.sign(c - _lag(c))
    s = np.full(len(c), np.nan)
    cs = np.nancumsum(np.nan_to_num(r))
    s[n:] = (cs[n:] - cs[:-n]) / np.sqrt(n)
    return s


def divergence(h, l, c):
    osc = [ta.rsi(c, 14), ta.macd(c, 12, 26, 9)[2]]
    ph, pl = ta.pivots(h, l, PIV_L, PIV_R)
    n = len(c)
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
                if np.isfinite(x[p]) and np.isfinite(x[q]) and (
                        (d == "top" and px[p] > px[q] and x[p] < x[q]) or (d == "bot" and px[p] < px[q] and x[p] > x[q])):
                    k += 1
            out[d][at] = k / 2.0
    return out


def weekly_features(df, relvol):
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    atr = ta.atr(h, l, c, 14)
    rsi = ta.rsi(c, 14)
    rg = h - l
    body = np.abs(c - o)
    with np.errstate(invalid="ignore", divide="ignore"):
        wu = h - np.maximum(o, c)
        wd = np.minimum(o, c) - l
        f = {"dd": (highest(h, 52) - c) / atr, "rally": (c - lowest(l, 52)) / atr, "tsm": tsmom(c),
             "rsi": rsi, "rsi1": _lag(rsi),
             "hammer": (wd >= 2 * body) & (wd >= 0.5 * rg) & (l <= lowest(l, L)),
             "star": (wu >= 2 * body) & (wu >= 0.5 * rg) & (h >= highest(h, L)),
             "vr": np.log(ta.atr(h, l, c, 5) / ta.atr(h, l, c, L)),
             "wdshare": np.where(rg > 0, wd / rg, 0.0), "wushare": np.where(rg > 0, wu / rg, 0.0)}
    f["relvol"] = relvol if relvol is not None else np.full(len(c), np.nan)
    f["div"] = divergence(h, l, c)
    return f


def _cross_up(x, lev):
    with np.errstate(invalid="ignore"):
        return (x > lev) & (_lag(x) <= lev)


def evidence(df, st, variant: str) -> dict:
    """Per side: family strengths (0..1), the zone-active mask and the family weights.
    variant: 'W1' = KC families on weekly; 'W2' = weekly families + asymmetric regime gates."""
    from . import kenny_cluster as KC
    F = st["F"]
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    n = len(c)
    wf = weekly_features(df, F["relvol"].to_numpy(float))
    cc, m = q_of(L), L // 2
    out = {}
    for d in ("top", "bot"):
        p, th = st[d]["p"], st[d]["theta"]
        ext = np.zeros(n)
        for k, e in KC.TIER_E.items():
            ext[st[d][k]] = np.maximum(ext[st[d][k]], e)
        cnf = np.zeros(n)
        cnf[st[d]["K_CONF"]] = 1.0
        with np.errstate(invalid="ignore"):
            warm = np.convolve(np.nan_to_num(p, nan=-np.inf) >= th["warning"], np.ones(cc), "full")[:n] > 0
        win = np.zeros(n, bool)
        for s0 in st[d]["K_S"]:
            win[s0:min(n, s0 + m + 1)] = True
        active = warm | win
        if variant == "W1":
            pa = KC.price_action(o, h, l, c, L)[d]
            vv = KC.vol_burst(o, h, l, c, F["relvol"].to_numpy(float), L)[d]
            fam = {"ext": ext, "cnf": cnf, "div": KC.divergence(h, l, c)[d], "pa": pa, "vv": vv}
            w = {"ext": 1.0, "cnf": 0.75, "div": 1.0, "pa": 0.75, "vv": 0.75}
        else:
            with np.errstate(invalid="ignore"):
                if d == "bot":
                    deep = np.nan_to_num(wf["dd"]) >= 8.0
                    ddx = np.where(_cross_up(wf["dd"], 8.0), 0.6, 0.0) + np.where(_cross_up(wf["dd"], 14.0), 0.4, 0.0)
                    rev = wf["hammer"].astype(float)
                    turn = _cross_up(wf["rsi"], 35.0).astype(float)
                    cap = (((np.nan_to_num(wf["relvol"], nan=-9) >= 1.0) | (np.nan_to_num(wf["vr"], nan=-9) >= 0.4)) & (wf["wdshare"] >= 0.4)).astype(float)
                    fam = {"ext": ext, "dd": ddx, "div": wf["div"]["bot"], "rev": rev, "turn": turn, "cap": cap}
                    w = {"ext": 1.0, "dd": 1.0, "div": 1.0, "rev": 0.75, "turn": 0.75, "cap": 0.5}
                    active = (active | deep) & (np.nan_to_num(wf["tsm"], nan=0.0) <= 1.0)       # not inside a strong uptrend
                else:
                    strong = np.nan_to_num(wf["tsm"], nan=0.0) >= 0.5                          # tops need a mature advance
                    rly = np.where(_cross_up(wf["rally"], 12.0), 0.6, 0.0) + np.where(_cross_up(wf["rally"], 20.0), 0.4, 0.0)
                    rev = wf["star"].astype(float)
                    turn = _cross_up(-wf["rsi"], -65.0).astype(float)
                    fam = {"ext": ext, "cnf": cnf, "rally": rly, "div": wf["div"]["top"], "rev": rev, "turn": turn}
                    w = {"ext": 1.0, "cnf": 0.75, "rally": 0.75, "div": 1.0, "rev": 0.75, "turn": 0.75}
                    active = active & strong
        out[d] = {"fam": fam, "w": w, "active": active}
    out["trend"] = KC.htf_trend(df, None)          # weekly: no HTF context multiplier (monthly trend lags major turns)
    return out


def run(ev: dict, hl: float, theta: dict, delta: float = 0.15, kappa: float = 0.5):
    """Side-specific clusters (hl = half-life in weeks; theta = {'bot': x, 'top': y})."""
    lam = 0.5 ** (1.0 / max(1.0, hl))
    n = len(ev["trend"])
    keys = {d: list(ev[d]["fam"]) for d in ("top", "bot")}
    E = {d: np.column_stack([ev[d]["fam"][k] for k in keys[d]]) for d in ("top", "bot")}
    W = {d: np.array([ev[d]["w"][k] for k in keys[d]]) for d in ("top", "bot")}
    T = {d: np.zeros(len(keys[d])) for d in ("top", "bot")}
    score = {d: np.zeros(n) for d in ("top", "bot")}
    qual = {d: np.zeros(n, bool) for d in ("top", "bot")}
    for i in range(n):
        new = {}
        for d, od in (("top", "bot"), ("bot", "top")):
            opp = float(E[od][i].max())
            t = T[d] * lam * (1.0 - kappa * opp)
            inc = np.maximum(0.0, W[d] * E[d][i] * (1.0 - t / W[d]))
            T[d] = np.minimum(t + inc, W[d])
            new[d] = float(inc.sum())
        for d in ("top", "bot"):
            score[d][i] = float(T[d].sum())
            qual[d][i] = ev[d]["active"][i] and new[d] >= delta and score[d][i] >= theta[d]
    both = qual["top"] & qual["bot"]
    buy = qual["bot"] & ~(both & (score["top"] >= score["bot"]))
    sell = qual["top"] & ~(both & (score["bot"] >= score["top"]))
    return np.flatnonzero(buy), np.flatnonzero(sell), score
