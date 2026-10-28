"""Weekly Cycle Engine (WCE) for Kenny's Divergence Indicator — research only (reports/KW6_SPEC.md).

A weekly market-state engine with three feature groups that each answer ONE question (one witness
per role, to avoid double counting correlated oscillators):
  A. phase       - fast (13w) vs slow (52w) volatility-normalised momentum -> regime
                   BULL / CORRECTION / BEAR / REBOUND (sign rule of the momentum-turning-point
                   literature), plus stretch of price vs its own history.
  B. exhaustion  - location (stretch), momentum (deceleration of fast momentum vs its recent
                   extreme) and trigger (rejection candle / failed breakout), counted once each.
  C. transition  - persistent fast-momentum sign change plus a weekly structure break.
States (top side; the bottom side is its own model, see below):
  BULL_ACCEL -> BULL_MATURE (stretched) -> BULL_EXHAUSTED (all three exhaustion roles within the
  evidence window) -> BEARISH_TRANSITION (persistent negative fast momentum + structure break
  within 26 weeks of exhaustion). A correction WITHOUT prior exhaustion is an ordinary pullback
  and raises nothing.
Signals: SELL warning = entry into BULL_EXHAUSTED; SELL confirmed = entry into BEARISH_TRANSITION.
BUY warning = entry into BEAR_EXHAUSTED (downside stretch + deceleration of the decline + a
capitulation/rejection trigger, which also admits a volatility burst); BUY confirmed = entry into
BULLISH_TRANSITION (persistent positive fast momentum + reclaim of the 8-week high).
Evidence decays: each exhaustion role stays live for EVID weeks; the exhaustion -> transition link
for LINK weeks. Re-entry into a signal state needs the state to have been left for REARM weeks, so
one persistent condition cannot emit unlimited signals. All inputs use closed weekly candles <= i.
"""

from __future__ import annotations

import numpy as np

from hcmtf import ta

from .cycle_features import highest, lowest, percentrank

FAST, SLOW = 13, 52
PCT_N = 156                # stretch percentile window (3 years of weeks)
STRETCH_HI, STRETCH_LO = 0.90, 0.10
DECEL = 1.0                # fast momentum this far (normalised units) off its 8-week extreme
EVID, LINK, REARM = 8, 26, 4
STRUCT = 8                 # structure = prior 8-week low / high


def _lag(x, k=1):
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


def _recent(mask, n):
    m = np.asarray(mask, float)
    return np.convolve(np.nan_to_num(m), np.ones(n), "full")[:len(m)] > 0


def features(df):
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    atr = ta.atr(h, l, c, 14)
    sma40 = ta.sma(c, 40)
    rg = h - l
    body = np.abs(c - o)
    with np.errstate(invalid="ignore", divide="ignore"):
        fm = (c - _lag(c, FAST)) / (atr * np.sqrt(FAST))
        sm = (c - _lag(c, SLOW)) / (atr * np.sqrt(SLOW))
        ext40 = (c - sma40) / atr
        f = {"o": o, "h": h, "l": l, "c": c, "atr": atr, "fm": fm, "sm": sm, "ext40": ext40,
             "pct": percentrank(ext40, PCT_N) / 100.0,
             "fm_max8": highest(fm, 8), "fm_min8": lowest(fm, 8),
             "hh26p": _lag(highest(h, 26), 1), "ll26p": _lag(lowest(l, 26), 1),
             "hh8p": _lag(highest(h, STRUCT), 1), "ll8p": _lag(lowest(l, STRUCT), 1),
             "up_wick": np.where(rg > 0, (h - np.maximum(o, c)) / rg, 0.0),
             "dn_wick": np.where(rg > 0, (np.minimum(o, c) - l) / rg, 0.0),
             "close_pos": np.where(rg > 0, (c - l) / rg, 0.5),
             "bear_engulf": (c < o) & (_lag(c) > _lag(o)) & (o >= _lag(c)) & (c <= _lag(o)),
             "bull_engulf": (c > o) & (_lag(c) < _lag(o)) & (o <= _lag(c)) & (c >= _lag(o)),
             "vburst": np.log(ta.atr(h, l, c, 5) / ta.atr(h, l, c, 26)) >= 0.4,
             "body": body, "rg": rg}
    return f


def regime(f):
    """0 BULL (slow>=0, fast>=0), 1 CORRECTION (slow>=0, fast<0), 2 BEAR, 3 REBOUND; -1 undefined."""
    fm, sm = f["fm"], f["sm"]
    r = np.full(len(fm), -1)
    ok = np.isfinite(fm) & np.isfinite(sm)
    r[ok & (sm >= 0) & (fm >= 0)] = 0
    r[ok & (sm >= 0) & (fm < 0)] = 1
    r[ok & (sm < 0) & (fm < 0)] = 2
    r[ok & (sm < 0) & (fm >= 0)] = 3
    return r


def roles(f, side, use=("stretch", "decel", "trigger")):
    """Per-candle exhaustion roles for side 'top' / 'bot' (each a boolean array)."""
    with np.errstate(invalid="ignore"):
        if side == "top":
            stretch = np.nan_to_num(f["pct"]) >= STRETCH_HI
            decel = np.nan_to_num(f["fm"], nan=99) <= np.nan_to_num(f["fm_max8"]) - DECEL
            trig = ((f["h"] > f["hh26p"]) & (f["c"] < f["hh26p"])) | ((f["up_wick"] >= 0.5) & (f["close_pos"] <= 0.5)) | f["bear_engulf"]
        else:
            stretch = np.nan_to_num(f["pct"], nan=1.0) <= STRETCH_LO
            decel = np.nan_to_num(f["fm"], nan=-99) >= np.nan_to_num(f["fm_min8"]) + DECEL
            trig = ((f["l"] < f["ll26p"]) & (f["c"] > f["ll26p"])) | ((f["dn_wick"] >= 0.5) & (f["close_pos"] >= 0.5)) | f["bull_engulf"] \
                | (f["vburst"] & (f["dn_wick"] >= 0.4))
    out = {"stretch": stretch, "decel": decel, "trigger": np.asarray(trig, bool)}
    return {k: (v if k in use else np.ones(len(v), bool)) for k, v in out.items()}


def _entries(mask, rearm):
    """Candles where mask turns on after being off for >= rearm candles."""
    idx = np.flatnonzero(mask)
    out, last = [], -10**9
    for i in idx:
        if i - last > rearm:
            out.append(int(i))
        last = i
    return np.array(out, int)


def signals(f, side, use=("stretch", "decel", "trigger"), need_exhaustion=True, need_structure=True):
    """WCE signals for one side. Returns {'warn': idx, 'conf': idx, 'state': per-candle state code}.
    use / need_* switch feature groups off for ablation."""
    n = len(f["c"])
    r = regime(f)
    R = roles(f, side, use)
    # exhaustion: the trigger fires now while location and momentum roles were live within EVID weeks
    exhausted = R["trigger"] & _recent(R["stretch"], EVID) & _recent(R["decel"], EVID)
    if side == "top":
        exhausted &= (r == 0) | (r == 1)                    # an exhausted top needs a bull/late-bull regime
    else:
        exhausted &= (r == 2) | (r == 3)
    warn = _entries(exhausted, REARM)
    with np.errstate(invalid="ignore"):
        if side == "top":
            persist = (np.nan_to_num(f["fm"], nan=1) < 0) & (_lag(np.nan_to_num(f["fm"], nan=1), 1) < 0)
            struct = f["c"] < f["ll8p"]
        else:
            persist = (np.nan_to_num(f["fm"], nan=-1) >= 0) & (_lag(np.nan_to_num(f["fm"], nan=-1), 1) >= 0)
            struct = f["c"] > f["hh8p"]
    trans = persist & (_recent(struct, 3) if need_structure else True)
    if need_exhaustion:
        armed = _recent(exhausted, LINK)
        trans = trans & armed
    conf = _entries(trans, REARM)
    state = np.full(n, 0)                                   # 0 none, 1 exhausted, 2 transition (for tests / diagnostics)
    state[exhausted] = 1
    state[trans] = 2
    return {"warn": warn, "conf": conf, "state": state}


# ----------------------------------------------------------------------------- baselines

def regime_transition(f, side):
    """Simple fast/slow baseline: BULL -> CORRECTION (SELL) / BEAR -> REBOUND (BUY)."""
    r = regime(f)
    pr = _lag(r.astype(float), 1)
    if side == "top":
        return np.flatnonzero((r == 1) & (pr == 0))
    return np.flatnonzero((r == 3) & (pr == 2))


def ma_cross(f, side, ma=40):
    """Long-term trend baseline: first close below (SELL) / above (BUY) SMA40 after >= 13 weeks on the other side."""
    sma = f["c"] - f["ext40"] * f["atr"]
    with np.errstate(invalid="ignore"):
        side_now = (f["c"] < sma) if side == "top" else (f["c"] > sma)
    prev = np.convolve(_lag(side_now.astype(float)), np.ones(13), "full")[:len(sma)]
    return np.flatnonzero(side_now & ~(np.nan_to_num(prev) > 0) & np.isfinite(sma))


def rsi_recross(f, side):
    r = ta.rsi(f["c"], 14)
    with np.errstate(invalid="ignore"):
        if side == "top":
            return np.flatnonzero((r < 70) & (_lag(r) >= 70))
        return np.flatnonzero((r > 30) & (_lag(r) <= 30))
