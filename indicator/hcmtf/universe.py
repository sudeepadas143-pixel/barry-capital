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
    tier: str = ""  # crypto only: large / mid / small / defunct


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
    Asset("BTCUSDT", "crypto", "binance", True, "24h", "large"),
    Asset("ETHUSDT", "crypto", "binance", True, "24h", "large"),
    Asset("XRPUSDT", "crypto", "binance", True, "24h", "large"),
    Asset("LTCUSDT", "crypto", "binance", True, "24h", "mid"),
    Asset("ADAUSDT", "crypto", "binance", True, "24h", "mid"),
    Asset("BNBUSDT", "crypto", "binance", True, "24h", "large"),
    Asset("LINKUSDT", "crypto", "binance", True, "24h", "mid"),
]

# FRESH: symbols added for v2 BEFORE any v2 result existed, and never used to design,
# screen or tune anything. They are the cross-sectional out-of-sample test. The crypto
# list spans large caps, mid caps, thin small caps and coins that collapsed or were
# delisted (LUNA, FTT, SRM, WAVES; MATIC was migrated to POL), which is the closest free
# data gets to a survivorship-free sample.
FRESH = [
    Asset("SOLUSDT", "crypto", "binance", True, "24h", "large"),
    Asset("DOGEUSDT", "crypto", "binance", True, "24h", "large"),
    Asset("TRXUSDT", "crypto", "binance", True, "24h", "large"),
    Asset("BCHUSDT", "crypto", "binance", True, "24h", "large"),
    Asset("DOTUSDT", "crypto", "binance", True, "24h", "mid"),
    Asset("ATOMUSDT", "crypto", "binance", True, "24h", "mid"),
    Asset("ETCUSDT", "crypto", "binance", True, "24h", "mid"),
    Asset("XLMUSDT", "crypto", "binance", True, "24h", "mid"),
    Asset("FILUSDT", "crypto", "binance", True, "24h", "mid"),
    Asset("ALGOUSDT", "crypto", "binance", True, "24h", "mid"),
    Asset("NEOUSDT", "crypto", "binance", True, "24h", "small"),
    Asset("ZECUSDT", "crypto", "binance", True, "24h", "small"),
    Asset("ICXUSDT", "crypto", "binance", True, "24h", "small"),
    Asset("ZILUSDT", "crypto", "binance", True, "24h", "small"),
    Asset("LUNAUSDT", "crypto", "binance", True, "24h", "defunct"),
    Asset("FTTUSDT", "crypto", "binance", True, "24h", "defunct"),
    Asset("SRMUSDT", "crypto", "binance", True, "24h", "defunct"),
    Asset("WAVESUSDT", "crypto", "binance", True, "24h", "defunct"),
    Asset("MATICUSDT", "crypto", "binance", True, "24h", "defunct"),
    Asset("MSFT", "equity", "yahoo", True, "rth"),
    Asset("KO", "equity", "yahoo", True, "rth"),
    Asset("WMT", "equity", "yahoo", True, "rth"),
    Asset("CVX", "equity", "yahoo", True, "rth"),
    Asset("C", "equity", "yahoo", True, "rth"),
    Asset("DIS", "equity", "yahoo", True, "rth"),
    Asset("VZ", "equity", "yahoo", True, "rth"),
    Asset("NKE", "equity", "yahoo", True, "rth"),
    Asset("DIA", "equity_index", "yahoo", True, "rth"),
    Asset("EWJ", "equity_index", "yahoo", True, "rth"),
    Asset("FXI", "equity_index", "yahoo", True, "rth"),
    Asset("EWZ", "equity_index", "yahoo", True, "rth"),
    Asset("HYG", "bond", "yahoo", True, "rth"),
    Asset("LQD", "bond", "yahoo", True, "rth"),
    Asset("UNG", "commodity", "yahoo", True, "rth"),
    Asset("CPER", "commodity", "yahoo", True, "rth"),
    Asset("CORN", "commodity", "yahoo", True, "rth"),
    Asset("USDCAD=X", "fx", "yahoo", False, "24h"),
    Asset("USDCHF=X", "fx", "yahoo", False, "24h"),
    Asset("NZDUSD=X", "fx", "yahoo", False, "24h"),
    Asset("EURJPY=X", "fx", "yahoo", False, "24h"),
]

BY_SYMBOL = {a.symbol: a for a in UNIVERSE + FRESH}
