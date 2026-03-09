from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastmcp import FastMCP

from arbiter.config.universe import MARKET_SYMBOLS
from arbiter.data.schemas.market import MarketBarModel
from arbiter.data.services import (
    market_data_service,
    news_service,
    refresh_state_service,
    universe_service,
)


mcp = FastMCP("Arbiter Data MCP")


def _parse_iso8601(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@mcp.tool
def get_market_bars(
    symbol: str,
    timeframe: str,
    start: str,
    end: str,
) -> List[Dict[str, Any]]:
    """Query historical market bars from Arbiter's database."""
    start_dt = _parse_iso8601(start)
    end_dt = _parse_iso8601(end)
    bars = market_data_service.get_market_bars(symbol, timeframe, start_dt, end_dt)
    return [MarketBarModel.model_validate(b).model_dump() for b in bars]


@mcp.tool
def get_latest_bars(
    symbol: str,
    timeframe: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Query latest N market bars for a symbol/timeframe."""
    bars = market_data_service.get_latest_bars(symbol, timeframe, limit)
    return [MarketBarModel.model_validate(b).model_dump() for b in bars]


@mcp.tool
def get_news(
    symbol: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Query latest news events for a symbol."""
    events = news_service.get_news(symbol, limit)
    return [
        {
            "event_id": e.event_id,
            "timestamp": e.timestamp.isoformat(),
            "symbols": e.symbols,
            "headline": e.headline,
            "summary": e.summary,
            "source": e.source,
            "url": e.url,
        }
        for e in events
    ]


@mcp.tool
def get_refresh_state(
    dataset_type: str,
    dataset_key: str,
) -> List[Dict[str, Any]]:
    """Query refresh_state records for a dataset."""
    rows = refresh_state_service.get_refresh_state(dataset_type, dataset_key)
    return [
        {
            "dataset_type": r.dataset_type,
            "dataset_key": r.dataset_key,
            "source": r.source,
            "last_success_at": r.last_success_at.isoformat() if r.last_success_at else None,
            "last_event_timestamp": r.last_event_timestamp.isoformat() if r.last_event_timestamp else None,
            "refresh_status": r.refresh_status,
            "error_message": r.error_message,
        }
        for r in rows
    ]


@mcp.tool
def refresh_market_data(
    symbol: str,
    timeframe: str,
) -> Dict[str, Any]:
    """Manually trigger market data refresh and return summary."""
    result = market_data_service.refresh_market_data_and_get_state(symbol, timeframe)
    return result


@mcp.tool
def refresh_news(
    symbol: str,
) -> Dict[str, Any]:
    """Manually trigger news refresh and return summary."""
    result = news_service.refresh_news_and_get_state(symbol)
    return result


@mcp.tool
def refresh_market_batch(
    symbols: list[str],
    timeframe: str,
) -> list[Dict[str, Any]]:
    """Sequentially refresh market data for a batch of symbols."""
    results: list[Dict[str, Any]] = []
    for symbol in symbols:
        results.append(market_data_service.refresh_market_data_and_get_state(symbol, timeframe))
    return results


@mcp.tool
def refresh_news_batch(
    symbols: list[str],
) -> list[Dict[str, Any]]:
    """Sequentially refresh news for a batch of symbols."""
    results: list[Dict[str, Any]] = []
    for symbol in symbols:
        results.append(news_service.refresh_news_and_get_state(symbol))
    return results


@mcp.tool
def get_universe_data_summary(
    symbols: list[str] | None = None,
    timeframe: str = "1d",
    limit: int | None = None,
) -> list[Dict[str, Any]]:
    """Get a lightweight data summary for a set of symbols.

    If `symbols` is omitted, uses the default MARKET_SYMBOLS universe
    (optionally truncated by `limit`).
    """
    if symbols is None:
        symbols = MARKET_SYMBOLS if limit is None else MARKET_SYMBOLS[:limit]

    return universe_service.get_universe_data_summary(symbols, timeframe)


def main() -> None:
    """CLI entrypoint: run the Arbiter MCP server."""
    mcp.run()
