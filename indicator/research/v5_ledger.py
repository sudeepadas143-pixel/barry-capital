"""V5 trial ledger (reports/V5_HYPOTHESIS_REGISTER.md §4): every evaluated variant is recorded.

Append-only JSON Lines at reports/V5_TRIAL_LEDGER.jsonl (machine-checkable; replaces the
".md" name written in the register before the format was designed; recorded in the plan).

Each record: trial_id, hypothesis_id, partitions, recorded_at (UTC), code fingerprint (sha256
per file + git HEAD + whether those files had uncommitted changes), config fingerprint (sha256
of canonical JSON) and the committed configuration FILE it came from, a DATA fingerprint (sha256
per data file read; detects vendor revisions of cached candles), metrics_requested,
outcomes_accessed, notes, prev_hash, record_hash.

Protections
* prev_hash chains every record to the one before; record_hash covers the whole record. Any
  edit, deletion or reordering of earlier lines breaks verify().
* record() verifies the chain before appending and refuses a trial_id that already exists, so a
  trial can never be silently overwritten or re-recorded with different results.
* The file is only ever opened in append mode.
* Every trial must name a configuration file that is committed in git and unmodified (the
  configuration is pre-registered before outcomes are computed).
* Partitions: only "exploration" is accepted. Reserved partitions ("reserve_xs", "forward")
  require a confirmatory pre-registration that is committed and unmodified, lives at
  reports/V5_*PREREG*.md and names the hypothesis id; until a family reaches gate G2 none exists.
* Appends are serialised with an exclusive file lock. A local chain cannot detect deletion of
  the whole file or of its newest records; verify_against_git() checks that the committed ledger
  is a prefix of the working one (commit the ledger after every trial).
* outcomes_accessed is self-reported: the ledger records it, it cannot verify it.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "reports" / "V5_TRIAL_LEDGER.jsonl"
HYPOTHESES = ("A1", "A2", "B1", "B2", "B3", "C1", "C2", "C3", "C4", "C5",
              "D1", "D2", "D3", "D4", "D5", "E1", "E2", "E3",
              "M-A", "M-B1", "M-B2", "M-B3", "M-B4",           # workstream M: reports/V5_M_B_CONFIG.md
              "V6-P", "V6-S",
              "CY-1W", "CY-1D", "CY-4H", "CY-1H",
              "CY2-1W", "CY2-1D", "CY2-4H", "CY2-1H",
              "KB-1W", "KB-1D", "KB-4H", "KB-1H", "KC-1", "KW-1", "KW-2", "KW-3D", "KW-3", "KW-4", "KW-5", "KW-6")  # cycle engine CY-1: reports/CYCLE_CONFIG.md                                 # HC-MTF 6.0 stage 1: reports/V6_CONT_CONFIG.md
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


def _git(root: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def committed_and_clean(rel: str, root: Path = ROOT) -> bool:
    """True if `rel` is tracked by git and has no uncommitted changes."""
    if not (root / rel).is_file():
        return False
    if _git(root, "ls-files", "--error-unmatch", rel).returncode != 0:
        return False
    return _git(root, "status", "--porcelain", "--", rel).stdout.strip() == ""


def data_fingerprint(files: list[str], root: Path = ROOT) -> dict:
    out = {}
    for f in sorted(files):
        p = Path(f) if Path(f).is_absolute() else root / f
        out[str(f)] = sha(p.read_bytes())
    return out


def verify_against_git(path: Path = LEDGER, rev: str = "HEAD", root: Path = ROOT) -> None:
    """The ledger committed at `rev` must be a prefix of the working ledger (no rewritten,
    deleted or truncated history). A ledger not yet committed passes trivially."""
    rel = str(path.relative_to(root)) if path.is_absolute() and root in path.parents else str(path)
    r = _git(root, "show", f"{rev}:{rel}")
    if r.returncode != 0:
        return
    if not (path.read_text() if path.exists() else "").startswith(r.stdout):
        raise LedgerError(f"working ledger does not extend the ledger committed at {rev}")


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
           metrics_requested: list[str], outcomes_accessed: bool, config_file: str, data_files: list[str],
           notes: str = "", confirmatory_prereg: str | None = None, path: Path = LEDGER, root: Path = ROOT) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,80}", trial_id or ""):
        raise LedgerError("trial_id must be 3-81 characters of letters, digits, . _ -")
    if hypothesis_id not in HYPOTHESES:
        raise LedgerError(f"unregistered hypothesis {hypothesis_id!r}")
    if not partitions or any(p not in PARTITIONS for p in partitions):
        raise LedgerError(f"unknown partition in {partitions}")
    if any(p != "exploration" for p in partitions):
        ok = (confirmatory_prereg is not None
              and re.fullmatch(r"reports/V5_[A-Za-z0-9_]*PREREG[A-Za-z0-9_]*\.md", confirmatory_prereg)
              and committed_and_clean(confirmatory_prereg, root)
              and hypothesis_id in (root / confirmatory_prereg).read_text())
        if not ok:
            raise LedgerError("reserved partitions need a committed, unmodified reports/V5_*PREREG*.md naming the hypothesis")
    if not isinstance(outcomes_accessed, bool):
        raise LedgerError("outcomes_accessed must be True or False")
    if not config_file or not committed_and_clean(config_file, root):
        raise LedgerError("config_file must be committed in git and unmodified before a trial is recorded")
    if not data_files:
        raise LedgerError("data_files must list every data file the trial read")
    dfp = data_fingerprint(data_files, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            return _append(fh, path, trial_id, hypothesis_id, partitions, config, code_files, metrics_requested,
                           outcomes_accessed, config_file, dfp, notes, confirmatory_prereg, root)
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _append(fh, path, trial_id, hypothesis_id, partitions, config, code_files, metrics_requested,
            outcomes_accessed, config_file, dfp, notes, confirmatory_prereg, root) -> dict:
    recs = verify(path)
    if any(r["trial_id"] == trial_id for r in recs):
        raise LedgerError(f"trial {trial_id} already recorded; trials are never overwritten")
    body = {
        "trial_id": trial_id, "hypothesis_id": hypothesis_id, "partitions": list(partitions),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code": code_fingerprint(code_files, root), "config": config, "config_sha256": sha(_canon(config)),
        "config_file": config_file, "config_file_sha256": sha((root / config_file).read_bytes()), "data": dfp,
        "metrics_requested": list(metrics_requested), "outcomes_accessed": outcomes_accessed,
        "confirmatory_prereg": confirmatory_prereg, "notes": notes,
        "prev_hash": recs[-1]["record_hash"] if recs else GENESIS,
    }
    body["record_hash"] = sha(_canon(body))
    fh.write(json.dumps(body, sort_keys=True) + "\n")
    fh.flush()
    return body
