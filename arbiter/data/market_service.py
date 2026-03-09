from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Sequence

from arbiter.protocols.market import MarketBar

from .providers.market_provider import MarketDataProvider
from .storage.market_store import MarketStore


class MarketService:
    """Market data 垂直切片的协调服务。

    - 从 provider 拉取 `MarketBar`
    - 写入本地 `MarketStore`
    - 提供统一的查询接口
    """

    def __init__(
        self,
        provider: MarketDataProvider,
        store: MarketStore,
    ) -> None:
        self._provider = provider
        self._store = store

    def ingest_latest(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> Sequence[MarketBar]:
        """从 provider 拉取最近若干根 K 线并写入存储。"""
        bars = self._provider.fetch_latest_bars(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        self._store.write_bars(bars)
        return list(bars)

    def query_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[MarketBar]:
        """从存储中按条件查询 K 线。"""
        return self._store.read_bars(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
        )

