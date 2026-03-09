from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from arbiter.protocols.market import MarketBar

from .models import MarketBarORM


class MarketRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append_bars(self, bars: Iterable[MarketBar]) -> int:
        """追加写入 MarketBar，按唯一键去重。"""
        bar_list = list(bars)
        if not bar_list:
            return 0

        stmt = insert(MarketBarORM).values(
            [
                {
                    "symbol": b.symbol,
                    "timeframe": b.timeframe,
                    "timestamp": b.timestamp,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                    "source": b.source,
                }
                for b in bar_list
            ]
        ).on_conflict_do_nothing(
            constraint="uq_market_bars_symbol_tf_ts_source",
        )
        result = self.session.execute(stmt)
        # result.rowcount is not reliable for ON CONFLICT DO NOTHING across drivers,
        # but in PostgreSQL it should reflect inserted rows.
        return int(result.rowcount or 0)

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> List[MarketBar]:
        stmt = (
            select(MarketBarORM)
            .where(
                MarketBarORM.symbol == symbol,
                MarketBarORM.timeframe == timeframe,
                MarketBarORM.timestamp >= start,
                MarketBarORM.timestamp <= end,
            )
            .order_by(MarketBarORM.timestamp.asc())
        )
        rows = self.session.execute(stmt).scalars().all()
        return [
            MarketBar(
                symbol=row.symbol,
                timestamp=row.timestamp,
                timeframe=row.timeframe,
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
                volume=row.volume,
                source=row.source,
            )
            for row in rows
        ]

    def get_latest_bars(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> List[MarketBar]:
        """按 timestamp 降序 LIMIT N 查询最新的 K 线."""
        stmt: Select[MarketBarORM] = (
            select(MarketBarORM)
            .where(
                MarketBarORM.symbol == symbol,
                MarketBarORM.timeframe == timeframe,
            )
            .order_by(MarketBarORM.timestamp.desc())
            .limit(limit)
        )
        rows = self.session.execute(stmt).scalars().all()
        bars: List[MarketBar] = [
            MarketBar(
                symbol=row.symbol,
                timestamp=row.timestamp,
                timeframe=row.timeframe,
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
                volume=row.volume,
                source=row.source,
            )
            for row in rows
        ]
        # 统一按时间升序返回
        bars.sort(key=lambda b: b.timestamp)
        return bars

