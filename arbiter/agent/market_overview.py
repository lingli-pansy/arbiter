from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence

from arbiter.config.universe import MARKET_SYMBOLS
from arbiter.mcp import server as mcp_server


def run_market_overview(
    symbols: Sequence[str] | None = None,
    timeframe: str = "1d",
    universe_limit: int = 10,
    news_per_symbol: int = 3,
) -> Dict[str, Any]:
    """High-level market + news overview for a small universe of symbols.

    This function is intended as the task entrypoint for the
    `market_overview` / `news_overview` / `refresh_and_scan` tasks in the
    arbiter-data-assistant OpenClaw agent.
    """
    if symbols is None:
        symbols = MARKET_SYMBOLS[:universe_limit]
    else:
        symbols = list(symbols)

    # 1) Universe-level data summary（基于 refresh_state）
    universe_summary = mcp_server.get_universe_data_summary(
        symbols=list(symbols),
        timeframe=timeframe,
        limit=None,
    )

    # 2) News snapshot（每个标的取若干条最新新闻标题）
    news_summary: Dict[str, List[str]] = {}
    for symbol in symbols:
        try:
            items = mcp_server.get_news(symbol=symbol, limit=news_per_symbol)
        except Exception:
            items = []
        headlines = [item.get("headline", "") for item in items]
        news_summary[symbol] = headlines

    return {
        "symbols": list(symbols),
        "timeframe": timeframe,
        "universe_summary": universe_summary,
        "news_summary": news_summary,
    }


def main() -> None:
    """CLI entrypoint for a minimal market overview demo."""
    result = run_market_overview()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

