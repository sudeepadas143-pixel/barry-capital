"""V4 audit: bullish and bearish logic are mirror images.

Negating every price (open, close -> -open, -close; high <-> -low) turns every up-move into a
down-move of the same size. EMA, MACD, ATR and the pivot/structure rules are all linear or
mirror-symmetric under that map, so a correct engine must give the same breaks, classes and
signals on the same candles with the direction flipped. The only allowed difference is the
documented tie-break when one candle closes through both swing levels (close == open).
Research test: it reads the engine, it changes nothing.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf import engine as G  # noqa: E402
from hcmtf.data import _resample  # noqa: E402
from test_engine_v2 import minute_bars  # noqa: E402


def mirror(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"open": -df["open"], "high": -df["low"], "low": -df["high"],
                         "close": -df["close"], "volume": df["volume"]}, index=df.index)


def ctx(m15: pd.DataFrame) -> G.Ctx:
    r = lambda rule: _resample(m15, rule, label="left", closed="left")
    return G.Ctx(r("1h"), r("4h"), r("1D"), m15, True, True)


def run(c: G.Ctx):
    p = G.DEFAULTS["1H"]
    f = G.features(c, p)
    t = G.breaks(f, p)
    return f, t, G.classify(G.score(t, f, p), p)


def test_breaks_classes_and_signals_mirror_exactly():
    for seed in (1, 4, 9):
        m = minute_bars(n15=16000, seed=seed)
        f, t, s = run(ctx(m))
        fm, tm, sm = run(ctx(mirror(m)))
        assert len(t) > 50 and (t["dir"] > 0).any() and (t["dir"] < 0).any()
        np.testing.assert_allclose(fm.t1, -f.t1)          # HTF trend states flip
        np.testing.assert_allclose(fm.t2, -f.t2)
        a = t.set_index("i")
        b = tm.set_index("i")
        assert list(a.index) == list(b.index)
        assert ((a["dir"] == -b["dir"]) & (a["choch"] == b["choch"]) & (a["cls"] == b["cls"])).all()
        assert list(s["i"]) == list(sm["i"]) and list(s["tier"]) == list(sm["tier"])
        assert (s["dir"].to_numpy() == -sm["dir"].to_numpy()).all()
        # both sides actually occur, so the check is not vacuous
        assert (s["dir"] > 0).any() and (s["dir"] < 0).any()
