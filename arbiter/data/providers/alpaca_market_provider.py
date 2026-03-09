from __future__ import annotations

import os
from datetime import datetime
from typing import List, Sequence

import requests

from arbiter.protocols.market import MarketBar


ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://data.alpaca.markets")


def _get_alpaca_headers() -> dict[str, str]:
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment")
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
    }


_TIMEFRAME_MAP: dict[str, str] = {
    "1m": "1Min",
    "5m": "5Min",
    "15m": "15Min",
    "1h": "1Hour",
    "1d": "1Day",
    "1D": "1Day",
}


class AlpacaMarketProvider:
    """Alpaca Market Data provider.

    只负责调用 Alpaca API 并返回 `MarketBar` 列表，不直接写数据库。
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or ALPACA_BASE_URL

    def _normalize_timeframe(self, timeframe: str) -> str:
        tf = _TIMEFRAME_MAP.get(timeframe)
        if not tf:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        return tf

    def _parse_bars(self, symbol: str, timeframe: str, data: dict) -> List[MarketBar]:
        bars: List[MarketBar] = []
        items = data.get("bars") or data.get("barset") or []
        tf = timeframe
        for item in items:
            # Alpaca v2: 't' ISO8601, 'o','h','l','c','v'
            ts_raw = item.get("t")
            if ts_raw is None:
                continue
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            bars.append(
                MarketBar(
                    symbol=symbol,
                    timestamp=ts,
                    timeframe=tf,
                    open=float(item.get("o")),
                    high=float(item.get("h")),
                    low=float(item.get("l")),
                    close=float(item.get("c")),
                    volume=float(item.get("v")),
                    source="alpaca",
                )
            )
        return bars

    def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> List[MarketBar]:
        tf = self._normalize_timeframe(timeframe)
        url = f"{self.base_url}/v2/stocks/{symbol}/bars"
        params = {
            "timeframe": tf,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "limit": 1000,
        }
        resp = requests.get(url, headers=_get_alpaca_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return self._parse_bars(symbol=symbol, timeframe=timeframe, data=data)

    def fetch_latest_bars(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> List[MarketBar]:
        tf = self._normalize_timeframe(timeframe)
        url = f"{self.base_url}/v2/stocks/{symbol}/bars"
        params = {
            "timeframe": tf,
            "limit": limit,
        }
        resp = requests.get(url, headers=_get_alpaca_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return self._parse_bars(symbol=symbol, timeframe=timeframe, data=data)

