from __future__ import annotations

import os

import pytest

from arbiter.scheduler.jobs.agent_market_scan_job import run_agent_market_scan_job


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set; scheduler/agent integration tests skipped",
)


def test_agent_market_scan_job_invokes_subprocess(monkeypatch, tmp_path) -> None:
    calls = {}

    def fake_run(cmd, check, capture_output, text):
        calls["cmd"] = cmd
        calls["check"] = check
        calls["capture_output"] = capture_output
        calls["text"] = text

        class Result:
            returncode = 0
            stdout = "ok"
            stderr = ""

        return Result()

    monkeypatch.setattr("arbiter.scheduler.jobs.agent_market_scan_job.subprocess.run", fake_run)

    run_agent_market_scan_job()

    assert "cmd" in calls
    # 确保是通过当前 Python 可执行文件和 -m arbiter.openclaw.market_scan_task 调用的
    assert calls["cmd"][-2:] == ["-m", "arbiter.openclaw.market_scan_task"]
    assert calls["check"] is False
    assert calls["capture_output"] is True
    assert calls["text"] is True

