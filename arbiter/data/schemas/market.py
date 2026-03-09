from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class MarketBarModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    timestamp: datetime
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str


class NewsEventModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    symbol: str
    timestamp: datetime
    headline: str
    summary: str | None = None
    source: str
    url: str | None = None

