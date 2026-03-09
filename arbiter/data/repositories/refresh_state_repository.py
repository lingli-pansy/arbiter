from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .models import RefreshStateORM


class RefreshStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_state(
        self,
        dataset_type: str,
        dataset_key: str,
        source: str,
    ) -> Optional[RefreshStateORM]:
        stmt = select(RefreshStateORM).where(
            RefreshStateORM.dataset_type == dataset_type,
            RefreshStateORM.dataset_key == dataset_key,
            RefreshStateORM.source == source,
        )
        return self.session.execute(stmt).scalars().first()

    def upsert_state(
        self,
        dataset_type: str,
        dataset_key: str,
        source: str,
        last_success_at: datetime | None,
        last_event_timestamp: datetime | None,
        refresh_status: str,
        error_message: str | None,
    ) -> None:
        stmt = insert(RefreshStateORM).values(
            dataset_type=dataset_type,
            dataset_key=dataset_key,
            source=source,
            last_success_at=last_success_at,
            last_event_timestamp=last_event_timestamp,
            refresh_status=refresh_status,
            error_message=error_message,
        ).on_conflict_do_update(
            constraint="uq_refresh_state_dataset_source",
            set_={
                "last_success_at": last_success_at,
                "last_event_timestamp": last_event_timestamp,
                "refresh_status": refresh_status,
                "error_message": error_message,
            },
        )
        self.session.execute(stmt)

