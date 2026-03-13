"""
Sector mapping for exposure analysis (TICKET_0009).
Symbol -> sector/industry, used by analyze_exposure.
"""
from __future__ import annotations

# 常见美股 sector/industry 静态映射
SECTOR_MAP: dict[str, dict[str, str]] = {
    "AAPL": {"sector": "Technology", "industry": "Consumer Electronics"},
    "MSFT": {"sector": "Technology", "industry": "Software"},
    "NVDA": {"sector": "Technology", "industry": "Semiconductors"},
    "GOOGL": {"sector": "Communication Services", "industry": "Internet"},
    "GOOG": {"sector": "Communication Services", "industry": "Internet"},
    "AMZN": {"sector": "Consumer Cyclical", "industry": "Internet Retail"},
    "META": {"sector": "Communication Services", "industry": "Internet"},
    "TSLA": {"sector": "Consumer Cyclical", "industry": "Auto Manufacturers"},
    "BRK.B": {"sector": "Financial Services", "industry": "Insurance"},
    "BRK-A": {"sector": "Financial Services", "industry": "Insurance"},
    "JPM": {"sector": "Financial Services", "industry": "Banks"},
    "V": {"sector": "Financial Services", "industry": "Credit Services"},
    "UNH": {"sector": "Healthcare", "industry": "Healthcare Plans"},
    "JNJ": {"sector": "Healthcare", "industry": "Drug Manufacturers"},
    "HD": {"sector": "Consumer Cyclical", "industry": "Home Improvement"},
    "PG": {"sector": "Consumer Defensive", "industry": "Household Products"},
    "MA": {"sector": "Financial Services", "industry": "Credit Services"},
    "XOM": {"sector": "Energy", "industry": "Oil & Gas"},
    "CVX": {"sector": "Energy", "industry": "Oil & Gas"},
    "AVGO": {"sector": "Technology", "industry": "Semiconductors"},
    "COST": {"sector": "Consumer Defensive", "industry": "Discount Stores"},
    "NFLX": {"sector": "Communication Services", "industry": "Entertainment"},
    "AMD": {"sector": "Technology", "industry": "Semiconductors"},
    "PEP": {"sector": "Consumer Defensive", "industry": "Beverages"},
    "ADBE": {"sector": "Technology", "industry": "Software"},
    "KO": {"sector": "Consumer Defensive", "industry": "Beverages"},
    "WMT": {"sector": "Consumer Defensive", "industry": "Discount Stores"},
    "MCD": {"sector": "Consumer Cyclical", "industry": "Restaurants"},
    "ORCL": {"sector": "Technology", "industry": "Software"},
    "CRM": {"sector": "Technology", "industry": "Software"},
    "INTC": {"sector": "Technology", "industry": "Semiconductors"},
    "NEE": {"sector": "Utilities", "industry": "Utilities"},
    "TMO": {"sector": "Healthcare", "industry": "Diagnostics"},
    "ACN": {"sector": "Technology", "industry": "Consulting"},
    "LIN": {"sector": "Basic Materials", "industry": "Chemicals"},
    "ABT": {"sector": "Healthcare", "industry": "Medical Devices"},
    "DHR": {"sector": "Healthcare", "industry": "Diagnostics"},
    "DIS": {"sector": "Communication Services", "industry": "Entertainment"},
    "PFE": {"sector": "Healthcare", "industry": "Drug Manufacturers"},
    "ABBV": {"sector": "Healthcare", "industry": "Drug Manufacturers"},
    "MRK": {"sector": "Healthcare", "industry": "Drug Manufacturers"},
    "BMY": {"sector": "Healthcare", "industry": "Drug Manufacturers"},
    "NKE": {"sector": "Consumer Cyclical", "industry": "Footwear"},
    "PM": {"sector": "Consumer Defensive", "industry": "Tobacco"},
    "RTX": {"sector": "Industrials", "industry": "Aerospace & Defense"},
    "HCA": {"sector": "Healthcare", "industry": "Healthcare Facilities"},
    "UPS": {"sector": "Industrials", "industry": "Integrated Freight"},
    "GS": {"sector": "Financial Services", "industry": "Capital Markets"},
    "MS": {"sector": "Financial Services", "industry": "Capital Markets"},
    "BLK": {"sector": "Financial Services", "industry": "Asset Management"},
    "LOW": {"sector": "Consumer Cyclical", "industry": "Home Improvement"},
    "SPGI": {"sector": "Financial Services", "industry": "Financial Data"},
    "CVS": {"sector": "Healthcare", "industry": "Healthcare Plans"},
    "AXP": {"sector": "Financial Services", "industry": "Credit Services"},
    "C": {"sector": "Financial Services", "industry": "Banks"},
    "AMGN": {"sector": "Healthcare", "industry": "Biotechnology"},
    "GILD": {"sector": "Healthcare", "industry": "Biotechnology"},
    "REGN": {"sector": "Healthcare", "industry": "Biotechnology"},
    "QCOM": {"sector": "Technology", "industry": "Semiconductors"},
    "TXN": {"sector": "Technology", "industry": "Semiconductors"},
    "HON": {"sector": "Industrials", "industry": "Conglomerates"},
    "AMAT": {"sector": "Technology", "industry": "Semiconductor Equipment"},
    "SBUX": {"sector": "Consumer Cyclical", "industry": "Restaurants"},
    "DE": {"sector": "Industrials", "industry": "Farm & Construction"},
    "CAT": {"sector": "Industrials", "industry": "Farm & Construction"},
    "BA": {"sector": "Industrials", "industry": "Aerospace & Defense"},
    "IBM": {"sector": "Technology", "industry": "Information Technology"},
    "GE": {"sector": "Industrials", "industry": "Conglomerates"},
    "F": {"sector": "Consumer Cyclical", "industry": "Auto Manufacturers"},
    "GM": {"sector": "Consumer Cyclical", "industry": "Auto Manufacturers"},
}


def get_sector(symbol: str) -> str:
    """Get sector for symbol. Returns 'Unknown' if not in map."""
    s = symbol.upper().strip()
    info = SECTOR_MAP.get(s)
    return info["sector"] if info else "Unknown"


def get_industry(symbol: str) -> str:
    """Get industry for symbol. Returns 'Unknown' if not in map."""
    s = symbol.upper().strip()
    info = SECTOR_MAP.get(s)
    return info["industry"] if info else "Unknown"


def map_symbols(symbols: list[str]) -> dict[str, dict[str, str]]:
    """Map symbols to sector/industry."""
    return {s: {"sector": get_sector(s), "industry": get_industry(s)} for s in symbols}
