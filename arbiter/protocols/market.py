from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Instrument:
    symbol: str
    asset_type: str
    exchange: str
    currency: str
    tick_size: float
    lot_size: float
    price_precision: int
    size_precision: int


@dataclass(slots=True)
class MarketBar:
    symbol: str
    timestamp: datetime
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str


