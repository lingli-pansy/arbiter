from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Order:
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    timestamp: datetime
    status: str
    source: str
    limit_price: float | None = None
    stop_price: float | None = None


@dataclass(slots=True)
class TradeFill:
    fill_id: str
    order_id: str
    symbol: str
    side: str
    price: float
    quantity: float
    timestamp: datetime
    fee: float | None = None
    venue: str | None = None


@dataclass(slots=True)
class ExecutionResult:
    timestamp: datetime
    order_count: int
    executed_order_count: int
    trade_count: int
    execution_status: str
    fills: list[TradeFill]
    notes: str | None = None


