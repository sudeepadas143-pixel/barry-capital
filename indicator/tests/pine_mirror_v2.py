"""Bar-by-bar transliteration of pine/HighConvictionMTF.pine (v2) signal logic.

Same statements, same order, Pine-style `var` state and x[k] history. The ta.* arrays,
HTF trends and LTF readings come from the engine's Feat (their own causality is tested
elsewhere); everything that decides a signal is re-done here, one candle at a time.
"""

import numpy as np

from hcmtf import engine as G


def _roll(x, n, fn):
    out = np.full(len(x), np.nan)
    for i in range(n - 1, len(x)):
        out[i] = fn(x[i - n + 1:i + 1])
    return out


def run(f, profile, p):
    o, h, l, c = f.o, f.h, f.l, f.c
    n = len(c)
    pivL, pivR = p.pivot_left, p.pivot_right
    evidence, filters = G.effective(p, f.is_crypto)
    ev = set(evidence)
    uMom, uStr, uDisp, uFvg = "momentum" in ev, "strength" in ev, "displacement" in ev, "fvg" in ev
    uVol, uSwp, uLtf = "volume" in ev, "sweep" in ev, "ltf_momentum" in ev
    fl = set(filters)
    hh, hr = _roll(h, pivL, np.max), _roll(h, pivR, np.max)
    ll, lr = _roll(l, pivL, np.min), _roll(l, pivR, np.min)
    at = lambda x, i, k: x[i - k] if i - k >= 0 else np.nan
    eqf = lambda a, b: (not np.isnan(a)) and a == b

    sh = sl = np.nan
    shUsed = slUsed = True
    trend = 0
    lastDir, lastBar = 0, None
    pend = None                  # acceptance mode: (dir, level, major, bar, cls, met, avail)
    leg, armed = 0, -1
    sweepUp_h, sweepDn_h = [], []
    trend_h = []
    sigs, warns = [], []
    for i in range(n):
        newPH = i >= pivL + pivR and at(h, i, pivR) > at(hh, i, pivR + 1) and at(h, i, pivR) >= hr[i]
        newPL = i >= pivL + pivR and at(l, i, pivR) < at(ll, i, pivR + 1) and at(l, i, pivR) <= lr[i]
        if newPH:
            sh, shUsed = at(h, i, pivR), False
        if newPL:
            sl, slUsed = at(l, i, pivR), False
        sweepUp_h.append((not np.isnan(sl)) and l[i] < sl and c[i] > sl)
        sweepDn_h.append((not np.isnan(sh)) and h[i] > sh and c[i] < sh)
        up = (not shUsed) and c[i] > sh
        dn = (not slUsed) and c[i] < sl
        if up and dn:
            up, dn = c[i] >= o[i], c[i] < o[i]
        d = 1 if up else -1 if dn else 0
        level = sh if up else sl
        choch = d != 0 and trend == -d
        if d != 0:
            trend = d
            if up:
                shUsed = True
            else:
                slUsed = True

        t1, t2 = f.t1[i], f.t2[i]
        a1 = 0.0 if np.isnan(t1) else t1 * d
        a2 = 0.0 if np.isnan(t2) else t2 * d
        against = a1 < 0 or a2 < 0
        htfWith = a1 + a2 >= 1 and not against
        cls = ("counter_reversal" if choch else "counter") if against else ("realignment" if choch else "continuation")

        eMom = (f.rsi[i] > 50 and f.hist[i] > 0) if d > 0 else (f.rsi[i] < 50 and f.hist[i] < 0)
        eStr = f.adx[i] >= p.adx_min and ((f.pdi[i] > f.mdi[i]) if d > 0 else (f.mdi[i] > f.pdi[i]))
        eDisp = d * (c[i] - o[i]) >= p.disp_atr * f.atr[i]
        if d > 0:
            eFvg = l[i] > at(h, i, 2) or at(l, i, 1) > at(h, i, 3)
        else:
            eFvg = h[i] < at(l, i, 2) or at(h, i, 1) < at(l, i, 3)
        eVol = f.vol_ok and f.rvol[i] >= p.vol_mult
        win = slice(max(0, i - p.sweep_lookback), i + 1)
        eSwp = any(sweepUp_h[win]) if d > 0 else any(sweepDn_h[win])
        eLtf = eqf(f.ltf_mom[i], d)

        met = avail = 0.0
        if uMom:
            avail += 1; met += eMom
        if uStr:
            avail += 1; met += eStr
        if uDisp or uFvg:
            avail += 1; met += (uDisp and eDisp) or (uFvg and eFvg)
        if uVol and f.vol_ok:
            avail += 1; met += eVol
        if uSwp:
            avail += 1; met += eSwp
        if uLtf and not np.isnan(f.ltf_mom[i]):
            avail += 1; met += eLtf
        frac = met / avail if avail > 0 else 0.0

        opp = (h[i] - max(o[i], c[i])) if d > 0 else (min(o[i], c[i]) - l[i])
        spike = opp > p.spike_wick_atr * f.atr[i] and h[i] - l[i] > 0 and ((not f.vol_ok) or f.rvol[i] >= 1.2)
        weekend = f.is_crypto and f.index[i].dayofweek >= 5
        passes = (not ("not_range" in fl and f.adx[i] < p.range_adx)) and \
                 (not ("not_shock" in fl and f.vol_rank[i] >= p.shock_rank)) and \
                 (not ("not_spike_wick" in fl and spike)) and (not ("not_weekend" in fl and weekend))
        warm = not (np.isnan(f.atr[i]) or np.isnan(f.rsi[i]) or np.isnan(f.hist[i]) or np.isnan(f.adx[i]))

        if p.accept and pend is not None:
            pdir, plev, pmaj, pbar, pcls, pmet, pav = pend
            if i == pbar + 1 and pdir * (c[i] - plev) > 0 and \
                    not (pdir == lastDir and lastBar is not None and i - lastBar < p.cooldown):
                sigs.append((i, pdir, pcls, "major" if pmaj else "confirmed", pmet, pav))
                lastDir, lastBar = pdir, i
            pend = None
        if d != 0 and warm and passes and cls == "counter_reversal":
            sigs.append((i, d, cls, "watch", met, avail))
        elif d != 0 and warm and passes and cls in ("realignment", "continuation") and htfWith and frac >= p.confirm - 1e-9:
            major = cls == "realignment" and frac >= p.major - 1e-9
            if p.accept:
                pend = (d, level, major, i, cls, met, avail)
            elif not (d == lastDir and lastBar is not None and i - lastBar < p.cooldown):
                sigs.append((i, d, cls, "major" if major else "confirmed", met, avail))
                lastDir, lastBar = d, i

        if trend_h and trend != trend_h[-1]:
            leg += 1
        trend_h.append(trend)
        wDir = -trend
        ls = f.ltf_struct
        if not np.isnan(ls[i]):
            wFire = eqf(ls[i], wDir) and not (i > 0 and eqf(ls[i - 1], wDir))
        else:
            wFire = (wDir * (c[i] - f.ema[i]) > 0 and i > 0 and wDir * (c[i - 1] - f.ema[i - 1]) <= 0
                     and wDir * (f.rsi[i] - 50) > 0 and wDir * f.hist[i] > 0)
        if trend != 0 and wFire and armed != leg:
            warns.append((i, wDir))
            armed = leg
    return sigs, warns
