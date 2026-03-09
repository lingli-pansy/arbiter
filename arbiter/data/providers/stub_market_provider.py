from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence

from arbiter.protocols.market import MarketBar

from .market_provider import MarketDataProvider


class StubMarketDataProvider(MarketDataProvider):
    """用于测试与 demo 的本地 stub provider。

    返回构造好的 `MarketBar` 样本数据，而不依赖真实第三方行情源。
    """

    def __init__(self, *, base_time: datetime | None = None) -> None:
        self._base_time = base_time or datetime.now(tz=timezone.utc)

    def _generate_bars(
        self,
        symbol: str,
        timeframe: str,
        count: int,
    ) -> list[MarketBar]:
        bars: list[MarketBar] = []
        for i in range(count):
            ts = self._base_time - timedelta(minutes=i)
            price = 100.0 + i
            bar = MarketBar(
                symbol=symbol,
                timestamp=ts,
                timeframe=timeframe,
                open=price - 0.5,
                high=price + 1.0,
                low=price - 1.0,
                close=price,
                volume=1000.0 + i * 10,
                source="stub",
            )
            bars.append(bar)
        # 统一按时间升序返回
        return sorted(bars, key=lambda b: b.timestamp)

    def fetch_latest_bars(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> Sequence[MarketBar]:
        return self._generate_bars(symbol=symbol, timeframe=timeframe, count=limit)

    def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[MarketBar]:
        # 简化逻辑：按时间窗口裁剪 _generate_bars 结果
        # 为确保覆盖区间，上限多生成一些。
        bars = self._generate_bars(symbol=symbol, timeframe=timeframe, count=100)
        return [
            b for b in bars
            if start <= b.timestamp <= end
        ]

