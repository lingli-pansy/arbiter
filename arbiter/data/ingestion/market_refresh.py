from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from arbiter.data.providers.finnhub_market_provider import FinnhubMarketProvider
from arbiter.data.repositories.db import get_session
from arbiter.data.repositories.market_repository import MarketRepository
from arbiter.data.repositories.refresh_state_repository import RefreshStateRepository


DATASET_TYPE = "market_bars"
SOURCE = "finnhub"


def _dataset_key(symbol: str, timeframe: str) -> str:
    return f"{symbol}:{timeframe}"


def bootstrap_market_data(symbol: str, timeframe: str) -> None:
    provider = FinnhubMarketProvider()
    # 简单起见：初始化拉最近 30 天
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=30)

    with get_session() as session:
        market_repo = MarketRepository(session)
        state_repo = RefreshStateRepository(session)

        bars = provider.fetch_bars(symbol=symbol, timeframe=timeframe, start=start, end=end)
        inserted = market_repo.append_bars(bars)

        last_event_ts = max((b.timestamp for b in bars), default=None)
        state_repo.upsert_state(
            dataset_type=DATASET_TYPE,
            dataset_key=_dataset_key(symbol, timeframe),
            source=SOURCE,
            last_success_at=datetime.now(tz=timezone.utc),
            last_event_timestamp=last_event_ts,
            refresh_status="success",
            error_message=None,
        )

        print(f"[bootstrap_market_data] inserted={inserted}, last_event_timestamp={last_event_ts}")


def refresh_market_data(symbol: str, timeframe: str) -> None:
    provider = FinnhubMarketProvider()

    with get_session() as session:
        market_repo = MarketRepository(session)
        state_repo = RefreshStateRepository(session)

        key = _dataset_key(symbol, timeframe)
        state = state_repo.get_state(DATASET_TYPE, key, SOURCE)

        now = datetime.now(tz=timezone.utc)
        if state is None or state.last_event_timestamp is None:
            # 没有 checkpoint，则退化为 bootstrap 行为（最近 30 天）
            start = now - timedelta(days=30)
        else:
            start = state.last_event_timestamp

        end = now
        bars = provider.fetch_bars(symbol=symbol, timeframe=timeframe, start=start, end=end)
        inserted = market_repo.append_bars(bars)
        last_event_ts = max((b.timestamp for b in bars), default=state.last_event_timestamp)

        state_repo.upsert_state(
            dataset_type=DATASET_TYPE,
            dataset_key=key,
            source=SOURCE,
            last_success_at=now,
            last_event_timestamp=last_event_ts,
            refresh_status="success",
            error_message=None,
        )

        print(f"[refresh_market_data] inserted={inserted}, last_event_timestamp={last_event_ts}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Market data bootstrap/refresh using Alpaca and PostgreSQL.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser("bootstrap", help="Bootstrap historical market data")
    bootstrap_parser.add_argument("symbol", type=str)
    bootstrap_parser.add_argument("timeframe", type=str)

    refresh_parser = subparsers.add_parser("refresh", help="Refresh incremental market data")
    refresh_parser.add_argument("symbol", type=str)
    refresh_parser.add_argument("timeframe", type=str)

    args = parser.parse_args()

    if args.command == "bootstrap":
        bootstrap_market_data(args.symbol, args.timeframe)
    elif args.command == "refresh":
        refresh_market_data(args.symbol, args.timeframe)


if __name__ == "__main__":
    main()

