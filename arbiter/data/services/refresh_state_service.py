from __future__ import annotations

import argparse

from sqlalchemy import select

from arbiter.data.repositories.db import get_session
from arbiter.data.repositories.models import RefreshStateORM


def show_refresh_state() -> None:
    with get_session() as session:
        stmt = select(RefreshStateORM)
        rows = session.execute(stmt).scalars().all()
        for row in rows:
            print(
                f"{row.dataset_type} {row.dataset_key} source={row.source} "
                f"status={row.refresh_status} last_success_at={row.last_success_at} "
                f"last_event_timestamp={row.last_event_timestamp} "
                f"error={row.error_message}"
            )


def get_refresh_state(
    dataset_type: str,
    dataset_key: str,
):
    """Return refresh_state rows for given dataset_type and dataset_key."""
    with get_session() as session:
        stmt = select(RefreshStateORM).where(
            RefreshStateORM.dataset_type == dataset_type,
            RefreshStateORM.dataset_key == dataset_key,
        )
        return session.execute(stmt).scalars().all()


def main() -> None:
    parser = argparse.ArgumentParser(description="Show refresh_state records.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("show", help="Show all refresh_state rows")

    args = parser.parse_args()
    if args.command == "show":
        show_refresh_state()


if __name__ == "__main__":
    main()

