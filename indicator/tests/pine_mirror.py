"""A literal, bar-by-bar transliteration of pine/HighConvictionMTF.pine's signal logic.

Pine runs the script once per bar with `var` state carried forward. This file does the
same, statement for statement, using Pine-style history references (x[k]) built from
the ta.* arrays. test_pine_mirror.py checks that it produces exactly the signals of
the research engine (hcmtf/signals.py), so a rule changed in one place and not the
other fails the build.
"""

import numpy as np

from hcmtf import ta


def _highest(x, n):
    out = np.full(len(x), np.nan)
    for i in range(n - 1, len(x)):
        out[i] = x[i - n + 1:i + 1].max()
    return out


def _lowest(x, n):
    out = np.full(len(x), np.nan)
    for i in range(n - 1, len(x)):
        out[i] = x[i - n + 1:i + 1].min()
    return out


def run(f, pivL, pivR, cooldown, confirmT, majorT, volOn, adxMin=20.0, dispAtr=0.5, volMult=1.3):
    o, h, l, c = f.o, f.h, f.l, f.c
    n = len(c)
    hh, hr = _highest(h, pivL), _highest(h, pivR)
    ll, lr = _lowest(l, pivL), _lowest(l, pivR)

    def at(x, i, k):          # Pine x[k] on bar i
        j = i - k
        return x[j] if j >= 0 else np.nan

    def eq(a, b):             # Pine == with na gives false
        return (not np.isnan(a)) and a == b

    sh = sl = np.nan
    shUsed = slUsed = True
    trend = 0
    lastDir, lastBar = 0, None
    leg, armedLeg = 0, -1
    trend_hist = []
    sigs, warns = [], []
    for i in range(n):
        newPH = i >= pivL + pivR and at(h, i, pivR) > at(hh, i, pivR + 1) and at(h, i, pivR) >= hr[i]
        newPL = i >= pivL + pivR and at(l, i, pivR) < at(ll, i, pivR + 1) and at(l, i, pivR) <= lr[i]
        if newPH:
            sh, shUsed = at(h, i, pivR), False
        if newPL:
            sl, slUsed = at(l, i, pivR), False
        upBreak = (not shUsed) and c[i] > sh
        dnBreak = (not slUsed) and c[i] < sl
        if upBreak and dnBreak:
            upBreak, dnBreak = c[i] >= o[i], c[i] < o[i]
        d = 1 if upBreak else -1 if dnBreak else 0
        kind = "reversal" if d != 0 and trend == -d else "continuation"
        if d != 0:
            trend = d
            if upBreak:
                shUsed = True
            else:
                slUsed = True

        nearT, anchorT = f.near[i], f.anchor[i]
        cNear, cAnchor = eq(nearT, d), eq(anchorT, d)
        cMom = (f.rsi[i] > 50 and f.hist[i] > 0) if d > 0 else (f.rsi[i] < 50 and f.hist[i] < 0)
        cStr = f.adx[i] >= adxMin and ((f.pdi[i] > f.mdi[i]) if d > 0 else (f.mdi[i] > f.pdi[i]))
        cDisp = d * (c[i] - o[i]) >= dispAtr * f.atr[i]
        cVol = volOn and f.rvol[i] >= volMult
        avail = (6.0 if volOn else 5.0) - float(np.isnan(nearT)) - float(np.isnan(anchorT))
        score = sum(map(bool, (cNear, cAnchor, cMom, cStr, cDisp, cVol)))
        frac = score / avail
        warm = not (np.isnan(f.atr[i]) or np.isnan(f.rsi[i]) or np.isnan(f.hist[i]) or np.isnan(f.adx[i]))

        if d != 0 and warm and frac >= confirmT - 1e-9:
            if not (d == lastDir and lastBar is not None and i - lastBar < cooldown):
                major = frac >= majorT - 1e-9 and (cAnchor or np.isnan(anchorT))
                sigs.append((i, d, kind, "major" if major else "confirmed", score, avail))
                lastDir, lastBar = d, i

        prev = trend_hist[-1] if trend_hist else None
        if prev is not None and trend != prev:
            leg += 1
        trend_hist.append(trend)
        wDir = -trend
        crossBack = (wDir != 0 and wDir * (c[i] - f.ema[i]) > 0
                     and i > 0 and wDir * (c[i - 1] - f.ema[i - 1]) <= 0)
        if trend != 0 and crossBack and wDir * (f.rsi[i] - 50) > 0 and wDir * f.hist[i] > 0 and armedLeg != leg:
            warns.append((i, wDir))
            armedLeg = leg
    return sigs, warns
