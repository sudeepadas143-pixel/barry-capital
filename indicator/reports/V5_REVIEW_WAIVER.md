# V5 review waiver (family C, first exploration)

External review: UNAVAILABLE
Self-audit: COMPLETED
Scope: EXPLORATION ONLY
Self-audit report: reports/V5_SELF_AUDIT.md

* **Why this exists.** The project owner instructed on 2026-10-27 that no external reviewer is
  available and that the work should not wait for one. The owner also instructed that
  independent review must not be marked complete. It is not.
* **What it permits.** `research.v5_gate.require_c_ready()` accepts this waiver for the first
  family-C exploration only, and returns the mode `self_audited_exploration_only`. Every result
  produced in that mode carries the label.
* **What it does not permit.** It never satisfies `research.v5_gate.confirmatory_blockers()`.
  Selecting variants for G2, running the reserve-instrument check (G3a) or the forward test (G3b)
  all need an independent review. So does adopting protocol Amendment 1 for confirmatory scope.
* **Signed by**: the authoring agent, recording the owner's instruction. Not an approval.
