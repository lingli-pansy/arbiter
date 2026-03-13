#!/usr/bin/env python3
"""simulate_rebalance 最小测试"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"


def _run(params: dict) -> tuple[int, dict]:
    raw = json.dumps(params)
    r = subprocess.run(
        [sys.executable, str(IMPL_DIR / "simulate_rebalance.py")],
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


def test_simulate_rebalance_validation() -> None:
    """缺少 portfolio 或 target_weights 应返回错误"""
    code, out = _run({})
    assert code != 0 or out.get("success") is False
    code2, out2 = _run({"portfolio": {"assets": []}})
    assert code2 != 0 or out2.get("success") is False


def test_simulate_rebalance_equal_weight() -> None:
    """等权调仓"""
    params = {
        "portfolio": {
            "assets": [
                {"symbol": "NVDA", "weight": 0.4},
                {"symbol": "MSFT", "weight": 0.35},
                {"symbol": "AAPL", "weight": 0.25},
            ],
            "initial_capital": 100000,
        },
        "target_weights": {"type": "equal"},
    }
    code, out = _run(params)
    assert code == 0, f"Failed: {out}"
    assert out.get("success") is True
    rb = out.get("rebalance", {})
    assert rb["current_weights"]["NVDA"] == 0.4
    assert rb["current_weights"]["MSFT"] == 0.35
    assert rb["current_weights"]["AAPL"] == 0.25
    for s in ["NVDA", "MSFT", "AAPL"]:
        assert abs(rb["target_weights"][s] - 0.3333) < 0.01
    assert rb["differences"]["NVDA"] < 0
    assert rb["differences"]["AAPL"] > 0
    trades = {t["symbol"]: t for t in rb["trades"]}
    assert trades["NVDA"]["action"] == "SELL"
    assert trades["AAPL"]["action"] == "BUY"


def test_simulate_rebalance_custom_weight() -> None:
    """自定义权重调仓"""
    params = {
        "portfolio": {
            "assets": [
                {"symbol": "NVDA", "weight": 0.4},
                {"symbol": "MSFT", "weight": 0.35},
                {"symbol": "AAPL", "weight": 0.25},
            ],
        },
        "target_weights": {"type": "custom", "weights": {"NVDA": 0.3, "MSFT": 0.35, "AAPL": 0.35}},
    }
    code, out = _run(params)
    assert code == 0, f"Failed: {out}"
    rb = out["rebalance"]
    assert rb["target_weights"]["NVDA"] == 0.3
    assert rb["target_weights"]["MSFT"] == 0.35
    assert rb["target_weights"]["AAPL"] == 0.35
    assert rb["differences"]["NVDA"] == -0.1
    assert rb["differences"]["MSFT"] == 0
    assert rb["differences"]["AAPL"] == 0.1
    trades = {t["symbol"]: t for t in rb["trades"]}
    assert trades["NVDA"]["action"] == "SELL"
    assert trades["MSFT"]["action"] == "HOLD"
    assert trades["AAPL"]["action"] == "BUY"
