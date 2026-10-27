"""The Pine transliteration and the research engine must agree signal for signal."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pine_mirror  # noqa: E402
from hcmtf import signals as S  # noqa: E402
from test_integrity import bars, contexts  # noqa: E402


@pytest.mark.parametrize("seed,vol,profile", [(1, True, "1H"), (2, False, "1H"), (3, True, "4H"),
                                              (4, True, "1D"), (5, False, "1W")])
def test_pine_logic_matches_research_engine(seed, vol, profile):
    df = bars(2000, seed=seed, vol=vol)
    near, anchor = contexts(df)
    p = S.DEFAULTS[profile]
    f, trig, sig, warn = S.run(df, near, anchor, p, vol)
    ps, pw = pine_mirror.run(f, p.pivot_left, p.pivot_right, p.cooldown, p.confirm, p.major, vol)
    ours = list(zip(sig["i"], sig["dir"], sig["kind"], sig["tier"], sig["score"], sig["available"]))
    assert len(ours) > 5
    assert [(int(a), int(b), c, d, float(e), float(g)) for a, b, c, d, e, g in ours] == \
           [(a, b, c, d, float(e), float(g)) for a, b, c, d, e, g in ps]
    assert list(zip(warn["i"], warn["dir"])) == pw


def test_pine_file_has_the_same_constants():
    """Spot-check that the Pine source still uses the parameters the research code tests."""
    src = (Path(__file__).resolve().parent.parent / "pine" / "HighConvictionMTF.pine").read_text()
    for needle in ["ta.atr(14)", "ta.ema(close, 21)", "ta.rsi(close, 14)", "ta.macd(close, 12, 26, 9)",
                   "ta.dmi(14, 14)", "ta.sma(volume, 20)", "htfTrend()[1], lookahead = barmerge.lookahead_on",
                   'input.float(20.0, "ADX minimum"', 'input.float(0.5, "Displacement', 'input.float(1.3, "Volume multiple',
                   'pivL  = profile == "1W" ? 4 : 5', 'pivR  = profile == "1D" or profile == "1W" ? 2 : 3',
                   'coolP = profile == "1H" ? 12 : profile == "4H" ? 6 : profile == "1D" ? 5 : 4']:
        assert needle in src, needle
    for tf, p in S.DEFAULTS.items():
        assert p.adx_min == 20.0 and p.disp_atr == 0.5 and p.vol_mult == 1.3 and p.ema_len == 21
