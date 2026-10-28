"""Download the extra series v2 needs (cached; safe to re-run)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf import derivs  # noqa: E402
from hcmtf.data import DATA_DIR, load_native, write_manifest  # noqa: E402
from hcmtf.universe import FRESH, UNIVERSE  # noqa: E402

for a in FRESH:
    for iv in ("1d", "1h"):
        try:
            df = load_native(a.symbol, iv)
            print(f"fresh {a.symbol:10s} {iv} {len(df):7d} {df.index[0].date()} -> {df.index[-1].date()}", flush=True)
        except Exception as e:
            print(f"fresh {a.symbol:10s} {iv} FAILED {e}", flush=True)

for a in UNIVERSE + FRESH:
    if a.cls != "crypto":
        continue
    for name, fn in (("15m", derivs.spot_15m), ("perp1h", derivs.perp_1h), ("funding", derivs.funding)):
        try:
            df = fn(a.symbol)
            print(f"{name:7s} {a.symbol:10s} {len(df):7d} {df.index[0].date() if len(df) else '-'} -> {df.index[-1].date() if len(df) else '-'}", flush=True)
        except Exception as e:
            print(f"{name:7s} {a.symbol:10s} FAILED {e}", flush=True)

for a in UNIVERSE:
    if a.cls == "crypto":
        oi = derivs.open_interest(a.symbol)
        print(f"oi      {a.symbol:10s} {len(oi):7d}", flush=True)
write_manifest(DATA_DIR / "MANIFEST.json")
