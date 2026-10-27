"""V4.1 holdout instruments (reports/V4_1_PREREGISTRATION.md §1).

Never downloaded, loaded or used before 2026-10-27; see the pre-registration for the check.
Registering them in hcmtf.universe.BY_SYMBOL lets the existing hcmtf.data loaders fetch them,
without editing hcmtf.
"""

from hcmtf.universe import BY_SYMBOL, FRESH, UNIVERSE, Asset

_C = lambda s: Asset(s, "crypto", "binance", True, "24h")
_Y = lambda s, cls, vol=True, sess="rth": Asset(s, cls, "yahoo", vol, sess)

HOLDOUT = (
    [_C(s) for s in ("AVAXUSDT", "NEARUSDT", "UNIUSDT", "AAVEUSDT", "XTZUSDT", "EOSUSDT", "VETUSDT",
                     "THETAUSDT", "HBARUSDT", "ICPUSDT")]
    + [_Y(s, "equity") for s in ("ORCL", "CSCO", "HD", "MRK", "PG", "UNH", "CAT", "MMM", "PEP", "ADBE")]
    + [_Y(s, "equity_index") for s in ("XLE", "XLF", "XLK", "XLU", "EWG", "EWU")]
    + [_Y(s, "commodity") for s in ("PPLT", "PALL", "WEAT", "DBB")]
    + [_Y(s, "bond") for s in ("TIP", "SHY", "MUB", "EMB")]
    + [_Y(s, "fx", False, "24h") for s in ("USDSEK=X", "USDNOK=X", "USDMXN=X", "USDZAR=X")]
)
SEEN = UNIVERSE + FRESH

for _a in HOLDOUT:
    assert _a.symbol not in BY_SYMBOL or BY_SYMBOL[_a.symbol] == _a, _a.symbol
    BY_SYMBOL[_a.symbol] = _a
assert not {a.symbol for a in HOLDOUT} & {a.symbol for a in SEEN}
