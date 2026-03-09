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

from .db import Base


class Instrument(Base):
    __tablename__ = "instruments"

    symbol = Column(String, primary_key=True)
    asset_type = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    tick_size = Column(Float, nullable=False)
    lot_size = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class MarketBarORM(Base):
    __tablename__ = "market_bars"
    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", "source", name="uq_market_bars_symbol_tf_ts_source"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    ingested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)


class NewsEventORM(Base):
    __tablename__ = "news_events"
    __table_args__ = (
        UniqueConstraint("event_id", "source", name="uq_news_events_event_source"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    headline = Column(String, nullable=False)
    summary = Column(String, nullable=True)
    source = Column(String, nullable=False)
    url = Column(String, nullable=True)
    ingested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)


class RefreshStateORM(Base):
    __tablename__ = "refresh_state"
    __table_args__ = (
        UniqueConstraint("dataset_type", "dataset_key", "source", name="uq_refresh_state_dataset_source"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_type = Column(String, nullable=False)
    dataset_key = Column(String, nullable=False)
    source = Column(String, nullable=False)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_event_timestamp = Column(DateTime(timezone=True), nullable=True)
    refresh_status = Column(String, nullable=False, default="idle")
    error_message = Column(String, nullable=True)

