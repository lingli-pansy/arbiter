from __future__ import annotations

import logging
from datetime import datetime, timezone

from arbiter.config.universe import MARKET_SYMBOLS
from arbiter.data.ingestion.market_refresh import refresh_market_data


logger = logging.getLogger(__name__)


def run_market_refresh_job() -> None:
    """Refresh daily market data for all configured symbols."""
    start_time = datetime.now(tz=timezone.utc)
    symbols_processed = 0
    errors = 0

    for symbol in MARKET_SYMBOLS:
        try:
            bars_fetched, bars_inserted = refresh_market_data(symbol, "1d")
            symbols_processed += 1
            logger.info(
                "market_refresh: symbol=%s bars_fetched=%s bars_inserted=%s",
                symbol,
                bars_fetched,
                bars_inserted,
            )
        except Exception:  # noqa: BLE001
            errors += 1
            logger.exception("market_refresh: symbol=%s error", symbol)

    end_time = datetime.now(tz=timezone.utc)
    logger.info(
        "market_refresh_job: start=%s end=%s symbols_processed=%s errors=%s",
        start_time.isoformat(),
        end_time.isoformat(),
        symbols_processed,
        errors,
    )

