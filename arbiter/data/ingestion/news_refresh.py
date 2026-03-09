from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone

from arbiter.data.providers.finnhub_news_provider import FinnhubNewsProvider
from arbiter.data.repositories.db import get_session
from arbiter.data.repositories.news_repository import NewsRepository
from arbiter.data.repositories.refresh_state_repository import RefreshStateRepository


DATASET_TYPE = "news_events"
SOURCE = "finnhub"


def _dataset_key(symbol: str) -> str:
    return symbol


def bootstrap_news(symbol: str) -> None:
    provider = FinnhubNewsProvider()
    today = date.today()
    start = today - timedelta(days=30)
    end = today

    with get_session() as session:
        news_repo = NewsRepository(session)
        state_repo = RefreshStateRepository(session)

        events = provider.fetch_company_news(symbol=symbol, start=start, end=end)
        inserted = news_repo.append_events(events)

        last_event_ts = max((e.timestamp for e in events), default=None)
        state_repo.upsert_state(
            dataset_type=DATASET_TYPE,
            dataset_key=_dataset_key(symbol),
            source=SOURCE,
            last_success_at=datetime.now(tz=timezone.utc),
            last_event_timestamp=last_event_ts,
            refresh_status="success",
            error_message=None,
        )

        print(f"[bootstrap_news] inserted={inserted}, last_event_timestamp={last_event_ts}")


def refresh_news(symbol: str) -> None:
    provider = FinnhubNewsProvider()

    with get_session() as session:
        news_repo = NewsRepository(session)
        state_repo = RefreshStateRepository(session)

        key = _dataset_key(symbol)
        state = state_repo.get_state(DATASET_TYPE, key, SOURCE)

        today = date.today()
        if state is None or state.last_event_timestamp is None:
            start = today - timedelta(days=30)
        else:
            start = state.last_event_timestamp.date()
        end = today

        events = provider.fetch_company_news(symbol=symbol, start=start, end=end)
        inserted = news_repo.append_events(events)
        last_event_ts = max((e.timestamp for e in events), default=state.last_event_timestamp)

        state_repo.upsert_state(
            dataset_type=DATASET_TYPE,
            dataset_key=key,
            source=SOURCE,
            last_success_at=datetime.now(tz=timezone.utc),
            last_event_timestamp=last_event_ts,
            refresh_status="success",
            error_message=None,
        )

        print(f"[refresh_news] inserted={inserted}, last_event_timestamp={last_event_ts}")


def main() -> None:
    parser = argparse.ArgumentParser(description="News bootstrap/refresh using Finnhub and PostgreSQL.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser("bootstrap", help="Bootstrap historical news")
    bootstrap_parser.add_argument("symbol", type=str)

    refresh_parser = subparsers.add_parser("refresh", help="Refresh incremental news")
    refresh_parser.add_argument("symbol", type=str)

    args = parser.parse_args()

    if args.command == "bootstrap":
        bootstrap_news(args.symbol)
    elif args.command == "refresh":
        refresh_news(args.symbol)


if __name__ == "__main__":
    main()

