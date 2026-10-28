"""Compare the TradingView indicator with the Python engine on TradingView's own candles.

1. In TradingView, add HC-MTF to a chart, tick "Parity export" in its settings.
2. Chart menu → Export chart data → keep "ISO time" off (UNIX time) → save the CSV.
3. python scripts/compare_tv_export.py export.csv --profile 4H [--crypto] [--no-volume]

The export carries the chart OHLCV plus the indicator's per-candle HTF trends, LTF
readings and signal codes. This script feeds the same candles AND the exported HTF/LTF
readings to hcmtf.engine, recomputes everything else (structure, sweeps, evidence,
classes, tiers, cooldown, warnings) and lists every candle where the two disagree.
Feeding the exported HTF/LTF values isolates the signal logic from feed differences;
the HTF/LTF computations themselves are covered by tests/test_engine_v2.py.

The first ~250 candles are skipped as warm-up (ATR percentile rank needs 200 bars).
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf import engine as G  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--profile", required=True, choices=list(G.LADDER))
    ap.add_argument("--crypto", action="store_true")
    ap.add_argument("--no-volume", action="store_true")
    ap.add_argument("--warmup", type=int, default=250)
    ap.add_argument("--accept", action="store_true", help="the chart had 'Require next-candle acceptance' on")
    a = ap.parse_args()

    raw = pd.read_csv(a.csv)
    cols = {c.lower(): c for c in raw.columns}
    idx = pd.to_datetime(raw[cols["time"]], unit="s", utc=True)
    df = pd.DataFrame({k: raw[cols[k]].astype(float).to_numpy() for k in ("open", "high", "low", "close")}, index=idx)
    vol_col = next((c for c in raw.columns if c.lower() == "volume"), None)
    df["volume"] = raw[vol_col].astype(float).to_numpy() if vol_col else 0.0

    from hcmtf.report2 import active_params
    p = G.with_(active_params(a.profile), accept=a.accept)
    ctx = G.Ctx(df, None, None, None, not a.no_volume, a.crypto)
    f = G.features(ctx, p)
    get = lambda name: pd.to_numeric(raw[name], errors="coerce").to_numpy(float) if name in raw else np.full(len(df), np.nan)
    f.t1, f.t2 = get("parity_htf1"), get("parity_htf2")
    f.ltf_mom, f.ltf_struct = get("parity_ltf_mom"), get("parity_ltf_struct")
    t = G.breaks(f, p)
    t = G.score(t, f, p)
    sig = G.classify(t, p)
    warn = G.warnings(f)

    trade = sig[sig["tier"].isin(["major", "confirmed"])]
    py = np.zeros(len(df))
    py[trade["i"].to_numpy(int)] = trade["dir"].to_numpy() * np.where(trade["tier"] == "major", 2, 1)
    watch = sig[sig["tier"] == "watch"]
    pwa = np.zeros(len(df))
    pwa[watch["i"].to_numpy(int)] = watch["dir"].to_numpy()
    pw = np.zeros(len(df))
    pw[warn["i"].to_numpy(int)] = warn["dir"].to_numpy()
    tv = np.nan_to_num(get("parity_signal"))
    tw = np.nan_to_num(get("parity_warning"))
    twa = np.nan_to_num(get("parity_watch"))
    w = a.warmup
    bad_s = np.where(py[w:] != tv[w:])[0] + w
    bad_w = np.where((pw[w:] != tw[w:]) | (pwa[w:] != twa[w:]))[0] + w
    n_sig = int((tv[w:] != 0).sum())
    print(f"candles compared: {len(df) - w}; TradingView signals: {n_sig}; Python signals: {int((py[w:] != 0).sum())}")
    print(f"signal mismatches: {len(bad_s)}; warning mismatches: {len(bad_w)} (early warnings + WATCH)")
    for i in bad_s[:20]:
        print(f"  {df.index[i]}  tv={tv[i]:+.0f} py={py[i]:+.0f}")
    sys.exit(1 if len(bad_s) or len(bad_w) else 0)


if __name__ == "__main__":
    main()
