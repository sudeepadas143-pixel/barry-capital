# V5 validation protocol, Amendment 1: small-cluster inference (PROPOSED, NOT IN FORCE)

| | |
|---|---|
| amends | [`V5_VALIDATION_PROTOCOL.md`](V5_VALIDATION_PROTOCOL.md) §5 (sample minimums and dependence) and the inference parts of §6 |
| version | protocol 1.0 → 1.1 if adopted |
| status | **PROPOSED.** Not applied to any confirmatory result. Adoption requires the external review (audit blocker B1) to approve it in writing, then a commit that changes this status line to "ADOPTED" and records the date. It must be adopted, or replaced, before any G3 (confirmatory) run |
| motivation | audit finding S1 (`V5_INDEPENDENT_AUDIT.md`): the percentile cluster bootstrap is anti-conservative with few clusters, and the protocol allows G = 8 |
| written | 2026-10-27, before any V5 detector output existed |

## Change

1. **Decision statistic.** For every mean-excess or lift test (A–D):
   * the wild cluster bootstrap with the null imposed (`research.v5_inference.cluster_mean_test`):
     Rademacher weights when G ≥ 12, Webb six-point weights when G < 12, 9,999 replicates;
   * one-sided when the hypothesis is directional;
   * the t(G−1) confidence interval from the same CR1 standard error is reported as the interval.

   The existing percentile cluster bootstrap stays as a secondary statistic, for continuity with
   V4.1.
2. **Minimum clusters.**
   * Exploratory decisions (variant selection, rejection at exploration): G ≥ 10.
   * **Confirmatory (G3) cells: G ≥ 20.** A cell below that is reported but cannot pass a gate.
   * The other minimums (signals, instruments) are unchanged.
3. **Multiple testing.** Holm within each family, applied to the wild-bootstrap p-values.
   Unchanged otherwise.

## Assumptions (stated; they limit what the method supports)

* Calendar blocks are independent of each other. Dependence across block edges is ignored.
  Blocks are 1H 1 month, 4H 2 months, 1D 3 months, 1W 12 months.
* Arbitrary dependence within a block is allowed: across instruments and across overlapping
  outcome windows.
* Cluster sizes are not wildly unequal. They are reported, and very unequal sizes weaken the
  method.
* Per-unit benchmarks are treated as fixed. That is exact for the causal benchmark; for
  whole-window benchmarks it ignores their estimation error, which is small when benchmark
  samples are much larger than signal samples.

## Why this method

* **The literature.** The wild cluster restricted bootstrap and t(G−1) reference distributions
  are the standard recommendations for few clusters (Cameron, Gelbach & Miller 2008; MacKinnon &
  Webb 2017; Webb's weights for very small G).
* **A synthetic check.** This is a method check on simulated null data, not an empirical result.
  * Setup: mean-zero units sharing heavy-tailed t(3) shocks within each cluster; cluster sizes
    20–200; 400 simulations; one-sided test at nominal 5%.
  * Rejection rates:

    | G | percentile bootstrap | wild bootstrap | t(G−1) |
    |---:|---:|---:|---:|
    | 8 | 8.5% | 3.8% | 3.3% |
    | 12 | 9.5% | 5.8% | 6.0% |
    | 20 | 7.0% | 4.8% | 6.0% |

  * `tests/test_v5_baselines.py::test_wild_cluster_test_holds_size_where_percentile_bootstrap_over_rejects`
    re-checks the G = 8 case.

## What it does not fix

* Dependence across block edges.
* 1D/1W label windows longer than their blocks (audit U5): those need longer blocks before any
  1D/1W evaluation.
* The trial count of exploration. It is disclosed, not corrected for.
