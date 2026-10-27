"""Design check on DEVELOPMENT data only (run after screening; fresh symbols not loaded).

Screening dropped every add-on condition, so the remaining question is what, if anything,
should separate MAJOR from CONFIRMED. Two candidates, both measured on with-HTF breaks:
  (a) HTF alignment strength: one HTF agreeing (other flat) vs both agreeing
  (b) the combined count of the v1 core conditions (momentum, strength, displacement, volume)
Writes reports/DESIGN_CHECK.md.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from screen_components import boot_diff, load_breaks  # noqa: E402
from hcmtf.metrics import cluster_ci  # noqa: E402

B = load_breaks()
W = B[B["cls"].isin(["continuation", "realignment"])].copy()
W["core"] = W[["momentum", "strength", "displacement"]].sum(1) + np.where(W["cls_asset"] == "fx", 0, W["volume"])
L = ["# Design check (development data only)", "",
     "With-HTF breaks (continuation + realignment) on the 30 dev symbols before each holdout.", ""]
for grp, sub in (("crypto", W[W.cls_asset == "crypto"]), ("non-crypto", W[W.cls_asset != "crypto"])):
    L += [f"## {grp}", "", "| TF | split | n | mean r_h [95% CI] |", "|---|---|---:|---:|"]
    for tf in ["1H", "4H", "1D", "1W", "all"]:
        s = sub if tf == "all" else sub[sub.tf == tf]
        for name, m in [("one HTF agrees", s.htf_bias == 1), ("both HTFs agree", s.htf_bias == 2),
                        ("core 0-1", s.core <= 1), ("core 2", s.core == 2), ("core 3", s.core == 3), ("core 4", s.core == 4)]:
            g = s[m]
            if len(g) >= 20:
                mu, lo, hi = cluster_ci(g, "r_h")
                L.append(f"| {tf} | {name} | {len(g)} | {mu:+.3f} [{lo:+.2f}, {hi:+.2f}] |")
        d = boot_diff(s[s.htf_bias == 2], s[s.htf_bias == 1])
        L.append(f"| {tf} | both − one (90% CI) | | {d[0]:+.3f} [{d[1]:+.2f}, {d[2]:+.2f}] |")
        d = boot_diff(s[s.core >= 3], s[s.core <= 2])
        L.append(f"| {tf} | core ≥3 − core ≤2 (90% CI) | | {d[0]:+.3f} [{d[1]:+.2f}, {d[2]:+.2f}] |")
    L.append("")
C = B[B["cls"] == "counter_reversal"]
L += ["## counter-HTF reversals, by TF", "", "| TF | market | n | mean r_h [95% CI] |", "|---|---|---:|---:|"]
for tf in ["1H", "4H", "1D", "1W"]:
    for grp, s in (("crypto", C[(C.tf == tf) & (C.cls_asset == "crypto")]), ("non-crypto", C[(C.tf == tf) & (C.cls_asset != "crypto")])):
        if len(s) >= 20:
            mu, lo, hi = cluster_ci(s, "r_h")
            L.append(f"| {tf} | {grp} | {len(s)} | {mu:+.3f} [{lo:+.2f}, {hi:+.2f}] |")
out = Path(__file__).resolve().parent.parent / "reports" / "DESIGN_CHECK.md"
out.write_text("\n".join(L) + "\n")
print("\n".join(L))
