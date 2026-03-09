from __future__ import annotations

import os
from datetime import date, datetime
from typing import List

import requests

from arbiter.protocols.news import NewsEvent


FINNHUB_BASE_URL = os.getenv("FINNHUB_BASE_URL", "https://finnhub.io/api/v1")


def _get_finnhub_api_key() -> str:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise RuntimeError("FINNHUB_API_KEY must be set in environment")
    return api_key


class FinnhubNewsProvider:
    """Finnhub company news provider.

    只负责从 Finnhub 拉取新闻并返回 `NewsEvent` 列表，不直接写数据库。
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or FINNHUB_BASE_URL

    def fetch_company_news(
        self,
        symbol: str,
        start: date,
        end: date,
    ) -> List[NewsEvent]:
        url = f"{self.base_url}/company-news"
        params = {
            "symbol": symbol,
            "from": start.isoformat(),
            "to": end.isoformat(),
            "token": _get_finnhub_api_key(),
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        events: List[NewsEvent] = []
        for item in data:
            # Finnhub response: 'id', 'datetime', 'headline', 'summary', 'url', 'source'...
            event_id = str(item.get("id"))
            ts = datetime.fromtimestamp(item.get("datetime", 0), tz=datetime.utcnow().astimezone().tzinfo)
            headline = item.get("headline") or ""
            summary = item.get("summary") or ""
            source = item.get("source") or "finnhub"
            url_val = item.get("url") or None

            events.append(
                NewsEvent(
                    event_id=event_id,
                    timestamp=ts,
                    symbols=[symbol],
                    headline=headline,
                    summary=summary,
                    source=source,
                    url=url_val,
                )
            )

        return events

