"""Fingerprint of the cached EXPLORATION data (audit blocker B4).

build() records, for every cached file of an exploration instrument: file name, symbol, native
kind (1h, 1d, 15m, funding, oi, perp1h), size, rows, first and last timestamp in the file, and
sha256; and for every instrument the coverage of the guarded frames research.v5_data.load returns
for 1H/4H/1D/1W (rows, first and last candle after the freeze/closed-candle cut). A combined hash
over all (file, sha256) pairs identifies the whole data set. Nothing is fetched; reserved
instruments cannot appear (build() raises if one does).

verify() recomputes every file hash and lists missing or changed files, so a trial can prove it
read exactly the fingerprinted data (vendor revisions or re-downloads are detected).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from hcmtf import data

from . import v5_data as DG
from .v5_reserve import FREEZE

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "reports" / "V5_EXPLORATION_DATA_MANIFEST.json"
KINDS = ("1h", "1d", "15m", "funding", "oi", "perp1h")
TFS = ("1H", "4H", "1D", "1W")


def _symbol_of(fname: str) -> tuple[str, str]:
    stem = fname[: -len(".csv.gz")]
    safe, kind = stem.rsplit("_", 1)
    by_safe = {s.replace("=", "_").replace("^", "_"): s for s in DG.EXPLORATION}
    by_safe.update({s.replace("=", "_").replace("^", "_"): s for s in DG.RESERVED})
    return by_safe.get(safe, safe), kind


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(data_dir: Path | None = None, coverage: bool = True) -> dict:
    d = Path(data_dir or data.DATA_DIR)
    files, combined = {}, hashlib.sha256()
    for p in sorted(d.glob("*.csv.gz")):
        sym, kind = _symbol_of(p.name)
        if sym in DG.RESERVED:
            raise RuntimeError(f"reserved instrument {sym} found in the exploration cache: {p.name}")
        if sym not in DG.EXPLORATION:
            raise RuntimeError(f"unregistered file in the exploration cache: {p.name}")
        idx = pd.to_datetime(pd.read_csv(p, usecols=[0]).iloc[:, 0], utc=True, format="ISO8601")
        h = sha_file(p)
        files[p.name] = {"symbol": sym, "kind": kind, "bytes": p.stat().st_size, "rows": int(len(idx)),
                         "first": str(idx.iloc[0]) if len(idx) else None, "last": str(idx.iloc[-1]) if len(idx) else None,
                         "sha256": h}
        combined.update(f"{p.name}:{h}\n".encode())
    cov = {}
    if coverage:
        for sym in sorted({f["symbol"] for f in files.values()}):
            cov[sym] = {}
            for tf in TFS:
                try:
                    df = DG.load(sym, tf)
                    cov[sym][tf] = {"rows": int(len(df)), "first": str(df.index[0]) if len(df) else None,
                                    "last": str(df.index[-1]) if len(df) else None}
                except DG.ReservedDataError as e:
                    cov[sym][tf] = {"unavailable": str(e)}
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"purpose": "fingerprint of the cached V5 exploration data; see research/v5_manifest.py",
            "freeze": str(FREEZE), "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "git_head_at_generation": head, "file_count": len(files), "combined_sha256": combined.hexdigest(),
            "eval_symbols": list(DG.EVAL_SYMBOLS), "excluded_from_pooling": sorted(set(DG.EXPLORATION) - set(DG.EVAL_SYMBOLS)),
            "files": files, "coverage": cov}


def verify(manifest: dict | Path = MANIFEST, data_dir: Path | None = None) -> dict:
    """{"missing": [...], "changed": [...], "extra": [...]} (all empty when the cache matches)."""
    m = json.loads(Path(manifest).read_text()) if not isinstance(manifest, dict) else manifest
    d = Path(data_dir or data.DATA_DIR)
    present = {p.name for p in d.glob("*.csv.gz")}
    missing = sorted(n for n in m["files"] if n not in present)
    changed = sorted(n for n, f in m["files"].items() if n in present and sha_file(d / n) != f["sha256"])
    extra = sorted(present - set(m["files"]))
    return {"missing": missing, "changed": changed, "extra": extra}


def files_for(symbol: str, tf: str, manifest: dict | Path = MANIFEST) -> list[str]:
    """Cache files a guarded load of (symbol, tf) reads, for the trial ledger's data_files."""
    m = json.loads(Path(manifest).read_text()) if not isinstance(manifest, dict) else manifest
    native = DG.NATIVE[tf]
    safe = symbol.replace("=", "_").replace("^", "_")
    names = [f"{safe}_{native}.csv.gz", f"{safe}_1d.csv.gz"]       # 1d is always read (integrity rule)
    return sorted({str(data.DATA_DIR / n) for n in names if n in m["files"]})


if __name__ == "__main__":
    out = build()
    MANIFEST.write_text(json.dumps(out, indent=1))
    print(out["file_count"], "files; combined sha256", out["combined_sha256"])
