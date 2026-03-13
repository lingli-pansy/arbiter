"""
Venue mapping for BarType generation (TICKET_0004).
Symbol -> exchange venue, used by convert_bars_to_nt.
"""
from __future__ import annotations

# US major exchanges - symbol -> venue for NautilusTrader BarType
# 扩展此表以支持更多标的
NASDAQ_SYMBOLS = frozenset({
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST",
    "NFLX", "AMD", "PEP", "ADBE", "CSCO", "TMUS", "CMCSA", "INTC", "INTU", "AMGN",
    "QCOM", "TXN", "HON", "AMAT", "SBUX", "VRTX", "LRCX", "BKNG", "ADP", "REGN",
    "PANW", "MDLZ", "GILD", "ADI", "ISRG", "VRSK", "SNPS", "CDNS", "KLAC", "MAR",
    "CRWD", "MRVL", "CTAS", "DXCM", "ABNB", "ORLY", "MNST", "PCAR", "WDAY", "PAYX",
    "FTNT", "ROST", "FAST", "CHTR", "CPRT", "KDP", "AZN", "MELI", "ASML", "DDOG",
    "CTSH", "TEAM", "IDXX", "LULU", "ODFL", "EA", "XEL", "FANG", "ZS", "TTD",
    "GEHC", "MCHP", "CCEP", "KHC", "CDW", "EXC", "BKR", "AEP", "FTV", "DXCM",
})
NYSE_SYMBOLS = frozenset({
    "JPM", "V", "UNH", "HD", "PG", "MA", "DIS", "CVX", "ABBV", "MRK",
    "PFE", "KO", "PEP", "WMT", "MCD", "COST", "NEE", "TMO", "ACN", "LIN",
    "ABT", "DHR", "BMY", "PM", "TXN", "NKE", "RTX", "HCA", "UPS", "ORCL",
    "MS", "LOW", "INTC", "QCOM", "AMGN", "INTU", "SPGI", "CVS", "AXP",
    "MDT", "GILD", "ADP", "C", "SYK", "BLK", "CI", "TJX", "DE", "BDX",
    "ISRG", "SO", "DUK", "BSX", "EOG", "SLB", "ZTS", "GS", "CB", "REGN",
})
ARCA_SYMBOLS = frozenset()  # 可扩展
DEFAULT_VENUE = "XNAS"  # NautilusTrader 常用 venue 标识


def resolve_symbol_venue(symbol: str) -> str:
    """Resolve symbol to NautilusTrader venue code."""
    s = symbol.upper().strip()
    if s in NASDAQ_SYMBOLS:
        return "NASDAQ"
    if s in NYSE_SYMBOLS:
        return "NYSE"
    if s in ARCA_SYMBOLS:
        return "ARCA"
    # Fallback: 常见 ETFs、指数多在 ARCA；个股默认 NASDAQ
    return "NASDAQ"


def resolve_venues(symbols: list[str]) -> dict[str, str]:
    """Resolve multiple symbols to venue mapping."""
    return {s: resolve_symbol_venue(s) for s in symbols}
