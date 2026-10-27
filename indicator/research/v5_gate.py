"""Readiness gate for the first V5 family-C (major tops) exploration (audit blockers B1-B5).

c_blockers() lists every unmet condition; any evaluation runner for family C must call
require_c_ready() first and stop if anything is listed. Conditions:

* B1 external review: reports/V5_EXTERNAL_REVIEW.md committed and unmodified, containing
  "Decision: APPROVED", "Reviewer is not the author: yes" and "Reviewed commit: <hash>".
  (Code cannot verify who the reviewer is; the file is the reviewer's signed statement.)
* B2 baselines: research/v5_baselines.py committed and unmodified.
* B3/B5 configuration: reports/V5_C_EXPLORATION_CONFIG.md committed and unmodified with
  "Status: FROZEN" (a DRAFT does not pass).
* B4 data: reports/V5_EXPLORATION_DATA_MANIFEST.json committed and unmodified, and the cache
  matches it (no missing, changed or extra files).
* detector code: research/v5_detect_c.py committed and unmodified (written only after the
  configuration is frozen).
The full test suite must also pass; the runner records that in the trial ledger (code cannot
check its own test run here).
"""

from __future__ import annotations

from pathlib import Path

from .v5_ledger import ROOT, committed_and_clean

REVIEW = "reports/V5_EXTERNAL_REVIEW.md"
CONFIG = "reports/V5_C_EXPLORATION_CONFIG.md"
MANIFEST = "reports/V5_EXPLORATION_DATA_MANIFEST.json"
BASELINES = "research/v5_baselines.py"
DETECTORS = "research/v5_detect_c.py"


class NotReady(RuntimeError):
    pass


def c_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    out = []
    if not committed_and_clean(REVIEW, root):
        out.append(f"B1: {REVIEW} missing, uncommitted or modified")
    else:
        t = (root / REVIEW).read_text()
        for need in ("Decision: APPROVED", "Reviewer is not the author: yes", "Reviewed commit:"):
            if need not in t:
                out.append(f"B1: {REVIEW} lacks '{need}'")
    if not committed_and_clean(BASELINES, root):
        out.append(f"B2: {BASELINES} missing, uncommitted or modified")
    if not committed_and_clean(CONFIG, root):
        out.append(f"B5: {CONFIG} missing, uncommitted or modified")
    elif "Status: FROZEN" not in (root / CONFIG).read_text():
        out.append(f"B5: {CONFIG} is not frozen (Status: FROZEN absent)")
    if not committed_and_clean(MANIFEST, root):
        out.append(f"B4: {MANIFEST} missing, uncommitted or modified")
    elif check_cache:
        from .v5_manifest import verify
        v = verify(root / MANIFEST)
        if any(v.values()):
            out.append(f"B4: cache differs from the manifest: {v}")
    if not committed_and_clean(DETECTORS, root):
        out.append(f"detectors: {DETECTORS} missing, uncommitted or modified")
    return out


def require_c_ready(root: Path = ROOT) -> None:
    b = c_blockers(root)
    if b:
        raise NotReady("family-C evaluation is blocked:\n  " + "\n  ".join(b))
