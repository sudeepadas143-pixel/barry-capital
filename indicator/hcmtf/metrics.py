"""Summary statistics with honest uncertainty.

Events from different symbols on the same dates are not independent (crypto moves
together, so do equities in a sell-off). Confidence intervals therefore come from a
cluster bootstrap that resamples whole calendar months, not individual events.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import evaluate as E

RNG_SEED = 20261027


def cluster_ci(ev: pd.DataFrame, col: str, reps: int = 2000, seed: int = RNG_SEED):
    """Mean of ``col`` with a 95% month-cluster bootstrap interval."""
    if len(ev) == 0:
        return np.nan, np.nan, np.nan
    x = ev[col].to_numpy(float)
    months = ev["time"].dt.tz_localize(None).dt.to_period("M").astype(str).to_numpy()
    uniq, inv = np.unique(months, return_inverse=True)
    sums = np.bincount(inv, weights=x, minlength=len(uniq))
    cnts = np.bincount(inv, minlength=len(uniq)).astype(float)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(uniq), size=(reps, len(uniq)))
    s = sums[pick].sum(1)
    c = cnts[pick].sum(1)
    boot = s / np.where(c == 0, np.nan, c)
    lo, hi = np.nanpercentile(boot, [2.5, 97.5])
    return float(x.mean()), float(lo), float(hi)


def summary(ev: pd.DataFrame, symbol_years: float | None = None) -> dict:
    n = len(ev)
    if n == 0:
        return {"n": 0}
    m, lo, hi = cluster_ci(ev, "r_h")
    pm, plo, phi = cluster_ci(ev.assign(hit=(ev["barrier"] == 1).astype(float)), "hit")
    out = {
        "n": n,
        "per_sym_yr": n / symbol_years if symbol_years else np.nan,
        "precision": pm, "precision_lo": plo, "precision_hi": phi,
        "false_pos": float((ev["barrier"] == -1).mean()),
        "win_h": float((ev["ret_h"] > 0).mean()),
        "mean_r": m, "mean_r_lo": lo, "mean_r_hi": hi,
        "mean_ret_pct": 100 * float(ev["ret_h"].mean()),
        "mfe_med": float(ev["mfe"].median()), "mae_med": float(ev["mae"].median()),
        "long_share": float((ev["dir"] > 0).mean()),
    }
    return out


def random_baseline(ev: pd.DataFrame, series_by_symbol: dict, windows: list, reps: int = 500,
                    seed: int = RNG_SEED) -> dict:
    """Random entries: same symbol, same window, same count, same long/short mix.

    Returns the distribution of the pooled mean r_h and precision, and the one-sided
    p-value of the observed mean r_h (share of random draws at least as good).
    """
    rng = np.random.default_rng(seed)
    if len(ev) == 0:
        return {}
    groups = []
    for sym, g in ev.groupby("symbol"):
        s = series_by_symbol[sym]
        t = s.index
        for a, b in windows:
            gg = g[(g["time"] >= a) & (g["time"] < b)]
            if len(gg) == 0:
                continue
            ok = np.where((t >= a) & (t < b) & ~np.isnan(s.table[1]["r_h"]))[0]
            if len(ok) == 0:
                continue
            groups.append((s, ok, gg["dir"].to_numpy(int)))
    means, precs = np.empty(reps), np.empty(reps)
    for r in range(reps):
        tot_r = tot_h = cnt = 0.0
        for s, ok, dirs in groups:
            i = rng.choice(ok, size=len(dirs), replace=len(dirs) > len(ok))
            d = rng.permutation(dirs)
            rr = np.where(d > 0, s.table[1]["r_h"][i], s.table[-1]["r_h"][i])
            bb = np.where(d > 0, s.table[1]["barrier"][i], s.table[-1]["barrier"][i])
            tot_r += rr.sum()
            tot_h += (bb == 1).sum()
            cnt += len(d)
        means[r], precs[r] = tot_r / cnt, tot_h / cnt
    obs = ev["r_h"].mean()
    obs_p = (ev["barrier"] == 1).mean()
    return {
        "rand_mean_r": float(means.mean()), "rand_mean_r_p95": float(np.percentile(means, 95)),
        "rand_precision": float(precs.mean()),
        "p_value": float((1 + (means >= obs).sum()) / (reps + 1)),
        "p_value_precision": float((1 + (precs >= obs_p).sum()) / (reps + 1)),
    }


def symbol_years(series, windows) -> float:
    tot = 0.0
    for s in series:
        t = s.index
        for a, b in windows:
            m = (t >= a) & (t < b)
            if m.any():
                tot += (t[m][-1] - t[m][0]).total_seconds() / (365.25 * 86400)
    return tot


def holm(pvals: dict) -> dict:
    """Holm-Bonferroni adjusted p-values."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for k, (name, p) in enumerate(items):
        running = max(running, min(1.0, (m - k) * p))
        out[name] = running
    return out


# ----------------------------------------------------------------- trade simulation


def portfolio(series, events_by_symbol: dict, windows: list, max_hold: int) -> dict:
    """Equal-weight portfolio of per-symbol strategies, marked to market daily.

    Each symbol trades its own signals with evaluate.simulate. Daily returns are the
    average across symbols that had a bar that day. Only the test windows count.
    """
    daily, trades = [], []
    for s in series:
        ev = events_by_symbol.get(s.symbol)
        if ev is None or len(ev) == 0:
            continue
        t = E.simulate(ev, s.f, s.cost, max_hold)
        # a position cannot lose more than the capital behind it (a short through a
        # several-fold squeeze would otherwise go below -100%)
        r = np.maximum(E.bar_returns(t, s.f, s.cost), -0.9999)
        mask = np.zeros(len(r), bool)
        for a, b in windows:
            mask |= (s.index >= a) & (s.index < b)
        rr = pd.Series(np.log1p(r[mask]), index=s.index[mask])
        daily.append(rr.groupby(rr.index.normalize()).sum().rename(s.symbol))
        entry_t = s.index[t["entry_i"].to_numpy(int)]
        inwin = np.zeros(len(t), bool)
        for a, b in windows:
            inwin |= (entry_t >= a) & (entry_t < b)
        trades.append(t[inwin].assign(symbol=s.symbol))
    return _perf(daily, pd.concat(trades) if trades else pd.DataFrame(columns=["ret"]))


def buy_hold(series, windows: list) -> dict:
    daily = []
    for s in series:
        r = np.r_[0.0, s.f.c[1:] / s.f.c[:-1] - 1.0]
        mask = np.zeros(len(r), bool)
        for a, b in windows:
            mask |= (s.index >= a) & (s.index < b)
        rr = pd.Series(np.log1p(r[mask]), index=s.index[mask])
        daily.append(rr.groupby(rr.index.normalize()).sum().rename(s.symbol))
    return _perf(daily, None)


def _perf(daily: list, trades) -> dict:
    if not daily:
        return {}
    df = pd.concat(daily, axis=1).sort_index()
    port = np.expm1(df).mean(axis=1, skipna=True).fillna(0.0)
    eq = (1 + port).cumprod()
    years = max((port.index[-1] - port.index[0]).days / 365.25, 1e-9)
    ann = 365.25 / max(np.median(np.diff(port.index.values).astype("timedelta64[D]").astype(float)), 1)
    ann = min(ann, 365.25)
    sharpe = port.mean() / port.std() * np.sqrt(ann) if port.std() > 0 else np.nan
    # 95% interval for Sharpe from a moving-block bootstrap of the daily returns
    rng = np.random.default_rng(RNG_SEED)
    x = port.to_numpy()
    blk = 20
    nb = int(np.ceil(len(x) / blk))
    sh = []
    for _ in range(500):
        st = rng.integers(0, max(len(x) - blk, 1), nb)
        y = np.concatenate([x[k:k + blk] for k in st])[:len(x)]
        sh.append(y.mean() / y.std() * np.sqrt(ann) if y.std() > 0 else np.nan)
    out = {
        "cagr": float(eq.iloc[-1] ** (1 / years) - 1),
        "vol": float(port.std() * np.sqrt(ann)),
        "sharpe": float(sharpe),
        "sharpe_lo": float(np.nanpercentile(sh, 2.5)), "sharpe_hi": float(np.nanpercentile(sh, 97.5)),
        "max_dd": float((eq / eq.cummax() - 1).min()),
    }
    if trades is not None and len(trades):
        r = trades["ret"].to_numpy()
        out.update({
            "trades": int(len(r)), "win": float((r > 0).mean()), "avg_trade_pct": float(100 * r.mean()),
            "profit_factor": float(r[r > 0].sum() / -r[r < 0].sum()) if (r < 0).any() else np.inf,
            "avg_bars": float(trades["bars"].mean()),
        })
    return out


def score_curve(trig: pd.DataFrame) -> pd.DataFrame:
    """Out-of-sample outcome by score, over ALL triggers (no threshold applied).

    If the score carries information, mean r_h and precision should rise with it.
    """
    t = trig.copy()
    t["bucket"] = pd.cut(t["frac"], [-0.01, 0.34, 0.5, 0.67, 0.84, 1.0],
                         labels=["0-33%", "34-50%", "51-67%", "68-84%", "85-100%"])
    rows = []
    for b, g in t.groupby("bucket", observed=True):
        m, lo, hi = cluster_ci(g, "r_h")
        rows.append({"score": str(b), "n": len(g), "mean_r": m, "lo": lo, "hi": hi,
                     "precision": float((g["barrier"] == 1).mean())})
    return pd.DataFrame(rows)


def component_lift(trig: pd.DataFrame, components: list[str]) -> pd.DataFrame:
    """Mean r_h of triggers with vs without each condition (out of sample)."""
    rows = []
    for k in components:
        a, b = trig[trig[k]], trig[~trig[k]]
        if len(a) < 10 or len(b) < 10:
            continue
        ma, la, ha = cluster_ci(a, "r_h")
        mb, _, _ = cluster_ci(b, "r_h")
        rows.append({"condition": k, "n_with": len(a), "mean_r_with": ma, "ci_with": f"[{la:+.2f}, {ha:+.2f}]",
                     "n_without": len(b), "mean_r_without": mb, "diff": ma - mb})
    return pd.DataFrame(rows)


def boot_diff(a: pd.DataFrame, b: pd.DataFrame, reps: int = 1000, seed: int = 7):
    """Difference of mean r_h (a - b) with a 90% month-cluster bootstrap interval."""
    if len(a) < 20 or len(b) < 20:
        return np.nan, np.nan, np.nan
    allm = pd.concat([a.assign(g=1), b.assign(g=0)])
    m = allm["time"].dt.tz_localize(None).dt.to_period("M").astype(str).to_numpy()
    u, inv = np.unique(m, return_inverse=True)
    x = allm["r_h"].to_numpy()
    g = allm["g"].to_numpy()
    sa = np.bincount(inv, weights=x * g, minlength=len(u))
    na = np.bincount(inv, weights=g, minlength=len(u))
    sb = np.bincount(inv, weights=x * (1 - g), minlength=len(u))
    nb = np.bincount(inv, weights=1 - g, minlength=len(u))
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(u), (reps, len(u)))
    with np.errstate(invalid="ignore", divide="ignore"):
        d = sa[pick].sum(1) / na[pick].sum(1) - sb[pick].sum(1) / nb[pick].sum(1)
    lo, hi = np.nanpercentile(d, [5, 95])
    return float(a["r_h"].mean() - b["r_h"].mean()), float(lo), float(hi)
