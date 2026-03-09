from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Sequence

from arbiter.protocols.market import MarketBar

from ..providers.market_provider import MarketDataProvider
from ..storage.market_store import MarketStore, RefreshState


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

    流程（带 checkpoint）：
    1. 查询当前 symbol/timeframe 的 refresh metadata（checkpoint）
    2. 有 checkpoint 时优先尝试调用 provider.fetch_bars 增量拉取
       - 若 provider 不支持，则回退到 latest-window 模式
    3. 无 checkpoint 时走首次 latest-window 初始化逻辑
    4. 将新的 bar 追加写入 store
    5. 更新 refresh metadata
    6. 返回本次追加的条数
    """
    state: RefreshState | None = store.get_refresh_state(symbol=symbol, timeframe=timeframe)

    bars: Sequence[MarketBar]
    path = "initial"

    if state is not None:
        # checkpoint 模式：从上次最后一根 K 线时间开始增量拉取
        start_ts = state.last_bar_timestamp
        # 为避免依赖 provider 的具体行为，这里使用等于 checkpoint 的窄窗口；
        # 真实 provider 可以在实现中选择返回更广的时间段。
        end_ts = start_ts
        try:
            bars = provider.fetch_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start_ts,
                end=end_ts,
            )
            path = "checkpoint"
        except NotImplementedError:
            bars = provider.fetch_latest_bars(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )
            path = "latest_fallback"
    else:
        # 首次：latest-window 初始化
        bars = provider.fetch_latest_bars(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        path = "initial_latest"

    if not bars:
        return 0

    inserted = store.append_bars(bars)

    # 无论是否真正插入新数据，只要 store 中有该 symbol/timeframe 的数据，就更新 metadata
    last_ts = store.get_last_bar_timestamp(symbol=symbol, timeframe=timeframe)
    if last_ts is None:
        return inserted

    total_rows = store.get_total_rows(symbol=symbol, timeframe=timeframe)
    now = datetime.now(tz=timezone.utc)
    source = bars[-1].source if bars else (state.source if state is not None else "unknown")

    store.update_refresh_state(
        symbol=symbol,
        timeframe=timeframe,
        last_bar_timestamp=last_ts,
        last_refresh_at=now,
        source=source,
        total_rows=total_rows,
    )

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


def get_refresh_state(
    symbol: str,
    timeframe: str,
    store: MarketStore,
) -> RefreshState | None:
    """对外暴露的最小 refresh state 查询接口。"""
    return store.get_refresh_state(symbol=symbol, timeframe=timeframe)


