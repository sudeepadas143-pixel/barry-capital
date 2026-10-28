"""Technical-analysis primitives that reproduce Pine Script's built-ins.

Each function follows the reference implementation in the Pine v6 manual, including the
warm-up: ta.ema and ta.rma seed with an SMA of the first ``length`` values, so the first
``length - 1`` outputs are NaN. Matching the warm-up matters less than matching the
recursion, but both are kept so a Python bar and a TradingView bar can be compared.

Every function uses values at or before bar i to produce output at bar i. Nothing here
can look ahead; tests/test_no_lookahead.py checks that by truncating the input.
"""

from __future__ import annotations

import numpy as np

NaN = np.nan


def sma(x: np.ndarray, n: int) -> np.ndarray:
    x = np.asarray(x, float)
    out = np.full(len(x), NaN)
    if len(x) < n:
        return out
    c = np.cumsum(np.insert(np.nan_to_num(x), 0, 0.0))
    valid = np.cumsum(np.insert(~np.isnan(x), 0, False).astype(int))
    s = c[n:] - c[:-n]
    k = valid[n:] - valid[:-n]
    out[n - 1:] = np.where(k == n, s / n, NaN)
    return out


def _seeded(x: np.ndarray, n: int, alpha: float) -> np.ndarray:
    x = np.asarray(x, float)
    out = np.full(len(x), NaN)
    seed = sma(x, n)
    prev = NaN
    for i in range(len(x)):
        if np.isnan(prev):
            prev = seed[i]
        elif np.isnan(x[i]):
            prev = NaN
        else:
            prev = alpha * x[i] + (1.0 - alpha) * prev
        out[i] = prev
    return out


def ema(x: np.ndarray, n: int) -> np.ndarray:
    return _seeded(x, n, 2.0 / (n + 1))


def rma(x: np.ndarray, n: int) -> np.ndarray:
    return _seeded(x, n, 1.0 / n)


def shift(x: np.ndarray, k: int = 1) -> np.ndarray:
    out = np.full(len(x), NaN)
    if k < len(x):
        out[k:] = x[:-k] if k else x
    return out


def true_range(h, l, c, handle_na: bool) -> np.ndarray:
    pc = shift(c)
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    if handle_na:
        tr[0] = h[0] - l[0]
    return tr


def atr(h, l, c, n: int) -> np.ndarray:
    return rma(true_range(h, l, c, True), n)


def rsi(x: np.ndarray, n: int) -> np.ndarray:
    d = x - shift(x)
    up = rma(np.where(np.isnan(d), NaN, np.maximum(d, 0.0)), n)
    dn = rma(np.where(np.isnan(d), NaN, np.maximum(-d, 0.0)), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(dn == 0, 100.0, np.where(up == 0, 0.0, 100.0 - 100.0 / (1.0 + up / dn)))
    out[np.isnan(up) | np.isnan(dn)] = NaN
    return out


def _fixnan(x: np.ndarray) -> np.ndarray:
    out = x.copy()
    for i in range(1, len(out)):
        if np.isnan(out[i]):
            out[i] = out[i - 1]
    return out


def dmi(h, l, c, n: int, adx_n: int):
    """Returns (+DI, -DI, ADX) exactly as ta.dmi(n, adx_n)."""
    up = h - shift(h)
    dn = shift(l) - l
    plus_dm = np.where(np.isnan(up), NaN, np.where((up > dn) & (up > 0), up, 0.0))
    minus_dm = np.where(np.isnan(dn), NaN, np.where((dn > up) & (dn > 0), dn, 0.0))
    trur = rma(true_range(h, l, c, False), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        plus = _fixnan(100.0 * rma(plus_dm, n) / trur)
        minus = _fixnan(100.0 * rma(minus_dm, n) / trur)
        s = plus + minus
        adx = 100.0 * rma(np.abs(plus - minus) / np.where(s == 0, 1.0, s), adx_n)
    return plus, minus, adx


def macd(x: np.ndarray, fast: int, slow: int, signal: int):
    line = ema(x, fast) - ema(x, slow)
    sig = ema(line, signal)
    return line, sig, line - sig


def supertrend(h, l, c, factor: float, n: int):
    """ta.supertrend: returns (value, direction) with direction -1 = up, +1 = down."""
    a = atr(h, l, c, n)
    src = (h + l) / 2.0
    up = src - factor * a
    dn = src + factor * a
    lo = np.full(len(c), NaN)
    hi = np.full(len(c), NaN)
    st = np.full(len(c), NaN)
    d = np.full(len(c), NaN)
    for i in range(len(c)):
        if np.isnan(a[i]):
            continue
        plo = lo[i - 1] if i and not np.isnan(lo[i - 1]) else 0.0
        phi = hi[i - 1] if i and not np.isnan(hi[i - 1]) else 0.0
        pc = c[i - 1] if i else NaN
        lo[i] = up[i] if (up[i] > plo or pc < plo) else plo
        hi[i] = dn[i] if (dn[i] < phi or pc > phi) else phi
        pst = st[i - 1] if i else NaN
        if i == 0 or np.isnan(a[i - 1]):
            d[i] = 1.0
        elif pst == phi:
            d[i] = -1.0 if c[i] > hi[i] else 1.0
        else:
            d[i] = 1.0 if c[i] < lo[i] else -1.0
        st[i] = lo[i] if d[i] == -1 else hi[i]
    return st, d


def pivots(h: np.ndarray, l: np.ndarray, left: int, right: int):
    """Swing points as they become KNOWN, not where they sit.

    ph[i] is the price of a swing high centred at bar i - right, reported on bar i, the
    first bar on which the right-hand side is complete. A swing high is strictly above
    the ``left`` bars before it and at least as high as the ``right`` bars after it.
    Same for lows. Reporting on the confirming bar is what makes this non-repainting.
    """
    n = len(h)
    ph = np.full(n, NaN)
    pl = np.full(n, NaN)
    for i in range(left + right, n):
        c = i - right
        hv, lv = h[c], l[c]
        if hv > h[c - left:c].max() and hv >= h[c + 1:i + 1].max():
            ph[i] = hv
        if lv < l[c - left:c].min() and lv <= l[c + 1:i + 1].min():
            pl[i] = lv
    return ph, pl
