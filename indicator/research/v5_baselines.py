"""V5 baseline reversal signals and matched-frequency thinning (V5_VALIDATION_PROTOCOL.md §3;
audit blocker B2 / finding U6).

Baselines for family C (tops: bearish side) and family D (bottoms: bullish side). Each fires on a
CLOSED chart candle using data up to that candle only, and emits at most one alert per candle:

  htf_flip         the HTF state turns to the side on this candle (v5_state direction:
                   "bear" onset for tops, "bull" onset for bottoms); unknown -> side does not
                   count as a flip (warm-up is not an event)
  ema_cross        EMA20 crosses EMA50 in the side's direction (hcmtf.evaluate.ema_cross)
  supertrend_flip  Supertrend(10, 3) flips to the side (hcmtf.evaluate.supertrend_flip)
  counter_reversal the engine's counter-HTF change of character in the side's direction
                   (hcmtf.engine.breaks, shipped DEFAULTS pivots, class "counter_reversal",
                   warm breaks only)

Side convention: side = -1 for tops (bearish), +1 for bottoms (bullish).

Matched frequency (protocol: compare at matched signal frequency). A baseline usually fires at a
different rate than a detector, which changes recall and false alarms mechanically. thin() keeps,
for every (instrument, calendar block), a uniformly random subset of the baseline's alerts no
larger than the detector's alert count in that block, repeated over seeded replicates.

  * It never adds alerts: if a baseline fires LESS often than the detector in a block, all its
    alerts are kept and the shortfall is reported (achieved/target ratio). Matching is therefore
    "at most the detector's frequency", stated, never padded with invented alerts.
  * Within-block matching keeps the baseline's alerts in the same periods as the detector's, so a
    baseline cannot win or lose by firing in different market regimes.
  * Thinning is an EVALUATION device: it uses the detector's alert counts per block, which are
    known only after the block. The thinned set is a benchmark, not a tradable signal; the
    unthinned baseline is always reported as well.
  * Random thinning leaves expected precision unchanged and scales recall and false alarms; the
    replicate spread is reported, so the thinning noise is visible.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hcmtf import engine as G, evaluate as E

from .v41 import cluster_id
from .v5_state import UNKNOWN

BASELINES = ("htf_flip", "ema_cross", "supertrend_flip", "counter_reversal")


def _side(side: int) -> int:
    if side not in (1, -1):
        raise ValueError("side must be +1 (bottoms, bullish) or -1 (tops, bearish)")
    return side


def htf_flip(state: pd.DataFrame, side: int) -> np.ndarray:
    """Candle indices where the v5_state direction becomes the side's label from a KNOWN other
    label (bull/neutral -> bear for tops). Transitions out of 'unknown' are warm-up, not flips."""
    lab = state["direction_label"].to_numpy(object)
    want = "bear" if _side(side) < 0 else "bull"
    prev = np.concatenate([np.array([UNKNOWN], dtype=object), lab[:-1]])   # (np.r_ would parse the string)
    return np.flatnonzero((lab == want) & (prev != want) & (prev != UNKNOWN))


def _feat(df: pd.DataFrame):
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))

    class F:  # the minimal attribute set hcmtf.evaluate's baselines read
        pass
    f = F()
    f.o, f.h, f.l, f.c = o, h, l, c
    return f


def ema_cross(df: pd.DataFrame, side: int) -> np.ndarray:
    ev = E.ema_cross(_feat(df))
    return np.sort(ev.loc[ev["dir"] == _side(side), "i"].to_numpy(int))


def supertrend_flip(df: pd.DataFrame, side: int) -> np.ndarray:
    ev = E.supertrend_flip(_feat(df))
    return np.sort(ev.loc[ev["dir"] == _side(side), "i"].to_numpy(int))


def counter_reversal(df: pd.DataFrame, htf1: pd.DataFrame, htf2: pd.DataFrame | None, tf: str, side: int) -> np.ndarray:
    ctx = G.Ctx(df, htf1, htf2, None, False, False)
    p = G.DEFAULTS[tf]
    f = G.features(ctx, p)
    t = G.breaks(f, p)
    if len(t) == 0:
        return np.array([], int)
    t = t[t["warm"] & (t["cls"] == "counter_reversal") & (t["dir"] == _side(side))]
    return np.unique(t["i"].to_numpy(int))


def generate(df: pd.DataFrame, htf1: pd.DataFrame, htf2: pd.DataFrame | None, state: pd.DataFrame,
             tf: str, side: int) -> dict[str, np.ndarray]:
    """All four baselines for one instrument: name -> sorted unique candle indices."""
    return {"htf_flip": htf_flip(state, side), "ema_cross": ema_cross(df, side),
            "supertrend_flip": supertrend_flip(df, side), "counter_reversal": counter_reversal(df, htf1, htf2, tf, side)}


def thin(baseline_alerts, detector_alerts, index: pd.DatetimeIndex, tf: str, reps: int = 50,
         seed: int = 20261027) -> dict:
    """Matched-frequency thinning of one instrument's baseline alerts (see module docstring).

    Returns {"replicates": [sorted index arrays], "target": detector alerts after de-duplication,
    "available": baseline alerts after de-duplication, "achieved": alerts kept per replicate,
    "shortfall_blocks": blocks where the baseline had fewer alerts than the detector}.
    """
    b = np.unique(np.asarray(baseline_alerts, int))
    d = np.unique(np.asarray(detector_alerts, int))
    for x in (b, d):
        if len(x) and (x.min() < 0 or x.max() >= len(index)):
            raise IndexError("alert index outside the instrument's candles")
    cl = cluster_id(index, tf)
    bcl, dcl = cl[b], cl[d]
    target = pd.Series(dcl).value_counts().to_dict()
    groups = {k: b[bcl == k] for k in np.unique(bcl)}
    rng = np.random.default_rng(seed)
    reps_out = []
    for _ in range(reps):
        keep = []
        for k, members in groups.items():
            m = target.get(k, 0)
            if m >= len(members):
                keep.append(members)
            elif m > 0:
                keep.append(rng.choice(members, m, replace=False))
        reps_out.append(np.sort(np.concatenate(keep)) if keep else np.array([], int))
    short = sorted(int(k) for k, m in target.items() if len(groups.get(k, [])) < m)
    return {"replicates": reps_out, "target": int(len(d)), "available": int(len(b)),
            "achieved": int(len(reps_out[0])) if reps_out else 0, "shortfall_blocks": short}
