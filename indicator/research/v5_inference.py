"""Small-cluster inference for V5 (audit finding S1; PROPOSED protocol amendment 1,
reports/V5_PROTOCOL_AMENDMENT_1.md, not in force until adopted).

Problem: the percentile cluster bootstrap used so far (research.v41.boot_excess) is
anti-conservative when the number of clusters G is small (the protocol allows G = 8): its
intervals are too narrow and its p-values too small.

Method (for a mean of unit-level values x_u, e.g. per-unit excess over a benchmark, with units
grouped into G calendar-block clusters shared by all instruments):

* point estimate: the pooled unit mean  m = sum_u x_u / n.
* cluster-robust standard error (CR1): with cluster residual sums s_g = sum_{u in g} (x_u - m),
  se^2 = G/(G-1) * sum_g s_g^2 / n^2.  Test statistic t = m / se.
* reference distribution 1 (analytic): Student t with G-1 degrees of freedom.
* reference distribution 2 (primary): WILD CLUSTER BOOTSTRAP with the null imposed (WCR):
  x*_u = 0 + w_g * (x_u - m)  with one weight w_g per cluster, re-compute t*; p = share of
  |t*| >= |t| (two-sided) or t* >= t (one-sided, H1: mean > 0). Weights: Rademacher (+-1) when
  G >= 12, Webb's six-point distribution when G < 12 (Rademacher has only 2^G distinct draws).
* confidence interval: by test inversion would be best; for simplicity the reported 95% interval
  is m +- t_{G-1, 0.975} * se, and the wild-bootstrap p-value is the decision statistic.

Assumptions (stated, not tested by the code):
1. clusters are independent of each other (dependence across block edges is ignored);
2. within a cluster, any dependence across instruments and overlapping outcome windows is
   allowed;
3. clusters are roughly comparable in size; very unequal cluster sizes weaken both references
   (cluster sizes are reported so this can be checked);
4. the benchmark of each unit is treated as fixed. For whole-window benchmarks estimated from the
   same data this ignores benchmark estimation error (small when benchmark samples are much larger
   than signal samples); the causal benchmark (research.v5_eval.causal_benchmark) depends only on
   the past and is fixed by construction.

What it supports: an approximately valid test of "mean excess = 0" with as few as about 10
clusters (simulation evidence in the econometrics literature: Cameron, Gelbach & Miller 2008;
MacKinnon & Webb 2017; Webb 2023). What it does not: exact inference, independence across
blocks, multiplicity correction, or any correction for exploratory trial counts.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])


def _cluster_sums(x: np.ndarray, cl: np.ndarray):
    u, inv = np.unique(cl, return_inverse=True)
    return u, inv


def cr1(x: np.ndarray, inv: np.ndarray, G: int, m: float) -> float:
    s = np.bincount(inv, weights=x - m, minlength=G)
    n = len(x)
    return float(np.sqrt(G / (G - 1) * np.sum(s ** 2)) / n)


def cluster_mean_test(x, clusters, reps: int = 9999, seed: int = 20261027, alternative: str = "greater",
                      weights: str | None = None) -> dict:
    """Mean of x with cluster-robust t (G-1 df) and wild cluster bootstrap (null imposed)."""
    x = np.asarray(x, float)
    cl = np.asarray(clusters)
    ok = ~np.isnan(x)
    x, cl = x[ok], cl[ok]
    u, inv = _cluster_sums(x, cl)
    G, n = len(u), len(x)
    out = {"n": int(n), "clusters": int(G), "cluster_sizes": np.bincount(inv).tolist() if n else []}
    if G < 2 or n < 2:
        out.update({"mean": float(x.mean()) if n else None, "valid": False, "why": "fewer than 2 clusters"})
        return out
    m = float(x.mean())
    se = cr1(x, inv, G, m)
    t = m / se if se > 0 else np.inf * np.sign(m)
    q = stats.t.ppf(0.975, G - 1)
    if alternative == "greater":
        p_t = float(stats.t.sf(t, G - 1))
    elif alternative == "two-sided":
        p_t = float(2 * stats.t.sf(abs(t), G - 1))
    else:
        raise ValueError(alternative)
    wkind = weights or ("rademacher" if G >= 12 else "webb")
    rng = np.random.default_rng(seed)
    if wkind == "rademacher":
        W = rng.choice([-1.0, 1.0], size=(reps, G))
    elif wkind == "webb":
        W = rng.choice(WEBB, size=(reps, G))
    else:
        raise ValueError(wkind)
    r = x - m                                   # residuals under H0: mean = 0 (null imposed)
    rs = np.bincount(inv, weights=r, minlength=G)            # cluster residual sums
    cnt = np.bincount(inv, minlength=G).astype(float)
    # bootstrap sample x* = w_g * r_u ; its mean and CR1 se, vectorised over replicates
    m_star = (W @ rs) / n
    # sum_g (sum_{u in g} (x*_u - m*))^2 = sum_g (w_g rs_g - cnt_g m*)^2
    dev = W * rs[None, :] - cnt[None, :] * m_star[:, None]
    se_star = np.sqrt(G / (G - 1) * np.sum(dev ** 2, axis=1)) / n
    with np.errstate(divide="ignore", invalid="ignore"):
        t_star = np.where(se_star > 0, m_star / se_star, 0.0)
    if alternative == "greater":
        p_w = float((1 + np.sum(t_star >= t)) / (reps + 1))
    else:
        p_w = float((1 + np.sum(np.abs(t_star) >= abs(t))) / (reps + 1))
    out.update({"mean": m, "se_cr1": se, "t": float(t), "df": int(G - 1),
                "ci95": [m - q * se, m + q * se], "p_t": p_t, "p_wild": p_w, "wild_weights": wkind,
                "alternative": alternative, "valid": bool(G >= 10),
                "why": None if G >= 10 else "fewer than 10 clusters: report, do not decide"})
    return out
