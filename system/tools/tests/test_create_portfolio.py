#!/usr/bin/env python3
"""create_portfolio / get_portfolio 最小测试"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"
STATE_DIR = IMPL_DIR.parent.parent / "state" / "portfolios"


def _run_create(params: dict) -> tuple[int, dict]:
    raw = json.dumps(params)
    r = subprocess.run(
        [sys.executable, str(IMPL_DIR / "create_portfolio.py")],
        input=raw.encode(),
        capture_output=True,
        timeout=10,
        cwd=str(IMPL_DIR),
    )
    out = {}
    if r.stdout:
        try:
            out = json.loads(r.stdout.decode())
        except json.JSONDecodeError:
            out = {"_raw": r.stdout.decode()[:500]}
    return r.returncode, out


def _run_get(portfolio_id: str) -> tuple[int, dict]:
    raw = json.dumps({"portfolio_id": portfolio_id})
    r = subprocess.run(
        [sys.executable, str(IMPL_DIR / "get_portfolio.py")],
        input=raw.encode(),
        capture_output=True,
        timeout=10,
        cwd=str(IMPL_DIR),
    )
    out = {}
    if r.stdout:
        try:
            out = json.loads(r.stdout.decode())
        except json.JSONDecodeError:
            out = {"_raw": r.stdout.decode()[:500]}
    return r.returncode, out


def test_create_portfolio_validation() -> None:
    """缺少必填字段应返回错误"""
    code, out = _run_create({"name": "x", "assets": []})
    assert code != 0 or out.get("success") is False
    assert "portfolio_id" in str(out.get("errors", [])).lower() or "assets" in str(out.get("errors", [])).lower()


def test_create_portfolio_weight_validation() -> None:
    """权重总和不为 1 应返回错误"""
    params = {
        "portfolio_id": "TEST_WEIGHT",
        "name": "Test",
        "assets": [{"symbol": "AAPL", "weight": 0.5}, {"symbol": "MSFT", "weight": 0.3}],
    }
    code, out = _run_create(params)
    assert code != 0 or out.get("success") is False


def test_get_portfolio_not_found() -> None:
    """不存在的组合应返回错误"""
    code, out = _run_get("NONEXISTENT_PORTFOLIO_XYZ")
    assert code != 0 or out.get("success") is False
    assert out.get("portfolio") is None or "not found" in str(out.get("errors", [])).lower()


def test_create_and_get_portfolio() -> None:
    """创建组合后可读取"""
    pid = "MODEL_TEST_001"
    params = {
        "portfolio_id": pid,
        "name": "Tech Growth Model",
        "assets": [
            {"symbol": "NVDA", "weight": 0.4},
            {"symbol": "MSFT", "weight": 0.35},
            {"symbol": "AAPL", "weight": 0.25},
        ],
        "initial_capital": 100000,
        "strategy": "momentum_20d",
    }
    code, out = _run_create(params)
    assert code == 0, f"create failed: {out}"
    assert out.get("success") is True
    assert out["portfolio"]["portfolio_id"] == pid
    assert out["portfolio"]["total_weight"] == 1.0
    assert "state_path" in out["portfolio"]

    code2, out2 = _run_get(pid)
    assert code2 == 0, f"get failed: {out2}"
    assert out2.get("success") is True
    assert out2["portfolio"]["portfolio_id"] == pid
    assert len(out2["portfolio"]["assets"]) == 3

    # 清理
    state_file = STATE_DIR / "MODEL_TEST_001.json"
    if state_file.exists():
        state_file.unlink()
