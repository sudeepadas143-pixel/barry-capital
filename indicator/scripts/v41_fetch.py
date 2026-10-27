"""Download the V4.1 holdout instruments and write the data-freeze manifest (pre-registration §1, §7.4).

    python scripts/v41_fetch.py

Computes no outcome, signal or statistic: it only downloads native 1h/1d bars through the
existing hcmtf.data loaders and records sha256, rows and span per file, plus the sha256 of the
frozen V4.1 code (the configuration hash), into reports/V4_1_DATA_MANIFEST.json.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hcmtf import data  # noqa: E402
from research.universe41 import HOLDOUT  # noqa: E402

CODE = ["research/v41.py", "research/universe41.py", "scripts/v41_run.py", "scripts/v41_fetch.py",
        "reports/V4_1_PREREGISTRATION.md"]


def main():
    files, failed = {}, {}
    for a in HOLDOUT:
        for iv in ("1h", "1d"):
            try:
                data.load_native(a.symbol, iv)
                p = data._cache_path(a.symbol, iv)
                df = data._read(p)
                files[p.name] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "rows": len(df),
                                 "first": str(df.index[0]), "last": str(df.index[-1])}
                print(f"{a.symbol} {iv}: {len(df)} rows {df.index[0]} → {df.index[-1]}", flush=True)
            except Exception as e:
                failed[f"{a.symbol} {iv}"] = f"{type(e).__name__}: {e}"[:200]
                print(f"{a.symbol} {iv}: FAILED {failed[f'{a.symbol} {iv}']}", flush=True)
    out = {"files": files, "failed": failed,
           "config_hash": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in CODE}}
    (ROOT / "reports" / "V4_1_DATA_MANIFEST.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
