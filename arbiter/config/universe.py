from __future__ import annotations

"""Symbol universe configuration for Arbiter data refresh."""

MARKET_SYMBOLS: list[str] = [
    # Major index ETFs
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
    # Large-cap US tech and growth
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "GOOG",
    "META",
    "TSLA",
    "AVGO",
    "AMD",
    "NFLX",
    "ADBE",
    "CRM",
    "INTC",
    "CSCO",
    "ORCL",
    "IBM",
    "QCOM",
    "TXN",
    "SHOP",
    "UBER",
    "ABNB",
    "SNOW",
    "PANW",
    "CRWD",
    "NOW",
    "MU",
    "AMAT",
    "LRCX",
    "ASML",
    "TSM",
    # Financials / others
    "JPM",
    "BAC",
    "GS",
    "MS",
    "V",
    "MA",
    # Selected consumer / diversified
    "DIS",
    "NKE",
    "MCD",
    "HD",
    "PG",
    "KO",
    "PEP",
]

# 新闻关注标的，默认与市场标的相同，后续可细分
NEWS_SYMBOLS: list[str] = MARKET_SYMBOLS.copy()

