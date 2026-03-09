from __future__ import annotations

from datetime import datetime
from typing import List

import yfinance as yf

from arbiter.protocols.market import MarketBar


_INTERVAL_MAP: dict[str, str] = {
    "1m": "1m",
    "2m": "2m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "60m": "60m",
    "1h": "60m",
    "1d": "1d",
    "1D": "1d",
}


class YahooMarketProvider:
    """使用 yfinance/Yahoo Finance 作为 MarketBar 主数据源。

    只负责从 Yahoo 拉取 OHLCV 并返回 `MarketBar` 列表，不直接写数据库。
    """

    def _normalize_timeframe(self, timeframe: str) -> str:
        interval = _INTERVAL_MAP.get(timeframe)
        if not interval:
            raise ValueError(f"Unsupported timeframe for Yahoo provider: {timeframe}")
        return interval

    def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> List[MarketBar]:
        interval = self._normalize_timeframe(timeframe)

        ticker = yf.Ticker(symbol)
        # yfinance 期望 naive 或本地时区，统一用 UTC naive 时间戳
        df = ticker.history(
            start=start,
            end=end,
            interval=interval,
            auto_adjust=False,
        )

        if df.empty:
            return []

        # 尽量确保索引为 tz-aware UTC，若是 naive，则按 UTC 解释
        idx = df.index
        if getattr(idx, "tz", None) is None:
            df.index = idx.tz_localize("UTC")
        else:
            df.index = idx.tz_convert("UTC")

        bars: List[MarketBar] = []
        for ts, row in df.iterrows():
            # 行列名为: Open, High, Low, Close, Volume
            bars.append(
                MarketBar(
                    symbol=symbol,
                    timestamp=ts.to_pydatetime(),
                    timeframe=timeframe,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                    source="yahoo",
                )
            )

        bars.sort(key=lambda b: b.timestamp)
        return bars

    def fetch_latest_bars(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> List[MarketBar]:
        """通过最近一段区间拉取后截取最后 limit 条。"""
        # 用 period 参数拉最近一段时间，避免需要 start/end
        interval = self._normalize_timeframe(timeframe)

        # 经验上给一个足够长的 period，后面再裁剪
        if timeframe in ("1d", "1D"):
            period = "1y"
        else:
            period = "60d"

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=False)
        if df.empty:
            return []

        idx = df.index
        if getattr(idx, "tz", None) is None:
            df.index = idx.tz_localize("UTC")
        else:
            df.index = idx.tz_convert("UTC")

        bars: List[MarketBar] = []
        for ts, row in df.iterrows():
            bars.append(
                MarketBar(
                    symbol=symbol,
                    timestamp=ts.to_pydatetime(),
                    timeframe=timeframe,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                    source="yahoo",
                )
            )

        bars.sort(key=lambda b: b.timestamp)
        if len(bars) <= limit:
            return bars
        return bars[-limit:]

