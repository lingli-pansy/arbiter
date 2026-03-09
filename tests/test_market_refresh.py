from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from arbiter.data.ingestion.market_refresh import (
    get_refresh_state,
    refresh_market_data,
    refresh_symbols,
)
from arbiter.data.providers.stub_market_provider import StubMarketDataProvider
from arbiter.data.storage.market_store import MarketStore


def _fixed_time() -> datetime:
    return datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


def test_refresh_market_data_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "market.db"
    store = MarketStore(db_path=db_path)
    provider = StubMarketDataProvider(base_time=_fixed_time())

    symbol = "TEST"
    timeframe = "1m"

    first = refresh_market_data(
        symbol=symbol,
        timeframe=timeframe,
        provider=provider,
        store=store,
        limit=10,
    )
    # 第二次 refresh 基于 checkpoint 工作，但由于 provider 数据固定，不会新增条目
    second = refresh_market_data(
        symbol=symbol,
        timeframe=timeframe,
        provider=provider,
        store=store,
        limit=10,
    )

    assert first == 10
    assert second == 0

    # store 中应该只有 10 条，不会重复
    start = _fixed_time() - timedelta(minutes=20)
    end = _fixed_time() + timedelta(minutes=1)
    stored = store.read_bars(symbol=symbol, timeframe=timeframe, start=start, end=end)
    assert len(stored) == 10

    # metadata 应该已被创建
    state = get_refresh_state(symbol=symbol, timeframe=timeframe, store=store)
    assert state is not None
    assert state.symbol == symbol
    assert state.timeframe == timeframe
    assert state.total_rows == 10


def test_refresh_symbols_handles_multiple_symbols(tmp_path: Path) -> None:
    db_path = tmp_path / "market_multi.db"
    store = MarketStore(db_path=db_path)
    provider = StubMarketDataProvider(base_time=_fixed_time())

    symbols = ["AAA", "BBB"]
    timeframe = "5m"

    result = refresh_symbols(
        symbols=symbols,
        timeframe=timeframe,
        provider=provider,
        store=store,
        limit=3,
    )

    assert result == {"AAA": 3, "BBB": 3}

    for sym in symbols:
        stored = store.read_bars(
            symbol=sym,
            timeframe=timeframe,
            start=_fixed_time() - timedelta(minutes=20),
            end=_fixed_time() + timedelta(minutes=1),
        )
        assert len(stored) == 3

    # 每个 symbol 都应有对应 metadata
    for sym in symbols:
        state = get_refresh_state(symbol=sym, timeframe=timeframe, store=store)
        assert state is not None
        assert state.symbol == sym
        assert state.timeframe == timeframe
        assert state.total_rows == 3


def test_refresh_pipeline_store_and_query(tmp_path: Path) -> None:
    db_path = tmp_path / "market_roundtrip.db"
    store = MarketStore(db_path=db_path)
    provider = StubMarketDataProvider(base_time=_fixed_time())

    symbol = "PIPE"
    timeframe = "1m"

    count = refresh_market_data(
        symbol=symbol,
        timeframe=timeframe,
        provider=provider,
        store=store,
        limit=5,
    )
    assert count == 5

    # 宽时间窗口查询，验证数据可以从 store 中读回
    start = _fixed_time() - timedelta(minutes=20)
    end = _fixed_time() + timedelta(minutes=1)
    stored = store.read_bars(symbol=symbol, timeframe=timeframe, start=start, end=end)

    assert len(stored) == 5
    # 时间戳应为升序
    timestamps = [b.timestamp for b in stored]
    assert timestamps == sorted(timestamps)

    # refresh state query 返回正确结果
    state = get_refresh_state(symbol=symbol, timeframe=timeframe, store=store)
    assert state is not None
    assert state.last_bar_timestamp == timestamps[-1]
    assert state.total_rows == 5


