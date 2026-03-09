from __future__ import annotations

import os

import pytest

from arbiter.data.ingestion.news_refresh import bootstrap_news, refresh_news


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set; PostgreSQL tests skipped",
)


def test_news_refresh_runs_without_error() -> None:
    symbol = "NVDA"

    if not os.getenv("FINNHUB_API_KEY"):
        pytest.skip("FINNHUB_API_KEY not set; skipping news refresh test")

    bootstrap_news(symbol)
    refresh_news(symbol)

