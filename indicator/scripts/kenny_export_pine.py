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

_s = importlib.util.spec_from_file_location("cycle_export_pine", ROOT / "scripts" / "cycle_export_pine.py")
_X = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_X)
PINE_FEAT = {**_X.PINE_FEAT,  # CY-2 features (research/cycle2_features.py), same definitions in the feature block
             "bbz": "fBbz", "roc": "fRoc", "roc_acc": "fRocAcc", "wick_up": "fWickUp", "wick_dn": "fWickDn",
             "td_up": "fTdUp", "td_dn": "fTdDn", "vratio": "fVRatio", "dd_hh": "fDdHH", "du_ll": "fDuLL",
             "above": "fAbove", "climax": "fClimax"}


def _f(x: float) -> str:
    """Pine float literal: positional (no exponent), always with a decimal point."""
    import numpy as np
    s = np.format_float_positional(float(x), unique=True, trim="0")
    return s if "." in s else s + ".0"


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


STR_CHUNK = 900                 # characters per Pine string literal (kept well under Pine's string limits)


def _g9(x: float) -> str:
    """10 significant digits, never exponent notation (str.tonumber input)."""
    import numpy as np
    return np.format_float_positional(float(x), precision=10, unique=False, fractional=False, trim="-")


def encode(fl: dict) -> list[str]:
    """Flat trees -> compact text: nodes separated by ';', a split node is 'f,t,m,l,r' (absolute
    child indices), a leaf is its value; 'T' marks the first node of a tree. Split into string
    chunks only at node boundaries. TradingView rejects long scripts (CE10295), so the trees
    travel as a few string literals instead of thousands of array elements."""
    roots = set(fl["roots"])
    toks = []
    for k in range(len(fl["nf"])):
        t = _g9(fl["nv"][k]) if fl["nf"][k] < 0 else f"{fl['nf'][k]},{_g9(fl['nt'][k])},{fl['nm'][k]},{fl['nl'][k]},{fl['nr'][k]}"
        toks.append(("T" if k in roots else "") + t)
    chunks, cur = [], ""
    for t in toks:
        if cur and len(cur) + 1 + len(t) > STR_CHUNK:
            chunks.append(cur)
            cur = t
        else:
            cur = f"{cur};{t}" if cur else t
    if cur:
        chunks.append(cur)
    return chunks


def decode(chunks: list[str]) -> dict:
    """Python twin of the Pine loadModel() function."""
    out = {k: [] for k in ("nf", "nt", "nm", "nl", "nr", "nv", "roots")}
    for ch in chunks:
        for tok in ch.split(";"):
            if tok.startswith("T"):
                out["roots"].append(len(out["nf"]))
                tok = tok[1:]
            p = tok.split(",")
            if len(p) == 1:
                vals = (-1, 0.0, 0, -1, -1, float(p[0]))
            else:
                vals = (int(float(p[0])), float(p[1]), int(float(p[2])), int(float(p[3])), int(float(p[4])), 0.0)
            for k, v in zip(("nf", "nt", "nm", "nl", "nr", "nv"), vals):
                out[k].append(v)
    return out


def model_block(S: dict, d: str) -> tuple[str, str]:
    """(data functions, first-bar loading block) for direction d."""
    D = d.capitalize()
    funcs, L = [], [f"if barstate.isfirst"]
    for tf, b in BUCKET.items():
        if tf not in S["tfs"]:
            continue
        sp = S["tfs"][tf]["models"][d]
        th = sp["theta"]
        L += [f"    if bucket == {b}", f"        th{D}W := {_f(th['warning'])}", f"        th{D}S := {_f(th['standard'])}",
              f"        th{D}H := {_f(th['high'])}", f"        name{D} := \"{sp['model']}\""]
        if sp["kind"] == "gb":
            FV_ORDER_PINE(sp["features"])                                # refuses unportable features
            fl = flatten(sp)
            fn = f"data{D}{b}"
            funcs += [f"{fn}() =>", "    a = array.new<string>()"] + [f'    a.push("{c}")' for c in encode(fl)] + ["    a"]
            L += [f"        gb{D} := true", f"        base{D} := {_f(fl['base'])}",
                  f"        loadModel({fn}(), nf{D}, nt{D}, nm{D}, nl{D}, nr{D}, nv{D}, roots{D})"]
        elif sp["kind"] == "base":
            L += [f"        gb{D} := false", f"        sign{D} := {_f(sp['sign'])}"]
            if sp["feature"] != "ext_c":
                raise ValueError("baseline must be B_ext")
        else:
            raise ValueError(f"unsupported model kind {sp['kind']!r}")
    return "\n".join(funcs), "\n".join(L)


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
//   Which state draws the triangles is chosen per timeframe so that arrows are "right enough in
//   retrospect" (near the low/high and followed by a move the right way; reports/KR_RESULTS.md):
//   BUY = High Conviction (threshold x1.1 on 1W/4H); SELL = early top states (1D High Conviction
//   x0.9, 4H Early Warning x0.9, 1H Early Warning; 1W exhaustion + reversal near the 52-week high).
//   Input "Signal profile = Previous" restores BUY High Conviction / SELL Confirmed everywhere.
//   Stocks/indices on 1D/1W: a BUY right after a VIX spike-and-reversal is drawn larger
//   (input "Larger BUY after a VIX spike-and-reversal"; reports/KX_RESULTS.md).
//   4H and below also show a small red X when a mature uptrend breaks down (exit / protect;
//   reports/KT_RESULTS.md); input "Breakdown / exit markers" turns it off. A candle with both BUY and SELL draws neither; a same-direction repeat within
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
profile  = input.string("Optimized", "Signal profile", options = ["Optimized", "Previous"], group = grpS, tooltip = "Optimized = per-timeframe BUY/SELL choice that is most often right in retrospect (reports/KR_RESULTS.md). Previous = BUY High Conviction / SELL Confirmed on every timeframe (rollback).")
showBuy  = input.bool(true, "BUY triangles", group = grpS)
showSell = input.bool(true, "SELL triangles", group = grpS)
volMode  = input.string("Auto", "Volume features", options = ["Auto", "Off"], group = grpS, tooltip = "Auto uses volume features when the feed has volume on >90% of the last 50 candles; otherwise they are treated as missing (as for no-volume instruments in the research).")
showBrk  = input.bool(true, "Breakdown / exit markers (4H and below)", group = grpS, tooltip = "Small red X above the candle: a mature uptrend has broken down (exit / protect). Shown only where it beat its baseline in research (reports/KT_RESULTS.md).")
showVixW = input.bool(true, "Larger BUY after a VIX spike-and-reversal (stocks/indices, 1D/1W)", group = grpS, tooltip = "Stocks, ETFs and indices on 1D/1W only: a BUY that comes within 10 days after VIX spiked (>= 30 and >= its 1-year 90th percentile) and then fell >= 20% is drawn larger. Research (reports/KX_RESULTS.md): stronger in early data, only modestly better in later data; it did not pass the full test.")
showDz   = input.bool(true, "Daily BUY zone on 4H and below", group = grpS, tooltip = "On 4H and lower charts: a green '1D' marker on the first candle after a completed daily BUY, and a faint green background for the following 15 days (a quarter of the daily cycle). The daily BUY is the same arrow the 1D chart shows, read from the previous completed day, so it never repaints. Research: 4H/1H BUYs alone are weak (reports/KLB_RESULTS.md); a daily BUY is right in retrospect about 54% of the time.")
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

// unpack the compact tree text (see scripts/kenny_export_pine.py encode/decode); runs on the first bar only
loadModel(array<string> chunks, array<int> nf, array<float> nt, array<int> nm, array<int> nl, array<int> nr, array<float> nv, array<int> roots) =>
    for ch in chunks
        for tok in str.split(ch, ";")
            string t = tok
            if str.startswith(t, "T")
                roots.push(nf.size())
                t := str.substring(t, 1)
            p = str.split(t, ",")
            if p.size() == 1
                nf.push(-1)
                nt.push(0.0)
                nm.push(0)
                nl.push(-1)
                nr.push(-1)
                nv.push(str.tonumber(p.get(0)))
            else
                nf.push(int(str.tonumber(p.get(0))))
                nt.push(str.tonumber(p.get(1)))
                nm.push(int(str.tonumber(p.get(2))))
                nl.push(int(str.tonumber(p.get(3))))
                nr.push(int(str.tonumber(p.get(4))))
                nv.push(0.0)
    nf.size()

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
prevTop = nz(ta.highest(pTop, Q)[1], -999999999.0)      // computed on every bar (consistent series history)
prevBot = nz(ta.highest(pBot, Q)[1], -999999999.0)
onset(float p, float prev, float th) => barstate.isconfirmed and not na(p) and p >= th and not (prev >= th)
warnTop = onset(pTop, prevTop, thTopW)
stdTop  = onset(pTop, prevTop, thTopS)
highTop = onset(pTop, prevTop, thTopH)
warnBot = onset(pBot, prevBot, thBotW)
stdBot  = onset(pBot, prevBot, thBotS)
highBot = onset(pBot, prevBot, thBotH)

// completed higher-timeframe trend (previous closed HTF candle): +1 up, -1 down
htfDir() => close > ta.ema(close, 21) ? 1 : -1
htfTrend = request.security(syminfo.tickerid, htfStr, htfDir()[1], lookahead = barmerge.lookahead_on)

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
// weekly SELL (Optimized profile): exhaustion + reversal near the 52-week high (= research/kenny_weekly_sell.cand_A, R = 6)
atrW     = ta.atr(14)
rsiW     = ta.rsi(close, 14)
rsiMax8  = ta.highest(rsiW, 8)
tsmW     = math.sum(math.sign(close - close[1]), 52) / math.sqrt(52)
rally52  = (close - ta.lowest(low, 52)) / atrW
dd52     = (ta.highest(high, 52) - close) / atrW
hh52p    = ta.highest(high, 52)[1]
bodyW    = math.abs(close - open)
upW      = high - math.max(open, close)
starW    = upW >= 2 * bodyW and upW >= 0.5 * rg
engulfW  = close < open and close[1] > open[1] and open >= close[1] and close <= open[1]
failedW  = high > hh52p and close < hh52p
wkTop    = rally52 >= 6.0 and tsmW >= 0.5 and rsiMax8 >= 65 and rsiW <= rsiMax8 - 5 and dd52 <= 2.0 and (starW or engulfW or failedW)
// per-timeframe choice (reports/KR_RESULTS.md): threshold scale x state, chosen on early data, checked on later data
kBuy  = __KBUY__
kSell = __KSELL__
optBuy  = onset(pBot, prevBot, thBotH * kBuy)
optSell = bucket == 3 ? barstate.isconfirmed and wkTop : __SELLSTATE__
// BUY strength (reports/KS_RESULTS.md, = research/kenny_strength.py): margin + independent evidence + HTF agreement;
// "strong only" where it was more often right in retrospect (1W and 1H-and-below BUY)
pivLo = low[5] < ta.lowest(low, 5)[6] and low[5] <= ta.lowest(low, 5)
divScore(array<int> pb, array<float> pp, array<float> pr, array<float> ph, bool isPiv, float px, float rs, float hs) =>
    float out = 0.0
    if isPiv
        int p = bar_index - 5
        while pb.size() > 0 and p - pb.get(0) > 60
            pb.shift()
            pp.shift()
            pr.shift()
            ph.shift()
        if pb.size() > 0
            for j = pb.size() - 1 to 0
                int q = pb.get(j)
                if p - q >= 5
                    float k = 0.0
                    bool pxDiv = px < pp.get(j)
                    if pxDiv and not na(rs) and not na(pr.get(j)) and rs > pr.get(j)
                        k += 0.5
                    if pxDiv and not na(hs) and not na(ph.get(j)) and hs > ph.get(j)
                        k += 0.5
                    out := k
                    break
        pb.push(p)
        pp.push(px)
        pr.push(rs)
        ph.push(hs)
    out
var array<int> plB = array.new<int>()
var array<float> plP = array.new<float>()
var array<float> plR = array.new<float>()
var array<float> plH = array.new<float>()
float eDivBot = 0.0
if barstate.isconfirmed
    eDivBot := divScore(plB, plP, plR, plH, pivLo, low[5], r[5], hst[5])
llPrev = ta.lowest(low, L)[1]
posPrev = rngOf(L)[1]
wdNow = rg > 0 ? (math.min(open, close) - low) / rg : 0.0
paBot = (low < llPrev and close > llPrev) or (close > open and close[1] < open[1] and open <= close[1] and close >= open[1] and posPrev <= 0.1) or (wdNow >= 0.6 and low <= llPrev)
burstBot = (nz(fRelVol, -9.0) >= 1.0 or nz(fVRatio, -9.0) >= 0.5) and wdNow >= 0.4
evBot = (ta.highest(eDivBot > 0 ? 1.0 : 0.0, 8) > 0 ? 1 : 0) + (ta.highest(paBot ? 1.0 : 0.0, 3) > 0 ? 1 : 0) + (ta.highest(burstBot ? 1.0 : 0.0, 3) > 0 ? 1 : 0)
strBuy = (not na(pBot) and pBot >= 1.1 * thBotH * kBuy ? 1 : 0) + evBot + (nz(htfTrend) > 0 ? 1 : 0)
kStrongBuy = __KSBUY__
rawBuy  = profile == "Optimized" ? optBuy and strBuy >= kStrongBuy : highBot
rawSell = profile == "Optimized" ? optSell : confTop
wkA     = profile == "Optimized" and bucket == 3                   // the weekly-A SELL is not cooled down (as researched)
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
        sellSig := wkA or bar_index - lastSell > Q
        lastSell := bar_index
cBuy  = #00C853
cSell = #FF1744
// VIX weighting (= research/kenny_context.vix_reversal; previous completed VIX day, no repaint)
vixF() =>
    mx10 = ta.highest(close, 10)
    p90 = ta.percentile_linear_interpolation(close, 252, 90)
    flag = mx10 >= math.max(30.0, p90) and close <= 0.8 * mx10
    ta.highest(flag ? 1.0 : 0.0, 10)
vixAct = request.security("CBOE:VIX", "D", vixF()[1], lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)
isEquity = syminfo.type == "stock" or syminfo.type == "index" or syminfo.type == "fund" or syminfo.type == "dr"
buyHeavy = showVixW and isEquity and bucket >= 2 and nz(vixAct) > 0
// arrow size follows the timeframe: 4H and below small, 1D normal, 1W large (VIX-confirmed BUY one step larger)
buyN = showBuy and buySig and not buyHeavy
buyV = showBuy and buySig and buyHeavy
sellN = showSell and sellSig
plotshape(buyN and bucket <= 1, "BUY", shape.triangleup, location.belowbar, cBuy, size = size.small)
plotshape(buyN and bucket == 2, "BUY 1D", shape.triangleup, location.belowbar, cBuy, size = size.normal)
plotshape(buyN and bucket == 3, "BUY 1W", shape.triangleup, location.belowbar, cBuy, size = size.large)
plotshape(buyV and bucket == 2, "BUY 1D (VIX-confirmed)", shape.triangleup, location.belowbar, cBuy, size = size.large)
plotshape(buyV and bucket == 3, "BUY 1W (VIX-confirmed)", shape.triangleup, location.belowbar, cBuy, size = size.huge)
plotshape(sellN and bucket <= 1, "SELL", shape.triangledown, location.abovebar, cSell, size = size.small)
plotshape(sellN and bucket == 2, "SELL 1D", shape.triangledown, location.abovebar, cSell, size = size.normal)
plotshape(sellN and bucket == 3, "SELL 1W", shape.triangledown, location.abovebar, cSell, size = size.large)
// daily BUY zone on 4H and below (the 1D chart's BUY, previous completed day, no repaint; reports/KBAL_CONFIG.md)
dFlag() => buySig ? 1.0 : 0.0
dNew   = request.security(syminfo.tickerid, "D", dFlag()[1], lookahead = barmerge.lookahead_on)
dSince = request.security(syminfo.tickerid, "D", ta.barssince(buySig)[1], lookahead = barmerge.lookahead_on)
dOn = showDz and bucket <= 1
dMark = dOn and nz(dNew) > 0 and timeframe.change("D")
plotshape(dMark, "Daily BUY (on 4H and below)", shape.labelup, location.belowbar, cBuy, text = "1D", textcolor = color.white, size = size.small)
bgcolor(dOn and not na(dSince) and dSince < 15 ? color.new(cBuy, 92) : na, title = "Daily BUY zone")
alertcondition(dMark, "Kenny Div: Daily BUY (on 4H and below)", "Kenny Div DAILY BUY {{ticker}} {{interval}} {{close}}")
// breakdown / exit (= research/kenny_types.breakdown; 4H and below, reports/KT_RESULTS.md)
hh2L   = ta.highest(high, 2 * L)
nearHi = (hh2L - close) / atr <= 2.0
matureUp = ta.highest(nearHi ? 1.0 : 0.0, M) > 0
sma15  = ta.sma(close, int(math.round(1.5 * L)))
belowS = close < sma15
firstBelow = belowS and math.sum(belowS[1] ? 1.0 : 0.0, M) == 0
brkSig = barstate.isconfirmed and bucket <= 1 and firstBelow and matureUp and nz(hst, 1.0) < 0 and (hh2L - close) / atr < 8.0
plotshape(showBrk and brkSig, "Breakdown", shape.xcross, location.abovebar, cSell, size = size.normal)
alertcondition(brkSig, "Kenny Div: Breakdown / exit", "Kenny Div BREAKDOWN {{ticker}} {{interval}} {{close}}")
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


# reports/KR_RESULTS.md adopted choices per bucket (3 = 1W, 2 = 1D, 1 = 4H, 0 = 1H and below)
KR_BUY_SCALE = {3: 1.1, 2: 1.0, 1: 1.1, 0: 1.0}                       # High Conviction threshold scale
KR_SELL = {2: ("H", 0.9), 1: ("W", 0.9), 0: ("W", 1.0)}              # bucket 3 uses weekly Candidate A


KS_BUY_K = {3: 1, 2: 0, 1: 0, 0: 1}                                  # reports/KS_RESULTS.md adopted strength cut-offs (0 = all arrows)

# reports/KBAL_CONFIG.md: what the Pine uses (more BUYs on 4H/1H; 1W/1D unchanged)
BAL_BUY_SCALE = {**KR_BUY_SCALE, 0: 0.8}                            # 4H back to x1.1 after reports/KLB_RESULTS.md (user decision)
BAL_BUY_K = {**KS_BUY_K, 0: 0}


def kr_block() -> dict:
    kb = " : ".join(f"bucket == {b} ? {_f(BAL_BUY_SCALE[b])}" for b in (3, 2, 1)) + f" : {_f(BAL_BUY_SCALE[0])}"
    ks = " : ".join(f"bucket == {b} ? {_f(KR_SELL[b][1])}" for b in (2, 1)) + f" : {_f(KR_SELL[0][1])}"
    th = {"H": "thTopH", "W": "thTopW"}
    st = " : ".join(f"bucket == {b} ? onset(pTop, prevTop, {th[KR_SELL[b][0]]} * kSell)" for b in (2, 1)) \
        + f" : onset(pTop, prevTop, {th[KR_SELL[0][0]]} * kSell)"
    kk = " : ".join(f"bucket == {b} ? {BAL_BUY_K[b]}" for b in (3, 2, 1)) + f" : {BAL_BUY_K[0]}"
    return {"__KBUY__": kb, "__KSELL__": ks, "__SELLSTATE__": st, "__KSBUY__": kk}


def generate(S: dict, R: dict | None = None) -> str:
    feats = feature_order(S)
    fv = ", ".join(FV_ORDER_PINE(feats)) if feats else "0.0"
    ft, lt = model_block(S, "top")
    fb, lb = model_block(S, "bot")
    blocks = "\n".join(x for x in (ft, fb) if x) + "\n\n" + lt + "\n\n" + lb
    src = TEMPLATE.replace("__FV__", fv).replace("__MODELS__", blocks).replace("__EVID__", evidence_block(S, R))
    for k, v in kr_block().items():
        src = src.replace(k, v)
    return src


def parse_arrays(src: str, d: str, bucket: int) -> dict:
    """Read the tree data for (direction, bucket) back out of generated Pine (for parity tests)."""
    D = d.capitalize()
    body = src.split(f"data{D}{bucket}() =>\n")[1].split("\n    a\n")[0]
    out = decode(re.findall(r'^    a\.push\("([^"]*)"\)$', body, re.M))
    blk = src.split("if barstate.isfirst\n")[1 if d == "top" else 2]
    part = blk.split(f"    if bucket == {bucket}\n")[1].split("\n    if bucket")[0]
    out["base"] = float(re.search(rf"base{D} := (\S+)", part).group(1))
    return out


if __name__ == "__main__":
    S = json.loads(SPEC.read_text())
    R = json.loads(RESULTS.read_text()) if RESULTS.exists() else None
    OUT.write_text(generate(S, R))
    print("wrote", OUT)
