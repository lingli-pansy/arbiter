from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from arbiter.data.market_service import MarketService
from arbiter.data.providers.stub_market_provider import StubMarketDataProvider
from arbiter.data.storage.market_store import MarketStore
from arbiter.protocols.market import MarketBar


def test_stub_provider_returns_marketbar() -> None:
    provider = StubMarketDataProvider()
    bars = provider.fetch_latest_bars(symbol="TEST", timeframe="1m", limit=5)

    assert len(bars) == 5
    assert all(isinstance(b, MarketBar) for b in bars)
    assert all(b.symbol == "TEST" for b in bars)
    assert all(b.timeframe == "1m" for b in bars)
    # 时间应为升序
    timestamps = [b.timestamp for b in bars]
    assert timestamps == sorted(timestamps)


def test_market_store_write_and_read(tmp_path: Path) -> None:
    db_path = tmp_path / "market.db"
    store = MarketStore(db_path=db_path)

    base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
    bars = [
        MarketBar(
            symbol="TEST",
            timestamp=base_time + timedelta(minutes=i),
            timeframe="1m",
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.5 + i,
            volume=1000.0 + i,
            source="unit-test",
        )
        for i in range(3)
    ]

    store.write_bars(bars)

    result = store.read_bars(
        symbol="TEST",
        timeframe="1m",
        start=base_time,
        end=base_time + timedelta(minutes=2),
    )

    assert len(result) == 3
    assert [b.timestamp for b in result] == [b.timestamp for b in bars]


def test_market_service_fetch_store_query_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "market.db"
    store = MarketStore(db_path=db_path)
    provider = StubMarketDataProvider()
    service = MarketService(provider=provider, store=store)

    ingested = service.ingest_latest(symbol="TEST", timeframe="1m", limit=10)
    assert len(ingested) == 10

    start = ingested[0].timestamp - timedelta(seconds=1)
    end = ingested[-1].timestamp + timedelta(seconds=1)

    result = service.query_bars(
        symbol="TEST",
        timeframe="1m",
        start=start,
        end=end,
    )

    assert len(result) == len(ingested)
    # round-trip 后字段应保持一致（按 timestamp 对齐）
    for original, loaded in zip(ingested, result):
        assert original.symbol == loaded.symbol
        assert original.timestamp == loaded.timestamp
        assert original.timeframe == loaded.timeframe
        assert original.open == loaded.open
        assert original.high == loaded.high
        assert original.low == loaded.low
        assert original.close == loaded.close
        assert original.volume == loaded.volume
        assert original.source == loaded.source

