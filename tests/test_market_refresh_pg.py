from __future__ import annotations

import os

import pytest

from arbiter.data.ingestion.market_refresh import bootstrap_market_data, refresh_market_data


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or not os.getenv("FINNHUB_API_KEY"),
    reason="DATABASE_URL or FINNHUB_API_KEY not set; PostgreSQL/Finnhub tests skipped",
)


def test_market_refresh_runs_without_error(monkeypatch) -> None:
    # 仅验证函数可以跑通到 provider 调用层，具体网络交互依赖外部服务。
    symbol = "NVDA"
    timeframe = "1d"

    bootstrap_market_data(symbol, timeframe)
    refresh_market_data(symbol, timeframe)

