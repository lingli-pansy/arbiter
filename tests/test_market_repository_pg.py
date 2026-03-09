from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from arbiter.data.repositories.db import get_session
from arbiter.data.repositories.market_repository import MarketRepository
from arbiter.protocols.market import MarketBar


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set; PostgreSQL tests skipped",
)


def test_market_repository_append_and_query() -> None:
    now = datetime.now(tz=timezone.utc)
    symbol = "TEST"
    timeframe = "1d"

    with get_session() as session:
        repo = MarketRepository(session)

        bars = [
            MarketBar(
                symbol=symbol,
                timestamp=now - timedelta(days=1),
                timeframe=timeframe,
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000.0,
                source="test",
            )
        ]

        inserted = repo.append_bars(bars)
        assert inserted >= 0

        result = repo.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            start=now - timedelta(days=2),
            end=now,
        )
        assert any(b.symbol == symbol for b in result)

