from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from arbiter.config import universe
from arbiter.data.repositories.db import get_session
from arbiter.data.repositories.refresh_state_repository import RefreshStateRepository
from arbiter.scheduler.jobs.market_job import run_market_refresh_job
from arbiter.scheduler.jobs.news_job import run_news_refresh_job


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set; scheduler tests skipped",
)


def test_scheduler_jobs_update_refresh_state(monkeypatch) -> None:
    # 将 symbol universe 收敛到少量测试标的，避免大规模刷新。
    monkeypatch.setattr(universe, "MARKET_SYMBOLS", ["SCHED_MKT"])
    monkeypatch.setattr(universe, "NEWS_SYMBOLS", ["SCHED_NEWS"])
    # 同时覆盖 job 模块中的列表引用，确保只处理测试标的。
    monkeypatch.setattr("arbiter.scheduler.jobs.market_job.MARKET_SYMBOLS", ["SCHED_MKT"])
    monkeypatch.setattr("arbiter.scheduler.jobs.news_job.NEWS_SYMBOLS", ["SCHED_NEWS"])

    # 使用 fake refresh 函数，避免真实网络依赖，只验证 scheduler wiring + refresh_state。
    def fake_refresh_market_data(symbol: str, timeframe: str) -> tuple[int, int]:
        now = datetime.now(tz=timezone.utc)
        with get_session() as session:
            repo = RefreshStateRepository(session)
            repo.upsert_state(
                dataset_type="market_bars",
                dataset_key=f"{symbol}:{timeframe}",
                source="scheduler-test",
                last_success_at=now,
                last_event_timestamp=now,
                refresh_status="success",
                error_message=None,
            )
        return 1, 1

    def fake_refresh_news(symbol: str) -> int:
        now = datetime.now(tz=timezone.utc)
        with get_session() as session:
            repo = RefreshStateRepository(session)
            repo.upsert_state(
                dataset_type="news_events",
                dataset_key=symbol,
                source="scheduler-test",
                last_success_at=now,
                last_event_timestamp=now,
                refresh_status="success",
                error_message=None,
            )
        return 1

    monkeypatch.setattr(
        "arbiter.scheduler.jobs.market_job.refresh_market_data",
        fake_refresh_market_data,
    )
    monkeypatch.setattr(
        "arbiter.scheduler.jobs.news_job.refresh_news",
        fake_refresh_news,
    )

    run_market_refresh_job()
    run_news_refresh_job()

    with get_session() as session:
        repo = RefreshStateRepository(session)
        state_m = repo.get_state(
            dataset_type="market_bars",
            dataset_key="SCHED_MKT:1d",
            source="scheduler-test",
        )
        state_n = repo.get_state(
            dataset_type="news_events",
            dataset_key="SCHED_NEWS",
            source="scheduler-test",
        )

        assert state_m is not None
        assert state_n is not None

