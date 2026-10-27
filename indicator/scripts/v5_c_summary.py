"""Compact tables for reports/V5_C_EXPLORATION_SUMMARY.md, read from reports/v5_c_x1_results.json.

Reporting only: no data is loaded and nothing is recomputed. The frozen selection outcome is
copied from the results file, and the per-requirement breakdown below repeats the frozen §8 checks
on the stored numbers so a reader can see which requirement each variant failed."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = json.loads((ROOT / "reports" / "v5_c_x1_results.json").read_text())
C = R["cells"]
TFS, GROUPS = ("1H", "4H"), ("crypto", "equities", "commodities", "rates", "pooled")
WARN = ("C1a", "C1b", "C2", "C3", "C4")
CONF = ("C3", "C5a", "C5b")
BASE = ("htf_flip", "ema_cross", "supertrend_flip", "counter_reversal")


def ci(t, d=3, sign=False):
    if not t or t[0] is None:
        return "–"
    f = f"{{:{'+' if sign else ''}.{d}f}}"
    return f"{f.format(t[0])} [{f.format(t[1])}, {f.format(t[2])}]" if len(t) == 3 else f.format(t[0])


def lead(t):
    return "–" if not t or t[0] is None else f"{t[0]:.0f} [{t[1]:.0f}, {t[2]:.0f}]"


def coverage():
    L = ["| TF | kind | detector | " + " | ".join(f"{g} n·G·eval" for g in GROUPS[:-1]) + " | groups evaluable |",
         "|---|---|---|" + "---|" * 5]
    for tf in TFS:
        for kind, dets in (("warning", WARN), ("confirmation", CONF)):
            for d in dets:
                cells, ok = [], 0
                for g in GROUPS[:-1]:
                    c = C[f"{tf}|{g}|{d}|{kind}"]
                    ok += bool(c["evaluable"])
                    cells.append(f"{c['detection']['instruments']}·{c['lift'].get('clusters', 0)}·{'yes' if c['evaluable'] else '**no**'}")
                L.append(f"| {tf} | {kind} | {d} | " + " | ".join(cells) + f" | {ok}/4 |")
    return L


def warnings(tf):
    L = ["| detector | group | inst | events | alerts | recall [CI] | precision [CI] | prec* | FA /inst-yr | lead [CI] | remain | lift excess [t-CI] | p wild |",
         "|---|---|---:|---:|---:|---|---|---:|---:|---|---:|---|---:|"]
    for d in WARN:
        for g in GROUPS:
            c = C[f"{tf}|{g}|{d}|warning"]
            x, l = c["detection"], c["lift"]
            e = l.get("ci95_t")
            gl = g if c["evaluable"] else f"{g} (not eval.)"
            L.append(f"| {d} | {gl} | {x['instruments']} | {x['events']} | {x['alerts']} | {ci(x['recall'])} | {ci(x['precision'])} | "
                     f"{x['precision_excluding_duplicates']:.3f} | {x['false_alarms_per_instrument_year']:.1f} | {lead(x['lead_median'])} | "
                     f"{x['remaining_median']:.2f} | {l['excess']:+.4f} [{e[0]:+.4f}, {e[1]:+.4f}] | {l['p_wild']:.4f} |")
    return L


def confirmations(tf):
    L = ["| detector | group | inst | alerts | recall | prec* | FA /inst-yr | lead | remain | lift excess [t-CI] | p wild | "
         + " | ".join(f"{b} prec* · recall" for b in BASE) + " | best baseline prec* |",
         "|---|---|---:|---:|---|---:|---:|---|---:|---|---:|" + "---|" * 5]
    for d in CONF:
        for g in GROUPS:
            c = C[f"{tf}|{g}|{d}|confirmation"]
            x, l, m = c["detection"], c["lift"], c["matched_baselines"]
            e = l.get("ci95_t")
            bp = [(m[b]["precision_excl_dup"][0], b) for b in BASE if m[b].get("precision_excl_dup") and m[b]["precision_excl_dup"][0] is not None]
            best = max(bp) if bp else (None, "–")
            mine = x["precision_excluding_duplicates"]
            flag = "" if best[0] is None else (" ≥" if mine >= best[0] else " **<**")
            gl = g if c["evaluable"] else f"{g} (not eval.)"
            L.append(f"| {d} | {gl} | {x['instruments']} | {x['alerts']} | {ci(x['recall'])} | {mine:.3f}{flag} | "
                     f"{x['false_alarms_per_instrument_year']:.1f} | {lead(x['lead_median'])} | {x['remaining_median']:.2f} | "
                     f"{l['excess']:+.4f} [{e[0]:+.4f}, {e[1]:+.4f}] | {l['p_wild']:.4f} | "
                     + " | ".join(f"{m[b]['precision_excl_dup'][0]:.3f} · {m[b]['recall'][0]:.3f}" if m[b].get("recall") else "–" for b in BASE)
                     + f" | {best[0]:.3f} ({best[1]}) |")
    return L


def shortfall():
    L = ["| TF | detector | baseline | kept / target alerts (available) | shortfall blocks |", "|---|---|---|---|---:|"]
    for tf in TFS:
        for d in CONF:
            m = C[f"{tf}|pooled|{d}|confirmation"]["matched_baselines"]
            for b in BASE:
                s = m[b]
                L.append(f"| {tf} | {d} | {b} | {s['alerts'][0]:.0f} / {s['target_alerts']} ({s['available_alerts']}) | {s['shortfall_blocks']} |")
    return L


def requirements():
    L = ["| detector | kind | best TF (frozen: highest score) | score | p wild < 0.05 | lead > 0 (W) | remain ≥ 0.5 (C) | prec* ≥ best matched baseline (C) | qualifies | §9 |",
         "|---|---|---|---:|---|---|---|---|---|---|"]
    for e in R["selection"]["eligible"]:
        d, k, tf = e["detector"], e["kind"], e["tf"]
        c = C[f"{tf}|pooled|{d}|{k}"]
        x, l = c["detection"], c["lift"]
        yn = lambda b: "yes" if b else "**no**"
        w = yn(x["lead_median"][0] > 0) if k == "warning" else "n/a"
        if k == "confirmation":
            m = c["matched_baselines"]
            bp = max((m[b]["precision_excl_dup"][0], b) for b in BASE if m[b].get("precision_excl_dup"))
            r = yn(x["remaining_median"] >= 0.5)
            p = f"{yn(x['precision_excluding_duplicates'] >= bp[0])} ({x['precision_excluding_duplicates']:.3f} vs {bp[0]:.3f} {bp[1]})"
        else:
            r = p = "n/a"
        L.append(f"| {d} | {k} | {tf} | {e['score']:+.4f} | {yn(l['p_wild'] < 0.05)} ({l['p_wild']:.4f}) | {w} | {r} | {p} | "
                 f"{'yes' if e['meets_requirements'] else 'no'} | {R['rejection'][f'{d}|{k}']} |")
    return L


def trading():
    L = ["| TF | detector | trades | net mean (ATR) | r_h − causal benchmark [CI] (p wild) | holding-cost sources |", "|---|---|---:|---:|---|---|"]
    for tf in TFS:
        for d in CONF:
            t = C[f"{tf}|pooled|{d}|confirmation"]["trading"]
            e = t["causal_excess"]
            L.append(f"| {tf} | {d} | {t['trades']} | {t['net_mean']:+.4f} | "
                     f"{e['mean']:+.3f} [{e['ci95'][0]:+.3f}, {e['ci95'][1]:+.3f}] ({e['p_wild']:.4f}) | {t['cost_sources']} |")
    return L


if __name__ == "__main__":
    import sys
    part = sys.argv[1]
    out = {"coverage": coverage, "requirements": requirements, "shortfall": shortfall, "trading": trading}.get(part)
    if out:
        print("\n".join(out()))
    elif part.startswith("warn"):
        print("\n".join(warnings(part[-2:])))
    elif part.startswith("conf"):
        print("\n".join(confirmations(part[-2:])))
