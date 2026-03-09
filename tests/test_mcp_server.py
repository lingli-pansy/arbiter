from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from arbiter.mcp import server
from arbiter.protocols.market import MarketBar
from arbiter.protocols.news import NewsEvent


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set; MCP server tests skipped",
)


def test_get_market_bars_tool_uses_service(monkeypatch) -> None:
    called = {}

    def fake_get_market_bars(symbol, timeframe, start, end):
        called["args"] = (symbol, timeframe, start, end)
        return [
            MarketBar(
                symbol=symbol,
                timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
                timeframe=timeframe,
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000.0,
                source="test",
            )
        ]

    monkeypatch.setattr(
        "arbiter.data.services.market_data_service.get_market_bars",
        fake_get_market_bars,
    )

    result = server.get_market_bars(
        symbol="TEST",
        timeframe="1d",
        start="2025-01-01T00:00:00+00:00",
        end="2025-01-02T00:00:00+00:00",
    )

    assert called["args"][0] == "TEST"
    assert isinstance(result, list)
    assert result[0]["symbol"] == "TEST"
    assert result[0]["timeframe"] == "1d"


def test_get_news_tool_uses_service(monkeypatch) -> None:
    def fake_get_news(symbol, limit):
        return [
            NewsEvent(
                event_id="evt-1",
                timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
                symbols=[symbol],
                headline="Test",
                summary="Summary",
                source="test",
                url=None,
            )
        ]

    monkeypatch.setattr(
        "arbiter.data.services.news_service.get_news",
        fake_get_news,
    )

    result = server.get_news(symbol="TEST", limit=1)
    assert isinstance(result, list)
    assert result[0]["headline"] == "Test"


def test_refresh_tools_call_services(monkeypatch) -> None:
    called_market = {}
    called_news = {}

    def fake_refresh_market(symbol, timeframe):
        called_market["args"] = (symbol, timeframe)
        return {"symbol": symbol, "timeframe": timeframe, "inserted": 1}

    def fake_refresh_news(symbol):
        called_news["args"] = (symbol,)
        return {"symbol": symbol, "inserted": 1}

    monkeypatch.setattr(
        "arbiter.data.services.market_data_service.refresh_market_data_and_get_state",
        fake_refresh_market,
    )
    monkeypatch.setattr(
        "arbiter.data.services.news_service.refresh_news_and_get_state",
        fake_refresh_news,
    )

    r1 = server.refresh_market_data(symbol="TEST", timeframe="1d")
    r2 = server.refresh_news(symbol="TEST")

    assert called_market["args"] == ("TEST", "1d")
    assert called_news["args"] == ("TEST",)
    assert r1["inserted"] == 1
    assert r2["inserted"] == 1


def test_batch_refresh_tools(monkeypatch) -> None:
    called_market: list[tuple[str, str]] = []
    called_news: list[str] = []

    def fake_refresh_market(symbol, timeframe):
        called_market.append((symbol, timeframe))
        return {"symbol": symbol, "timeframe": timeframe, "inserted": 1}

    def fake_refresh_news(symbol):
        called_news.append(symbol)
        return {"symbol": symbol, "inserted": 1}

    monkeypatch.setattr(
        "arbiter.data.services.market_data_service.refresh_market_data_and_get_state",
        fake_refresh_market,
    )
    monkeypatch.setattr(
        "arbiter.data.services.news_service.refresh_news_and_get_state",
        fake_refresh_news,
    )

    symbols = ["AAA", "BBB"]
    mr = server.refresh_market_batch(symbols=symbols, timeframe="1d")
    nr = server.refresh_news_batch(symbols=symbols)

    assert called_market == [("AAA", "1d"), ("BBB", "1d")]
    assert called_news == symbols
    assert len(mr) == 2
    assert len(nr) == 2


def test_get_universe_data_summary_uses_service(monkeypatch) -> None:
    def fake_get_universe_data_summary(symbols, timeframe):
        return [
            {
                "symbol": s,
                "timeframe": timeframe,
                "latest_bar_timestamp": "2025-01-01T00:00:00+00:00",
                "latest_news_timestamp": "2025-01-02T00:00:00+00:00",
                "market_refresh_status": "success",
                "news_refresh_status": "success",
            }
            for s in symbols
        ]

    monkeypatch.setattr(
        "arbiter.data.services.universe_service.get_universe_data_summary",
        fake_get_universe_data_summary,
    )

    res = server.get_universe_data_summary(symbols=["AAA", "BBB"], timeframe="1d")
    assert len(res) == 2
    assert {r["symbol"] for r in res} == {"AAA", "BBB"}

