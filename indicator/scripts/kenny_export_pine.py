"""Generate pine/Kenny_Divergence_Indicator.pine from reports/cycle2_model_spec.json (CYCLE2_CONFIG.md §8).

Per TF bucket and direction the CY-2 spec ships either a promoted gradient-boosted model (trees
exported from sklearn: feature, threshold, missing-goes-left, children, leaf value) or the B_ext
baseline. The trees are written into the Pine source as flat arrays and evaluated by a loop
that mirrors sklearn's prediction (`flat_logodds` below is the Python twin of that loop and is
tested against sklearn). Walk-forward evidence from reports/cycle2_results.json is embedded as
display text only. The production indicator pine/HighConvictionMTF*.pine is not touched.

    python scripts/kenny_export_pine.py
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "reports" / "cycle2_model_spec.json"
RESULTS = ROOT / "reports" / "cycle2_results.json"
OUT = ROOT / "pine" / "Kenny_Divergence_Indicator.pine"
BUCKET = {"1W": 3, "1D": 2, "4H": 1, "1H": 0}
TIERS = ("warning", "standard", "high")
CHUNK = 64

_s = importlib.util.spec_from_file_location("cycle_export_pine", ROOT / "scripts" / "cycle_export_pine.py")
_X = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_X)
PINE_FEAT = {**_X.PINE_FEAT,  # CY-2 features (research/cycle2_features.py), same definitions in the feature block
             "bbz": "fBbz", "roc": "fRoc", "roc_acc": "fRocAcc", "wick_up": "fWickUp", "wick_dn": "fWickDn",
             "td_up": "fTdUp", "td_dn": "fTdDn", "vratio": "fVRatio", "dd_hh": "fDdHH", "du_ll": "fDuLL",
             "above": "fAbove", "climax": "fClimax"}


def _f(x: float) -> str:
    """Pine float literal (always with a decimal point so array.from infers float)."""
    s = repr(float(x))
    if "e" in s and "." not in s.split("e")[0]:
        m, e = s.split("e")
        s = f"{m}.0e{e}"
    return s


def flatten(sp: dict) -> dict:
    """Trees -> flat node arrays with absolute child indices; feature -1 marks a leaf."""
    nf, nt, nm, nl, nr, nv, roots = [], [], [], [], [], [], []
    for tree in sp["trees"]:
        off = len(nf)
        roots.append(off)
        for nd in tree:
            nf.append(-1 if nd["leaf"] else nd["f"])
            nt.append(nd["t"] if not nd["leaf"] else 0.0)
            nm.append(1 if nd["ml"] else 0)
            nl.append(off + nd["l"] if not nd["leaf"] else -1)
            nr.append(off + nd["r"] if not nd["leaf"] else -1)
            nv.append(nd["v"] if nd["leaf"] else 0.0)
    return {"nf": nf, "nt": nt, "nm": nm, "nl": nl, "nr": nr, "nv": nv, "roots": roots, "base": sp["baseline"]}


def flat_logodds(fl: dict, x) -> float:
    """Python twin of the Pine gbScore loop (NaN = Pine na)."""
    s = fl["base"]
    for k in fl["roots"]:
        while fl["nf"][k] >= 0:
            xv = x[fl["nf"][k]]
            go_l = (fl["nm"][k] == 1) if (xv is None or (isinstance(xv, float) and math.isnan(xv))) else xv <= fl["nt"][k]
            k = fl["nl"][k] if go_l else fl["nr"][k]
        s += fl["nv"][k]
    return s


def _fill(name: str, vals: list, fmt) -> list[str]:
    out = [f"        {name} := array.new<{'float' if fmt is _f else 'int'}>()"]
    for i in range(0, len(vals), CHUNK):
        out.append(f"        {name}.concat(array.from({', '.join(fmt(v) for v in vals[i:i + CHUNK])}))")
    return out


def model_block(S: dict, d: str) -> str:
    """Per-bucket model loading for direction d (runs once, on the first bar)."""
    D = d.capitalize()
    L = [f"if barstate.isfirst"]
    for tf, b in BUCKET.items():
        if tf not in S["tfs"]:
            continue
        sp = S["tfs"][tf]["models"][d]
        L.append(f"    if bucket == {b}")
        th = sp["theta"]
        L += [f"        th{D}W := {_f(th['warning'])}", f"        th{D}S := {_f(th['standard'])}", f"        th{D}H := {_f(th['high'])}",
              f"        name{D} := \"{sp['model']}\""]
        if sp["kind"] == "gb":
            FV_ORDER_PINE(sp["features"])                                # refuses unportable features
            fl = flatten(sp)
            L += [f"        gb{D} := true", f"        base{D} := {_f(fl['base'])}"]
            for k, fmt in (("nf", str), ("nt", _f), ("nm", str), ("nl", str), ("nr", str), ("nv", _f), ("roots", str)):
                L += _fill(f"{k}{D}", fl[k], fmt)
        elif sp["kind"] == "base":
            L += [f"        gb{D} := false", f"        sign{D} := {_f(sp['sign'])}"]
            if sp["feature"] != "ext_c":
                raise ValueError("baseline must be B_ext")
        else:
            raise ValueError(f"unsupported model kind {sp['kind']!r}")
    return "\n".join(L)


def FV_ORDER_PINE(feats):  # noqa: N802
    bad = [f for f in feats if f not in PINE_FEAT]
    if bad:
        raise ValueError(f"shipped spec uses features Pine cannot compute: {bad}")
    return [PINE_FEAT[f] for f in feats]


def evidence_block(S: dict, R: dict | None) -> str:
    """Walk-forward evidence per bucket/direction (display only)."""
    L = ["evid(int b, bool top) =>", "    string s = \"no research evidence (unvalidated timeframe)\""]
    for tf, b in BUCKET.items():
        if tf not in S["tfs"]:
            continue
        for d in ("top", "bot"):
            name = S["tfs"][tf]["models"][d]["model"]
            txt = "n/a"
            if R and tf in R.get("tfs", {}):
                m = R["tfs"][tf][d]["models"].get(name, {})
                cf = R["tfs"][tf][d]["confirm"].get(name, {}).get("cy1_rule", {})
                try:
                    hp = m["high"]["det"]["precision"]
                    hp = hp[0] if isinstance(hp, list) else hp
                    cp = cf["det"]["precision"]
                    cp = cp[0] if isinstance(cp, list) else cp
                    txt = (f"{name}: HC prec {hp:.2f}, lift {m['high']['lift']['lift']:.2f}x; "
                           f"Confirmed prec {cp:.2f}; HC win {m['high']['trade']['win_rate']:.2f}")
                except (KeyError, TypeError):
                    pass
            L.append(f"    if b == {b} and {'top' if d == 'top' else 'not top'}")
            L.append(f"        s := \"{txt}\"")
    L.append("    s")
    return "\n".join(L)


TEMPLATE = r'''//@version=6
// Kenny's Divergence Indicator. Generated by scripts/kenny_export_pine.py from
// reports/cycle2_model_spec.json (research: HC-MTF cycle engine CY-2) - do not edit the model
// block by hand; regenerate instead.
//
// WHAT IT DOES
//   On the chart: a green upward triangle below the candle = BUY, a red downward triangle above
//   the candle = SELL. Nothing else is drawn by default.
//   Underneath, separate TOP and BOTTOM probabilities per closed candle come from the CY-2
//   walk-forward research (reports/CYCLE2_RESULTS.md): per timeframe and direction either a
//   promoted gradient-boosted tree ensemble (extension, RSI/MACD momentum and divergence gaps,
//   volatility, volume anomalies, wicks/exhaustion counts, range structure) or the extension
//   baseline where no learned model beat it. Three internal states trade timing for confirmation:
//     Early Warning   - probability crosses the WARNING threshold (earliest, most false alerts)
//     High Conviction - probability crosses the HIGH threshold (fewer, more precise; still early)
//     Confirmed       - after a standard-threshold zone, within L/2 candles: close beyond EMA21
//                       and a D/4 ATR retreat from the extreme (later, fewer false alerts)
//   One state (input "BUY/SELL signal"; default chosen in reports/KB_RESULTS.md) draws the
//   triangles. A candle with both BUY and SELL draws neither; a same-direction repeat within
//   Q candles is suppressed. Timeframe sets the turn scale: >= 1W major, >= 1D intermediate,
//   >= 1H swing, < 1H local (reuses the 1H model; UNVALIDATED).
//
// TIMING / NON-REPAINTING
//   Every model input uses closed candles of the chart only; states and alerts fire only on
//   barstate.isconfirmed. The higher-timeframe trend reads the previous COMPLETED HTF candle
//   (request.security(..., f()[1], lookahead_on)), so it never changes after the fact.
//
// EVIDENCE: EXPLORATORY ONLY - all research data had been examined before; no independent
//   confirmation exists. The diagnostics table shows walk-forward precision/lift per state.
//   Short (top) signals lost money after costs in the research; tops are best used to protect
//   or reduce longs. Not financial advice.
indicator("Kenny's Divergence Indicator", shorttitle = "Kenny Div", overlay = true, max_labels_count = 500)

// ---------------------------------------------------------------- inputs
grpS = "Signal"
sigMode  = input.string("__SIGDEF__", "BUY/SELL signal", options = [__SIGOPTS__], group = grpS,
                        tooltip = "Which internal state draws the BUY/SELL triangles. Early Warning = earliest and most false alerts; High Conviction = fewer, more precise, still early; Confirmed = later entry, fewer false alerts. The default was chosen in reports/KB_RESULTS.md.")
showBuy  = input.bool(true, "BUY triangles", group = grpS)
showSell = input.bool(true, "SELL triangles", group = grpS)
volMode  = input.string("Auto", "Volume features", options = ["Auto", "Off"], group = grpS,
                        tooltip = "Auto uses volume features when the feed has volume on >90% of the last 50 candles; otherwise they are treated as missing (as for no-volume instruments in the research).")
grpA = "Advanced display (off by default)"
showStates = input.bool(false, "Mark every internal state (dots and labels)", group = grpA)
showBg     = input.bool(false, "Shade candles above the High Conviction threshold", group = grpA)
showTbl    = input.bool(false, "Diagnostics table", group = grpA)

// ---------------------------------------------------------------- timeframe scale
tfSec  = timeframe.in_seconds(timeframe.period)
bucket = tfSec >= 604800 ? 3 : tfSec >= 86400 ? 2 : tfSec >= 14400 ? 1 : 0
L      = bucket == 3 ? 26 : bucket == 2 ? 63 : bucket == 1 ? 126 : 168
D      = bucket == 3 ? 5.0 : 8.0
Q      = math.max(2, int(L / 4))   // cooldown c and lag q
M      = int(L / 2)                // confirmation window m
validated = tfSec == 3600 or tfSec == 14400 or tfSec == 86400 or tfSec == 604800
turnType  = tfSec >= 604800 ? "Major" : tfSec >= 86400 ? "Intermediate" : tfSec >= 3600 ? "Swing" : "Local"
htfStr    = bucket == 3 ? "M" : bucket == 2 ? "W" : bucket == 1 ? "D" : "240"

// ---------------------------------------------------------------- helpers
clip(float x, float lo, float hi) => math.max(lo, math.min(hi, x))
rngOf(simple int n) =>
    hh = ta.highest(high, n)
    ll = ta.lowest(low, n)
    hh > ll ? (close - ll) / (hh - ll) : na
fin(float x) => na(x) ? na : x

// ---------------------------------------------------------------- features (= research/cycle_features.py, cycle2_features.py)
atr  = ta.atr(14)
emaL = ta.ema(close, L)
emaF = ta.ema(close, 21)
r    = ta.rsi(close, 14)
[_ml, _ms, hst] = ta.macd(close, 12, 26, 9)
hasVol = ta.sma(volume > 0 ? 1.0 : 0.0, 50) > 0.9
useVol = volMode == "Auto" and hasVol
fExtC     = fin((close - emaL) / atr)
fExtF     = fin((close - emaF) / atr)
fRng      = fin(rngOf(L))
fSlope    = fin((emaL - emaL[Q]) / atr)
fSinceHH  = -ta.highestbars(high, L) / float(L)
fSinceLL  = -ta.lowestbars(low, L) / float(L)
fAtrRank  = ta.percentrank(atr / close, 100) / 100.0
fRsi      = r / 100.0
fRsiSlope = (r - r[3]) / 100.0
fRsiGapHi = (ta.highest(r, L) - r) / 100.0
fRsiGapLo = (r - ta.lowest(r, L)) / 100.0
fHist     = fin(hst / atr)
fHistAcc  = fin((hst - hst[3]) / atr)
v         = volume > 0 ? volume : na
relV      = clip(math.log(v / ta.sma(v, 20)), -3, 3)
vtrV      = clip(math.log(ta.sma(v, 5) / ta.sma(v, L)), -3, 3)
effV      = clip(math.log(math.abs(close - open) / atr + 0.05) - relV, -5, 5)
vprV      = math.sum(math.sign(close - close[1]) * v, 10) / math.sum(v, 10)
fRelVol   = useVol ? fin(relV) : na
fVTrend   = useVol ? fin(vtrV) : na
fEffort   = useVol ? fin(effV) : na
fVPress   = useVol ? fin(vprV) : na
fIRngGapHi  = fRng * fRsiGapHi
fIRngGapLo  = (1 - fRng) * fRsiGapLo
fIExtRelVol = fExtC * fRelVol
sdL       = ta.stdev(close, L)
fBbz      = fin((close - ta.sma(close, L)) / sdL)
fRoc      = fin((close - close[Q]) / atr)
fRocAcc   = fRoc - fRoc[Q]
rg        = high - low
fWickUp   = ta.sma(rg > 0 ? (high - math.max(open, close)) / rg : 0.0, 3)
fWickDn   = ta.sma(rg > 0 ? (math.min(open, close) - low) / rg : 0.0, 3)
var int nUp = 0
var int nDn = 0
nUp := close > close[4] ? math.min(nUp + 1, 13) : 0
nDn := close < close[4] ? math.min(nDn + 1, 13) : 0
fTdUp     = bar_index < 4 ? na : nUp / 13.0
fTdDn     = bar_index < 4 ? na : nDn / 13.0
fVRatio   = fin(math.log(ta.atr(5) / ta.atr(L)))
fDdHH     = fin((ta.highest(high, L) - close) / atr)
fDuLL     = fin((close - ta.lowest(low, L)) / atr)
fAbove    = na(emaL) ? na : close > emaL ? 1.0 : 0.0
fClimax   = fRelVol * math.sign(close - open)
fv = array.from(__FV__)

// ---------------------------------------------------------------- shipped CY-2 models (generated)
gbScore(array<int> nf, array<float> nt, array<int> nm, array<int> nl, array<int> nr, array<float> nv, array<int> roots, float base, array<float> x) =>
    float s = base
    for t = 0 to roots.size() - 1
        int k = roots.get(t)
        while nf.get(k) >= 0
            float xv = x.get(nf.get(k))
            bool goL = na(xv) ? nm.get(k) == 1 : xv <= nt.get(k)
            k := goL ? nl.get(k) : nr.get(k)
        s += nv.get(k)
    1.0 / (1.0 + math.exp(-s))

var bool gbTop = false
var bool gbBot = false
var float baseTop = 0.0
var float baseBot = 0.0
var float signTop = 1.0
var float signBot = -1.0
var float thTopW = na
var float thTopS = na
var float thTopH = na
var float thBotW = na
var float thBotS = na
var float thBotH = na
var string nameTop = ""
var string nameBot = ""
var array<int> nfTop = array.new<int>()
var array<float> ntTop = array.new<float>()
var array<int> nmTop = array.new<int>()
var array<int> nlTop = array.new<int>()
var array<int> nrTop = array.new<int>()
var array<float> nvTop = array.new<float>()
var array<int> rootsTop = array.new<int>()
var array<int> nfBot = array.new<int>()
var array<float> ntBot = array.new<float>()
var array<int> nmBot = array.new<int>()
var array<int> nlBot = array.new<int>()
var array<int> nrBot = array.new<int>()
var array<float> nvBot = array.new<float>()
var array<int> rootsBot = array.new<int>()

__MODELS__

coreOk = not (na(fExtC) or na(fExtF) or na(fRng) or na(fSlope) or na(fSinceHH) or na(fSinceLL) or na(fAtrRank))
// trees need the core price features (as in research); the baseline needs only fExtC
float pTop = gbTop ? na : signTop * fExtC
float pBot = gbBot ? na : signBot * fExtC
if coreOk and gbTop
    pTop := gbScore(nfTop, ntTop, nmTop, nlTop, nrTop, nvTop, rootsTop, baseTop, fv)
if coreOk and gbBot
    pBot := gbScore(nfBot, ntBot, nmBot, nlBot, nrBot, nvBot, rootsBot, baseBot, fv)

// ---------------------------------------------------------------- states (CYCLE2_CONFIG.md §4-5)
prevTop = nz(ta.highest(pTop, Q)[1], -1e10)      // computed on every bar (consistent series history)
prevBot = nz(ta.highest(pBot, Q)[1], -1e10)
onset(float p, float prev, float th) => barstate.isconfirmed and not na(p) and p >= th and not (prev >= th)
warnTop = onset(pTop, prevTop, thTopW)
stdTop  = onset(pTop, prevTop, thTopS)
highTop = onset(pTop, prevTop, thTopH)
warnBot = onset(pBot, prevBot, thBotW)
stdBot  = onset(pBot, prevBot, thBotS)
highBot = onset(pBot, prevBot, thBotH)

// completed higher-timeframe trend (previous closed HTF candle): +1 up, -1 down
htfTrend = request.security(syminfo.tickerid, htfStr, (close > ta.ema(close, 21) ? 1 : -1)[1], lookahead = barmerge.lookahead_on)

var array<int>   tS = array.new<int>()
var array<float> tX = array.new<float>()
var array<bool>  tC = array.new<bool>()
var array<int>   bS = array.new<int>()
var array<float> bX = array.new<float>()
var array<bool>  bC = array.new<bool>()
confTop = false
confBot = false
if barstate.isconfirmed
    // tops: process active standard-tier onsets first, then register a new one (checks start next candle)
    for j = tS.size() - 1 to 0
        if tS.size() == 0
            break
        age = bar_index - tS.get(j)
        ext = math.max(tX.get(j), high)
        tX.set(j, ext)
        if not tC.get(j) and age <= M and close < emaF and ext - close >= D / 4 * atr
            tC.set(j, true)
            confTop := true
        if age >= M
            tS.remove(j)
            tX.remove(j)
            tC.remove(j)
    if stdTop
        tS.push(bar_index)
        tX.push(high)
        tC.push(false)
    // bottoms (mirror)
    for j = bS.size() - 1 to 0
        if bS.size() == 0
            break
        age = bar_index - bS.get(j)
        ext = math.min(bX.get(j), low)
        bX.set(j, ext)
        if not bC.get(j) and age <= M and close > emaF and close - ext >= D / 4 * atr
            bC.set(j, true)
            confBot := true
        if age >= M
            bS.remove(j)
            bX.remove(j)
            bC.remove(j)
    if stdBot
        bS.push(bar_index)
        bX.push(low)
        bC.push(false)

// ---------------------------------------------------------------- final BUY/SELL (the only default marks)
rawBuy  = __SELBUY__
rawSell = __SELSELL__
// as-shipped de-duplication (= research/kb_signals.dedupe_final): a candle with both is dropped;
// a repeat in the same direction within Q candles of the previous one is suppressed
var int lastBuy = -1000000
var int lastSell = -1000000
buySig = false
sellSig = false
if barstate.isconfirmed and not (rawBuy and rawSell)
    if rawBuy
        buySig := bar_index - lastBuy > Q
        lastBuy := bar_index
    if rawSell
        sellSig := bar_index - lastSell > Q
        lastSell := bar_index
cBuy  = #00C853
cSell = #FF1744
plotshape(showBuy and buySig, "BUY", shape.triangleup, location.belowbar, cBuy, size = size.small)
plotshape(showSell and sellSig, "SELL", shape.triangledown, location.abovebar, cSell, size = size.small)
alertcondition(buySig, "Kenny Div: BUY", "Kenny Div BUY {{ticker}} {{interval}} {{close}}")
alertcondition(sellSig, "Kenny Div: SELL", "Kenny Div SELL {{ticker}} {{interval}} {{close}}")

// ---------------------------------------------------------------- advanced display (all off by default)
tag(bool top) => (top ? htfTrend < 0 : htfTrend > 0) ? "continuation" : "reversal"
plotshape(showStates and warnTop and not highTop, "Early Warning top", shape.circle, location.abovebar, color.new(cSell, 50), size = size.tiny)
plotshape(showStates and warnBot and not highBot, "Early Warning bottom", shape.circle, location.belowbar, color.new(cBuy, 50), size = size.tiny)
if showStates and highTop
    label.new(bar_index, high, "HC top\n" + turnType + " " + tag(true), style = label.style_label_down, color = color.new(cSell, 30), textcolor = color.white, size = size.tiny)
if showStates and highBot
    label.new(bar_index, low, "HC bottom\n" + turnType + " " + tag(false), style = label.style_label_up, color = color.new(cBuy, 30), textcolor = color.white, size = size.tiny)
if showStates and confTop
    label.new(bar_index, high, "Confirmed top\n" + turnType + " " + tag(true), style = label.style_label_down, color = color.new(cSell, 10), textcolor = color.white, size = size.tiny)
if showStates and confBot
    label.new(bar_index, low, "Confirmed bottom\n" + turnType + " " + tag(false), style = label.style_label_up, color = color.new(cBuy, 10), textcolor = color.white, size = size.tiny)
bgcolor(showBg and not na(pTop) and pTop >= thTopH ? color.new(cSell, 90) : showBg and not na(pBot) and pBot >= thBotH ? color.new(cBuy, 90) : na)

alertcondition(warnTop, "Kenny Div: Early Warning top", "Kenny Div EARLY WARNING top {{ticker}} {{interval}} {{close}}")
alertcondition(warnBot, "Kenny Div: Early Warning bottom", "Kenny Div EARLY WARNING bottom {{ticker}} {{interval}} {{close}}")
alertcondition(highTop, "Kenny Div: High Conviction top", "Kenny Div HIGH CONVICTION top {{ticker}} {{interval}} {{close}}")
alertcondition(highBot, "Kenny Div: High Conviction bottom", "Kenny Div HIGH CONVICTION bottom {{ticker}} {{interval}} {{close}}")
alertcondition(confTop, "Kenny Div: Confirmed top", "Kenny Div CONFIRMED top {{ticker}} {{interval}} {{close}}")
alertcondition(confBot, "Kenny Div: Confirmed bottom", "Kenny Div CONFIRMED bottom {{ticker}} {{interval}} {{close}}")

// ---------------------------------------------------------------- diagnostics (walk-forward evidence, display only)
__EVID__

fmt(float x) => na(x) ? "n/a" : str.tostring(x, "0.000")
var table tb = table.new(position.top_right, 2, 7, bgcolor = color.new(color.black, 20), border_width = 1)
if barstate.islast and showTbl
    tb.cell(0, 0, "Kenny's Divergence", text_color = color.white)
    tb.cell(1, 0, turnType + " (" + (bucket == 3 ? "1W" : bucket == 2 ? "1D" : bucket == 1 ? "4H" : "1H") + " model)" + (validated ? "" : " UNVALIDATED TF"), text_color = validated ? color.white : color.orange)
    tb.cell(0, 1, "top " + nameTop + " p / W,S,H", text_color = color.white)
    tb.cell(1, 1, fmt(pTop) + " / " + fmt(thTopW) + ", " + fmt(thTopS) + ", " + fmt(thTopH), text_color = color.white)
    tb.cell(0, 2, "bottom " + nameBot + " p / W,S,H", text_color = color.white)
    tb.cell(1, 2, fmt(pBot) + " / " + fmt(thBotW) + ", " + fmt(thBotS) + ", " + fmt(thBotH), text_color = color.white)
    tb.cell(0, 3, "HTF trend (closed)", text_color = color.white)
    tb.cell(1, 3, htfTrend > 0 ? "up" : htfTrend < 0 ? "down" : "n/a", text_color = color.white)
    tb.cell(0, 4, "volume features", text_color = color.white)
    tb.cell(1, 4, useVol ? "on" : "off (missing)", text_color = color.white)
    tb.cell(0, 5, "evidence tops", text_color = color.gray)
    tb.cell(1, 5, validated ? evid(bucket, true) : evid(-1, true), text_color = color.gray)
    tb.cell(0, 6, "evidence bottoms", text_color = color.gray)
    tb.cell(1, 6, validated ? evid(bucket, false) : evid(-1, false), text_color = color.gray)
'''


def feature_order(S: dict) -> list[str]:
    orders = {tuple(m["features"]) for t in S["tfs"].values() for m in t["models"].values() if m["kind"] == "gb"}
    if len(orders) > 1:
        raise ValueError("all shipped tree models must use one feature order")
    return list(orders.pop()) if orders else []


SIGNALS = {  # research candidate (reports/KB_CONFIG.md) -> (menu label, Pine BUY expr, Pine SELL expr)
    "K_CONF": ("Confirmed", "confBot", "confTop"),
    "K_H": ("High Conviction", "highBot", "highTop"),
    "K_W": ("Early Warning", "warnBot", "warnTop"),
}


def selection(default: str) -> dict:
    if default not in SIGNALS:
        raise ValueError(f"default signal {default!r} has no Pine implementation")
    order = [default] + [k for k in SIGNALS if k != default]
    buy = " : ".join(f'sigMode == "{SIGNALS[k][0]}" ? {SIGNALS[k][1]}' for k in order[:-1]) + f" : {SIGNALS[order[-1]][1]}"
    sell = " : ".join(f'sigMode == "{SIGNALS[k][0]}" ? {SIGNALS[k][2]}' for k in order[:-1]) + f" : {SIGNALS[order[-1]][2]}"
    return {"__SIGDEF__": SIGNALS[default][0], "__SIGOPTS__": ", ".join(f'"{SIGNALS[k][0]}"' for k in order),
            "__SELBUY__": buy, "__SELSELL__": sell}


def generate(S: dict, R: dict | None = None, default: str = "K_CONF") -> str:
    feats = feature_order(S)
    fv = ", ".join(FV_ORDER_PINE(feats)) if feats else "0.0"
    blocks = model_block(S, "top") + "\n\n" + model_block(S, "bot")
    src = TEMPLATE.replace("__FV__", fv).replace("__MODELS__", blocks).replace("__EVID__", evidence_block(S, R))
    for k, v in selection(default).items():
        src = src.replace(k, v)
    return src


def parse_arrays(src: str, d: str, bucket: int) -> dict:
    """Read the flat arrays for (direction, bucket) back out of generated Pine (for parity tests)."""
    D = d.capitalize()
    blk = src.split(f"if barstate.isfirst")[1 if d == "top" else 2]
    part = blk.split(f"    if bucket == {bucket}\n")[1].split("\n    if bucket")[0]
    out = {}
    for k in ("nf", "nt", "nm", "nl", "nr", "nv", "roots"):
        vals = []
        for m in re.finditer(rf"{k}{D}\.concat\(array\.from\(([^)]*)\)\)", part):
            vals += [float(x) for x in m.group(1).split(", ")]
        out[k] = [int(x) for x in vals] if k in ("nf", "nm", "nl", "nr", "roots") else vals
    out["base"] = float(re.search(rf"base{D} := (\S+)", part).group(1))
    return out


if __name__ == "__main__":
    S = json.loads(SPEC.read_text())
    R = json.loads(RESULTS.read_text()) if RESULTS.exists() else None
    OUT.write_text(generate(S, R))
    print("wrote", OUT)
