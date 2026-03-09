from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from arbiter.protocols.news import NewsEvent

from .models import NewsEventORM


class NewsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append_events(self, events: Iterable[NewsEvent]) -> int:
        event_list = list(events)
        if not event_list:
            return 0

        rows = []
        for e in event_list:
            symbol = e.symbols[0] if e.symbols else ""
            rows.append(
                {
                    "event_id": e.event_id,
                    "symbol": symbol,
                    "timestamp": e.timestamp,
                    "headline": e.headline,
                    "summary": e.summary,
                    "source": e.source,
                    "url": e.url,
                }
            )

        stmt = insert(NewsEventORM).values(rows).on_conflict_do_nothing(
            constraint="uq_news_events_event_source",
        )
        result = self.session.execute(stmt)
        return int(result.rowcount or 0)

    def get_events(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> List[NewsEvent]:
        stmt = (
            select(NewsEventORM)
            .where(
                NewsEventORM.symbol == symbol,
                NewsEventORM.timestamp >= start,
                NewsEventORM.timestamp <= end,
            )
            .order_by(NewsEventORM.timestamp.asc())
        )
        rows = self.session.execute(stmt).scalars().all()
        return [
            NewsEvent(
                event_id=row.event_id,
                timestamp=row.timestamp,
                symbols=[row.symbol],
                headline=row.headline,
                summary=row.summary or "",
                source=row.source,
                url=row.url,
            )
            for row in rows
        ]

