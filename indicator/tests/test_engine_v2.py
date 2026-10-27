"""Integrity tests for the v2 engine (LTF/MTF/HTF ladder, perp features)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcmtf import engine as G  # noqa: E402
from hcmtf.data import _resample  # noqa: E402

ALL_EVIDENCE = ("momentum", "strength", "displacement", "fvg", "volume", "sweep", "ltf_momentum",
                "perp_ok", "basis_ok", "oi_up")


def minute_bars(n15=12000, seed=1, start="2022-01-03"):
    rng = np.random.default_rng(seed)
    drift = np.repeat(rng.normal(0, 0.0008, n15 // 400 + 1), 400)[:n15]
    c = 100 * np.exp(np.cumsum(drift + rng.normal(0, 0.004, n15)))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.002, n15)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.002, n15)))
    v = rng.lognormal(8, 0.6, n15)
    idx = pd.date_range(start, periods=n15, freq="15min", tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}, index=idx)


def perp_frames(m15, seed=2):
    rng = np.random.default_rng(seed)
    spot1h = _resample(m15, "1h", label="left", closed="left")
    perp = spot1h.copy()
    perp["close"] = spot1h["close"] * (1 + rng.normal(0.0003, 0.0004, len(spot1h)))
    fidx = pd.date_range(m15.index[0], m15.index[-1], freq="8h")
    funding = pd.DataFrame({"rate": rng.normal(0.0001, 0.0002, len(fidx))}, index=fidx)
    oi = pd.DataFrame({"oi": np.cumsum(rng.normal(0, 1, len(spot1h))) + 1000}, index=spot1h.index)
    return spot1h, perp, funding, oi


def ctx_upto(m15, cut_time, extras):
    """Everything known at cut_time: 15m candles that CLOSED by then; the forming 1H/4H/1D
    candles are built from partial data, exactly as live; perp series likewise cut."""
    m = m15[m15.index + pd.Timedelta(minutes=15) <= cut_time]
    chart = _resample(m, "1h", label="left", closed="left")
    chart = chart[chart.index + pd.Timedelta(hours=1) <= cut_time]
    spot1h, perp, funding, oi = extras
    known = lambda df, step: df[df.index + step <= cut_time]
    return G.Ctx(chart, _resample(m, "4h", label="left", closed="left"), _resample(m, "1D", label="left", closed="left"),
                 m, True, True, perp=known(perp, pd.Timedelta(hours=1)), spot1h=known(spot1h, pd.Timedelta(hours=1)),
                 funding=funding[funding.index < cut_time], oi=known(oi, pd.Timedelta(hours=1)))


@pytest.mark.parametrize("seed", [1, 4])
def test_v2_signals_never_change_after_they_print(seed):
    m15 = minute_bars(seed=seed)
    extras = perp_frames(m15, seed)
    p = G.with_(G.DEFAULTS["1H"], evidence=ALL_EVIDENCE, filters=tuple(G.FILTERS), confirm=0.4, major=0.6)
    end = m15.index[-1] + pd.Timedelta(minutes=15)
    f_full, t_full, s_full, w_full = G.run(ctx_upto(m15, end, extras), p)
    assert len(s_full) > 5 and (s_full["tier"] == "major").any()
    assert t_full["ltf_available"].any() and t_full["perp_available"].any() and t_full["oi_available"].any()
    chart_index = f_full.index
    cols = ["i", "dir", "cls", "tier", "met", "available", "sweep", "fvg", "ltf_momentum", "perp_ok", "basis_ok",
            "oi_up", "not_range", "not_shock", "not_spike_wick", "htf1", "htf2"]
    for k in [700, 1500, 2200, 2999]:
        cut = chart_index[k] + pd.Timedelta(hours=1)
        f_k, t_k, s_k, w_k = G.run(ctx_upto(m15, cut, extras), p)
        a = s_full[s_full["i"] <= k].reset_index(drop=True)
        b = s_k.reset_index(drop=True)
        pd.testing.assert_frame_equal(a[cols], b[cols], check_dtype=False)
        wa = w_full[w_full["i"] <= k].reset_index(drop=True)
        pd.testing.assert_frame_equal(wa, w_k.reset_index(drop=True), check_dtype=False)


def test_v2_last_bar_context_is_final():
    """Newest-candle check, every 7th candle: LTF, HTF and perp readings on candle k are the
    same whether computed live at k's close or with the full history."""
    m15 = minute_bars(8000, seed=3)
    extras = perp_frames(m15, 3)
    p = G.DEFAULTS["1H"]
    end = m15.index[-1] + pd.Timedelta(minutes=15)
    full = G.features(ctx_upto(m15, end, extras), p)
    for k in range(400, len(full.index), 7):
        cut = full.index[k] + pd.Timedelta(hours=1)
        fk = G.features(ctx_upto(m15, cut, extras), p)
        for name in ("t1", "t2", "ltf_mom", "ltf_struct", "funding_z", "basis_z", "oi_chg", "vol_rank", "atr", "rvol"):
            a, b = getattr(full, name)[k], getattr(fk, name)[k]
            assert (np.isnan(a) and np.isnan(b)) or a == pytest.approx(b), (name, k, a, b)


def test_ltf_reads_only_candles_inside_the_closed_chart_candle():
    idx = pd.date_range("2024-01-01", periods=8, freq="1h", tz="UTC")
    ltf_idx = pd.date_range("2024-01-01", periods=32, freq="15min", tz="UTC")
    vals = np.arange(32, dtype=float)
    out = G._ltf_at_close(idx, pd.DataFrame(index=ltf_idx), vals)
    assert list(out) == [3, 7, 11, 15, 19, 23, 27, 31]   # the 4th quarter-hour of each hour


def test_classes_map_to_tiers():
    m15 = minute_bars(seed=6)
    extras = perp_frames(m15, 6)
    end = m15.index[-1] + pd.Timedelta(minutes=15)
    p = G.with_(G.DEFAULTS["1H"], cooldown=1)
    _, t, s, _ = G.run(ctx_upto(m15, end, extras), p)
    assert not (s["cls"] == "counter_continuation").any()
    assert set(s.loc[s["cls"] == "counter_reversal", "tier"]) == {"watch"}
    assert set(s.loc[s["cls"] == "realignment", "tier"]) <= {"major"}
    assert set(s.loc[s["cls"] == "continuation", "tier"]) <= {"confirmed"}
    assert s.loc[s["tier"].isin(["major", "confirmed"]), "htf_with"].all()
    assert (s["tier"] == "major").any() and (s["tier"] == "watch").any()
    # every with-HTF realignment/continuation break became a signal (cooldown 1, no gating)
    eligible = t[t["warm"] & t["htf_with"] & t["cls"].isin(["realignment", "continuation"])]
    assert len(eligible) == (s["tier"] != "watch").sum()


def test_families_count_once():
    m15 = minute_bars(seed=8)
    end = m15.index[-1] + pd.Timedelta(minutes=15)
    ctx = ctx_upto(m15, end, perp_frames(m15, 8))
    p = G.with_(G.DEFAULTS["1H"], evidence=("displacement", "fvg", "momentum"))
    f = G.features(ctx, p)
    t = G.score(G.breaks(f, p), f, p)
    assert (t["available"] == 2).all()        # impulse + momentum, not 3
    both = t["displacement"] & t["fvg"]
    assert (t.loc[both, "fam_impulse"]).all() and t["met"].max() <= 2


def test_percentrank_matches_pine_definition():
    x = np.array([1, 2, 3, 4, 5, 3, 1, 9, 2, 2], float)
    r = G.percentrank(x, 4)
    assert np.isnan(r[:4]).all()
    assert r[4] == 100.0                      # 5 vs [1,2,3,4]
    assert r[5] == 50.0                       # 3 vs [2,3,4,5]: 2 and 3 are <= 3


@pytest.mark.parametrize("profile,evidence,filters,seed,accept", [
    ("1H", (), (), 15, True),
    ("4H", (), ("not_shock",), 16, True),
    ("1H", ("momentum", "strength", "displacement", "volume"), (), 11, False),
    ("1H", ALL_EVIDENCE[:7], tuple(G.FILTERS), 12, False),
    ("1D", ("momentum", "displacement", "fvg", "sweep", "ltf_momentum"), ("not_range", "not_spike_wick"), 13, False),
    ("4H", ("strength", "volume", "sweep"), ("not_shock", "not_weekend"), 14, False),
])
def test_pine_v2_logic_matches_engine(profile, evidence, filters, seed, accept):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pine_mirror_v2
    m15 = minute_bars(seed=seed)
    end = m15.index[-1] + pd.Timedelta(minutes=15)
    ctx = ctx_upto(m15, end, perp_frames(m15, seed))
    p = G.with_(G.DEFAULTS[profile], evidence=evidence, filters=filters, confirm=0.4 if evidence else 0.0,
                major=0.6 if evidence else 0.0, accept=accept)
    f, t, s, w = G.run(ctx, p)
    ps, pw = pine_mirror_v2.run(f, profile, p)
    ours = [(int(a), int(b), c, d, float(e), float(g)) for a, b, c, d, e, g in
            zip(s["i"], s["dir"], s["cls"], s["tier"], s["met"], s["available"])]
    assert len(ours) > 5 and any(x[3] == "major" for x in ours)
    assert ours == [(a, b, c, d, float(e), float(g)) for a, b, c, d, e, g in ps]
    assert [(int(a), int(b)) for a, b in zip(w["i"], w["dir"])] == pw


def test_pine_v2_source_matches_engine_constants():
    src = (Path(__file__).resolve().parent.parent / "pine" / "HighConvictionMTF.pine").read_text()
    for needle in ["ta.percentrank(atr / close, 200)", "math.sum(sweepUp ? 1 : 0, 11)", "adx >= 20",
                   "0.5 * atr", "rvol >= 1.3", "oppWick > 0.8 * atr", "adx < 18", "volRank >= 95",
                   "structState(5, 3)", "htfTrend()[1], lookahead = barmerge.lookahead_on",
                   'ltfP  = profile == "1H" ? "15" : profile == "4H" ? "60" : profile == "1D" ? "240" : "D"',
                   'htf1P = profile == "1H" ? "240" : profile == "4H" ? "D" : profile == "1D" ? "W" : "M"',
                   'htf2P = profile == "1H" ? "D" : profile == "4H" ? "W" : profile == "1D" ? "M" : "3M"']:
        assert needle in src, needle
    assert G.LADDER == {"1H": ("15m", "4H", "1D"), "4H": ("1H", "1D", "1W"), "1D": ("4H", "1W", "1M"), "1W": ("1D", "1M", "3M")}
    for tf, p in G.DEFAULTS.items():
        assert (p.adx_min, p.disp_atr, p.vol_mult, p.sweep_lookback, p.range_adx, p.shock_rank, p.spike_wick_atr) == \
               (20.0, 0.5, 1.3, 10, 18.0, 95.0, 0.8)


def test_tradingview_parity_script_round_trip(tmp_path):
    """Build a fake 'Export chart data' CSV in the layout the Pine parity mode writes,
    from the engine itself, and check compare_tv_export finds zero mismatches, and that
    it does catch a flipped signal."""
    import subprocess
    m15 = minute_bars(seed=21)
    end = m15.index[-1] + pd.Timedelta(minutes=15)
    ctx = ctx_upto(m15, end, perp_frames(m15, 21))
    p = G.with_(G.DEFAULTS["1H"])
    f, t, s, w = G.run(ctx, p)
    n = len(f.index)
    sig = np.zeros(n)
    ss = s[s["tier"].isin(["major", "confirmed"])]
    sig[ss["i"].to_numpy(int)] = ss["dir"] * np.where(ss["tier"] == "major", 2, 1)
    warn = np.zeros(n)
    warn[w["i"].to_numpy(int)] = w["dir"].to_numpy()
    watch = np.zeros(n)
    wa = s[s["tier"] == "watch"]
    watch[wa["i"].to_numpy(int)] = wa["dir"].to_numpy()
    df = ctx.df
    csv = pd.DataFrame({"time": ((df.index - pd.Timestamp(0, tz="UTC")).total_seconds()).astype(int), "open": df["open"].values,
                        "high": df["high"].values, "low": df["low"].values, "close": df["close"].values,
                        "Volume": df["volume"].values, "parity_signal": sig, "parity_warning": warn, "parity_watch": watch,
                        "parity_htf1": f.t1, "parity_htf2": f.t2, "parity_ltf_mom": f.ltf_mom,
                        "parity_ltf_struct": f.ltf_struct})
    path = tmp_path / "export.csv"
    csv.to_csv(path, index=False)
    script = Path(__file__).resolve().parent.parent / "scripts" / "compare_tv_export.py"
    ok = subprocess.run([sys.executable, str(script), str(path), "--profile", "1H", "--crypto", "--warmup", "0"],
                        capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "signal mismatches: 0; warning mismatches: 0" in ok.stdout and "Python signals: 0" not in ok.stdout
    k = int(ss["i"].iloc[len(ss) // 2])
    csv.loc[k, "parity_signal"] = -csv.loc[k, "parity_signal"]
    csv.to_csv(path, index=False)
    bad = subprocess.run([sys.executable, str(script), str(path), "--profile", "1H", "--crypto", "--warmup", "0"],
                         capture_output=True, text=True)
    assert bad.returncode == 1 and "signal mismatches: 1" in bad.stdout



def test_acceptance_mode_never_changes_after_print():
    """Truncation test for the acceptance option: a signal prints on the candle after the
    break, using that candle's close, and never moves once printed."""
    m15 = minute_bars(seed=31)
    extras = perp_frames(m15, 31)
    p = G.with_(G.DEFAULTS["1H"], accept=True)
    end = m15.index[-1] + pd.Timedelta(minutes=15)
    f_full, _, s_full, _ = G.run(ctx_upto(m15, end, extras), p)
    s_full = s_full[s_full["tier"] != "watch"]
    assert len(s_full) > 5 and (s_full["i"] == s_full["break_i"] + 1).all()
    for k in [800, 1600, 2400]:
        _, _, s_k, _ = G.run(ctx_upto(m15, f_full.index[k] + pd.Timedelta(hours=1), extras), p)
        s_k = s_k[s_k["tier"] != "watch"]
        a = s_full[s_full["i"] <= k][["i", "dir", "tier"]].reset_index(drop=True)
        pd.testing.assert_frame_equal(a, s_k[["i", "dir", "tier"]].reset_index(drop=True), check_dtype=False)
