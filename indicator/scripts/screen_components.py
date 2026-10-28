"""Screen every candidate component on DEVELOPMENT data only. Run once.

    python scripts/screen_components.py

Population: every warm MTF structure break on the DEV symbols (universe.UNIVERSE),
dated before the holdout start of its timeframe, excluding counter-HTF continuations
(which can never signal). FRESH symbols are not loaded.

For each yes/no candidate: diff = mean r_h of breaks WITH it minus breaks WITHOUT it.
90% intervals from a month-cluster bootstrap. Done separately for crypto and non-crypto.

DECISION RULE (fixed before the first run; applied mechanically below):

  KEEP (all assets)   crypto pooled-over-timeframes diff > 0 with 90% CI above 0,
                      AND diff > 0 on at least 3 of the 4 timeframes (crypto),
                      AND non-crypto pooled diff not significantly negative (CI upper >= 0).
  KEEP (crypto only)  the two crypto tests pass but non-crypto IS significantly negative.
  DROP                otherwise.

  Perp features (perp_ok, basis_ok, oi_up) can only be KEEP (crypto only) or DROP.
  Filters are screened the same way, "with" meaning the break passes the filter.
  Counter-HTF reversal MAJOR path: the sweep requirement is kept only if, among
  counter-HTF reversals, sweep diff passes the crypto tests; if the counter-reversal
  class as a whole has a negative crypto mean r_h whatever the sweep, the path is closed
  (counter-HTF reversals can be CONFIRMED but never MAJOR).
  Families: if two kept conditions from different families have |phi| > 0.5 on these
  breaks, they are merged into one family (counted once).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf import engine as G, evaluate as E, study as St  # noqa: E402
from hcmtf.universe import UNIVERSE  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "reports"
EVIDENCE = ["momentum", "strength", "displacement", "fvg", "volume", "sweep", "ltf_momentum",
            "perp_ok", "basis_ok", "oi_up"]
PERP = {"perp_ok": "perp_available", "basis_ok": "basis_available", "oi_up": "oi_available"}
FILTERS = G.FILTERS
TFS = ["1H", "4H", "1D", "1W"]
SEED = 7


def boot_diff(a: pd.DataFrame, b: pd.DataFrame, reps: int = 1000):
    """diff of means (a - b) with a 90% month-cluster bootstrap interval."""
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
    rng = np.random.default_rng(SEED)
    pick = rng.integers(0, len(u), (reps, len(u)))
    with np.errstate(invalid="ignore", divide="ignore"):
        d = sa[pick].sum(1) / na[pick].sum(1) - sb[pick].sum(1) / nb[pick].sum(1)
    lo, hi = np.nanpercentile(d, [5, 95])
    return float(a["r_h"].mean() - b["r_h"].mean()), float(lo), float(hi)


def load_breaks() -> pd.DataFrame:
    rows = []
    for tf in TFS:
        series = St.prepare(tf, UNIVERSE)
        hold = pd.Timestamp(St.HOLDOUT[tf], tz="UTC")
        for s in series:
            t = s.trig[s.trig["warm"] & (s.trig["cls"] != "counter_continuation")]
            t = St.tag(s, t)
            t = t[t["time"] < hold - St.PURGE[tf]]
            t["tf"] = tf
            rows.append(t)
        print(f"[{tf}] {sum(len(r) for r in rows if (r['tf'] == tf).all())} breaks", flush=True)
    return pd.concat(rows, ignore_index=True)


def screen(B: pd.DataFrame, col: str, mask_avail: str | None = None) -> dict:
    out = {}
    for grp, sub in (("crypto", B[B["cls_asset"] == "crypto"]), ("other", B[B["cls_asset"] != "crypto"])):
        if mask_avail:
            sub = sub[sub[mask_avail]]
        res = {"pooled": boot_diff(sub[sub[col]], sub[~sub[col]]), "n_with": int(sub[col].sum()),
               "n_without": int((~sub[col]).sum())}
        for tf in TFS:
            s2 = sub[sub["tf"] == tf]
            res[tf] = boot_diff(s2[s2[col]], s2[~s2[col]])
        out[grp] = res
    return out


def decide(r: dict, perp: bool) -> str:
    c, o = r["crypto"], r["other"]
    d, lo, _ = c["pooled"]
    pos_tf = sum(1 for tf in TFS if c[tf][0] == c[tf][0] and c[tf][0] > 0)
    crypto_ok = d == d and lo > 0 and pos_tf >= 3
    if not crypto_ok:
        return "DROP"
    if perp:
        return "KEEP_CRYPTO"
    od, _, ohi = o["pooled"]
    return "KEEP_CRYPTO" if (od == od and ohi < 0) else "KEEP"


def main():
    B = load_breaks()
    res, dec = {}, {}
    for col in EVIDENCE + FILTERS:
        res[col] = screen(B, col, PERP.get(col) or ("ltf_available" if col == "ltf_momentum" else None))
        dec[col] = decide(res[col], col in PERP)
        print(f"{col:15s} {dec[col]:12s} crypto {res[col]['crypto']['pooled']}  other {res[col]['other']['pooled']}", flush=True)

    # counter-HTF reversal path
    CR = B[B["cls"] == "counter_reversal"]
    res["counter_reversal_sweep"] = screen(CR, "sweep")
    cls_means = {}
    for grp, sub in (("crypto", B[B["cls_asset"] == "crypto"]), ("other", B[B["cls_asset"] != "crypto"])):
        cls_means[grp] = {k: (int(len(g)), float(g["r_h"].mean())) for k, g in sub.groupby("cls")}
    cr_sweep = res["counter_reversal_sweep"]["crypto"]
    cr_crypto = CR[CR["cls_asset"] == "crypto"]
    cr_sw_mean = float(cr_crypto[cr_crypto["sweep"]]["r_h"].mean()) if len(cr_crypto) else np.nan
    if cr_sw_mean <= 0 or cr_sw_mean != cr_sw_mean:
        dec["counter_major_path"] = "CLOSED"
    else:
        dec["counter_major_path"] = "OPEN_WITH_SWEEP" if decide(res["counter_reversal_sweep"], False) != "DROP" else "CLOSED"
    print("counter-HTF reversal:", dec["counter_major_path"], cr_sweep["pooled"], "mean r with sweep", cr_sw_mean)

    # correlation between kept conditions (phi), to merge families
    kept = [c for c in EVIDENCE if dec[c] != "DROP"]
    phi = B[kept].astype(float).corr().round(2) if kept else pd.DataFrame()
    fam_of = {m: fam for fam, ms in G.FAMILIES.items() for m in ms}
    merges = []
    for a in kept:
        for b in kept:
            if a < b and fam_of[a] != fam_of[b] and abs(phi.loc[a, b]) > 0.5:
                merges.append((a, b, float(phi.loc[a, b])))
    dec["merges"] = merges

    # also report the v1 condition set's correlation, for the record
    allphi = B[EVIDENCE[:6]].astype(float).corr().round(2)
    OUT.mkdir(exist_ok=True)
    (OUT / "screening.json").write_text(json.dumps({"decisions": dec, "results": res, "class_means": cls_means,
                                                    "phi_kept": phi.to_dict(), "phi_core": allphi.to_dict(),
                                                    "n_breaks": int(len(B))}, indent=1, default=float))
    write_md(res, dec, cls_means, allphi, len(B))
    print(json.dumps(dec, indent=1))


def write_md(res, dec, cls_means, phi, n):
    L = ["# Component screening (development data only)", "",
         f"{n} MTF structure breaks on the 30 development symbols, before each timeframe's holdout. ",
         "Fresh symbols were not loaded. diff = mean r_h (ATR, after costs) with minus without; ",
         "90% month-cluster bootstrap intervals. The rule is in `scripts/screen_components.py` and was ",
         "fixed before this ran.", "",
         "| component | decision | crypto diff [90% CI] | crypto TFs > 0 | non-crypto diff [90% CI] | n with / without (crypto) |",
         "|---|---|---:|---:|---:|---:|"]
    for col in EVIDENCE + FILTERS:
        c, o = res[col]["crypto"], res[col]["other"]
        pos = sum(1 for tf in TFS if c[tf][0] == c[tf][0] and c[tf][0] > 0)
        fmt = lambda t: "–" if t[0] != t[0] else f"{t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}]"
        L.append(f"| {col} | **{dec[col]}** | {fmt(c['pooled'])} | {pos}/4 | {fmt(o['pooled'])} | {c['n_with']} / {c['n_without']} |")
    L += ["", "Per timeframe (crypto diff):", "", "| component | 1H | 4H | 1D | 1W |", "|---|---:|---:|---:|---:|"]
    for col in EVIDENCE + FILTERS:
        c = res[col]["crypto"]
        L.append(f"| {col} | " + " | ".join("–" if c[tf][0] != c[tf][0] else f"{c[tf][0]:+.3f}" for tf in TFS) + " |")
    cr = res["counter_reversal_sweep"]["crypto"]["pooled"]
    L += ["", f"Counter-HTF reversal MAJOR path: **{dec['counter_major_path']}** "
          f"(sweep diff among counter-HTF reversals, crypto: {cr[0]:+.3f} [{cr[1]:+.3f}, {cr[2]:+.3f}])", "",
          "Mean r_h by break class (n, mean):", "", "| class | crypto | non-crypto |", "|---|---:|---:|"]
    for k in ["continuation", "realignment", "counter_reversal"]:
        a = cls_means["crypto"].get(k, (0, np.nan))
        b = cls_means["other"].get(k, (0, np.nan))
        L.append(f"| {k} | {a[0]}, {a[1]:+.3f} | {b[0]}, {b[1]:+.3f} |")
    L += ["", f"Family merges (|phi| > 0.5 across families): {dec['merges'] or 'none'}", "",
          "Correlation (phi) between the core conditions:", "", "```\n" + phi.to_string() + "\n```"]
    (OUT / "SCREENING.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()
