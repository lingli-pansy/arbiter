from __future__ import annotations

import argparse
from datetime import datetime, timezone

from arbiter.data.repositories.db import get_session
from arbiter.data.repositories.market_repository import MarketRepository


def get_market_bars(
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
):
    with get_session() as session:
        repo = MarketRepository(session)
        return repo.get_bars(symbol=symbol, timeframe=timeframe, start=start, end=end)


def get_latest_bars(
    symbol: str,
    timeframe: str,
    limit: int,
):
    """Return latest N bars for a symbol/timeframe from PostgreSQL."""
    end = datetime(2100, 1, 1, tzinfo=timezone.utc)
    start = datetime(1970, 1, 1, tzinfo=timezone.utc)
    bars = get_market_bars(symbol, timeframe, start, end)
    bars = sorted(bars, key=lambda b: b.timestamp)
    if len(bars) <= limit:
        return bars
    return bars[-limit:]


def refresh_market_data_and_get_state(symbol: str, timeframe: str) -> dict:
    """Wrapper that refreshes market data and returns an updated refresh_state snapshot."""
    from arbiter.data.ingestion.market_refresh import refresh_market_data  # lazy import
    from arbiter.data.repositories.refresh_state_repository import RefreshStateRepository

    fetched, inserted = refresh_market_data(symbol, timeframe)

    with get_session() as session:
        state_repo = RefreshStateRepository(session)
        key = f"{symbol}:{timeframe}"
        state = state_repo.get_state("market_bars", key, "yahoo")

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "fetched": fetched,
        "inserted": inserted,
        "state": {
            "dataset_type": state.dataset_type if state else None,
            "dataset_key": state.dataset_key if state else None,
            "source": state.source if state else None,
            "last_success_at": state.last_success_at.isoformat() if state and state.last_success_at else None,
            "last_event_timestamp": state.last_event_timestamp.isoformat() if state and state.last_event_timestamp else None,
            "refresh_status": state.refresh_status if state else None,
            "error_message": state.error_message if state else None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Query market bars from PostgreSQL.")
    parser.add_argument("symbol", type=str)
    parser.add_argument("timeframe", type=str)
    parser.add_argument("--start", type=str, default=None, help="ISO8601 start time (UTC)")
    parser.add_argument("--end", type=str, default=None, help="ISO8601 end time (UTC)")

    args = parser.parse_args()

    if args.start:
        start = datetime.fromisoformat(args.start)
    else:
        start = datetime(1970, 1, 1, tzinfo=timezone.utc)

    if args.end:
        end = datetime.fromisoformat(args.end)
    else:
        end = datetime(2100, 1, 1, tzinfo=timezone.utc)

    bars = get_market_bars(args.symbol, args.timeframe, start, end)
    for b in bars:
        print(
            f"{b.timestamp.isoformat()} {b.symbol} {b.timeframe} "
            f"O:{b.open} H:{b.high} L:{b.low} C:{b.close} V:{b.volume} source={b.source}"
        )


if __name__ == "__main__":
    main()

