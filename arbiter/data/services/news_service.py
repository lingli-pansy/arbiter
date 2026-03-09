from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from arbiter.data.repositories.db import get_session
from arbiter.data.repositories.news_repository import NewsRepository
from arbiter.data.repositories.refresh_state_repository import RefreshStateRepository
from arbiter.protocols.news import NewsEvent


def get_news(symbol: str, limit: int) -> List[NewsEvent]:
    """Query latest news events for a symbol from PostgreSQL."""
    with get_session() as session:
        repo = NewsRepository(session)
        # 使用一个较宽的时间窗口，然后按时间倒序截取 limit 条。
        end = datetime.now(tz=timezone.utc)
        start = end.replace(year=end.year - 5)
        events = repo.get_events(symbol=symbol, start=start, end=end)
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]


def refresh_news_and_get_state(symbol: str) -> dict:
    """Convenience wrapper to refresh news via ingestion and return updated state snapshot."""
    from arbiter.data.ingestion.news_refresh import refresh_news  # lazy import to avoid cycles

    inserted = refresh_news(symbol)

    with get_session() as session:
        state_repo = RefreshStateRepository(session)
        state = state_repo.get_state("news_events", symbol, "finnhub")

    return {
        "symbol": symbol,
        "inserted": inserted,
        "state": {
            "dataset_type": state.dataset_type if state else None,
            "dataset_key": state.dataset_key if state else None,
            "source": state.source if state else None,
            "last_success_at": state.last_success_at.isoformat() if state and state.last_success_at else None,
            "last_event_timestamp": state.last_event_timestamp.isoformat() if state and state.last_event_timestamp else None,
            "refresh_status": state.refresh_status if state else None,
            "error_message": state.error_message if state else None,
        },
    }

