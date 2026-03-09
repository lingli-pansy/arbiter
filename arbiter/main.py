"""
arbiter 入口模块。

当前提供一个最小的 MarketBar 垂直切片 demo：
- 使用 Stub provider 刷新样例行情
- 通过本地 SQLite 存储实现 append 模式
- 再从存储中查询并打印结果
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from arbiter.data.market_service import MarketService
from arbiter.data.ingestion.market_refresh import refresh_market_data
from arbiter.data.providers.stub_market_provider import StubMarketDataProvider
from arbiter.data.storage.market_store import MarketStore


def main() -> None:
    base_dir = Path(".")
    db_path = base_dir / "market_demo.db"

    provider = StubMarketDataProvider()
    store = MarketStore(db_path=db_path)
    service = MarketService(provider=provider, store=store)

    symbol = "DEMO"
    timeframe = "1m"

    print(f"[arbiter demo] refreshing market data for {symbol} ({timeframe})...")
    inserted = refresh_market_data(
        symbol=symbol,
        timeframe=timeframe,
        provider=provider,
        store=store,
        limit=10,
    )
    print(f"[arbiter demo] appended {inserted} new bars.")

    # 使用一个较宽的时间窗口从本地存储中查询结果
    start = datetime(1970, 1, 1, tzinfo=timezone.utc)
    end = datetime(2100, 1, 1, tzinfo=timezone.utc)

    print(f"[arbiter demo] querying bars for {symbol} ({timeframe}) from local store...")
    stored = service.query_bars(symbol=symbol, timeframe=timeframe, start=start, end=end)

    for bar in stored:
        ts = bar.timestamp.astimezone(timezone.utc).isoformat()
        print(
            f\"{ts} {bar.symbol} {bar.timeframe} "
            f\"O:{bar.open:.2f} H:{bar.high:.2f} "
            f\"L:{bar.low:.2f} C:{bar.close:.2f} V:{bar.volume:.0f} "
            f\"[source={bar.source}]\"
        )

    print(f"[arbiter demo] done. total bars: {len(stored)} (db: {db_path})")


if __name__ == "__main__":
    main()


