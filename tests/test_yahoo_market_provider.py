from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from arbiter.data.providers.yahoo_market_provider import YahooMarketProvider
from arbiter.protocols.market import MarketBar


def test_yahoo_provider_returns_marketbar_with_monkeypatched_history(monkeypatch) -> None:
    provider = YahooMarketProvider()

    # 构造一个假的 history DataFrame，避免真实网络依赖
    index = pd.DatetimeIndex(
        [
            datetime(2025, 1, 1, tzinfo=timezone.utc),
            datetime(2025, 1, 2, tzinfo=timezone.utc),
        ]
    )
    df = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [101.0, 102.0],
            "Low": [99.0, 100.0],
            "Close": [100.5, 101.5],
            "Volume": [1000.0, 1100.0],
        },
        index=index,
    )

    class DummyTicker:
        def history(self, *args, **kwargs):
            return df

    def fake_ticker(symbol: str):
        return DummyTicker()

    monkeypatch.setattr("arbiter.data.providers.yahoo_market_provider.yf.Ticker", fake_ticker)

    bars = provider.fetch_bars(
        symbol="TEST",
        timeframe="1d",
        start=datetime(2024, 12, 31, tzinfo=timezone.utc),
        end=datetime(2025, 1, 3, tzinfo=timezone.utc),
    )

    assert len(bars) == 2
    assert all(isinstance(b, MarketBar) for b in bars)
    assert all(b.symbol == "TEST" for b in bars)
    assert all(b.timeframe == "1d" for b in bars)

