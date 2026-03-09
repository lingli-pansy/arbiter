from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import requests

from arbiter.protocols.market import MarketBar

from .finnhub_news_provider import FINNHUB_BASE_URL, _get_finnhub_api_key


_RESOLUTION_MAP: dict[str, str] = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "60m": "60",
    "1h": "60",
    "1d": "D",
    "1D": "D",
}


class FinnhubMarketProvider:
    """使用 Finnhub stock candle API 作为 MarketBar 数据源。

    只负责从 Finnhub 拉取 K 线并返回 `MarketBar` 列表，不直接写数据库。
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or FINNHUB_BASE_URL

    def _normalize_timeframe(self, timeframe: str) -> str:
        res = _RESOLUTION_MAP.get(timeframe)
        if not res:
            raise ValueError(f"Unsupported timeframe for Finnhub: {timeframe}")
        return res

    def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> List[MarketBar]:
        resolution = self._normalize_timeframe(timeframe)
        url = f"{self.base_url}/stock/candle"
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": int(start.timestamp()),
            "to": int(end.timestamp()),
            "token": _get_finnhub_api_key(),
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("s") != "ok":
            # 可能是 no_data 或 error，直接返回空列表
            return []

        timestamps = data.get("t", [])
        opens = data.get("o", [])
        highs = data.get("h", [])
        lows = data.get("l", [])
        closes = data.get("c", [])
        volumes = data.get("v", [])

        bars: List[MarketBar] = []
        for ts, o, h, l, c, v in zip(
            timestamps,
            opens,
            highs,
            lows,
            closes,
            volumes,
        ):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            bars.append(
                MarketBar(
                    symbol=symbol,
                    timestamp=dt,
                    timeframe=timeframe,
                    open=float(o),
                    high=float(h),
                    low=float(l),
                    close=float(c),
                    volume=float(v),
                    source="finnhub",
                )
            )

        # Finnhub 返回的时间一般已按升序，但这里不妨再排序一次
        bars.sort(key=lambda b: b.timestamp)
        return bars

    def fetch_latest_bars(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> List[MarketBar]:
        """通过较宽时间窗口拉取后截取最近 limit 条。

        目前只在需要 latest 行为时使用，主要服务于潜在的高层调用。
        """
        # 粗略估算时间窗口：按 timeframe 不同给一个安全倍数
        now = datetime.now(tz=timezone.utc)
        if timeframe in ("1d", "1D"):
            days = max(limit * 2, 30)
            start = now - timedelta(days=days)
        else:
            # 对于分钟/小时级别，这里只是兜底实现，当前主要用 1d
            minutes = max(limit * 5, 60)
            start = now - timedelta(minutes=minutes)

        bars = self.fetch_bars(symbol=symbol, timeframe=timeframe, start=start, end=now)
        if len(bars) <= limit:
            return bars
        return bars[-limit:]

