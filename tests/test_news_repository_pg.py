from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from arbiter.data.repositories.db import get_session
from arbiter.data.repositories.news_repository import NewsRepository
from arbiter.protocols.news import NewsEvent


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set; PostgreSQL tests skipped",
)


def test_news_repository_append_and_query() -> None:
    now = datetime.now(tz=timezone.utc)
    symbol = "NEWS"

    with get_session() as session:
        repo = NewsRepository(session)

        events = [
            NewsEvent(
                event_id="evt-1",
                timestamp=now,
                symbols=[symbol],
                headline="Test headline",
                summary="Test summary",
                source="test",
                url=None,
            )
        ]

        inserted = repo.append_events(events)
        assert inserted >= 0

        result = repo.get_events(
            symbol=symbol,
            start=now.replace(hour=0, minute=0, second=0, microsecond=0),
            end=now,
        )
        assert any(symbol in e.symbols for e in result)

