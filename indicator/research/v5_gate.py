"""Readiness gate for the first V5 family-C (major tops) exploration (audit blockers B1-B5).

c_blockers() lists every unmet condition; any evaluation runner for family C must call
require_c_ready() first and stop if anything is listed. Conditions:

* B1 review, one of:
  - INDEPENDENT: reports/V5_EXTERNAL_REVIEW.md committed and unmodified, containing
    "Decision: APPROVED", "Reviewer is not the author: yes" and "Reviewed commit: <hash>"
    (code cannot verify who the reviewer is; the file is the reviewer's signed statement); or
  - SELF-AUDITED WAIVER (exploration only): reports/V5_REVIEW_WAIVER.md committed and unmodified,
    containing "External review: UNAVAILABLE", "Self-audit: COMPLETED", "Scope: EXPLORATION ONLY"
    and "Self-audit report: reports/V5_SELF_AUDIT.md", with that report committed. Results run in
    this mode must be labelled self-audited; the waiver never satisfies confirmatory_blockers().
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
WAIVER = "reports/V5_REVIEW_WAIVER.md"
SELF_AUDIT = "reports/V5_SELF_AUDIT.md"
CONFIG = "reports/V5_C_EXPLORATION_CONFIG.md"
MANIFEST = "reports/V5_EXPLORATION_DATA_MANIFEST.json"
BASELINES = "research/v5_baselines.py"
DETECTORS = "research/v5_detect_c.py"


class NotReady(RuntimeError):
    pass


def _review_problems(root: Path) -> list[str]:
    if not committed_and_clean(REVIEW, root):
        return [f"B1: {REVIEW} missing, uncommitted or modified"]
    t = (root / REVIEW).read_text()
    return [f"B1: {REVIEW} lacks '{need}'" for need in
            ("Decision: APPROVED", "Reviewer is not the author: yes", "Reviewed commit:") if need not in t]


def _waiver_problems(root: Path) -> list[str]:
    if not committed_and_clean(WAIVER, root):
        return [f"B1 waiver: {WAIVER} missing, uncommitted or modified"]
    t = (root / WAIVER).read_text()
    out = [f"B1 waiver: {WAIVER} lacks '{need}'" for need in
           ("External review: UNAVAILABLE", "Self-audit: COMPLETED", "Scope: EXPLORATION ONLY",
            f"Self-audit report: {SELF_AUDIT}") if need not in t]
    if not committed_and_clean(SELF_AUDIT, root):
        out.append(f"B1 waiver: {SELF_AUDIT} missing, uncommitted or modified")
    return out


def review_mode(root: Path = ROOT) -> str | None:
    """"independent", "self_audited_exploration_only", or None (no valid review state)."""
    if not _review_problems(root):
        return "independent"
    if not _waiver_problems(root):
        return "self_audited_exploration_only"
    return None


def c_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    out = []
    if review_mode(root) is None:
        out += _review_problems(root) + _waiver_problems(root)
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


def require_c_ready(root: Path = ROOT) -> str:
    """Raise if any blocker remains; otherwise return the review mode to stamp on every result."""
    b = c_blockers(root)
    if b:
        raise NotReady("family-C evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def confirmatory_blockers(root: Path = ROOT) -> list[str]:
    """Confirmatory (G3) runs need an INDEPENDENT review and the small-cluster amendment adopted
    for confirmatory scope. A self-audit waiver never satisfies this."""
    out = _review_problems(root)
    amd = root / "reports" / "V5_PROTOCOL_AMENDMENT_1.md"
    if not amd.exists() or "CONFIRMATORY SCOPE: ADOPTED" not in amd.read_text():
        out.append("S1: protocol Amendment 1 is not adopted for confirmatory scope")
    return out
