from __future__ import annotations

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from arbiter.scheduler.jobs.agent_market_scan_job import run_agent_market_scan_job
from arbiter.scheduler.jobs.market_job import run_market_refresh_job
from arbiter.scheduler.jobs.news_job import run_news_refresh_job


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        run_market_refresh_job,
        "interval",
        minutes=10,
        id="market_refresh_job",
        replace_existing=True,
    )

    scheduler.add_job(
        run_news_refresh_job,
        "interval",
        minutes=20,
        id="news_refresh_job",
        replace_existing=True,
    )

    # 由 Arbiter 侧定时触发 OpenClaw 风格的市场巡视任务
    scheduler.add_job(
        run_agent_market_scan_job,
        "interval",
        minutes=60,
        id="agent_market_scan_job",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Arbiter scheduler started with market/news refresh jobs and agent market scan job.")
    return scheduler


def main() -> None:
    configure_logging()
    scheduler = start_scheduler()
    try:
        # Run forever until interrupted.
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()

