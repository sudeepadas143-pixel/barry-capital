"""Count major-top / major-bottom labels on EXPLORATION data, for sample-size planning only.

    python scripts/v5_label_counts.py   # → reports/v5_label_counts.json

Labels are the frozen definitions in research/v5_labels.py (committed before this ran). No
detector, signal or predictive statistic is computed. The counts must not be used to retune the
label parameters (reports/V5_HYPOTHESIS_REGISTER.md §2.2).
"""

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf import data, ta  # noqa: E402
from research.universe41 import HOLDOUT, SEEN  # noqa: E402
from research.v41 import group_of, integrity_cut  # noqa: E402
from research.v5_labels import BOTTOM_PARAMS, TOP_PARAMS, major_bottoms, major_tops  # noqa: E402
from research.v5_reserve import exploration_only  # noqa: E402

START = {"1H": "2020-01-01", "4H": "2020-01-01", "1D": "2010-01-01", "1W": "2010-01-01"}


def one(args):
    a, tf = args
    try:
        df = exploration_only(data.load(a.symbol, tf))
    except Exception:
        return None
    cut = integrity_cut(a.symbol)
    if cut is not None:
        df = df[df.index < cut]
    import pandas as pd
    df = df[df.index >= pd.Timestamp(START[tf], tz="UTC") - pd.Timedelta(days=0)]
    if len(df) < 300:
        return None
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    atr = ta.atr(h, l, c, 14)
    tp, bp = TOP_PARAMS[tf], BOTTOM_PARAMS[tf]
    tops, bots = major_tops(h, l, atr, **tp), major_bottoms(h, l, atr, **bp)
    years = (df.index[-1] - df.index[0]).days / 365.25
    return {"symbol": a.symbol, "group": group_of(a.cls), "seen": a in SEEN, "tops": len(tops), "bottoms": len(bots),
            "candles": len(df), "years": years,
            "top_months": sorted({str(df.index[i])[:7] for i in tops}), "bottom_months": sorted({str(df.index[i])[:7] for i in bots})}


def main():
    out = {}
    for tf in ("1H", "4H", "1D", "1W"):
        with ProcessPoolExecutor(8) as ex:
            res = [r for r in ex.map(one, [(a, tf) for a in SEEN + HOLDOUT]) if r]
        cells = {}
        for g in ("crypto", "equities", "commodities", "rates_fx", "all"):
            rs = [r for r in res if g == "all" or r["group"] == g]
            if not rs:
                continue
            yrs = sum(r["years"] for r in rs)
            cells[g] = {"instruments": len(rs), "instrument_years": round(yrs, 1),
                        "tops": sum(r["tops"] for r in rs), "bottoms": sum(r["bottoms"] for r in rs),
                        "tops_per_instrument_year": round(sum(r["tops"] for r in rs) / yrs, 2),
                        "bottoms_per_instrument_year": round(sum(r["bottoms"] for r in rs) / yrs, 2),
                        "top_months": len({m for r in rs for m in r["top_months"]}),
                        "bottom_months": len({m for r in rs for m in r["bottom_months"]})}
        out[tf] = cells
        print(tf, {g: (c["tops"], c["bottoms"]) for g, c in cells.items()}, flush=True)
    (ROOT / "reports" / "v5_label_counts.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
