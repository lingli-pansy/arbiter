from __future__ import annotations

import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


logger = logging.getLogger(__name__)


def run_agent_market_scan_job() -> None:
    """Trigger the OpenClaw-style market scan task once via subprocess.

    This job belongs in Arbiter's scheduler and is responsible only for
    invoking the scan task CLI; the reasoning and MCP tool calls are
    handled inside the task itself.
    """
    start = datetime.now(tz=timezone.utc)
    logger.info("agent_market_scan_job: starting at %s", start.isoformat())

    # Use the current Python executable to run the scan task module.
    cmd = [sys.executable, "-m", "arbiter.openclaw.market_scan_task"]
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "agent_market_scan.log"

    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"\n=== Market scan started at {start.isoformat()} ===\n")
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
            )
            f.write(result.stdout)
            if result.stderr:
                f.write("\n[stderr]\n")
                f.write(result.stderr)

        if result.returncode != 0:
            logger.error("agent_market_scan_job: subprocess exited with code %s", result.returncode)
        else:
            logger.info("agent_market_scan_job: completed successfully")
    except Exception:  # noqa: BLE001
        logger.exception("agent_market_scan_job: error while running market_scan_task")

    end = datetime.now(tz=timezone.utc)
    logger.info(
        "agent_market_scan_job: finished at %s (duration=%.1fs)",
        end.isoformat(),
        (end - start).total_seconds(),
    )

