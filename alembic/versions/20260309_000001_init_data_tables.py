from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260309_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("symbol", sa.String(), primary_key=True),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("exchange", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("tick_size", sa.Float(), nullable=False),
        sa.Column("lot_size", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "market_bars",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("timeframe", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("symbol", "timeframe", "timestamp", "source", name="uq_market_bars_symbol_tf_ts_source"),
    )
    op.create_index("ix_market_bars_symbol", "market_bars", ["symbol"])
    op.create_index("ix_market_bars_timeframe", "market_bars", ["timeframe"])
    op.create_index("ix_market_bars_timestamp", "market_bars", ["timestamp"])
    op.create_index("ix_market_bars_ingested_at", "market_bars", ["ingested_at"])

    op.create_table(
        "news_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("headline", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("event_id", "source", name="uq_news_events_event_source"),
    )
    op.create_index("ix_news_events_symbol", "news_events", ["symbol"])
    op.create_index("ix_news_events_timestamp", "news_events", ["timestamp"])
    op.create_index("ix_news_events_ingested_at", "news_events", ["ingested_at"])

    op.create_table(
        "refresh_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dataset_type", sa.String(), nullable=False),
        sa.Column("dataset_key", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_event_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refresh_status", sa.String(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.UniqueConstraint("dataset_type", "dataset_key", "source", name="uq_refresh_state_dataset_source"),
    )


def downgrade() -> None:
    op.drop_table("refresh_state")
    op.drop_index("ix_news_events_ingested_at", table_name="news_events")
    op.drop_index("ix_news_events_timestamp", table_name="news_events")
    op.drop_index("ix_news_events_symbol", table_name="news_events")
    op.drop_table("news_events")
    op.drop_index("ix_market_bars_ingested_at", table_name="market_bars")
    op.drop_index("ix_market_bars_timestamp", table_name="market_bars")
    op.drop_index("ix_market_bars_timeframe", table_name="market_bars")
    op.drop_index("ix_market_bars_symbol", table_name="market_bars")
    op.drop_table("market_bars")
    op.drop_table("instruments")

