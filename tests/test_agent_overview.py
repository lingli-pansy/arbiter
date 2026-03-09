from __future__ import annotations

from typing import Any, Dict, List

from arbiter.agent.market_overview import run_market_overview
from arbiter.mcp import server


def test_run_market_overview_uses_mcp_tools(monkeypatch) -> None:
    calls: Dict[str, Any] = {"universe": None, "news": []}

    def fake_get_universe_data_summary(symbols, timeframe, limit=None):
        calls["universe"] = (tuple(symbols), timeframe, limit)
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

    def fake_get_news(symbol, limit):
        calls["news"].append((symbol, limit))
        return [
            {
                "headline": f"News for {symbol}",
            }
        ]

    monkeypatch.setattr(server, "get_universe_data_summary", fake_get_universe_data_summary)
    monkeypatch.setattr(server, "get_news", fake_get_news)

    symbols = ["AAA", "BBB"]
    result = run_market_overview(symbols=symbols, timeframe="1d", universe_limit=10, news_per_symbol=2)

    assert result["symbols"] == symbols
    assert len(result["universe_summary"]) == 2
    assert {s["symbol"] for s in result["universe_summary"]} == set(symbols)
    # universe 调用应使用传入 symbols 与 timeframe，limit=None
    assert calls["universe"] == (tuple(symbols), "1d", None)
    # 每个 symbol 调用一次 get_news，并带上 news_per_symbol
    assert calls["news"] == [("AAA", 2), ("BBB", 2)]
    # news_summary 中应包含对应 headlines
    assert result["news_summary"]["AAA"] == ["News for AAA"]
    assert result["news_summary"]["BBB"] == ["News for BBB"]

