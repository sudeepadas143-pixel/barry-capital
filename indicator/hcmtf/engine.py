"""v2 signal engine: LTF / MTF / HTF ladder. pine/HighConvictionMTF.pine mirrors it.

The chart timeframe is the MTF: it is where structure breaks are detected and signals
print. Two higher timeframes (HTF1, HTF2) set direction and decide how much a break
matters. One lower timeframe (LTF) is read from the candles inside each closed chart
candle and supplies the early warnings.

    chart  LTF   HTF1  HTF2
    1H     15m   4H    1D
    4H     1H    1D    1W
    1D     4H    1W    1M
    1W     1D    1M    3M

Every break is put in one of four classes by its relation to structure and to the HTFs:

    continuation        break WITH the MTF structure and WITH the HTFs     -> CONFIRMED
    realignment         MTF change of character BACK INTO the HTF direction
                        (a pullback ending; once per pullback)            -> MAJOR
    counter_reversal    MTF change of character AGAINST the HTFs: a possible
                        HTF reversal, recognised before any HTF trend
                        changes                                           -> WATCH only
    counter_continuation  break with MTF structure but against the HTFs   -> nothing

HTF bias b = HTF1 trend + HTF2 trend (each +1/0/-1). "With the HTFs" means b*d >= 1 and
neither HTF against; "against" means at least one HTF against. Breaks with both HTFs flat
produce nothing.

Why this shape: on development data (reports/SCREENING.md, reports/DESIGN_CHECK.md) the
HTF relation was the only thing that separated outcomes; none of the add-on conditions
(momentum, strength, displacement, FVG, volume, liquidity sweep, LTF momentum, funding,
basis, open interest, regime/shock/spike/weekend filters) passed the pre-set screening
rule, and requiring both HTFs to agree did worse than one agreeing. So the add-on
conditions are computed and shown, but do not gate signals (Params.evidence is empty and
the thresholds are 0). They can be switched back on for research via Params.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

from . import ta
from .htf import align, trend_state

LADDER = {
    "1H": ("15m", "4H", "1D"),
    "4H": ("1H", "1D", "1W"),
    "1D": ("4H", "1W", "1M"),
    "1W": ("1D", "1M", "3M"),
}

# Evidence families. Within a family conditions are correlated, so a family counts once.
FAMILIES = {
    "momentum": ["momentum"],            # RSI(14) vs 50 and MACD histogram vs 0
    "strength": ["strength"],            # ADX(14) >= 20, signal-side DI on top
    "impulse": ["displacement", "fvg"],  # body >= 0.5 ATR / a fair-value gap left behind
    "participation": ["volume"],         # relative volume where volume is meaningful
    "liquidity": ["sweep"],              # an opposite-side stop run shortly before the break
    "ltf": ["ltf_momentum"],             # LTF momentum agrees at the chart close
    "positioning": ["perp_ok", "basis_ok", "oi_up"],  # crypto perps, optional external data
}

# Filters: if switched on, a break that fails one cannot become a signal of any tier.
FILTERS = ["not_range", "not_shock", "not_spike_wick", "not_weekend"]


@dataclass(frozen=True)
class Params:
    pivot_left: int = 5
    pivot_right: int = 3
    cooldown: int = 10
    confirm: float = 0.0                # evidence fraction needed (0: evidence does not gate)
    major: float = 0.0
    counter_major: float = 2.0          # kept for the record: the counter-HTF MAJOR path is closed
    major_classes: tuple = ("realignment",)
    confirm_classes: tuple = ("continuation",)
    adx_min: float = 20.0
    disp_atr: float = 0.5
    vol_mult: float = 1.3
    sweep_lookback: int = 10
    vol_rank_len: int = 200
    shock_rank: float = 95.0
    range_adx: float = 18.0
    spike_wick_atr: float = 0.8
    strict_htf: bool = False            # require both HTFs to agree (tested; did worse; off)
    accept: bool = False                # signal only if the NEXT candle also closes beyond the level
    evidence: tuple = ()                # screening kept none; see reports/SCREENING.md
    filters: tuple = ()
    crypto_only: tuple = ()             # conditions/filters that apply on crypto charts only


DEFAULTS = {
    "1H": Params(pivot_left=5, pivot_right=3, cooldown=12),
    "4H": Params(pivot_left=5, pivot_right=3, cooldown=6),
    "1D": Params(pivot_left=5, pivot_right=2, cooldown=5),
    "1W": Params(pivot_left=4, pivot_right=2, cooldown=4),
}


@dataclass
class Ctx:
    """Everything a series needs: chart bars plus optional context frames."""
    df: pd.DataFrame
    htf1: pd.DataFrame | None
    htf2: pd.DataFrame | None
    ltf: pd.DataFrame | None
    vol_ok: bool
    is_crypto: bool
    perp: pd.DataFrame | None = None      # hourly perp bars (close)
    spot1h: pd.DataFrame | None = None    # hourly spot bars (close), for basis
    funding: pd.DataFrame | None = None   # funding rate events
    oi: pd.DataFrame | None = None        # hourly open interest


@dataclass
class Feat:
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
    rvol: np.ndarray
    vol_rank: np.ndarray
    t1: np.ndarray
    t2: np.ndarray
    ltf_mom: np.ndarray        # +1/-1/0/NaN: LTF momentum at the chart close
    ltf_struct: np.ndarray     # +1/-1/0/NaN: LTF structure at the chart close
    funding_z: np.ndarray      # funding rate z-score (crypto perps), NaN elsewhere
    basis_z: np.ndarray        # perp/spot basis z-score, NaN elsewhere
    oi_chg: np.ndarray         # open-interest % change over the chart candle, NaN elsewhere
    vol_ok: bool
    is_crypto: bool
    extra: dict = field(default_factory=dict)


def _bar_close_times(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Close time of each chart bar = next bar's open, capped at the median spacing.

    The cap keeps an overnight or weekend gap from swallowing the next session's
    lower-timeframe candles into the previous chart candle.
    """
    if len(index) < 2:
        return index
    step = pd.Series(index[1:] - index[:-1]).median()
    nxt = index[1:].append(pd.DatetimeIndex([index[-1] + step]))
    return pd.DatetimeIndex(np.minimum(nxt.values, (index + step).values)).tz_localize("UTC")


def _ltf_at_close(chart_index, ltf: pd.DataFrame, values: np.ndarray) -> np.ndarray:
    """Value on the last LTF candle that OPENED before the chart candle closed.

    That LTF candle closes no later than the chart candle (the grids nest), so on a
    closed chart candle the value is final. Pine: array.last(request.security_lower_tf(...)).
    """
    close_t = _bar_close_times(chart_index)
    pos = ltf.index.searchsorted(close_t, side="left") - 1
    out = np.full(len(chart_index), np.nan)
    ok = pos >= 0
    out[ok] = np.asarray(values, float)[pos[ok]]
    # an LTF candle from an earlier chart candle is not "inside" this one: ignore it
    first_inside = ltf.index.searchsorted(chart_index, side="left")
    out[pos < first_inside] = np.nan
    return out


def _momentum_state(df: pd.DataFrame) -> np.ndarray:
    c = df["close"].to_numpy(float)
    r = ta.rsi(c, 14)
    _, _, hst = ta.macd(c, 12, 26, 9)
    out = np.where((r > 50) & (hst > 0), 1.0, np.where((r < 50) & (hst < 0), -1.0, 0.0))
    out[np.isnan(r) | np.isnan(hst)] = np.nan
    return out


def structure_state(h, l, c, o, left: int, right: int) -> np.ndarray:
    """+1/-1 after each bullish/bearish structure break, 0 before the first."""
    ph, pl = ta.pivots(h, l, left, right)
    sh = sl = np.nan
    sh_used = sl_used = True
    trend = 0
    out = np.zeros(len(c))
    for i in range(len(c)):
        if not np.isnan(ph[i]):
            sh, sh_used = ph[i], False
        if not np.isnan(pl[i]):
            sl, sl_used = pl[i], False
        up = (not sh_used) and c[i] > sh
        dn = (not sl_used) and c[i] < sl
        if up and dn:
            up, dn = c[i] >= o[i], c[i] < o[i]
        if up:
            trend, sh_used = 1, True
        elif dn:
            trend, sl_used = -1, True
        out[i] = trend
    return out


def _funding_z(chart_index, funding: pd.DataFrame | None) -> np.ndarray:
    """Latest funding rate known at the chart close, as a z-score vs the prior 90 prints."""
    if funding is None or len(funding) == 0:
        return np.full(len(chart_index), np.nan)
    r = funding["rate"].astype(float)
    mu = r.rolling(90, min_periods=60).mean().shift(1)
    sd = r.rolling(90, min_periods=60).std().shift(1)
    z = ((r - mu) / sd).to_numpy()
    close_t = _bar_close_times(chart_index)
    pos = funding.index.searchsorted(close_t, side="left") - 1  # strictly before the close
    out = np.full(len(chart_index), np.nan)
    ok = pos >= 0
    out[ok] = z[pos[ok]]
    # stale if the last print is more than 2 days old (delisted perp, archive gap)
    stale = np.zeros(len(chart_index), bool)
    stale[ok] = (close_t[ok] - funding.index[pos[ok]]) > pd.Timedelta(days=2)
    out[stale] = np.nan
    return out


def _hourly_at_close(chart_index, idx: pd.DatetimeIndex, values: np.ndarray, max_age: pd.Timedelta) -> np.ndarray:
    """Hourly series (bars labelled by open time) read at each chart close: the last hour
    that opened before the chart candle closed, i.e. one that has itself closed."""
    close_t = _bar_close_times(chart_index)
    pos = idx.searchsorted(close_t, side="left") - 1
    out = np.full(len(chart_index), np.nan)
    ok = pos >= 0
    out[ok] = np.asarray(values, float)[pos[ok]]
    stale = np.zeros(len(chart_index), bool)
    stale[ok] = (close_t[ok] - idx[pos[ok]]) > max_age
    out[stale] = np.nan
    return out


def _basis_z(chart_index, perp, spot1h) -> np.ndarray:
    if perp is None or spot1h is None or len(perp) == 0 or len(spot1h) == 0:
        return np.full(len(chart_index), np.nan)
    j = perp[["close"]].join(spot1h[["close"]], lsuffix="_p", rsuffix="_s", how="inner")
    b = j["close_p"] / j["close_s"] - 1.0
    mu = b.rolling(720, min_periods=500).mean().shift(1)
    sd = b.rolling(720, min_periods=500).std().shift(1)
    return _hourly_at_close(chart_index, j.index, ((b - mu) / sd).to_numpy(), pd.Timedelta(hours=3))


def _oi_change(chart_index, oi) -> np.ndarray:
    if oi is None or len(oi) == 0:
        return np.full(len(chart_index), np.nan)
    now = _hourly_at_close(chart_index, oi.index, oi["oi"].to_numpy(), pd.Timedelta(hours=3))
    prev = np.r_[np.nan, now[:-1]]
    with np.errstate(invalid="ignore", divide="ignore"):
        return now / prev - 1.0


def features(ctx: Ctx, p: Params) -> Feat:
    df = ctx.df
    o, h, l, c, v = (df[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    pdi, mdi, adx = ta.dmi(h, l, c, 14, 14)
    _, _, hist = ta.macd(c, 12, 26, 9)
    a = ta.atr(h, l, c, 14)
    with np.errstate(divide="ignore", invalid="ignore"):
        rvol = v / ta.sma(v, 20)
        atr_pct = a / c
    vol_rank = percentrank(atr_pct, p.vol_rank_len)
    nan = np.full(len(c), np.nan)
    t1 = nan if ctx.htf1 is None else align(df.index, ctx.htf1.index, trend_state(ctx.htf1))
    t2 = nan if ctx.htf2 is None else align(df.index, ctx.htf2.index, trend_state(ctx.htf2))
    if ctx.ltf is not None and len(ctx.ltf) > 0:
        L = ctx.ltf
        lm = _ltf_at_close(df.index, L, _momentum_state(L))
        ls = _ltf_at_close(df.index, L, structure_state(*(L[k].to_numpy(float) for k in ("high", "low", "close", "open")), 5, 3))
    else:
        lm = ls = nan
    fz = _funding_z(df.index, ctx.funding) if ctx.is_crypto else nan
    bz = _basis_z(df.index, ctx.perp, ctx.spot1h) if ctx.is_crypto else nan
    oc = _oi_change(df.index, ctx.oi) if ctx.is_crypto else nan
    return Feat(df.index, o, h, l, c, v, a, ta.ema(c, 21), ta.rsi(c, 14), hist, pdi, mdi, adx,
                rvol, vol_rank, t1, t2, lm, ls, fz, bz, oc, ctx.vol_ok, ctx.is_crypto)


def percentrank(x: np.ndarray, n: int) -> np.ndarray:
    """ta.percentrank: % of the previous n values that are <= the current value."""
    out = np.full(len(x), np.nan)
    for i in range(n, len(x)):
        w = x[i - n:i]
        if np.isnan(x[i]) or np.isnan(w).any():
            continue
        out[i] = 100.0 * np.count_nonzero(w <= x[i]) / n
    return out


def breaks(f: Feat, p: Params) -> pd.DataFrame:
    """Every MTF structure break with its class and every candidate condition."""
    ph, pl = ta.pivots(f.h, f.l, p.pivot_left, p.pivot_right)
    sh = sl = np.nan
    sh_used = sl_used = True
    trend = 0
    n = len(f.c)
    struct = np.zeros(n)
    sweep_up = np.zeros(n, bool)   # bullish sweep: wick below the swing low, close back above
    sweep_dn = np.zeros(n, bool)
    rows = []
    for i in range(n):
        if not np.isnan(ph[i]):
            sh, sh_used = ph[i], False
        if not np.isnan(pl[i]):
            sl, sl_used = pl[i], False
        if not np.isnan(sl) and f.l[i] < sl and f.c[i] > sl:
            sweep_up[i] = True
        if not np.isnan(sh) and f.h[i] > sh and f.c[i] < sh:
            sweep_dn[i] = True
        up = (not sh_used) and f.c[i] > sh
        dn = (not sl_used) and f.c[i] < sl
        if up and dn:
            up, dn = f.c[i] >= f.o[i], f.c[i] < f.o[i]
        if up or dn:
            d = 1 if up else -1
            rows.append((i, d, trend == -d, sh if up else sl))
            trend = d
            if up:
                sh_used = True
            else:
                sl_used = True
        struct[i] = trend
    f.extra["struct"] = struct
    t = pd.DataFrame(rows, columns=["i", "dir", "choch", "level"])
    if len(t) == 0:
        return t
    i = t["i"].to_numpy(int)
    d = t["dir"].to_numpy(int)

    # HTF context
    t1, t2 = f.t1[i], f.t2[i]
    a1, a2 = np.nan_to_num(t1 * d), np.nan_to_num(t2 * d)
    t["htf1"], t["htf2"] = t1, t2
    t["htf_bias"] = a1 + a2
    t["htf_against"] = (a1 < 0) | (a2 < 0)
    both = (a1 > 0) & ((a2 > 0) | np.isnan(t2))
    t["htf_with"] = np.where(p.strict_htf, both, (a1 + a2 >= 1) & ~t["htf_against"].to_numpy())
    choch = t["choch"].to_numpy(bool)
    against = t["htf_against"].to_numpy(bool)
    t["cls"] = np.where(against, np.where(choch, "counter_reversal", "counter_continuation"),
                        np.where(choch, "realignment", "continuation"))

    # evidence candidates
    t["momentum"] = np.where(d > 0, (f.rsi[i] > 50) & (f.hist[i] > 0), (f.rsi[i] < 50) & (f.hist[i] < 0))
    t["strength"] = (f.adx[i] >= p.adx_min) & np.where(d > 0, f.pdi[i] > f.mdi[i], f.mdi[i] > f.pdi[i])
    t["displacement"] = d * (f.c[i] - f.o[i]) >= p.disp_atr * f.atr[i]
    h2 = np.r_[np.nan, np.nan, f.h[:-2]]
    l2 = np.r_[np.nan, np.nan, f.l[:-2]]
    fvg_now = np.where(d > 0, f.l[i] > h2[i], f.h[i] < l2[i])
    fvg_prev = np.where(d > 0, f.l[np.maximum(i - 1, 0)] > h2[np.maximum(i - 1, 0)],
                        f.h[np.maximum(i - 1, 0)] < l2[np.maximum(i - 1, 0)])
    t["fvg"] = fvg_now | fvg_prev
    t["volume"] = (f.rvol[i] >= p.vol_mult) if f.vol_ok else False
    k = p.sweep_lookback
    cs_up, cs_dn = np.r_[0, np.cumsum(sweep_up)], np.r_[0, np.cumsum(sweep_dn)]
    lo = np.maximum(i - k, 0)
    t["sweep"] = np.where(d > 0, cs_up[i + 1] - cs_up[lo] > 0, cs_dn[i + 1] - cs_dn[lo] > 0)
    t["ltf_momentum"] = f.ltf_mom[i] == d
    t["ltf_available"] = ~np.isnan(f.ltf_mom[i])
    fz = f.funding_z[i]
    t["perp_ok"] = ~np.isnan(fz) & (d * np.nan_to_num(fz) < 1.0)
    t["perp_available"] = ~np.isnan(fz)
    bz = f.basis_z[i]
    t["basis_ok"] = ~np.isnan(bz) & (d * np.nan_to_num(bz) < 1.5)
    t["basis_available"] = ~np.isnan(bz)
    oc = f.oi_chg[i]
    t["oi_up"] = ~np.isnan(oc) & (np.nan_to_num(oc) > 0)
    t["oi_available"] = ~np.isnan(oc)

    # filters
    t["not_range"] = ~(f.adx[i] < p.range_adx)
    t["not_shock"] = ~(f.vol_rank[i] >= p.shock_rank)
    rng = f.h[i] - f.l[i]
    opp_wick = np.where(d > 0, f.h[i] - np.maximum(f.o[i], f.c[i]), np.minimum(f.o[i], f.c[i]) - f.l[i])
    spike = (opp_wick > p.spike_wick_atr * f.atr[i]) & (rng > 0)
    if f.vol_ok:
        spike &= f.rvol[i] >= 1.2
    t["not_spike_wick"] = ~spike
    dow = f.index[i].dayofweek
    t["not_weekend"] = ~(f.is_crypto & (dow >= 5))

    nxt = np.r_[f.c[1:], np.nan]
    with np.errstate(invalid="ignore"):
        t["accepted"] = d * (nxt[i] - t["level"].to_numpy()) > 0   # known at the close of i + 1
    t["atr"] = f.atr[i]
    t["warm"] = ~np.isnan(f.atr[i]) & ~np.isnan(f.rsi[i]) & ~np.isnan(f.hist[i]) & ~np.isnan(f.adx[i])
    return t


def _available(t: pd.DataFrame, f: Feat, conds: tuple) -> np.ndarray:
    """How many of the chosen evidence conditions can be evaluated on each break.

    Conditions in the same family count once (the family is met if any of them is).
    """
    fams = [fam for fam, members in FAMILIES.items() if any(m in conds for m in members)]
    avail = np.zeros(len(t))
    for fam in fams:
        if fam == "participation" and not f.vol_ok:
            continue
        if fam == "ltf":
            avail += t["ltf_available"].to_numpy(float)
            continue
        if fam == "positioning":
            col = {"perp_ok": "perp_available", "basis_ok": "basis_available", "oi_up": "oi_available"}
            have = np.zeros(len(t), bool)
            for m in FAMILIES["positioning"]:
                if m in conds:
                    have |= t[col[m]].to_numpy(bool)
            avail += have
            continue
        avail += 1
    return avail


def effective(p: Params, is_crypto: bool) -> tuple[tuple, tuple]:
    """Evidence and filters in force on this instrument (crypto-only items dropped elsewhere)."""
    keep = lambda xs: tuple(x for x in xs if is_crypto or x not in p.crypto_only)
    return keep(p.evidence), keep(p.filters)


def score(t: pd.DataFrame, f: Feat, p: Params) -> pd.DataFrame:
    t = t.copy()
    evidence, filters = effective(p, f.is_crypto)
    p = replace(p, evidence=evidence, filters=filters)
    fams = {fam: [m for m in members if m in p.evidence] for fam, members in FAMILIES.items()}
    met = np.zeros(len(t))
    codes = []
    for fam, members in fams.items():
        if not members:
            continue
        hit = np.zeros(len(t), bool)
        for m in members:
            hit |= t[m].to_numpy(bool)
        t[f"fam_{fam}"] = hit
        met += hit
    t["met"] = met
    t["available"] = _available(t, f, p.evidence)
    with np.errstate(invalid="ignore", divide="ignore"):
        t["frac"] = np.where(t["available"] > 0, t["met"] / t["available"], 0.0)
    ok = np.ones(len(t), bool)
    for flt in p.filters:
        ok &= t[flt].to_numpy(bool)
    t["passes_filters"] = ok
    return t


def classify(t: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Tiers + de-duplication. Returns signals (MAJOR / CONFIRMED) and WATCH rows.

    MAJOR      a class in p.major_classes (default: realignment), HTFs with it,
               evidence >= p.major (0 by default: evidence does not gate, see DESIGN_CHECK)
    CONFIRMED  a class in p.confirm_classes (default: continuation), HTFs with it,
               evidence >= p.confirm
    WATCH      counter-HTF reversal (MTF change of character against the HTFs): a possible
               HTF reversal developing. Not a signal; does not touch the cooldown.
    Breaks with the HTFs neither with nor against them (all flat), and counter-HTF
    continuations, produce nothing: the indicator stays neutral.
    The cooldown applies to MAJOR and CONFIRMED together, per direction.
    """
    t = t[t["warm"] & t["passes_filters"]]
    keep = []
    last_dir, last_i = 0, -10**9
    for idx, r in zip(t.index, t.itertuples(index=False)):
        if r.cls == "counter_reversal":
            keep.append((idx, "watch"))
            continue
        if r.cls not in p.major_classes + p.confirm_classes or not r.htf_with:
            continue
        if r.frac < p.confirm - 1e-9:
            continue
        if p.accept and not r.accepted:
            continue
        at = r.i + 1 if p.accept else r.i       # the candle on which the signal prints
        if r.dir == last_dir and at - last_i < p.cooldown:
            continue
        major = r.cls in p.major_classes and r.frac >= p.major - 1e-9
        keep.append((idx, "major" if major else "confirmed"))
        last_dir, last_i = r.dir, at
    if not keep:
        return t.iloc[:0].assign(tier=pd.Series(dtype=str))
    idx, tiers = zip(*keep)
    out = t.loc[list(idx)].copy()
    out["tier"] = list(tiers)
    out["break_i"] = out["i"]
    if p.accept:
        sig = out["tier"] != "watch"
        out.loc[sig, "i"] = out.loc[sig, "i"] + 1
    return out


def warnings(f: Feat) -> pd.DataFrame:
    """Early warnings from the LTF: the LTF structure turns against the MTF structure.

    Fires on the chart candle whose close first shows the LTF structure flipped against
    the MTF structure, once per MTF leg. Where no LTF data exists it falls back to the
    v1 rule (close back across EMA 21 with RSI and MACD turned) so every chart has one.
    """
    s = f.extra["struct"]
    rows = []
    leg, armed = 0, None
    for i in range(1, len(f.c)):
        if s[i] != s[i - 1]:
            leg += 1
        if s[i] == 0:
            continue
        d = -int(s[i])
        if not np.isnan(f.ltf_struct[i]):
            fire = f.ltf_struct[i] == d and f.ltf_struct[i - 1] != d
            src = "ltf"
        else:
            cross = d * (f.c[i] - f.ema[i]) > 0 and d * (f.c[i - 1] - f.ema[i - 1]) <= 0
            fire = cross and d * (f.rsi[i] - 50) > 0 and d * f.hist[i] > 0
            src = "mtf"
        if fire and armed != leg:
            rows.append((i, d, src))
            armed = leg
    return pd.DataFrame(rows, columns=["i", "dir", "source"])


def run(ctx: Ctx, p: Params):
    f = features(ctx, p)
    t = breaks(f, p)
    if len(t) == 0:
        return f, t, t.assign(tier=pd.Series(dtype=str)), warnings(f)
    t = score(t, f, p)
    return f, t, classify(t, p), warnings(f)


def with_(p: Params, **kw) -> Params:
    return replace(p, **kw)
