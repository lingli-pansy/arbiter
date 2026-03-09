from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class NewsEvent:
    event_id: str
    timestamp: datetime
    symbols: list[str]
    headline: str
    summary: str
    source: str
    url: str | None = None
    sentiment: float | None = None
    entities: list[str] | None = None


