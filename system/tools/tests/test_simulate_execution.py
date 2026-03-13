"""
最小测试：验证 simulate_execution 输出符合契约（TICKET_20260314_002）。
"""
import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parent.parent / "impl"
SCRIPT = IMPL_DIR / "simulate_execution.py"


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


def test_contract_output_structure():
    """合法 order_plan 返回 execution_report 符合契约."""
    order_plan = {
        "plan_id": "plan_test",
        "created_at": "2026-03-14T00:00:00Z",
        "total_orders": 2,
        "total_value": 5000,
        "orders": [
            {"order_id": "ord_1", "symbol": "AAPL", "side": "BUY", "quantity": 10, "estimated_price": 150},
            {"order_id": "ord_2", "symbol": "NVDA", "side": "SELL", "quantity": 5, "estimated_price": 100},
        ],
    }
    code, out = _run([json.dumps({"order_plan": order_plan})])
    assert "success" in out
    assert out.get("success") is True
    assert "execution_report" in out
    er = out["execution_report"]
    assert "report_id" in er
    assert er.get("plan_id") == "plan_test"
    assert "executed_at" in er
    assert "orders" in er
    assert len(er["orders"]) == 2
    assert "summary" in er
    s = er["summary"]
    assert s.get("total_orders") == 2
    assert s.get("filled_orders") + s.get("partial_orders", 0) + s.get("rejected_orders", 0) == 2
    assert "slippage" in er["orders"][0]
    assert "filled_qty" in er["orders"][0]
    assert "avg_fill_price" in er["orders"][0]
    assert "status" in er["orders"][0]


def test_slippage_percentage():
    """slippage_model percentage 产生非零 slippage."""
    order_plan = {
        "plan_id": "plan_slip",
        "orders": [{"order_id": "o1", "symbol": "AAPL", "side": "BUY", "quantity": 100, "estimated_price": 100}],
    }
    cfg = {"slippage_model": "percentage", "slippage_value": 0.5}
    code, out = _run([json.dumps({"order_plan": order_plan, "simulation_config": cfg})])
    assert out.get("success") is True
    assert out["execution_report"]["orders"][0]["slippage"] != 0
    assert out["execution_report"]["summary"]["total_slippage"] != 0


def test_validation_missing_order_plan():
    """缺少 order_plan 返回错误."""
    code, out = _run([json.dumps({})])
    assert code != 0 or out.get("success") is False
    assert "errors" in out and len(out["errors"]) >= 1
