"""Download and cache every bar series the study uses. Safe to re-run; uses the cache."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf.data import DATA_DIR, load_native, write_manifest  # noqa: E402
from hcmtf.universe import UNIVERSE  # noqa: E402

refresh = "--refresh" in sys.argv
for a in UNIVERSE:
    for iv in ("1d", "1h"):
        try:
            df = load_native(a.symbol, iv, refresh=refresh)
            print(f"{a.symbol:10s} {iv} {len(df):7d} {df.index[0]} -> {df.index[-1]}", flush=True)
        except Exception as e:  # keep going; the report lists what is missing
            print(f"{a.symbol:10s} {iv} FAILED {e}", flush=True)
write_manifest(DATA_DIR / "MANIFEST.json")
