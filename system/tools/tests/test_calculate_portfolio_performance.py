#!/usr/bin/env python3
"""calculate_portfolio_performance 最小测试 - 验证契约与输出结构"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"
SCRIPT = (IMPL_DIR / "calculate_portfolio_performance.py").resolve()


def _run(params: dict) -> tuple[int, dict]:
    raw = json.dumps(params)
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=raw.encode(),
        capture_output=True,
        timeout=30,
        cwd=str(IMPL_DIR.resolve()),
    )
    out = {}
    if r.stdout:
        text = r.stdout.decode()
        try:
            out = json.loads(text)
        except json.JSONDecodeError:
            for line in reversed(text.strip().split("\n")):
                if line.strip().startswith("{"):
                    try:
                        out = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
    return r.returncode, out


def test_validation_missing_portfolio() -> None:
    """缺少 portfolio/portfolio_id 时应返回错误"""
    params = {}
    code, out = _run(params)
    assert code != 0 or out.get("success") is False
    assert "portfolio" in str(out.get("errors", [])).lower()


def test_contract_output_with_mock_data() -> None:
    """有效输入（mock market_data）应返回符合契约的输出结构"""
    base_ts = "2026-03-01T00:00:00Z"
    bars = []
    for i in range(14):
        close = 100.0 + i * 0.5
        bars.append({
            "timestamp": f"2026-03-{i+1:02d}T00:00:00Z",
            "open": close - 0.2,
            "high": close + 0.3,
            "low": close - 0.3,
            "close": close,
            "volume": 1000000,
        })
    bench_bars = []
    for i in range(14):
        close = 50.0 + i * 0.3
        bench_bars.append({
            "timestamp": f"2026-03-{i+1:02d}T00:00:00Z",
            "open": close - 0.1,
            "high": close + 0.2,
            "low": close - 0.2,
            "close": close,
            "volume": 2000000,
        })

    portfolio = {
        "portfolio_id": "TEST_PERF_001",
        "name": "Test",
        "initial_capital": 100000,
        "assets": [
            {"symbol": "AAPL", "weight": 0.5},
            {"symbol": "SPY", "weight": 0.5},
        ],
    }
    params = {
        "portfolio": portfolio,
        "market_data": {
            "AAPL": bars,
            "SPY": bench_bars,
        },
        "start_date": "2026-03-01",
        "end_date": "2026-03-14",
        "benchmark": "SPY",
    }
    code, out = _run(params)
    assert code == 0, f"Expected 0, got {code}, errors: {out.get('errors')}"
    assert out.get("success") is True
    perf = out.get("performance", {})
    assert "period" in perf
    assert "returns" in perf
    assert "drawdown" in perf
    assert "risk" in perf
    assert "benchmark" in perf
    assert "start" in perf["period"]
    assert "end" in perf["period"]
    assert "total_return_pct" in perf["returns"]
    assert "cagr_pct" in perf["returns"]
    assert "max_drawdown_pct" in perf["drawdown"]
    assert "volatility_annual_pct" in perf["risk"]
    assert "sharpe_ratio" in perf["risk"]
    assert perf["benchmark"]["symbol"] == "SPY"


def test_portfolio_id_resolution() -> None:
    """portfolio_id 或 portfolio 均可解析"""
    bars = [
        {"timestamp": f"2026-03-{i+1:02d}T00:00:00Z", "close": 100.0 + i, "open": 99, "high": 101, "low": 98, "volume": 1e6}
        for i in range(14)
    ]
    portfolio = {"initial_capital": 50000, "assets": [{"symbol": "A", "weight": 0.5}, {"symbol": "B", "weight": 0.5}]}
    params = {
        "portfolio": portfolio,
        "market_data": {"A": bars, "B": bars, "SPY": bars},
        "start_date": "2026-03-01",
        "end_date": "2026-03-14",
    }
    code, out = _run(params)
    assert code == 0
    assert out.get("success") is True
    assert "performance" in out


if __name__ == "__main__":
    test_validation_missing_portfolio()
    test_contract_output_with_mock_data()
    test_portfolio_id_resolution()
    print("All tests passed.")
