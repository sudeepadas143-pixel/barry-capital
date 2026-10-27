"""V4.1: H6 (HTF trend state), H7 (compression -> expansion), H1r (break increment over state).

Implements reports/V4_1_PREREGISTRATION.md exactly; section numbers below refer to it.
Reads hcmtf (engine, htf, evaluate, data, metrics) and never modifies it.

    python scripts/v41_run.py D      # stage D: the 70 seen symbols (exploratory)
    python scripts/v41_run.py H      # stage H: the 38 holdout instruments (decisions)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hcmtf import data, engine as G, evaluate as E, ta
from hcmtf.htf import align, trend_state
from hcmtf.universe import COST_BPS

from . import universe41  # noqa: F401  (registers holdout instruments for hcmtf.data)

TFS = ["1H", "4H", "1D", "1W"]
H = dict(E.HORIZON)                                   # §3 primary: 1H 24, 4H 30, 1D 20, 1W 13
H_SHORT = {tf: max(H[tf] // 4, 3) for tf in TFS}
H_LONG = {tf: 2 * H[tf] for tf in TFS}
START = {"1H": "2020-01-01", "4H": "2020-01-01", "1D": "2010-01-01", "1W": "2010-01-01"}
K_COMP = {"1H": 24, "4H": 12, "1D": 10, "1W": 6}       # §4 H7 minimum compressed run
CLUSTER_MONTHS = {"1H": 1, "4H": 2, "1D": 3, "1W": 12}  # §5
ROC_N = 20
LOW, HIGH = 100 / 3, 200 / 3
GROUPS = {"crypto": ("crypto",), "equities": ("equity", "equity_index"), "commodities": ("commodity",),
          "rates_fx": ("bond", "fx")}
MEI = {"r": 0.10, "rvr": 0.05}
REPS = 5000
SEED = 20261027


def group_of(cls: str) -> str:
    return next(g for g, m in GROUPS.items() if cls in m)


# ----------------------------------------------------------------------------- definitions

def state_rel(t1: np.ndarray, t2: np.ndarray, d: int) -> np.ndarray:
    """§2: 'with' / 'against' / 'neutral' for side d, exactly as engine.breaks."""
    a1, a2 = np.nan_to_num(t1 * d), np.nan_to_num(t2 * d)
    against = (a1 < 0) | (a2 < 0)
    with_ = (a1 + a2 >= 1) & ~against
    return np.where(against, "against", np.where(with_, "with", "neutral"))


def vol_tercile(vol_rank: np.ndarray) -> np.ndarray:
    """0 low / 1 mid / 2 high / -1 undefined, from engine.percentrank of ATR% (200)."""
    out = np.full(len(vol_rank), -1, np.int8)
    ok = ~np.isnan(vol_rank)
    out[ok] = np.where(vol_rank[ok] < LOW, 0, np.where(vol_rank[ok] < HIGH, 1, 2))
    return out


def compression_events(h, l, c, vol_rank, k: int) -> pd.DataFrame:
    """§4 H7: first close outside the box of a >= k-candle compressed run (ATR%-pct < 33.3).

    Box = highest high / lowest low of the run (its first candle to t-1). After an event the
    run restarts at t+1. Uses only data up to the close of t.
    """
    comp = np.nan_to_num(vol_rank, nan=100.0) < LOW
    rows = []
    run, hi, lo = 0, -np.inf, np.inf
    for t in range(len(c)):
        if run >= k:
            d = 1 if c[t] > hi else -1 if c[t] < lo else 0
            if d:
                rows.append((t, d, hi, lo, run))
                run, hi, lo = 0, -np.inf, np.inf
                continue
        if comp[t]:
            if run == 0:
                hi, lo = -np.inf, np.inf
            run += 1
            hi, lo = max(hi, h[t]), min(lo, l[t])
        else:
            run, hi, lo = 0, -np.inf, np.inf
    return pd.DataFrame(rows, columns=["i", "dir", "box_hi", "box_lo", "run"])


def roc_events(c: np.ndarray, rel_b: np.ndarray, rel_s: np.ndarray, n: int = ROC_N) -> pd.DataFrame:
    """§4 H1r M: ROC(n) changes sign to d while in the side-d state."""
    roc = np.full(len(c), np.nan)
    roc[n:] = c[n:] / c[:-n] - 1.0
    s = np.sign(roc)
    ps = np.r_[np.nan, s[:-1]]
    rows = []
    for d, rel in ((1, rel_b), (-1, rel_s)):
        i = np.flatnonzero((s == d) & (ps != d) & ~np.isnan(ps) & (rel == "with"))
        rows.append(pd.DataFrame({"i": i, "dir": d}))
    return pd.concat(rows, ignore_index=True)


def fwd_mean(x: np.ndarray, h: int) -> np.ndarray:
    """mean of x[t+1 .. t+h] (NaN where incomplete)."""
    n = len(x)
    cs = np.r_[0.0, np.cumsum(np.nan_to_num(x))]
    out = np.full(n, np.nan)
    t = np.arange(n - h)
    out[t] = (cs[t + h + 1] - cs[t + 1]) / h
    return out


# ------------------------------------------------------------------------- per instrument

JUMP = 20.0   # amendment 1


def integrity_cut(symbol: str):
    """Amendment 1: first day whose next daily open is > 20x or < 1/20 of its open (a token swap or
    relisting, e.g. LUNAUSDT 2022-05-12), or None. The instrument is used only before that day."""
    d1 = data.load(symbol, "1D")
    o = d1["open"].to_numpy(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        jump = np.abs(np.log(o[1:] / o[:-1])) > np.log(JUMP)
    k = np.flatnonzero(jump)
    return d1.index[k[0]] if len(k) else None


def cluster_id(idx: pd.DatetimeIndex, tf: str) -> np.ndarray:
    m = (idx.year.to_numpy() - 1970) * 12 + idx.month.to_numpy() - 1
    return (m // CLUSTER_MONTHS[tf]).astype(np.int32)


def one(args):
    """All units and benchmark aggregates for one instrument × TF. None if excluded (§1)."""
    asset, tf = args
    try:
        df = data.load(asset.symbol, tf)
        _, h1tf, h2tf = G.LADDER[tf]
        h1, h2 = data.load(asset.symbol, h1tf), data.load(asset.symbol, h2tf)
    except Exception as e:  # download failure → excluded and listed
        return {"excluded": f"{asset.symbol} {tf}: {type(e).__name__}: {e}"[:200]}
    cut = integrity_cut(asset.symbol)
    if cut is not None:   # amendment 1: token swap / relisting → stop the series the day before
        df, h1, h2 = df[df.index < cut], h1[h1.index < cut], h2[h2.index < cut]
    start = max(pd.Timestamp(START[tf], tz="UTC"), df.index[0])
    inwin = np.asarray(df.index >= start)
    if inwin.sum() < 300:
        return {"excluded": f"{asset.symbol} {tf}: {int(inwin.sum())} candles in window (< 300)"}
    cost = COST_BPS[asset.cls]
    ctx = G.Ctx(df, h1, h2, None, asset.volume, asset.cls == "crypto")
    p = G.DEFAULTS[tf]
    f = G.features(ctx, p)
    n = len(f.c)
    idx = f.index
    tabs = {"r": E.bar_outcomes(f, H[tf], cost), "rs": E.bar_outcomes(f, H_SHORT[tf], cost),
            "rl": E.bar_outcomes(f, H_LONG[tf], cost)}
    elig = inwin & ~np.isnan(f.atr) & ~np.isnan(f.t1) & ~np.isnan(tabs["r"][1]["r_h"])
    vt = vol_tercile(f.vol_rank)
    yr = idx.year.to_numpy().astype(np.int16)
    cl = cluster_id(idx, tf)
    hh = H[tf]
    t_ns = idx.as_unit("ns").asi8         # pandas 3 may store s/us: compare in ns everywhere
    t_end = np.full(n, np.iinfo(np.int64).max)
    t_end[: n - hh] = t_ns[hh:]
    rel = {1: state_rel(f.t1, f.t2, 1), -1: state_rel(f.t1, f.t2, -1)}
    # lagged state: HTF1 trend one more completed HTF1 candle back (§4 secondary)
    ts1 = trend_state(h1)
    t1lag = align(idx, h1.index, np.r_[np.nan, ts1[:-1]])
    rel_lag = {1: state_rel(t1lag, f.t2, 1), -1: state_rel(t1lag, f.t2, -1)}
    # H7 direction-free outcomes
    tr = ta.true_range(f.h, f.l, f.c, True)
    with np.errstate(divide="ignore", invalid="ignore"):
        rvr = np.log(fwd_mean(tr, hh) / f.atr)
        o_next = np.r_[f.o[1:], np.nan]
        c_h = np.full(n, np.nan)
        c_h[: n - hh] = f.c[hh:]
        mag = np.abs(c_h - o_next) / f.atr
    comp = vt == 0

    units = []

    def add(name, i, d, vals: dict, extra: dict | None = None):
        i = np.asarray(i, int)
        if len(i) == 0:
            return
        d = np.broadcast_to(np.asarray(d, np.int8), i.shape)
        u = pd.DataFrame({"set": name, "i": i, "side": d, "cl": cl[i], "t": t_ns[i], "t_end": t_end[i],
                          "vt": vt[i], "yr": yr[i]})
        for k, v in vals.items():
            u[k] = v
        for k, v in (extra or {}).items():
            u[k] = v
        units.append(u)

    def side_vals(i, d):
        out = {}
        for k, tab in tabs.items():
            out[k] = np.where(d > 0, tab[1]["r_h"][i], tab[-1]["r_h"][i]).astype(np.float32)
        out["mfe"] = np.where(d > 0, tabs["r"][1]["mfe"][i], tabs["r"][-1]["mfe"][i]).astype(np.float32)
        out["mae"] = np.where(d > 0, tabs["r"][1]["mae"][i], tabs["r"][-1]["mae"][i]).astype(np.float32)
        return out

    for d in (1, -1):
        st = elig & (rel[d] == "with")
        i = np.flatnonzero(st)
        add("state", i, d, side_vals(i, np.full(len(i), d)))
        prev = np.r_[False, (rel[d] == "with")[:-1]]
        i = np.flatnonzero(st & ~prev)
        add("onset", i, d, side_vals(i, np.full(len(i), d)))
        i = np.flatnonzero(elig & (rel_lag[d] == "with"))
        add("state_lag", i, d, side_vals(i, np.full(len(i), d)))

    # H7 events
    ev = compression_events(f.h, f.l, f.c, f.vol_rank, K_COMP[tf])
    ev = ev[elig[ev["i"].to_numpy(int)] & ~np.isnan(rvr[ev["i"].to_numpy(int)])] if len(ev) else ev
    if len(ev):
        i, d = ev["i"].to_numpy(int), ev["dir"].to_numpy(int)
        # secondary exit: first close back inside the box, else H
        rinv = np.empty(len(i))
        for j, (ii, dd, bh, bl) in enumerate(zip(i, d, ev["box_hi"], ev["box_lo"])):
            px, a = f.o[ii + 1], f.atr[ii]
            ex = f.c[ii + hh]
            for k in range(ii + 1, ii + hh + 1):
                if bl <= f.c[k] <= bh:
                    ex = f.c[k]
                    break
            rinv[j] = (dd * (ex - px) - cost / 1e4 * px) / a
        v = side_vals(i, d)
        add("h7", i, d, v, {"rvr": rvr[i].astype(np.float32), "mag": mag[i].astype(np.float32),
                             "rinv": rinv.astype(np.float32)})

    # H1r: state + structure break (engine.breaks, shipped DEFAULTS, no evidence/filters)
    trig = G.breaks(f, p)
    if len(trig):
        trig = trig[trig["warm"] & trig["htf_with"] & trig["cls"].isin(["continuation", "realignment"])]
        trig = trig[elig[trig["i"].to_numpy(int)]]
        for name, sub in (("B", trig), ("Bcont", trig[trig["cls"] == "continuation"]),
                          ("Breal", trig[trig["cls"] == "realignment"])):
            i, d = sub["i"].to_numpy(int), sub["dir"].to_numpy(int)
            add(name, i, d, side_vals(i, d))
    m = roc_events(f.c, rel[1], rel[-1])
    m = m[elig[m["i"].to_numpy(int)]]
    add("M", m["i"].to_numpy(int), m["dir"].to_numpy(int), side_vals(m["i"].to_numpy(int), m["dir"].to_numpy(int)))

    U = pd.concat(units, ignore_index=True) if units else pd.DataFrame()

    # benchmark aggregates (§4): sums and counts per side, kind, stratum and cluster
    bench = []
    e = np.flatnonzero(elig)

    def agg(kind, side, val, value, mask, stratum):
        j = e[mask[e]] if mask is not None else e
        x = value[j]
        ok = ~np.isnan(x)
        j, x = j[ok], x[ok]
        if len(j) == 0:
            return
        b = pd.DataFrame({"st": stratum[j], "cl": cl[j], "x": x}).groupby(["st", "cl"])["x"].agg(["sum", "count"]).reset_index()
        b["kind"], b["side"], b["val"] = kind, side, val
        bench.append(b)

    zero = np.zeros(n, np.int32)
    for d in (1, -1):
        for k, tab in tabs.items():
            r = tab[d]["r_h"]
            agg("U", d, k, r, None, zero)
            agg("S", d, k, r, rel[d] == "with", zero)
            if k == "r":
                agg("V", d, k, r, vt >= 0, vt.astype(np.int32))
                agg("Y", d, k, r, None, yr.astype(np.int32))
                agg("L", d, k, r, comp, zero)
    for k, v in (("rvr", rvr), ("mag", mag)):
        agg("L", 0, k, v, comp, zero)
        agg("U", 0, k, v, None, zero)
    B = pd.concat(bench, ignore_index=True)

    # H6 trading view (§4): open-to-open, position from the previous close, daily log returns
    daily = {}
    oo = np.r_[f.o[1:] / f.o[:-1] - 1.0, np.nan]
    half = cost / 2e4
    for d in (1, -1):
        pos_state = np.r_[0.0, (rel[d] == "with")[:-1].astype(float) * d]
        pos_static = np.full(n, float(d))
        for name, pos in (("timed", pos_state), ("static", pos_static)):
            pos = np.where(inwin, pos, 0.0)
            chg = np.abs(np.diff(np.r_[0.0, pos]))
            r = np.maximum(np.nan_to_num(pos * oo) - chg * half, -0.9999)
            rr = pd.Series(np.log1p(r[inwin]), index=idx[inwin])
            daily[(d, name)] = rr.groupby(rr.index.normalize()).sum()
    return {"symbol": asset.symbol, "group": group_of(asset.cls), "tf": tf, "units": U, "bench": B,
            "integrity_cut": None if cut is None else str(cut.date()),
            "start": int(start.value), "end": int(idx[-1].value), "daily": daily,
            "n_window": int(inwin.sum()), "n_elig": int(elig.sum())}


# ------------------------------------------------------------------------------ statistics

def boot_excess(units: pd.DataFrame, bench: pd.DataFrame, value: str, stratum: str | None,
                W: np.ndarray, clusters: np.ndarray):
    """Mean excess of units over their (instrument, stratum) benchmark, with the benchmark
    re-estimated from the same resampled clusters in every replicate (§5).

    units: columns sym, cl, [stratum], value. bench: sym, st, cl, sum, count.
    W: (reps, C) cluster multiplicities; clusters: the C cluster ids (column order of W).
    Returns (replicate means, point estimate, per-unit point excess).
    """
    cpos = {c: j for j, c in enumerate(clusters)}
    ukey = units["sym"].astype(str) + "|" + (units[stratum].astype(str) if stratum else "0")
    bkey = bench["sym"].astype(str) + "|" + bench["st"].astype(str)
    keys = pd.Index(sorted(set(ukey)))
    K, C = len(keys), len(clusters)
    ES, EN, BS, BN = (np.zeros((K, C)) for _ in range(4))
    uk, uc = keys.get_indexer(ukey), units["cl"].map(cpos).to_numpy()
    x = units[value].to_numpy(float)
    np.add.at(ES, (uk, uc), x)
    np.add.at(EN, (uk, uc), 1.0)
    bk = keys.get_indexer(bkey)
    ok = bk >= 0
    bc = bench["cl"].map(cpos).to_numpy()
    ok &= ~np.isnan(bc.astype(float))
    np.add.at(BS, (bk[ok], bc[ok].astype(int)), bench["sum"].to_numpy(float)[ok])
    np.add.at(BN, (bk[ok], bc[ok].astype(int)), bench["count"].to_numpy(float)[ok])

    def stat(w):
        bn = w @ BN.T
        with np.errstate(invalid="ignore", divide="ignore"):
            bm = (w @ BS.T) / bn
        en = w @ EN.T
        num = w @ ES.T - en * bm
        good = bn > 0
        num, en = np.where(good, num, 0.0), np.where(good, en, 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            return num.sum(-1) / en.sum(-1)

    point = float(stat(np.ones((1, C)))[0])
    reps = stat(W) if W is not None else None
    bm_point = BS.sum(1) / np.where(BN.sum(1) > 0, BN.sum(1), np.nan)
    per_unit = x - bm_point[uk]
    return reps, point, per_unit


def weights(clusters: np.ndarray, reps: int = REPS, seed: int = SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    C = len(clusters)
    W = np.zeros((reps, C))
    pick = rng.integers(0, C, (reps, C))
    for r in range(reps):
        W[r] = np.bincount(pick[r], minlength=C)
    return W
