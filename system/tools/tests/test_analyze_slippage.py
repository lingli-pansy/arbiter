"""
最小测试：验证 analyze_slippage 符合契约。TICKET_20260314_008
"""
import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parent.parent / "impl"
SCRIPT = IMPL_DIR / "analyze_slippage.py"


def _run(args: list[str], stdin: str | None = None) -> tuple[int, dict]:
    cmd = [sys.executable, str(SCRIPT)] + args
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=IMPL_DIR, input=stdin)
    out = {}
    if r.stdout:
        try:
            out = json.loads(r.stdout)
        except json.JSONDecodeError:
            out = {"_raw": r.stdout, "_stderr": r.stderr}
    return r.returncode, out


def test_contract_output():
    """合法 execution_report 返回 slippage_report 符合契约."""
    er = {
        "report_id": "exec_test",
        "plan_id": "plan_test",
        "orders": [
            {"order_id": "ord_1", "symbol": "AAPL", "side": "BUY", "quantity": 10, "filled_qty": 7,
             "avg_fill_price": 150.075, "status": "partial", "slippage": 0.525},
            {"order_id": "ord_2", "symbol": "NVDA", "side": "BUY", "quantity": 5, "filled_qty": 4,
             "avg_fill_price": 500.25, "status": "partial", "slippage": 1.0},
        ],
        "summary": {"total_orders": 2, "total_slippage": 1.525},
    }
    inp = {"execution_report": er, "analysis_config": {"high_slippage_threshold": 0.8}}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    r = out.get("slippage_report")
    assert r is not None
    assert "report_id" in r
    assert r.get("source_execution_report") == "exec_test"
    assert "summary" in r
    s = r["summary"]
    assert s["total_orders"] == 2
    assert s["analyzed_orders"] == 2
    assert s["total_slippage"] == 1.525
    assert "by_symbol" in r
    assert "by_side" in r
    assert "high_slippage_orders" in r


def test_high_slippage_detection():
    """高滑点阈值检测正确."""
    er = {
        "report_id": "exec_h",
        "orders": [
            {"order_id": "o1", "symbol": "AAPL", "side": "BUY", "slippage": 0.5, "filled_qty": 10, "avg_fill_price": 100},
            {"order_id": "o2", "symbol": "NVDA", "side": "BUY", "slippage": 2.0, "filled_qty": 5, "avg_fill_price": 500},
        ],
        "summary": {},
    }
    inp = {"execution_report": er, "analysis_config": {"high_slippage_threshold": 1.0}}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    high = out["slippage_report"]["high_slippage_orders"]
    assert len(high) == 1
    assert high[0]["symbol"] == "NVDA" and high[0]["slippage"] == 2.0
