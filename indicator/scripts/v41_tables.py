"""Render V4.1 result tables (markdown fragments) from reports/v41_H.json and reports/v41_D.json.

    python scripts/v41_tables.py   # → reports/v41_tables/*.md, included by the V4.1 reports
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "v41_tables"
TFS = ["1H", "4H", "1D", "1W"]
GROUPS = ["crypto", "equities", "commodities", "rates_fx", "all"]
SIDE = {"1": "bullish", "-1": "bearish", "0": "both"}


def f(x, nd=2, sign=True):
    if x is None:
        return "–"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def load(stage):
    p = ROOT / "reports" / f"v41_{stage}.json"
    return json.loads(p.read_text()) if p.exists() else None


def table(R, fam, setname, val, kind, sides, title, holm=None, passing=None):
    L = [f"#### {title}", "",
         "| TF | group | side | n | instr. | clusters | mean outcome | median outcome | benchmark mean | mean excess [95% CI] | p (one-sided) | Holm | median excess | w/o top 1% | spans + (of 3) | evaluable | passes §6 |",
         "|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|"]
    for tf in TFS:
        r = R["results"].get(tf)
        if not r:
            continue
        for g in GROUPS:
            for s in sides:
                k = f"{fam}|{tf}|{g}|{s}|{setname}|{val}|{kind}"
                c = r["cells"].get(k)
                if not c:
                    L.append(f"| {tf} | {g} | {SIDE[s]} | 0 | | | | | | no units | | | | | | no | |")
                    continue
                if not c.get("n"):
                    L.append(f"| {tf} | {g} | {SIDE[s]} | 0 | {c.get('instruments', 0)} | | | | | no units | | | | | | no | |")
                    continue
                hp = (holm or {}).get(k)
                ps = (passing or {}).get(k)
                L.append(f"| {tf} | {g} | {SIDE[s]} | {c['n']} | {c.get('instruments', '')} | {c.get('clusters', '')} | "
                         f"{f(c.get('mean_value'))} | {f(c.get('median_value'))} | {f(c.get('bench_mean'))} | "
                         f"{f(c['mean_excess'], 3)} [{f(c['lo'], 3)}, {f(c['hi'], 3)}] | {f(c['p'], 4, False)} | "
                         f"{f(hp, 4, False) if hp is not None else '–'} | {f(c.get('median_excess'), 3)} | "
                         f"{f(c.get('mean_excess_ex_top1'), 3)} | {c.get('spans_positive', '–')} | "
                         f"{'yes' if c.get('evaluable') else ('no' if g != 'all' else 'pooled')} | "
                         f"{('**yes**' if ps else 'no') if ps is not None else '–'} |")
    return "\n".join(L) + "\n"


def spans(R, fam, setname, val, kind, sides, title):
    L = [f"#### {title}", "", "| TF | group | side | span 1 | span 2 | span 3 | low vol | mid vol | high vol |",
         "|---|---|---|---|---|---|---|---|---|"]
    for tf in TFS:
        r = R["results"].get(tf)
        if not r:
            continue
        for g in GROUPS:
            for s in sides:
                c = r["cells"].get(f"{fam}|{tf}|{g}|{s}|{setname}|{val}|{kind}")
                if not c or not c.get("n"):
                    continue
                sp = [f"{f(x['mean_excess'])} (n={x['n']}; {x['from'][:7]}→{x['to'][:7]})" for x in c["spans"]]
                bv = c.get("by_vol", {})
                vv = [f"{f(bv[k]['mean_excess'])} (n={bv[k]['n']})" if k in bv else "–" for k in ("0", "1", "2")]
                L.append(f"| {tf} | {g} | {SIDE[s]} | " + " | ".join(sp + vv) + " |")
    return "\n".join(L) + "\n"


def trading(R, title):
    L = [f"#### {title}", "",
         "| TF | group | side | rule | CAGR | vol | Sharpe [95% CI] | max drawdown |", "|---|---|---|---|---:|---:|---|---:|"]
    for tf in TFS:
        r = R["results"].get(tf)
        if not r:
            continue
        for g in GROUPS:
            for s in ("1", "-1"):
                for name in ("timed", "static"):
                    p = r["trading"].get(f"{g}|{s}|{name}")
                    if not p:
                        continue
                    rule = ("in bullish state, else flat" if s == "1" else "short in bearish state, else flat") if name == "timed" else \
                        ("always long" if s == "1" else "always short")
                    L.append(f"| {tf} | {g} | {SIDE[s]} | {rule} | {100 * p['cagr']:+.1f}% | {100 * p['vol']:.1f}% | "
                             f"{f(p['sharpe'])} [{f(p['sharpe_lo'])}, {f(p['sharpe_hi'])}] | {100 * p['max_dd']:.1f}% |")
    return "\n".join(L) + "\n"


def coverage(R):
    L = ["| TF | instruments | excluded (mechanical, §1) |", "|---|---:|---|"]
    for tf in TFS:
        r = R["results"].get(tf)
        if r:
            L.append(f"| {tf} | {r['instruments']} | {'; '.join(r['excluded']) or '–'} |")
    L += ["", "| TF | instrument | window start | window end | eligible candles |", "|---|---|---|---|---:|"]
    for tf in TFS:
        r = R["results"].get(tf)
        if r:
            for s, (a, b, n) in r["coverage"].items():
                L.append(f"| {tf} | {s} | {a} | {b} | {n} |")
    return "\n".join(L) + "\n"


def main():
    OUT.mkdir(exist_ok=True)
    for stage in ("H", "D"):
        R = load(stage)
        if not R:
            continue
        D = R.get("decisions", {})
        hp, ps = D.get("holm_family", {}), D.get("passing", {})
        tag = "holdout (decisions)" if stage == "H" else "seen symbols (exploratory, no decisions)"
        parts = {
            "h6": [table(R, "H6", "state", "r", "U", ("1", "-1"), f"H6 primary: state vs U, r_h at H — {tag}", hp, ps),
                   table(R, "H6", "state", "r", "V", ("1", "-1"), f"H6: state vs V (same causal vol tercile) — {tag}"),
                   table(R, "H6", "state", "r", "Y", ("1", "-1"), f"H6: state vs Y (same calendar year, ex post) — {tag}"),
                   table(R, "H6", "state", "rs", "U", ("1", "-1"), f"H6: horizon H/4 vs U — {tag}"),
                   table(R, "H6", "state", "rl", "U", ("1", "-1"), f"H6: horizon 2H vs U — {tag}"),
                   table(R, "H6", "onset", "r", "U", ("1", "-1"), f"H6: state onset events vs U — {tag}"),
                   table(R, "H6", "state_lag", "r", "U", ("1", "-1"), f"H6: HTF1 lagged one candle vs U — {tag}"),
                   spans(R, "H6", "state", "r", "U", ("1", "-1"), f"H6 primary by purged chronological span and causal vol tercile — {tag}"),
                   trading(R, f"H6 trading view (open-to-open, costs, equal weight) — {tag}")],
            "h7": [table(R, "H7v", "h7", "rvr", "L", ("0",), f"H7v primary: realised range after events vs compressed candles (L) — {tag}", hp, ps),
                   table(R, "H7v", "h7", "rvr", "U", ("0",), f"H7v: vs all candles (U) — {tag}"),
                   table(R, "H7m", "h7", "mag", "L", ("0",), f"H7m: |net move| in ATR vs compressed candles — {tag}"),
                   table(R, "H7d", "h7", "r", "L", ("1", "-1"), f"H7d primary: r_h in breakout direction vs L_d (up = bullish, down = bearish) — {tag}", hp, ps),
                   table(R, "H7d", "h7", "r", "U", ("1", "-1"), f"H7d: vs U — {tag}"),
                   spans(R, "H7v", "h7", "rvr", "L", ("0",), f"H7v by span and vol tercile — {tag}"),
                   spans(R, "H7d", "h7", "r", "L", ("1", "-1"), f"H7d by span and vol tercile — {tag}")],
            "h1r": [table(R, "H1r", "B", "r", "S", ("1", "-1"), f"H1r primary: state + structure break (B) vs state candles (S) — {tag}", hp, ps),
                    table(R, "H1r", "M", "r", "S", ("1", "-1"), f"H1r: state + ROC20 momentum (M) vs S — {tag}"),
                    table(R, "H1r", "Bcont", "r", "S", ("1", "-1"), f"H1r: continuation breaks vs S (target cell: 4H crypto bullish) — {tag}", hp, ps),
                    table(R, "H1r", "Breal", "r", "S", ("1", "-1"), f"H1r: realignment breaks (MAJOR before cooldown) vs S — {tag}"),
                    spans(R, "H1r", "B", "r", "S", ("1", "-1"), f"H1r primary by span and vol tercile — {tag}")],
            "cov": [coverage(R)],
        }
        # B − M
        L = [f"#### H1r: B − M (break excess minus momentum excess, same replicates) — {tag}", "",
             "| TF | group | side | B − M [95% CI] | p (B > M) | n B / n M |", "|---|---|---|---|---:|---|"]
        for tf in TFS:
            r = R["results"].get(tf)
            if not r:
                continue
            for g in GROUPS:
                for s in ("1", "-1"):
                    c = r["cells"].get(f"H1r|{tf}|{g}|{s}|B-M|r|S")
                    if c:
                        L.append(f"| {tf} | {g} | {SIDE[s]} | {f(c['mean_excess'], 3)} [{f(c['lo'], 3)}, {f(c['hi'], 3)}] | {f(c['p'], 4, False)} | {c['n']} / {c['n_M']} |")
        parts["h1r"].insert(2, "\n".join(L) + "\n")
        for k, v in parts.items():
            (OUT / f"{k}_{stage}.md").write_text("\n".join(v))
    print("wrote", sorted(p.name for p in OUT.glob("*.md")))


if __name__ == "__main__":
    main()
