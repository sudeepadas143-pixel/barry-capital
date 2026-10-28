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
# workstream M (reports/V5_M_B_CONFIG.md §10.5)
M_CONFIG = "reports/V5_M_B_CONFIG.md"
M_CODE = ("research/v5_context.py", "research/v5_inference.py", "scripts/v5_m_explore.py")
# HC-MTF 6.0 stage 1 (reports/V6_CONT_CONFIG.md §11.3)
V6_CONFIG = "reports/V6_CONT_CONFIG.md"
V6_CODE = ("research/v6_signals.py", "research/v5_context.py", "research/v5_inference.py", "scripts/v6_cont_explore.py")
# cycle engine CY-1 (reports/CYCLE_CONFIG.md §8)
CY_CONFIG = "reports/CYCLE_CONFIG.md"
CY_CODE = ("research/cycle_features.py", "scripts/cycle_research.py", "research/v5_inference.py")
CY2_CONFIG = "reports/CYCLE2_CONFIG.md"
CY2_CODE = CY_CODE + ("research/cycle2_features.py", "scripts/cycle2_research.py")
KB_CONFIG = "reports/KB_CONFIG.md"
KB_CODE = CY2_CODE + ("research/kb_signals.py", "scripts/kb_bench.py")
KC_CONFIG = "reports/KC_CONFIG.md"
KW_CONFIG = "reports/KW_CONFIG.md"
KW_CODE = CY2_CODE + ("research/kenny_sim.py", "research/kenny_cluster.py", "research/kenny_weekly.py", "scripts/kw_eval.py", "scripts/kenny_export_pine.py")
KW2_CONFIG = "reports/KW2_CONFIG.md"
KW2_CODE = KW_CODE + ("scripts/kw2_eval.py",)
KW3D_CONFIG = "reports/KW3_DIAG_CONFIG.md"
KW3D_CODE = CY2_CODE + ("research/kenny_sim.py", "research/kenny_weekly_sell.py", "scripts/kw3_eval.py", "scripts/kenny_export_pine.py")
KW3_CONFIG = "reports/KW3_CONFIG.md"
KW3_CODE = KW3D_CODE + ("reports/kw3_grid.json",)
KW4_CONFIG = "reports/KW4_CONFIG.md"
KW4_CODE = KW3_CODE + ("scripts/kw4_eval.py",)
KW5_CONFIG = "reports/KW5_CONFIG.md"
KW5_CODE = KW3_CODE + ("scripts/kw5_eval.py",)
KW6_CONFIG = "reports/KW6_SPEC.md"
KW6_CODE = KW3_CODE + ("research/weekly_cycle.py", "scripts/kw6_eval.py")
KR_CONFIG = "reports/KR_CONFIG.md"
KR_CODE = CY2_CODE + ("research/kenny_sim.py", "research/kenny_retro.py", "research/kenny_weekly_sell.py", "research/weekly_cycle.py",
                      "scripts/kr_eval.py", "scripts/kenny_export_pine.py")
KS_CONFIG = "reports/KS_CONFIG.md"
KS_CODE = KR_CODE + ("research/kenny_strength.py", "research/kenny_cluster.py", "scripts/ks_eval.py")
KT_CONFIG = "reports/KT_CONFIG.md"
KT_CODE = KR_CODE + ("research/kenny_types.py", "scripts/kt_eval.py")
KF_CONFIG = "reports/KF_CONFIG.md"
KF_CODE = KT_CODE + ("research/kenny_freq.py", "scripts/kf_eval.py")
KC_CODE = KB_CODE + ("research/kenny_sim.py", "research/kenny_cluster.py", "scripts/kc_eval.py", "scripts/kenny_export_pine.py")


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


def m_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    """Workstream M (crypto BTC-regime context) exploration gate: review mode valid (independent
    or the self-audited exploration waiver), the M configuration committed, unmodified and
    FROZEN, baselines and the M code committed and unmodified, and the cache equal to the
    manifest. c_blockers() and confirmatory_blockers() are unaffected."""
    out = []
    if review_mode(root) is None:
        out += _review_problems(root) + _waiver_problems(root)
    if not committed_and_clean(M_CONFIG, root):
        out.append(f"M1: {M_CONFIG} missing, uncommitted or modified")
    elif "Status: FROZEN" not in (root / M_CONFIG).read_text():
        out.append(f"M1: {M_CONFIG} is not frozen (Status: FROZEN absent)")
    for f in (BASELINES, *M_CODE):
        if not committed_and_clean(f, root):
            out.append(f"M2: {f} missing, uncommitted or modified")
    if not committed_and_clean(MANIFEST, root):
        out.append(f"M3: {MANIFEST} missing, uncommitted or modified")
    elif check_cache:
        from .v5_manifest import verify
        v = verify(root / MANIFEST)
        if any(v.values()):
            out.append(f"M3: cache differs from the manifest: {v}")
    return out


def require_m_ready(root: Path = ROOT) -> str:
    """Raise if any workstream-M blocker remains; otherwise return the review mode."""
    b = m_blockers(root)
    if b:
        raise NotReady("workstream-M evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def v6_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    """HC-MTF 6.0 stage-1 exploration gate: valid review mode (independent or the self-audited
    exploration waiver), the V6 configuration committed, unmodified and FROZEN, baselines and the
    V6 code committed and unmodified, and the cache equal to the manifest."""
    out = []
    if review_mode(root) is None:
        out += _review_problems(root) + _waiver_problems(root)
    if not committed_and_clean(V6_CONFIG, root):
        out.append(f"V1: {V6_CONFIG} missing, uncommitted or modified")
    elif "Status: FROZEN" not in (root / V6_CONFIG).read_text():
        out.append(f"V1: {V6_CONFIG} is not frozen (Status: FROZEN absent)")
    for f in (BASELINES, *V6_CODE):
        if not committed_and_clean(f, root):
            out.append(f"V2: {f} missing, uncommitted or modified")
    if not committed_and_clean(MANIFEST, root):
        out.append(f"V3: {MANIFEST} missing, uncommitted or modified")
    elif check_cache:
        from .v5_manifest import verify
        v = verify(root / MANIFEST)
        if any(v.values()):
            out.append(f"V3: cache differs from the manifest: {v}")
    return out


def require_v6_ready(root: Path = ROOT) -> str:
    """Raise if any V6 blocker remains; otherwise return the review mode."""
    b = v6_blockers(root)
    if b:
        raise NotReady("HC-MTF 6.0 evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def cy_blockers(root: Path = ROOT, check_cache: bool = True, config: str = CY_CONFIG, code: tuple = CY_CODE) -> list[str]:
    """Cycle-engine exploration gate (CY-1 by default; CY-2 via cy2_blockers): valid review mode,
    config committed, unmodified and FROZEN, baselines and code committed and unmodified, cache
    equal to the manifest."""
    CY_CONFIG, CY_CODE = config, code                                   # noqa: N806 (local override)
    out = []
    if review_mode(root) is None:
        out += _review_problems(root) + _waiver_problems(root)
    if not committed_and_clean(CY_CONFIG, root):
        out.append(f"Y1: {CY_CONFIG} missing, uncommitted or modified")
    elif "Status: FROZEN" not in (root / CY_CONFIG).read_text():
        out.append(f"Y1: {CY_CONFIG} is not frozen (Status: FROZEN absent)")
    for f in (BASELINES, *CY_CODE):
        if not committed_and_clean(f, root):
            out.append(f"Y2: {f} missing, uncommitted or modified")
    if not committed_and_clean(MANIFEST, root):
        out.append(f"Y3: {MANIFEST} missing, uncommitted or modified")
    elif check_cache:
        from .v5_manifest import verify
        v = verify(root / MANIFEST)
        if any(v.values()):
            out.append(f"Y3: cache differs from the manifest: {v}")
    return out


def cy2_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, CY2_CONFIG, CY2_CODE)


def kb_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KB_CONFIG, KB_CODE)


def kc_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KC_CONFIG, KC_CODE)


def kw_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KW_CONFIG, KW_CODE)


def require_kw_ready(root: Path = ROOT) -> str:
    b = kw_blockers(root)
    if b:
        raise NotReady("KW weekly evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def kw2_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KW2_CONFIG, KW2_CODE)


def require_kw2_ready(root: Path = ROOT) -> str:
    b = kw2_blockers(root)
    if b:
        raise NotReady("KW-2 weekly evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def kw3d_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KW3D_CONFIG, KW3D_CODE)


def require_kw3d_ready(root: Path = ROOT) -> str:
    b = kw3d_blockers(root)
    if b:
        raise NotReady("KW-3 diagnosis is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def kw3_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KW3_CONFIG, KW3_CODE)


def require_kw3_ready(root: Path = ROOT) -> str:
    b = kw3_blockers(root)
    if b:
        raise NotReady("KW-3 evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def kw4_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KW4_CONFIG, KW4_CODE)


def require_kw4_ready(root: Path = ROOT) -> str:
    b = kw4_blockers(root)
    if b:
        raise NotReady("KW-4 evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def kw5_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KW5_CONFIG, KW5_CODE)


def require_kw5_ready(root: Path = ROOT) -> str:
    b = kw5_blockers(root)
    if b:
        raise NotReady("KW-5 evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def kw6_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KW6_CONFIG, KW6_CODE)


def require_kw6_ready(root: Path = ROOT) -> str:
    b = kw6_blockers(root)
    if b:
        raise NotReady("KW-6 evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def kr_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KR_CONFIG, KR_CODE)


def require_kr_ready(root: Path = ROOT) -> str:
    b = kr_blockers(root)
    if b:
        raise NotReady("KR evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def ks_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KS_CONFIG, KS_CODE)


def require_ks_ready(root: Path = ROOT) -> str:
    b = ks_blockers(root)
    if b:
        raise NotReady("KS evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def kt_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KT_CONFIG, KT_CODE)


def require_kt_ready(root: Path = ROOT) -> str:
    b = kt_blockers(root)
    if b:
        raise NotReady("KT evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def kf_blockers(root: Path = ROOT, check_cache: bool = True) -> list[str]:
    return cy_blockers(root, check_cache, KF_CONFIG, KF_CODE)


def require_kf_ready(root: Path = ROOT) -> str:
    b = kf_blockers(root)
    if b:
        raise NotReady("KF evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def require_kc_ready(root: Path = ROOT) -> str:
    b = kc_blockers(root)
    if b:
        raise NotReady("KC cluster evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def require_kb_ready(root: Path = ROOT) -> str:
    b = kb_blockers(root)
    if b:
        raise NotReady("KB benchmark is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def require_cy2_ready(root: Path = ROOT) -> str:
    b = cy2_blockers(root)
    if b:
        raise NotReady("cycle-engine CY-2 evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def require_cy_ready(root: Path = ROOT) -> str:
    b = cy_blockers(root)
    if b:
        raise NotReady("cycle-engine evaluation is blocked:\n  " + "\n  ".join(b))
    return review_mode(root)


def confirmatory_blockers(root: Path = ROOT) -> list[str]:
    """Confirmatory (G3) runs need an INDEPENDENT review and the small-cluster amendment adopted
    for confirmatory scope. A self-audit waiver never satisfies this."""
    out = _review_problems(root)
    amd = root / "reports" / "V5_PROTOCOL_AMENDMENT_1.md"
    if not amd.exists() or "CONFIRMATORY SCOPE: ADOPTED" not in amd.read_text():
        out.append("S1: protocol Amendment 1 is not adopted for confirmatory scope")
    return out
