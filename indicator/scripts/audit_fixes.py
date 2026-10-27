"""Audit of two candidate fixes, decided on DEVELOPMENT data, then checked on FRESH symbols.

    python scripts/audit_fixes.py

Fix 1, weekly ladder. The 1W profile's HTF2 was the quarterly (3M) trend: an EMA21 of
quarterly candles, i.e. a ~5-year trend that needs 5.5 years of history to exist at all.
On BTC it never turns down inside a bear market, so every bearish weekly break was
"counter-HTF" and could not signal; and whether it exists depends on how much history the
exchange feed has (Binance BTC: not until 2023; Bitstamp/INDEX: since ~2017).
Candidate: 1W profile uses HTF1 = 1M only (HTF2 none).
RULE (fixed before running): adopt unless the dev-data mean r_h of 1W signals gets
significantly worse (90% month-cluster CI of new minus old entirely below 0).

Fix 2, acceptance. A break is signalled only if the NEXT candle also closes beyond the
broken level (signal prints on that candle; entry the candle after). Targets false
breakouts that are invalidated immediately.
RULE (fixed before running): adopt only if, pooled over the four timeframes on dev data,
mean r_h of all signals improves with a 90% month-cluster CI above 0 AND the signal count
falls by less than half.

Writes reports/AUDIT_FIXES.md and reports/audit_fixes.json.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hcmtf import data, engine as G, evaluate as E, study as St  # noqa: E402
from hcmtf.metrics import cluster_ci, random_baseline  # noqa: E402
from hcmtf.report2 import active_params  # noqa: E402
from hcmtf.universe import COST_BPS, FRESH, UNIVERSE  # noqa: E402
from screen_components import boot_diff  # noqa: E402

TFS = ["1H", "4H", "1D", "1W"]


def series_1w_no_htf2(asset):
    """1W series built with HTF2 removed (Fix 1)."""
    ctx = St.build_ctx(asset, "1W")
    if ctx is None:
        return None
    ctx.htf2 = None
    p = G.DEFAULTS["1W"]
    f = G.features(ctx, p)
    t = G.breaks(f, p)
    if len(t) == 0:
        return None
    s = St.Series(asset.symbol, asset.cls, asset.tier or asset.cls, "1W", COST_BPS[asset.cls], f, t,
                  G.warnings(f), E.bar_outcomes(f, E.HORIZON["1W"], COST_BPS[asset.cls]))
    return s


def invalidated(s, ev, k=3):
    """Share of signals where a close within k candles after the signal is back through the level."""
    out = []
    for i, d, lv in zip(ev["i"].to_numpy(int), ev["dir"].to_numpy(int), ev["level"].to_numpy(float)):
        w = s.f.c[i + 1:i + 1 + k]
        out.append(bool(len(w)) and bool((d * (w - lv) < 0).any()))
    return np.array(out, bool)


def collect(series, p, start=None, end=None):
    rows = []
    for s in series:
        ev = St.signals_for(s, p)
        ev = ev[ev["tier"].isin(["major", "confirmed"])]
        t = s.index[ev["i"].to_numpy(int)]
        m = np.ones(len(ev), bool)
        if start is not None:
            m &= t >= start
        if end is not None:
            m &= t < end
        ev = ev[m]
        if len(ev) == 0:
            continue
        inv = invalidated(s, ev)
        ev = St.tag(s, ev.assign(invalid3=inv))
        rows.append(ev)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def summ(ev, series=None, windows=None):
    if len(ev) == 0:
        return {"n": 0}
    m, lo, hi = cluster_ci(ev, "r_h")
    out = {"n": int(len(ev)), "mean_r": m, "lo": lo, "hi": hi,
           "precision": float((ev["barrier"] == 1).mean()), "false_pos": float((ev["barrier"] == -1).mean()),
           "invalid3": float(ev["invalid3"].mean()), "ret_pct": 100 * float(ev["ret_h"].mean())}
    if series is not None:
        rb = random_baseline(ev, {s.symbol: s for s in series}, windows, reps=200)
        out.update({"rand_mean_r": rb.get("rand_mean_r"), "p_value": rb.get("p_value")})
    return out


def main():
    UTC = lambda x: pd.Timestamp(x, tz="UTC")
    res = {"fix1": {}, "fix2": {}}
    # ---------------- Fix 1: weekly ladder ----------------
    for name, assets in (("dev", UNIVERSE), ("fresh", FRESH)):
        old = St.prepare("1W", assets)
        new = [x for x in (series_1w_no_htf2(a) for a in assets) if x is not None]
        p = active_params("1W")
        hold = UTC(St.HOLDOUT["1W"])
        start, end = UTC("2010-01-01"), (hold if name == "dev" else None)
        eo, en = collect(old, p, start, end), collect(new, p, start, end)
        res["fix1"][name] = {"old": summ(eo), "new": summ(en),
                             "diff": list(boot_diff(en.assign(time=en["time"]), eo)) if len(en) and len(eo) else None,
                             "old_bear": int((eo["dir"] < 0).sum()), "new_bear": int((en["dir"] < 0).sum()),
                             "old_bull": int((eo["dir"] > 0).sum()), "new_bull": int((en["dir"] > 0).sum())}
        print("fix1", name, res["fix1"][name], flush=True)
    d = res["fix1"]["dev"]["diff"]
    res["fix1"]["decision"] = "REJECT" if (d and d[2] < 0) else "ADOPT"

    # ---------------- Fix 2: acceptance ----------------
    pooled_old, pooled_new = [], []
    for tf in TFS:
        series = St.prepare(tf, UNIVERSE)
        hold = UTC(St.HOLDOUT[tf])
        base = active_params(tf)
        eo = collect(series, base, None, hold - St.PURGE[tf])
        en = collect(series, G.with_(base, accept=True), None, hold - St.PURGE[tf])
        pooled_old.append(eo)
        pooled_new.append(en)
        res["fix2"][tf] = {"old": summ(eo), "new": summ(en)}
        print("fix2", tf, res["fix2"][tf], flush=True)
    po, pn = pd.concat(pooled_old), pd.concat(pooled_new)
    diff = boot_diff(pn, po)
    res["fix2"]["pooled"] = {"old": summ(po), "new": summ(pn), "diff": list(diff)}
    ok = diff[1] > 0 and len(pn) > 0.5 * len(po)
    res["fix2"]["decision"] = "ADOPT" if ok else "REJECT"
    # fresh check, reported only
    fo, fn = [], []
    for tf in TFS:
        series = St.prepare(tf, FRESH)
        start = UTC(St.WINDOWS[tf][0][0])
        base = active_params(tf)
        fo.append(collect(series, base, start))
        fn.append(collect(series, G.with_(base, accept=True), start))
    res["fix2"]["fresh"] = {"old": summ(pd.concat(fo)), "new": summ(pd.concat(fn)),
                            "diff": list(boot_diff(pd.concat(fn), pd.concat(fo)))}
    print(json.dumps({k: res[k]["decision"] for k in res}, indent=1))
    (ROOT / "reports" / "audit_fixes.json").write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
