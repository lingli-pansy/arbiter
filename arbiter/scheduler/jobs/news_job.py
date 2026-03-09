from __future__ import annotations

import logging
from datetime import datetime, timezone

from arbiter.config.universe import NEWS_SYMBOLS
from arbiter.data.ingestion.news_refresh import refresh_news


logger = logging.getLogger(__name__)


def run_news_refresh_job() -> None:
    """Refresh news data for all configured symbols."""
    start_time = datetime.now(tz=timezone.utc)
    symbols_processed = 0
    errors = 0

    for symbol in NEWS_SYMBOLS:
        try:
            inserted = refresh_news(symbol)
            symbols_processed += 1
            logger.info(
                "news_refresh: symbol=%s news_inserted=%s",
                symbol,
                inserted,
            )
        except Exception:  # noqa: BLE001
            errors += 1
            logger.exception("news_refresh: symbol=%s error", symbol)

    end_time = datetime.now(tz=timezone.utc)
    logger.info(
        "news_refresh_job: start=%s end=%s symbols_processed=%s errors=%s",
        start_time.isoformat(),
        end_time.isoformat(),
        symbols_processed,
        errors,
    )

