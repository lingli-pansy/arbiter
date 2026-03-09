"""
arbiter 入口模块。

当前提供一个最小的 MarketBar 垂直切片 demo：
- 使用 Stub provider 生成样例行情
- 写入本地 SQLite 存储
- 再从存储中查询并打印结果
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from arbiter.data.market_service import MarketService
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
    limit = 5

    print(f"[arbiter demo] ingesting latest {limit} bars for {symbol} ({timeframe})...")
    ingested = service.ingest_latest(symbol=symbol, timeframe=timeframe, limit=limit)

    start = ingested[0].timestamp - timedelta(seconds=1)
    end = ingested[-1].timestamp + timedelta(seconds=1)

    print(f"[arbiter demo] querying bars from local store between {start} and {end}...")
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


