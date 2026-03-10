from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from arbiter.market_store.schema import CanonicalBar, IngestSegment


def get_latest_bars(
    session: Session,
    *,
    symbol: str,
    timeframe: str,
    limit: int = 20,
) -> list[CanonicalBar]:
    return (
        session.query(CanonicalBar)
        .filter(
            CanonicalBar.symbol == symbol,
            CanonicalBar.timeframe == timeframe,
        )
        .order_by(CanonicalBar.timestamp.desc(), CanonicalBar.version.desc())
        .limit(limit)
        .all()
    )


def get_market_bars(
    session: Session,
    *,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
) -> list[CanonicalBar]:
    return (
        session.query(CanonicalBar)
        .filter(
            CanonicalBar.symbol == symbol,
            CanonicalBar.timeframe == timeframe,
            CanonicalBar.timestamp >= start,
            CanonicalBar.timestamp <= end,
        )
        .order_by(CanonicalBar.timestamp.asc(), CanonicalBar.version.desc())
        .all()
    )


def get_data_coverage(
    session: Session,
    *,
    symbols: Iterable[str],
    timeframe: str,
) -> list[dict]:
    """
    Return min/max timestamp and count for each symbol/timeframe pair.
    """

    rows = (
        session.query(
            CanonicalBar.symbol,
            CanonicalBar.timeframe,
            func.min(CanonicalBar.timestamp),
            func.max(CanonicalBar.timestamp),
            func.count(CanonicalBar.id),
        )
        .filter(
            CanonicalBar.symbol.in_(list(symbols)),
            CanonicalBar.timeframe == timeframe,
        )
        .group_by(CanonicalBar.symbol, CanonicalBar.timeframe)
        .all()
    )

    result: list[dict] = []
    for symbol, tf, min_ts, max_ts, count in rows:
        result.append(
            {
                "symbol": symbol,
                "timeframe": tf,
                "start": min_ts.isoformat() if min_ts else None,
                "end": max_ts.isoformat() if max_ts else None,
                "count": int(count),
            }
        )
    return result


def get_refresh_state(
    session: Session,
    *,
    symbols: Iterable[str],
    timeframe: str,
) -> list[dict]:
    """
    Lightweight refresh view derived from canonical bars themselves.

    For each symbol/timeframe, returns the latest bar timestamp and a simple
    status based on recency.
    """

    rows = (
        session.query(
            CanonicalBar.symbol,
            CanonicalBar.timeframe,
            func.max(CanonicalBar.timestamp),
        )
        .filter(
            CanonicalBar.symbol.in_(list(symbols)),
            CanonicalBar.timeframe == timeframe,
        )
        .group_by(CanonicalBar.symbol, CanonicalBar.timeframe)
        .all()
    )

    result: list[dict] = []
    for symbol, tf, max_ts in rows:
        result.append(
            {
                "symbol": symbol,
                "timeframe": tf,
                "latest_bar_timestamp": max_ts.isoformat() if max_ts else None,
            }
        )
    return result


def get_universe_data_summary(
    session: Session,
    *,
    symbols: Iterable[str],
    timeframe: str,
) -> list[dict]:
    """
    Combine coverage and refresh views into a single per-symbol summary.
    """

    coverage = {f"{row['symbol']}:{row['timeframe']}": row for row in get_data_coverage(session, symbols=symbols, timeframe=timeframe)}
    refresh = {f"{row['symbol']}:{row['timeframe']}": row for row in get_refresh_state(session, symbols=symbols, timeframe=timeframe)}

    summary: list[dict] = []
    for symbol in symbols:
        key = f"{symbol}:{timeframe}"
        cov = coverage.get(key)
        ref = refresh.get(key)
        summary.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "coverage_start": cov["start"] if cov else None,
                "coverage_end": cov["end"] if cov else None,
                "bar_count": cov["count"] if cov else 0,
                "latest_bar_timestamp": ref["latest_bar_timestamp"] if ref else None,
            }
        )
    return summary


def get_ingest_job_status(
    session: Session,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """
    Return recent ingest segments, optionally filtered by symbol/timeframe.
    """

    query = session.query(IngestSegment).order_by(IngestSegment.id.desc())
    if symbol is not None:
        query = query.filter(IngestSegment.symbol == symbol)
    if timeframe is not None:
        query = query.filter(IngestSegment.timeframe == timeframe)

    segments = query.limit(limit).all()

    result: list[dict] = []
    for seg in segments:
        result.append(
            {
                "id": seg.id,
                "operation": seg.operation,
                "mode": seg.mode,
                "symbol": seg.symbol,
                "venue": seg.venue,
                "timeframe": seg.timeframe,
                "status": seg.status,
                "created_at": seg.created_at.isoformat() if seg.created_at else None,
                "started_at": seg.started_at.isoformat() if seg.started_at else None,
                "finished_at": seg.finished_at.isoformat() if seg.finished_at else None,
                "error_message": seg.error_message,
            }
        )
    return result

