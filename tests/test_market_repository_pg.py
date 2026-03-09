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

        repo.append_bars(bars)

        result = repo.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            start=now - timedelta(days=2),
            end=now,
        )
        assert any(b.symbol == symbol for b in result)


def test_market_repository_get_latest_bars_limits_and_orders() -> None:
    now = datetime.now(tz=timezone.utc)
    symbol = "TEST_LATEST"
    timeframe = "1d"

    with get_session() as session:
        repo = MarketRepository(session)

        bars = [
            MarketBar(
                symbol=symbol,
                timestamp=now - timedelta(days=i),
                timeframe=timeframe,
                open=100.0 + i,
                high=101.0 + i,
                low=99.0 + i,
                close=100.5 + i,
                volume=1000.0 + i,
                source="test",
            )
            for i in range(5)
        ]

        repo.append_bars(bars)

        latest = repo.get_latest_bars(symbol=symbol, timeframe=timeframe, limit=3)
        assert len(latest) == 3
        # 应为时间升序，且为最近三天
        timestamps = [b.timestamp for b in latest]
        assert timestamps == sorted(timestamps)
        assert max(timestamps) == max(b.timestamp for b in bars)

