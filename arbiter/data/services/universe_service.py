from __future__ import annotations

from typing import Any, Dict, Iterable, List

from arbiter.data.services import refresh_state_service


def get_universe_data_summary(
    symbols: Iterable[str],
    timeframe: str = "1d",
) -> List[Dict[str, Any]]:
    """汇总一组 symbol 的最新行情/新闻时间与刷新状态。

    仅依赖 refresh_state 表，不直接访问底层表。
    """
    summary: List[Dict[str, Any]] = []
    for symbol in symbols:
        market_key = f"{symbol}:{timeframe}"

        market_states = refresh_state_service.get_refresh_state("market_bars", market_key)
        news_states = refresh_state_service.get_refresh_state("news_events", symbol)

        market_row = next(
            (s for s in market_states if s.source == "yahoo"),
            market_states[0] if market_states else None,
        )
        news_row = next(
            (s for s in news_states if s.source == "finnhub"),
            news_states[0] if news_states else None,
        )

        summary.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "latest_bar_timestamp": (
                    market_row.last_event_timestamp.isoformat()
                    if market_row and market_row.last_event_timestamp
                    else None
                ),
                "latest_news_timestamp": (
                    news_row.last_event_timestamp.isoformat()
                    if news_row and news_row.last_event_timestamp
                    else None
                ),
                "market_refresh_status": market_row.refresh_status if market_row else None,
                "news_refresh_status": news_row.refresh_status if news_row else None,
            }
        )

    return summary

