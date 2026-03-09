from __future__ import annotations

from datetime import datetime
from typing import Iterable, Mapping, Sequence

from arbiter.protocols.market import MarketBar

from ..providers.market_provider import MarketDataProvider
from ..storage.market_store import MarketStore


DEFAULT_REFRESH_LIMIT = 500


def refresh_market_data(
    symbol: str,
    timeframe: str,
    provider: MarketDataProvider,
    store: MarketStore,
    *,
    limit: int = DEFAULT_REFRESH_LIMIT,
) -> int:
    """刷新单个 symbol 的最新行情数据。

    流程：
    1. 通过 provider 获取最近若干根 `MarketBar`
    2. 从 store 读取该时间窗口内已存在的记录
    3. 仅将新的 bar 追加写入
    4. 返回本次追加的条数
    """
    latest: Sequence[MarketBar] = provider.fetch_latest_bars(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )
    if not latest:
        return 0

    start_ts = latest[0].timestamp
    end_ts = latest[-1].timestamp

    existing = store.read_bars(
        symbol=symbol,
        timeframe=timeframe,
        start=start_ts,
        end=end_ts,
    )
    existing_ts = {b.timestamp for b in existing}

    new_bars = [b for b in latest if b.timestamp not in existing_ts]
    if not new_bars:
        return 0

    inserted = store.append_bars(new_bars)
    return inserted


def refresh_symbols(
    symbols: Iterable[str],
    timeframe: str,
    provider: MarketDataProvider,
    store: MarketStore,
    *,
    limit: int = DEFAULT_REFRESH_LIMIT,
) -> dict[str, int]:
    """最简单版本的多标的 refresh 调度。

    依次对每个 symbol 执行 `refresh_market_data`，并返回每个 symbol 的追加条数。
    """
    result: dict[str, int] = {}
    for symbol in symbols:
        count = refresh_market_data(
            symbol=symbol,
            timeframe=timeframe,
            provider=provider,
            store=store,
            limit=limit,
        )
        result[symbol] = count
    return result

