from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol

from arbiter.data.repositories.db import get_session
from arbiter.market_store.operations import BarPayload, ingest_market_data
from arbiter.market_store.schema import init_canonical_schema


class NtBarLike(Protocol):
    """
    Minimal protocol representing the fields we need from a NautilusTrader bar.
    """

    symbol: str
    venue: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class IbkrRealtimeConfig:
    """
    Configuration for the IBKR realtime ingest bridge.

    In a real deployment, this would be wired to NautilusTrader's IBKR
    adapter and symbol universe configuration.
    """

    symbols: list[str]
    timeframe: str = "1m"
    source: str = "ibkr"


class IbkrNtBridge:
    """
    Thin bridge between NautilusTrader IBKR market data streams and
    Arbiter's canonical market store.

    This class is intentionally agnostic of NT internals; the caller is
    responsible for wiring NT subscription callbacks to `on_bars`.
    """

    def __init__(self, config: IbkrRealtimeConfig) -> None:
        self._config = config
        init_canonical_schema()

    def on_bars(self, bars: Iterable[NtBarLike]) -> int:
        """
        Ingest a batch of NT bars into the canonical store.

        This method is designed to be called from NT's IBKR adapter
        callbacks whenever new bars are produced.
        """

        payloads: list[BarPayload] = []
        for bar in bars:
            if bar.symbol not in self._config.symbols:
                continue

            payloads.append(
                BarPayload(
                    instrument_id=f"{bar.symbol}.{bar.timeframe}",
                    symbol=bar.symbol,
                    venue=bar.venue,
                    timeframe=bar.timeframe,
                    timestamp=bar.timestamp,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    currency="USD",
                    source=self._config.source,
                )
            )

        if not payloads:
            return 0

        with get_session() as session:
            inserted = ingest_market_data(session, bars=payloads, source=self._config.source)  # type: ignore[arg-type]
        return inserted


def main() -> None:
    """
    Minimal harness for manual testing.

    In a real deployment, this module would be imported and wired to
    NautilusTrader's IBKR adapter instead of being run as a script.
    """

    config = IbkrRealtimeConfig(symbols=["AAPL", "MSFT"])
    bridge = IbkrNtBridge(config)

    # This is only a placeholder to demonstrate wiring; real usage will
    # pass NT bar objects into `bridge.on_bars(...)` from the adapter.
    print("IBKR NT bridge initialized for symbols:", ", ".join(config.symbols))
    print("Use bridge.on_bars(...) from within NautilusTrader callbacks.")


if __name__ == "__main__":
    main()

