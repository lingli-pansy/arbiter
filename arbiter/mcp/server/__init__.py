from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastmcp import FastMCP

from arbiter.config.universe import MARKET_SYMBOLS
from arbiter.data.schemas.market import MarketBarModel
from arbiter.data.services import (
    news_service,
    refresh_state_service,
)
from arbiter.data.repositories.db import get_session
from arbiter.market_store import operations as store_ops
from arbiter.market_store import queries as store_queries


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
    """Query historical canonical market bars from Arbiter's store."""
    start_dt = _parse_iso8601(start)
    end_dt = _parse_iso8601(end)
    with get_session() as session:
        bars = store_queries.get_market_bars(
            session,
            symbol=symbol,
            timeframe=timeframe,
            start=start_dt,
            end=end_dt,
        )
        return [
            MarketBarModel(
                symbol=b.symbol,
                timestamp=b.timestamp,
                timeframe=b.timeframe,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
                source=b.source,
            ).model_dump()
            for b in bars
        ]


@mcp.tool
def get_latest_bars(
    symbol: str,
    timeframe: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Query latest N canonical market bars for a symbol/timeframe."""
    with get_session() as session:
        bars = store_queries.get_latest_bars(
            session,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        return [
            MarketBarModel(
                symbol=b.symbol,
                timestamp=b.timestamp,
                timeframe=b.timeframe,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
                source=b.source,
            ).model_dump()
            for b in bars
        ]


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

    with get_session() as session:
        return store_queries.get_universe_data_summary(session, symbols=symbols, timeframe=timeframe)


@mcp.tool
def get_data_coverage(
    symbols: list[str] | None = None,
    timeframe: str = "1d",
) -> list[Dict[str, Any]]:
    """Return coverage information (start, end, count) for the given universe."""
    if symbols is None:
        symbols = MARKET_SYMBOLS
    with get_session() as session:
        return store_queries.get_data_coverage(session, symbols=symbols, timeframe=timeframe)


@mcp.tool
def get_ingest_job_status(
    symbol: str | None = None,
    timeframe: str | None = None,
    limit: int = 20,
) -> list[Dict[str, Any]]:
    """Return recent ingest job (segment) status."""
    with get_session() as session:
        return store_queries.get_ingest_job_status(
            session,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )


@mcp.tool
def ingest_market_data(
    bars: list[Dict[str, Any]],
    source: str = "realtime-ingest",
) -> Dict[str, Any]:
    """
    Control API: write canonical bars using ingest semantics.

    This is primarily intended for orchestrated ingestion (e.g. NT bridge or
    batch jobs), not for ad-hoc user calls.
    """

    payloads: list[store_ops.BarPayload] = []
    for b in bars:
        payloads.append(
            store_ops.BarPayload(
                instrument_id=b["instrument_id"],
                symbol=b["symbol"],
                venue=b["venue"],
                timeframe=b["timeframe"],
                timestamp=_parse_iso8601(b["timestamp"]),
                open=b["open"],
                high=b["high"],
                low=b["low"],
                close=b["close"],
                volume=b["volume"],
                currency=b.get("currency", "USD"),
                source=source,
                status=b.get("status", "provisional"),
                version=int(b.get("version", 1)),
                priority=int(b.get("priority", 0)),
                quality_flag=b.get("quality_flag"),
            )
        )

    with get_session() as session:
        inserted = store_ops.ingest_market_data(session, bars=payloads, source=source)  # type: ignore[arg-type]
    return {"inserted": inserted}


@mcp.tool
def repair_market_data(
    bars: list[Dict[str, Any]],
    source: str = "repair",
) -> Dict[str, Any]:
    """Control API: write canonical bars using repair semantics."""

    payloads: list[store_ops.BarPayload] = []
    for b in bars:
        payloads.append(
            store_ops.BarPayload(
                instrument_id=b["instrument_id"],
                symbol=b["symbol"],
                venue=b["venue"],
                timeframe=b["timeframe"],
                timestamp=_parse_iso8601(b["timestamp"]),
                open=b["open"],
                high=b["high"],
                low=b["low"],
                close=b["close"],
                volume=b["volume"],
                currency=b.get("currency", "USD"),
                source=source,
                status=b.get("status", "provisional"),
                version=int(b.get("version", 1)),
                priority=int(b.get("priority", 0)),
                quality_flag=b.get("quality_flag"),
            )
        )

    with get_session() as session:
        inserted = store_ops.repair_market_data(session, bars=payloads, source=source)  # type: ignore[arg-type]
    return {"inserted": inserted}


@mcp.tool
def finalize_market_data(
    symbol: str,
    timeframe: str,
    start: str,
    end: str,
) -> Dict[str, Any]:
    """
    Minimal finalize implementation: mark matching bars as finalized.

    This follows the guide's semantic that finalized data should win in
    conflict resolution.
    """

    start_dt = _parse_iso8601(start)
    end_dt = _parse_iso8601(end)
    with get_session() as session:
        bars = store_queries.get_market_bars(
            session,
            symbol=symbol,
            timeframe=timeframe,
            start=start_dt,
            end=end_dt,
        )
        for b in bars:
            b.status = "finalized"
            session.add(b)
        updated = len(bars)
    return {"finalized": updated}


def main() -> None:
    """CLI entrypoint: run the Arbiter MCP server."""
    mcp.run()
