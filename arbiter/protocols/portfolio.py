from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class PortfolioPosition:
    symbol: str
    quantity: float
    market_value: float
    weight: float
    average_cost: float | None = None
    unrealized_pnl: float | None = None


@dataclass(slots=True)
class PortfolioSnapshot:
    timestamp: datetime
    equity: float
    cash: float
    positions: list[PortfolioPosition]
    source: str
    buying_power: float | None = None


