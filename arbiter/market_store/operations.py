from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import and_, delete
from sqlalchemy.orm import Session

from arbiter.market_store.schema import CanonicalBar, IngestSegment

Status = Literal["provisional", "finalized"]
Operation = Literal["import", "ingest", "repair", "finalize"]
Mode = Literal["append", "upsert", "replace_range", "repair_range"]


@dataclass(slots=True)
class BarPayload:
    instrument_id: str
    symbol: str
    venue: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    currency: str
    source: str
    status: Status = "provisional"
    version: int = 1
    priority: int = 0
    quality_flag: str | None = None


def _should_replace(existing: CanonicalBar, new: CanonicalBar) -> bool:
    """
    Decide whether *new* should replace *existing* according to guide rules.

    Rules (descending precedence):
    - finalized > provisional
    - repair > ordinary ingest/import
    - higher priority source > lower priority source
    - newer version > older version
    """

    status_rank = {"provisional": 0, "finalized": 1}
    op_rank = {"import": 0, "ingest": 1, "repair": 2}

    existing_status = status_rank.get(existing.status, 0)
    new_status = status_rank.get(new.status, 0)
    if new_status != existing_status:
        return new_status > existing_status

    existing_op = op_rank.get(existing.ingest_method, 0)
    new_op = op_rank.get(new.ingest_method, 0)
    if new_op != existing_op:
        return new_op > existing_op

    if new.priority != existing.priority:
        return new.priority > existing.priority

    if new.version != existing.version:
        return new.version > existing.version

    # If everything is equal, treat new as no-op.
    return False


def _create_segment(
    session: Session,
    *,
    operation: Operation,
    mode: Mode,
    symbol: str,
    venue: str | None,
    timeframe: str,
    start_timestamp: datetime | None,
    end_timestamp: datetime | None,
    source: str,
    ingest_method: str,
) -> IngestSegment:
    segment = IngestSegment(
        operation=operation,
        mode=mode,
        symbol=symbol,
        venue=venue,
        timeframe=timeframe,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        source=source,
        ingest_method=ingest_method,
        status="running",
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
    )
    session.add(segment)
    session.flush()
    return segment


def _finalize_segment(
    session: Session,
    segment: IngestSegment,
    *,
    status: str,
    error_message: str | None = None,
) -> None:
    segment.status = status
    segment.finished_at = datetime.utcnow()
    segment.error_message = error_message
    session.add(segment)


def write_bars(
    session: Session,
    *,
    bars: Iterable[BarPayload],
    operation: Operation,
    mode: Mode,
    source: str,
    ingest_method: str,
) -> int:
    """
    Core write primitive used by import/ingest/repair flows.

    It creates an ingest segment per (symbol, timeframe) batch and applies
    conflict resolution when bars already exist in the time range.
    """

    count_inserted = 0
    grouped: dict[tuple[str, str], list[BarPayload]] = {}

    for bar in bars:
        key = (bar.symbol, bar.timeframe)
        grouped.setdefault(key, []).append(bar)

    for (symbol, timeframe), payloads in grouped.items():
        if not payloads:
            continue

        start_ts = min(p.timestamp for p in payloads)
        end_ts = max(p.timestamp for p in payloads)

        segment = _create_segment(
            session,
            operation=operation,
            mode=mode,
            symbol=symbol,
            venue=None,
            timeframe=timeframe,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            source=source,
            ingest_method=ingest_method,
        )

        try:
            if mode in ("replace_range", "repair_range"):
                stmt = delete(CanonicalBar).where(
                    and_(
                        CanonicalBar.symbol == symbol,
                        CanonicalBar.timeframe == timeframe,
                        CanonicalBar.timestamp >= start_ts,
                        CanonicalBar.timestamp <= end_ts,
                    )
                )
                session.execute(stmt)

            for p in payloads:
                existing = (
                    session.query(CanonicalBar)
                    .filter(
                        CanonicalBar.instrument_id == p.instrument_id,
                        CanonicalBar.timeframe == p.timeframe,
                        CanonicalBar.timestamp == p.timestamp,
                    )
                    .order_by(CanonicalBar.version.desc())
                    .first()
                )

                new_row = CanonicalBar(
                    instrument_id=p.instrument_id,
                    symbol=p.symbol,
                    venue=p.venue,
                    timeframe=p.timeframe,
                    timestamp=p.timestamp,
                    open=p.open,
                    high=p.high,
                    low=p.low,
                    close=p.close,
                    volume=p.volume,
                    currency=p.currency,
                    source=p.source,
                    ingest_method=ingest_method,
                    status=p.status,
                    version=p.version if existing is None else max(existing.version + 1, p.version),
                    priority=p.priority,
                    quality_flag=p.quality_flag,
                    segment_id=segment.id,
                )

                if existing is None:
                    session.add(new_row)
                    count_inserted += 1
                    continue

                if mode == "append":
                    # Do not touch existing data in append mode.
                    continue

                if _should_replace(existing, new_row):
                    session.add(new_row)
                    count_inserted += 1

            _finalize_segment(session, segment, status="succeeded")
        except Exception as exc:  # noqa: BLE001
            _finalize_segment(session, segment, status="failed", error_message=str(exc))
            raise

    return count_inserted


def import_market_data(
    session: Session,
    *,
    bars: Iterable[BarPayload],
    mode: Mode = "append",
    source: str = "historical-import",
) -> int:
    """
    Historical bulk import entrypoint.

    Supports:
    - append
    - upsert
    - replace_range
    - repair_range
    """

    return write_bars(
        session,
        bars=bars,
        operation="import",
        mode=mode,
        source=source,
        ingest_method="import",
    )


def ingest_market_data(
    session: Session,
    *,
    bars: Iterable[BarPayload],
    source: str = "realtime-ingest",
    mode: Mode = "upsert",
) -> int:
    """
    Realtime ingest entrypoint (typically used by IBKR / NT adapter).
    """

    return write_bars(
        session,
        bars=bars,
        operation="ingest",
        mode=mode,
        source=source,
        ingest_method="ingest",
    )


def repair_market_data(
    session: Session,
    *,
    bars: Iterable[BarPayload],
    source: str = "repair",
    mode: Mode = "repair_range",
) -> int:
    """
    Repair entrypoint that uses higher precedence semantics.
    """

    return write_bars(
        session,
        bars=bars,
        operation="repair",
        mode=mode,
        source=source,
        ingest_method="repair",
    )


def get_ingest_job_status(session: Session, segment_id: int) -> dict | None:
    """
    Minimal helper to query ingest segment status for MCP / diagnostics.
    """

    segment = session.get(IngestSegment, segment_id)
    if segment is None:
        return None
    return {
        "id": segment.id,
        "operation": segment.operation,
        "mode": segment.mode,
        "symbol": segment.symbol,
        "venue": segment.venue,
        "timeframe": segment.timeframe,
        "status": segment.status,
        "created_at": segment.created_at.isoformat() if segment.created_at else None,
        "started_at": segment.started_at.isoformat() if segment.started_at else None,
        "finished_at": segment.finished_at.isoformat() if segment.finished_at else None,
        "error_message": segment.error_message,
    }

