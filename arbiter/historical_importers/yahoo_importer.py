from __future__ import annotations

from datetime import datetime
from typing import Iterable

from arbiter.config.universe import MARKET_SYMBOLS
from arbiter.data.providers.yahoo_market_provider import YahooMarketProvider
from arbiter.data.repositories.db import get_session
from arbiter.market_store.operations import BarPayload, import_market_data
from arbiter.market_store.schema import init_canonical_schema


def generate_bars(
    symbols: Iterable[str],
    *,
    timeframe: str,
    start: datetime,
    end: datetime,
) -> list[BarPayload]:
    provider = YahooMarketProvider()
    payloads: list[BarPayload] = []

    for symbol in symbols:
        bars = provider.fetch_bars(symbol=symbol, timeframe=timeframe, start=start, end=end)
        for bar in bars:
            payloads.append(
                BarPayload(
                    instrument_id=f"{symbol}.{bar.timeframe}",
                    symbol=symbol,
                    venue="US",
                    timeframe=bar.timeframe,
                    timestamp=bar.timestamp,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    currency="USD",
                    source="yahoo",
                )
            )
    return payloads


def run_import(
    *,
    symbols: Iterable[str] | None = None,
    timeframe: str = "1d",
    start: datetime | None = None,
    end: datetime | None = None,
    mode: str = "append",
) -> int:
    """
    Minimal historical import pipeline backed by Yahoo Finance.

    This is a convenience implementation used to populate the canonical
    store for local development and testing.
    """

    init_canonical_schema()

    if symbols is None:
        symbols = MARKET_SYMBOLS

    if end is None:
        end = datetime.utcnow()
    if start is None:
        # Default to ~60 days of history.
        start = end.replace(hour=0, minute=0, second=0, microsecond=0)

    bars = generate_bars(symbols, timeframe=timeframe, start=start, end=end)

    with get_session() as session:
        inserted = import_market_data(session, bars=bars, mode=mode)  # type: ignore[arg-type]
    return inserted


def main() -> None:
    inserted = run_import()
    print(f"Imported {inserted} canonical bars from Yahoo Finance.")


if __name__ == "__main__":
    main()

