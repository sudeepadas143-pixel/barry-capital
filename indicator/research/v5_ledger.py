"""V5 trial ledger (reports/V5_HYPOTHESIS_REGISTER.md §4): every evaluated variant is recorded.

Append-only JSON Lines at reports/V5_TRIAL_LEDGER.jsonl (machine-checkable; replaces the
".md" name written in the register before the format was designed; recorded in the plan).

Each record: trial_id, hypothesis_id, partitions, recorded_at (UTC), code fingerprint (sha256
per file + git HEAD + whether those files had uncommitted changes), config fingerprint (sha256
of canonical JSON), metrics_requested, outcomes_accessed, notes, prev_hash, record_hash.

Protections
* prev_hash chains every record to the one before; record_hash covers the whole record. Any
  edit, deletion or reordering of earlier lines breaks verify().
* record() verifies the chain before appending and refuses a trial_id that already exists, so a
  trial can never be silently overwritten or re-recorded with different results.
* The file is only ever opened in append mode.
* Partitions: only "exploration" is accepted. Reserved partitions ("reserve_xs", "forward")
  require a confirmatory pre-registration path that exists in the repository; until a family
  reaches gate G2 no such path exists, so they are refused.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "reports" / "V5_TRIAL_LEDGER.jsonl"
HYPOTHESES = ("A1", "A2", "B1", "B2", "B3", "C1", "C2", "C3", "C4", "C5",
              "D1", "D2", "D3", "D4", "D5", "E1", "E2", "E3")
PARTITIONS = ("exploration", "reserve_xs", "forward")
GENESIS = "0" * 64


class LedgerError(RuntimeError):
    pass


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha(s: str | bytes) -> str:
    return hashlib.sha256(s.encode() if isinstance(s, str) else s).hexdigest()


def code_fingerprint(files: list[str], root: Path = ROOT) -> dict:
    out = {"files": {f: sha((root / f).read_bytes()) for f in sorted(files)}}
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", *files], cwd=root,
                               capture_output=True, text=True).stdout.strip()
    except Exception:  # pragma: no cover - git unavailable
        head, dirty = "", "unknown"
    out["git_head"], out["uncommitted_changes"] = head, bool(dirty)
    return out


def read(path: Path = LEDGER) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def verify(path: Path = LEDGER) -> list[dict]:
    recs = read(path)
    prev = GENESIS
    seen = set()
    for k, r in enumerate(recs):
        body = {key: v for key, v in r.items() if key != "record_hash"}
        if r.get("prev_hash") != prev:
            raise LedgerError(f"chain broken at record {k} ({r.get('trial_id')})")
        if sha(_canon(body)) != r.get("record_hash"):
            raise LedgerError(f"record {k} ({r.get('trial_id')}) was modified")
        if r["trial_id"] in seen:
            raise LedgerError(f"duplicate trial_id {r['trial_id']}")
        seen.add(r["trial_id"])
        prev = r["record_hash"]
    return recs


def record(trial_id: str, hypothesis_id: str, partitions: list[str], config: dict, code_files: list[str],
           metrics_requested: list[str], outcomes_accessed: bool, notes: str = "",
           confirmatory_prereg: str | None = None, path: Path = LEDGER, root: Path = ROOT) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,80}", trial_id or ""):
        raise LedgerError("trial_id must be 3-81 characters of letters, digits, . _ -")
    if hypothesis_id not in HYPOTHESES:
        raise LedgerError(f"unregistered hypothesis {hypothesis_id!r}")
    if not partitions or any(p not in PARTITIONS for p in partitions):
        raise LedgerError(f"unknown partition in {partitions}")
    if any(p != "exploration" for p in partitions):
        if not confirmatory_prereg or not (root / confirmatory_prereg).is_file():
            raise LedgerError("reserved partitions need an existing confirmatory pre-registration file")
    if not isinstance(outcomes_accessed, bool):
        raise LedgerError("outcomes_accessed must be True or False")
    recs = verify(path)
    if any(r["trial_id"] == trial_id for r in recs):
        raise LedgerError(f"trial {trial_id} already recorded; trials are never overwritten")
    body = {
        "trial_id": trial_id, "hypothesis_id": hypothesis_id, "partitions": list(partitions),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code": code_fingerprint(code_files, root), "config": config, "config_sha256": sha(_canon(config)),
        "metrics_requested": list(metrics_requested), "outcomes_accessed": outcomes_accessed,
        "confirmatory_prereg": confirmatory_prereg, "notes": notes,
        "prev_hash": recs[-1]["record_hash"] if recs else GENESIS,
    }
    body["record_hash"] = sha(_canon(body))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(body, sort_keys=True) + "\n")
    return body
