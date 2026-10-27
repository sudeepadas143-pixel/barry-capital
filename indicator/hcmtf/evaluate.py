"""What happened after each signal, measured the way a trader could have traded it.

Execution model (conservative, used everywhere):
* A signal is known at the CLOSE of bar i. The earliest fill is the OPEN of bar i + 1.
* Stops are filled at the stop price, or at the open if the market gapped through it.
* If target and stop are both inside one bar, the stop is assumed to have come first.
* A round-trip cost in basis points (universe.COST_BPS, per asset class) is subtracted
  from every trade and every forward return.

Per-event outcomes, over a fixed horizon H bars after entry:
  ret_h       direction-adjusted return to the close of bar i + H, net of cost
  r_h         the same move in units of ATR(14) at the signal, net of cost
  mfe, mae    maximum favourable / adverse excursion in ATR units within H bars
  barrier     +1 if +2 ATR was reached before -1 ATR, -1 if the stop came first, 0 neither
These are the inputs to precision, false-positive rate, MFE/MAE and expectancy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import ta

HORIZON = {"1H": 24, "4H": 30, "1D": 20, "1W": 13}
TARGET_ATR = 2.0
STOP_ATR = 1.0


def outcomes(ev: pd.DataFrame, f, horizon: int, cost_bps: float) -> pd.DataFrame:
    """Add outcome columns to events (needs columns i, dir and an ATR array on f)."""
    n = len(f.c)
    cost = cost_bps / 1e4
    res = {k: [] for k in ("entry_i", "entry", "ret_h", "r_h", "mfe", "mae", "barrier", "bars_to_barrier")}
    for i, d in zip(ev["i"].to_numpy(int), ev["dir"].to_numpy(int)):
        a = f.atr[i]
        e = i + 1
        if e + horizon - 1 >= n or np.isnan(a) or a <= 0:
            for k in res:
                res[k].append(np.nan)
            continue
        px = f.o[e]
        sl = slice(e, e + horizon)
        hi, lo, cl, op = f.h[sl], f.l[sl], f.c[sl], f.o[sl]
        fav = (hi - px) if d > 0 else (px - lo)
        adv = (px - lo) if d > 0 else (hi - px)
        exit_px = cl[-1]
        ret = d * (exit_px / px - 1.0) - cost
        tgt = px + d * TARGET_ATR * a
        stp = px - d * STOP_ATR * a
        barrier, when = 0, np.nan
        for k in range(horizon):
            gap_stop = (op[k] <= stp) if d > 0 else (op[k] >= stp)
            hit_stop = (lo[k] <= stp) if d > 0 else (hi[k] >= stp)
            hit_tgt = (hi[k] >= tgt) if d > 0 else (lo[k] <= tgt)
            if gap_stop or hit_stop:
                barrier, when = -1, k
                break
            if hit_tgt:
                barrier, when = 1, k
                break
        res["entry_i"].append(e)
        res["entry"].append(px)
        res["ret_h"].append(ret)
        res["r_h"].append(d * (exit_px - px) / a - cost * px / a)
        res["mfe"].append(fav.max() / a)
        res["mae"].append(adv.max() / a)
        res["barrier"].append(barrier)
        res["bars_to_barrier"].append(when)
    out = ev.copy()
    for k, v in res.items():
        out[k] = v
    return out.dropna(subset=["ret_h"])


def bar_outcomes(f, horizon: int, cost_bps: float) -> dict[int, dict[str, np.ndarray]]:
    """``outcomes`` for a signal on EVERY bar, both directions, vectorised.

    Returns {+1: {...}, -1: {...}} with arrays indexed by signal bar. Bars too close to
    the end of the data (or without ATR) are NaN. Event lookups and the random-entry
    baseline both read from this table, so they are measured identically.
    """
    from numpy.lib.stride_tricks import sliding_window_view as win

    n = len(f.c)
    cost = cost_bps / 1e4
    out = {}
    m = n - horizon  # signal bars 0..m-1 have entry i+1 and a full window
    if m <= 0:
        nan = np.full(n, np.nan)
        return {d: {k: nan for k in ("ret_h", "r_h", "mfe", "mae", "barrier")} for d in (1, -1)}
    H, L, C, O = (win(x[1:], horizon)[:m] for x in (f.h, f.l, f.c, f.o))
    px = f.o[1:m + 1]
    a = f.atr[:m]
    first = lambda mask: np.where(mask.any(1), mask.argmax(1), horizon)
    for d in (1, -1):
        fav = (H.max(1) - px) if d > 0 else (px - L.min(1))
        adv = (px - L.min(1)) if d > 0 else (H.max(1) - px)
        tgt = px + d * TARGET_ATR * a
        stp = px - d * STOP_ATR * a
        if d > 0:
            s_hit = (O <= stp[:, None]) | (L <= stp[:, None])
            t_hit = H >= tgt[:, None]
        else:
            s_hit = (O >= stp[:, None]) | (H >= stp[:, None])
            t_hit = L <= tgt[:, None]
        fs, ft = first(s_hit), first(t_hit)
        bar = np.where(fs <= ft, np.where(fs < horizon, -1.0, 0.0), 1.0)
        ex = C[:, -1]
        res = {
            "ret_h": d * (ex / px - 1.0) - cost,
            "r_h": (d * (ex - px) - cost * px) / a,
            "mfe": fav / a,
            "mae": adv / a,
            "barrier": bar,
        }
        bad = np.isnan(a) | (a <= 0)
        full = {}
        for k, v in res.items():
            arr = np.full(n, np.nan)
            v = v.astype(float)
            v[bad] = np.nan
            arr[:m] = v
            full[k] = arr
        out[d] = full
    return out


def lookup(ev: pd.DataFrame, table) -> pd.DataFrame:
    """Attach outcome columns from a bar_outcomes table to events."""
    out = ev.copy()
    i = out["i"].to_numpy(int)
    d = out["dir"].to_numpy(int)
    for k in table[1]:
        out[k] = np.where(d > 0, table[1][k][i], table[-1][k][i])
    return out.dropna(subset=["ret_h"])


def simulate(ev: pd.DataFrame, f, cost_bps: float, max_hold: int, stop_atr: float = 2.0,
             trail_atr: float = 3.0) -> pd.DataFrame:
    """Sequential trades on one symbol, one position at a time, always in the market
    only when a signal says so.

    Entry: next open after a signal. Exit: an ATR trailing stop (initial ``stop_atr``,
    trailing ``trail_atr`` from the best close), an opposite signal (exit, and reverse, at
    the next open), or ``max_hold`` bars. Same-direction signals while in a trade are
    ignored. Returns one row per trade with the net return.
    """
    n = len(f.c)
    cost = cost_bps / 1e4
    sig = dict(zip(ev["i"].to_numpy(int), ev["dir"].to_numpy(int)))
    trades = []
    pos, entry_px, entry_i, stop, best = 0, np.nan, -1, np.nan, np.nan
    pending = None  # direction to enter at next open
    for i in range(n):
        if pending is not None:
            if pos != 0:
                trades.append((entry_i, i, pos, entry_px, f.o[i], "signal"))
            pos = pending
            entry_px, entry_i = f.o[i], i
            a = f.atr[i - 1]
            stop = entry_px - pos * stop_atr * a
            best = entry_px
            pending = None
        if pos != 0:
            # stop check on this bar (gap-through fills at the open)
            if (pos > 0 and f.o[i] <= stop) or (pos < 0 and f.o[i] >= stop):
                trades.append((entry_i, i, pos, entry_px, f.o[i], "stop"))
                pos = 0
            elif (pos > 0 and f.l[i] <= stop) or (pos < 0 and f.h[i] >= stop):
                trades.append((entry_i, i, pos, entry_px, stop, "stop"))
                pos = 0
            elif i - entry_i + 1 >= max_hold:
                trades.append((entry_i, i, pos, entry_px, f.c[i], "time"))
                pos = 0
            else:
                best = max(best, f.c[i]) if pos > 0 else min(best, f.c[i])
                a = f.atr[i]
                if not np.isnan(a):
                    trail = best - pos * trail_atr * a
                    stop = max(stop, trail) if pos > 0 else min(stop, trail)
        d = sig.get(i)
        if d is not None and i + 1 < n and d != pos:
            pending = d
    if pos != 0:
        trades.append((entry_i, n - 1, pos, entry_px, f.c[-1], "open"))
    t = pd.DataFrame(trades, columns=["entry_i", "exit_i", "dir", "entry", "exit", "reason"])
    t["ret"] = t["dir"] * (t["exit"] / t["entry"] - 1.0) - cost
    t["bars"] = t["exit_i"] - t["entry_i"] + 1
    return t


def bar_returns(trades: pd.DataFrame, f, cost_bps: float) -> np.ndarray:
    """Mark-to-market return of the position on every bar (for Sharpe and drawdown).

    Entry bar: open -> close. Middle bars: close -> close. Exit bar: previous close ->
    exit price (or open -> exit price when entry and exit share a bar). Half the
    round-trip cost is charged on the entry bar and half on the exit bar.
    """
    r = np.zeros(len(f.c))
    half = cost_bps / 2e4
    for e, x, d, px, ex in zip(trades["entry_i"], trades["exit_i"], trades["dir"],
                               trades["entry"], trades["exit"]):
        if x == e:
            r[e] += d * (ex / px - 1.0) - 2 * half
            continue
        r[e] += d * (f.c[e] / px - 1.0) - half
        if x > e + 1:
            seg = f.c[e:x]
            r[e + 1:x] += d * (seg[1:] / seg[:-1] - 1.0)
        r[x] += d * (ex / f.c[x - 1] - 1.0) - half
    return r


# ------------------------------------------------------------------ baseline signals


def ema_cross(f, fast: int = 20, slow: int = 50) -> pd.DataFrame:
    a, b = ta.ema(f.c, fast), ta.ema(f.c, slow)
    s = np.sign(a - b)
    ps = ta.shift(s)
    i = np.where((s != ps) & ~np.isnan(ps) & (s != 0))[0]
    return pd.DataFrame({"i": i, "dir": s[i].astype(int)})


def supertrend_flip(f, factor: float = 3.0, n: int = 10) -> pd.DataFrame:
    _, d = ta.supertrend(f.h, f.l, f.c, factor, n)
    pd_ = ta.shift(d)
    i = np.where((d != pd_) & ~np.isnan(pd_) & ~np.isnan(d))[0]
    return pd.DataFrame({"i": i, "dir": (-d[i]).astype(int)})


def raw_breaks(trig: pd.DataFrame) -> pd.DataFrame:
    """Every structure break, no evidence filter: isolates what the score adds."""
    t = trig[trig["warm"]]
    return t[["i", "dir"]].reset_index(drop=True)


def random_like(ev: pd.DataFrame, n_bars: int, warm: int, rng: np.random.Generator) -> pd.DataFrame:
    """Same number of events and same direction mix, at random bars."""
    if len(ev) == 0:
        return ev[["i", "dir"]]
    i = np.sort(rng.choice(np.arange(warm, n_bars - 1), size=len(ev), replace=False))
    return pd.DataFrame({"i": i, "dir": rng.permutation(ev["dir"].to_numpy())})


# --------------------------------------------------------------- turning points / lag


def zigzag(c: np.ndarray, atr: np.ndarray, k: float) -> list[tuple[int, int]]:
    """Ex-post swing extremes (uses the future, so ONLY for scoring timeliness).

    A swing ends when price retraces k x ATR from its extreme. Returns (bar, +1 for a
    low that starts an up-leg / -1 for a high that starts a down-leg).
    """
    piv: list[tuple[int, int]] = []
    start = int(np.argmax(~np.isnan(atr)))
    hi_i = lo_i = start
    d = 0
    for i in range(start + 1, len(c)):
        a = atr[i]
        if d == 0:
            if c[i] > c[hi_i]:
                hi_i = i
            if c[i] < c[lo_i]:
                lo_i = i
            if c[i] - c[lo_i] >= k * a:
                piv.append((lo_i, 1))
                d, hi_i = 1, i
            elif c[hi_i] - c[i] >= k * a:
                piv.append((hi_i, -1))
                d, lo_i = -1, i
        elif d == 1:
            if c[i] > c[hi_i]:
                hi_i = i
            elif c[hi_i] - c[i] >= k * a:
                piv.append((hi_i, -1))
                d, lo_i = -1, i
        else:
            if c[i] < c[lo_i]:
                lo_i = i
            elif c[i] - c[lo_i] >= k * a:
                piv.append((lo_i, 1))
                d, hi_i = 1, i
    return piv


def timeliness(ev: pd.DataFrame, f, k: float = 4.0) -> pd.DataFrame:
    """For each ex-post trend turn, the first event in the new direction inside that leg.

    lag_bars    bars from the turning extreme to the signal bar
    captured    share of the leg's move still ahead of the signal close (1 = caught at
                the extreme, 0 = caught at the end, negative = after the leg ended)
    """
    piv = zigzag(f.c, f.atr, k)
    evi = ev["i"].to_numpy(int)
    evd = ev["dir"].to_numpy(int)
    rows = []
    for j in range(len(piv) - 1):
        b, d = piv[j]
        e, _ = piv[j + 1]
        m = (evi >= b) & (evi < e) & (evd == d)
        leg = f.c[e] - f.c[b]
        if not m.any() or leg == 0:
            rows.append((b, d, np.nan, 0.0, False))
            continue
        s = evi[m][0]
        rows.append((b, d, s - b, (f.c[e] - f.c[s]) / leg, True))
    return pd.DataFrame(rows, columns=["turn_i", "dir", "lag_bars", "captured", "detected"])
