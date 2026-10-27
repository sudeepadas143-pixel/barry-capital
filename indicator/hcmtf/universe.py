"""The symbol universe, fixed before any result was looked at.

Selection rule: liquid instruments that were already trading in 2018, picked by asset
class rather than by how they performed afterwards. Laggards are included on purpose
(INTC, BA, PFE, T, F, USO, LTC, XRP, ADA) so the sample is not a list of winners.
It still contains no delisted names, which is the survivorship bias we cannot remove
with free data; the report says so.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Asset:
    symbol: str
    cls: str        # equity_index, equity, bond, commodity, fx, crypto
    source: str     # yahoo or binance
    volume: bool    # does the feed carry real traded volume?
    session: str    # "rth" (exchange hours) or "24h"


# Round-trip cost in basis points of notional (commission + half-spread both ways + slippage).
COST_BPS = {
    "equity_index": 4.0,
    "equity": 6.0,
    "bond": 4.0,
    "commodity": 8.0,
    "fx": 3.0,
    "crypto": 20.0,
}

UNIVERSE = [
    Asset("SPY", "equity_index", "yahoo", True, "rth"),
    Asset("QQQ", "equity_index", "yahoo", True, "rth"),
    Asset("IWM", "equity_index", "yahoo", True, "rth"),
    Asset("EFA", "equity_index", "yahoo", True, "rth"),
    Asset("EEM", "equity_index", "yahoo", True, "rth"),
    Asset("AAPL", "equity", "yahoo", True, "rth"),
    Asset("JPM", "equity", "yahoo", True, "rth"),
    Asset("XOM", "equity", "yahoo", True, "rth"),
    Asset("INTC", "equity", "yahoo", True, "rth"),
    Asset("BA", "equity", "yahoo", True, "rth"),
    Asset("PFE", "equity", "yahoo", True, "rth"),
    Asset("T", "equity", "yahoo", True, "rth"),
    Asset("F", "equity", "yahoo", True, "rth"),
    Asset("TLT", "bond", "yahoo", True, "rth"),
    Asset("IEF", "bond", "yahoo", True, "rth"),
    Asset("GLD", "commodity", "yahoo", True, "rth"),
    Asset("SLV", "commodity", "yahoo", True, "rth"),
    Asset("USO", "commodity", "yahoo", True, "rth"),
    Asset("DBA", "commodity", "yahoo", True, "rth"),
    Asset("EURUSD=X", "fx", "yahoo", False, "24h"),
    Asset("USDJPY=X", "fx", "yahoo", False, "24h"),
    Asset("GBPUSD=X", "fx", "yahoo", False, "24h"),
    Asset("AUDUSD=X", "fx", "yahoo", False, "24h"),
    Asset("BTCUSDT", "crypto", "binance", True, "24h"),
    Asset("ETHUSDT", "crypto", "binance", True, "24h"),
    Asset("XRPUSDT", "crypto", "binance", True, "24h"),
    Asset("LTCUSDT", "crypto", "binance", True, "24h"),
    Asset("ADAUSDT", "crypto", "binance", True, "24h"),
    Asset("BNBUSDT", "crypto", "binance", True, "24h"),
    Asset("LINKUSDT", "crypto", "binance", True, "24h"),
]

BY_SYMBOL = {a.symbol: a for a in UNIVERSE}
