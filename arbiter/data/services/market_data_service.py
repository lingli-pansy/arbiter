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

