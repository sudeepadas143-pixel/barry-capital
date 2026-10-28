"""Python twin of pine/Kenny_Divergence_Indicator.pine (signal path only), for diagnostics and
for evaluating the signal-cluster layer on permitted cached data.

Mirrors the Pine script: research features (Pine-identical), the shipped CY-2 scores (trees from
reports/cycle2_model_spec.json, or the B_ext extension baseline), zone onsets per tier, the
Confirmed rule, and the BUY/SELL selection. Closed candles only; no future data.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from . import cycle2_features as C2, cycle_features as CF

ROOT = Path(__file__).resolve().parent.parent
_s = importlib.util.spec_from_file_location("kenny_export_pine", ROOT / "scripts" / "kenny_export_pine.py")
K = importlib.util.module_from_spec(_s)
_s.loader.exec_module(K)

ALLF = CF.PRICE + CF.MOM + CF.VOL + CF.INTER + C2.NEW
STATE = {"K_W": "warning", "K_H": "high"}


def has_volume(df: pd.DataFrame) -> bool:
    """Research rule (per instrument); Pine uses a rolling 50-candle check instead."""
    return "volume" in df and float((df["volume"].fillna(0) > 0).mean()) > 0.9


def features(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    vol = has_volume(df)
    F = CF.features(df, tf, vol)
    F2 = C2.features(df, tf, F["relvol"].to_numpy(float) if vol else None)
    return pd.concat([F, F2], axis=1)


def tree_logodds(sp: dict, X: np.ndarray) -> np.ndarray:
    """Vectorised flat-tree evaluation (same routing as the Pine gbScore loop)."""
    fl = K.flatten(sp)
    nf, nt, nm = np.array(fl["nf"]), np.array(fl["nt"]), np.array(fl["nm"]) == 1
    nl, nr, nv = np.array(fl["nl"]), np.array(fl["nr"]), np.array(fl["nv"])
    s = np.full(len(X), fl["base"])
    rows = np.arange(len(X))
    for root in fl["roots"]:
        k = np.full(len(X), root)
        for _ in range(64):
            split = nf[k] >= 0
            if not split.any():
                break
            f = np.where(split, nf[k], 0)
            xv = X[rows, f]
            go_l = np.where(np.isnan(xv), nm[k], xv <= nt[k])
            k = np.where(split, np.where(go_l, nl[k], nr[k]), k)
        s += nv[k]
    return s


def score(spec_tf: dict, F: pd.DataFrame, d: str) -> np.ndarray:
    sp = spec_tf["models"][d]
    if sp["kind"] == "base":
        return sp["sign"] * F["ext_c"].to_numpy(float)
    X = F[sp["features"]].to_numpy(float)
    p = 1.0 / (1.0 + np.exp(-tree_logodds(sp, X)))
    p[np.isnan(F[CF.PRICE].to_numpy(float)).any(axis=1)] = np.nan       # Pine coreOk
    return p


def states(df: pd.DataFrame, tf: str, spec: dict) -> dict:
    """Per direction: score p, thresholds, and onset indices of each internal state."""
    S = spec["tfs"][tf]
    F = features(df, tf)
    L, D = CF.SCALE[tf]["L"], CF.SCALE[tf]["D"]
    c = CF.q_of(L)
    o, h, l, cl = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    out = {"F": F}
    for d, side in (("top", -1), ("bot", 1)):
        p = score(S, F, d)
        th = S["models"][d]["theta"]
        st = {"p": p, "theta": th}
        for k, tier in (("K_W", "warning"), ("K_S", "standard"), ("K_H", "high")):
            st[k] = CF.zone_onsets(p, th[tier], c)
        _, conf = CF.developing_and_confirmed(st["K_S"], side, o, h, l, cl, F["_rsi"].to_numpy(float), F["_hist"].to_numpy(float),
                                              F["_ema_f"].to_numpy(float), F["_atr"].to_numpy(float), L, D)
        st["K_CONF"] = conf
        out[d] = st
    return out


def shipped_signals(df: pd.DataFrame, tf: str, spec: dict, buy: str = "K_H", sell: str = "K_CONF", cooldown: bool = True):
    """Final BUY/SELL candle indices as the current Pine script draws them."""
    from .kb_signals import dedupe_final
    st = states(df, tf, spec)
    b, s = st["bot"][buy], st["top"][sell]
    if cooldown:
        return (*dedupe_final(b, s, CF.q_of(CF.SCALE[tf]["L"])), st)
    both = np.intersect1d(b, s)
    return np.setdiff1d(b, both), np.setdiff1d(s, both), st
