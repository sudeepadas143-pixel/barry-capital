"""Offline preview of the chart markers (not a TradingView screenshot).

Draws candles and the engine's displayed signals with the Pine marker style: a solid
label with white bold "▲ BULLISH" below the candle (pointer up) or "▼ BEARISH" above it
(pointer down). Light and dark backgrounds, desktop-ish and phone-ish sizes.

    python scripts/preview_markers.py BTC-USD 1D
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hcmtf import study as St  # noqa: E402
from hcmtf.report2 import active_params  # noqa: E402
from hcmtf.universe import BY_SYMBOL  # noqa: E402

THEMES = {"light": ("#FFFFFF", "#131722", "#089981", "#F23645"), "dark": ("#000000", "#D1D4DC", "#089981", "#F23645")}
BULL, BEAR = "#2962FF", "#D32F2F"


def draw(sym, tf, theme, phone, n):
    bg, fg, up_c, dn_c = THEMES[theme]
    s = St.prepare_one((BY_SYMBOL[sym], tf))
    sig = St.signals_for(s, active_params(tf))
    sig = sig[sig["tier"] == "major"]
    end = len(s.f.c) - 1
    lo_i = max(0, end - n + 1)
    o, h, l, c = (x[lo_i:end + 1] for x in (s.f.o, s.f.h, s.f.l, s.f.c))
    x = np.arange(len(c))
    size = (3.9, 7.0) if phone else (11, 5.5)
    fig, ax = plt.subplots(figsize=size, dpi=160)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_yscale("log")
    for xi, oo, hh, ll, cc in zip(x, o, h, l, c):
        col = up_c if cc >= oo else dn_c
        ax.vlines(xi, ll, hh, color=col, lw=0.7)
        ax.add_patch(plt.Rectangle((xi - 0.33, min(oo, cc)), 0.66, max(abs(cc - oo), 1e-9), color=col))
    fs = 9 if phone else 9.5
    for _, r in sig[(sig.i >= lo_i) & (sig.i <= end)].iterrows():
        xi = int(r.i) - lo_i
        if r.dir > 0:
            ax.annotate("▲ BULLISH", xy=(xi, l[xi] * 0.985), xytext=(0, -16), textcoords="offset points",
                        ha="center", va="top", fontsize=fs, fontweight="bold", color="white",
                        bbox=dict(boxstyle="round,pad=0.35", fc=BULL, ec=BULL),
                        arrowprops=dict(arrowstyle="wedge,tail_width=0.6", fc=BULL, ec=BULL))
        else:
            ax.annotate("▼ BEARISH", xy=(xi, h[xi] * 1.015), xytext=(0, 16), textcoords="offset points",
                        ha="center", va="bottom", fontsize=fs, fontweight="bold", color="white",
                        bbox=dict(boxstyle="round,pad=0.35", fc=BEAR, ec=BEAR),
                        arrowprops=dict(arrowstyle="wedge,tail_width=0.6", fc=BEAR, ec=BEAR))
    ax.set_ylim(l.min() * 0.82, h.max() * 1.18)
    ax.set_xlim(-2, len(c) + 1)
    ax.yaxis.tick_right()
    ax.tick_params(colors=fg, labelsize=7)
    ax.set_xticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.text(0.02, 0.98, f"{sym} · {tf} · HC-MTF", transform=ax.transAxes, va="top", fontsize=8, color=fg)
    out = ROOT / "reports" / f"preview_{sym}_{tf}_{theme}{'_phone' if phone else ''}.png"
    plt.tight_layout()
    plt.savefig(out, facecolor=bg)
    plt.close(fig)
    return out


if __name__ == "__main__":
    sym, tf = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 160
    for theme in THEMES:
        for phone in (False, True):
            print(draw(sym, tf, theme, phone, n if not phone else n // 2))
