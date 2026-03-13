#!/usr/bin/env python3
"""run_backtest 最小测试 - 验证契约与输出结构"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"
SCRIPT = IMPL_DIR / "run_backtest.py"


def _run(params: dict) -> tuple[int, dict]:
    raw = json.dumps(params)
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=raw.encode(),
        capture_output=True,
        timeout=60,
        cwd=str(IMPL_DIR),
    )
    out = {}
    if r.stdout:
        text = r.stdout.decode()
        try:
            out = json.loads(text)
        except json.JSONDecodeError:
            # NT 可能将日志打到 stdout，JSON 在最后一行
            for line in reversed(text.strip().split("\n")):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        out = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
            if not out:
                out = {"_raw": text[:500]}
    return r.returncode, out


def test_validation_missing_strategy_id() -> None:
    """缺少 strategy_id 时应返回错误"""
    params = {
        "nt_bars": {"data": {"AAPL": []}, "meta": {}},
    }
    code, out = _run(params)
    assert code != 0 or out.get("success") is False
    assert "strategy_id" in str(out.get("errors", [])).lower() or "nt_bars" in str(out.get("errors", [])).lower()


def test_validation_missing_nt_bars() -> None:
    """缺少 nt_bars 时应返回错误"""
    params = {"strategy_id": "momentum_20d"}
    code, out = _run(params)
    assert code != 0 or out.get("success") is False


def test_contract_output_structure() -> None:
    """有效输入应返回符合契约的输出结构"""
    nt_bars = {
        "data": {
            "AAPL": [
                {
                    "bar_type": "AAPL.NASDAQ-1-DAY-LAST",
                    "open": "185.0",
                    "high": "187.5",
                    "low": "184.2",
                    "close": "186.8",
                    "volume": "52000000",
                    "ts_event": 1704067200000000000,
                    "ts_init": 1704067200000000000,
                    "is_revision": False,
                }
                for i in range(25)
            ],
        },
        "meta": {"timeframe": "1d", "timeframe_nt": "1-DAY"},
    }
    for i, b in enumerate(nt_bars["data"]["AAPL"]):
        b["ts_event"] = 1704067200000000000 + i * 86400 * 1_000_000_000
        b["ts_init"] = b["ts_event"]
    params = {
        "strategy_id": "momentum_20d",
        "nt_bars": nt_bars,
        "symbols": ["AAPL"],
    }
    code, out = _run(params)
    assert code == 0, f"Expected 0, got {code}, stderr/out: {out}"
    assert out.get("success") is True
    assert "report" in out
    assert "meta" in out
    assert "strategy_id" in out["meta"]
    assert "bars_loaded" in out["meta"]
    assert out["meta"]["status"] in ("completed", "failed")
    report = out.get("report", {})
    assert "account_summary" in report or "order_fills" in report or "positions" in report
