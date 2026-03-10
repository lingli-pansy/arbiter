from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
)

from arbiter.data.repositories.db import Base, get_engine


class CanonicalInstrument(Base):
    """
    Canonical instrument definition for the market store.

    This is intentionally minimal and focuses on identifiers that are stable
    across historical import, realtime ingest, and NT datasets.
    """

    __tablename__ = "canonical_instruments"

    # Logical instrument identifier; can be mapped to NT instrument_id when needed.
    instrument_id = Column(String, primary_key=True)

    # Human-readable symbol and venue (e.g. NASDAQ, NYSE, SMART).
    symbol = Column(String, nullable=False, index=True)
    venue = Column(String, nullable=False, index=True)

    # Currency the instrument trades in (e.g. USD).
    currency = Column(String, nullable=False)

    # Free-form provider-specific identifiers (optional)
    provider_symbol = Column(String, nullable=True)
    ib_contract_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class CanonicalBar(Base):
    """
    Canonical OHLCV bar stored in the market store.

    This schema follows the phase guide and is shared by both historical
    imports and realtime ingest.
    """

    __tablename__ = "canonical_bars"
    __table_args__ = (
        UniqueConstraint(
            "instrument_id",
            "timeframe",
            "timestamp",
            "source",
            "version",
            name="uq_canonical_bars_inst_tf_ts_source_ver",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Instrument linkage and basic identity
    instrument_id = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    venue = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # OHLCV
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Currency and provenance
    currency = Column(String, nullable=False)
    source = Column(String, nullable=False)  # e.g. yahoo, ibkr, nt-replay
    ingest_method = Column(String, nullable=False)  # import | ingest | repair
    ingested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Status + conflict resolution fields
    status = Column(String, nullable=False, default="provisional")  # provisional | finalized
    version = Column(Integer, nullable=False, default=1)
    priority = Column(Integer, nullable=False, default=0)
    quality_flag = Column(String, nullable=True)  # e.g. partial, adjusted, corporate_action

    # Optional segment / batch linkage
    segment_id = Column(Integer, nullable=True, index=True)


class IngestSegment(Base):
    """
    Represents a logical ingest/import/repair segment.

    Segments provide a coarse-grained ledger for:
    - historical range imports
    - realtime ingest sessions
    - repair jobs
    """

    __tablename__ = "ingest_segments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # segment type: import | ingest | repair | finalize
    operation = Column(String, nullable=False)

    # append | upsert | replace_range | repair_range
    mode = Column(String, nullable=False)

    # symbol/timeframe range this segment is responsible for
    symbol = Column(String, nullable=False, index=True)
    venue = Column(String, nullable=True, index=True)
    timeframe = Column(String, nullable=False, index=True)
    start_timestamp = Column(DateTime(timezone=True), nullable=True)
    end_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Data source and write provenance
    source = Column(String, nullable=False)  # e.g. yahoo, ibkr
    ingest_method = Column(String, nullable=False)  # import | ingest | repair

    # Segment lifecycle
    status = Column(String, nullable=False, default="pending")  # pending | running | succeeded | failed
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)


def init_canonical_schema() -> None:
    """
    Ensure canonical market store tables exist in the current database.

    This is a convenience for development and local validation. In a
    production setting, Alembic migrations should be preferred.
    """

    engine = get_engine()
    CanonicalInstrument.metadata.create_all(bind=engine, tables=[CanonicalInstrument.__table__])
    CanonicalBar.metadata.create_all(bind=engine, tables=[CanonicalBar.__table__])
    IngestSegment.metadata.create_all(bind=engine, tables=[IngestSegment.__table__])

