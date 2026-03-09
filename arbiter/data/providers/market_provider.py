from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence

from arbiter.protocols.market import MarketBar


class MarketDataProvider(ABC):
    """Market data provider 抽象接口。

    所有具体行情数据源（真实或 stub）都应实现本接口。
    """

    @abstractmethod
    def fetch_latest_bars(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> Sequence[MarketBar]:
        """获取某标的最近若干根 K 线。"""

    @abstractmethod
    def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[MarketBar]:
        """按时间区间获取 K 线。"""

