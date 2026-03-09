from __future__ import annotations

import os

import pytest

from arbiter.data.ingestion.market_refresh import bootstrap_market_data, refresh_market_data
from arbiter.data.providers import yahoo_market_provider


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set; PostgreSQL tests skipped",
)


def test_market_refresh_runs_without_error(monkeypatch) -> None:
    # 避免真实网络依赖：将 Yahoo provider 的 fetch_bars 替换为固定数据。
    def fake_fetch_bars(self, symbol, timeframe, start, end):
        from datetime import timedelta, timezone, datetime as dt
        from arbiter.protocols.market import MarketBar

        base = dt(2025, 1, 1, tzinfo=timezone.utc)
        return [
            MarketBar(
                symbol=symbol,
                timestamp=base,
                timeframe=timeframe,
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000.0,
                source="yahoo-test",
            )
        ]

    monkeypatch.setattr(
        "arbiter.data.providers.yahoo_market_provider.YahooMarketProvider.fetch_bars",
        fake_fetch_bars,
    )
    symbol = "NVDA"
    timeframe = "1d"

    bootstrap_market_data(symbol, timeframe)
    refresh_market_data(symbol, timeframe)

