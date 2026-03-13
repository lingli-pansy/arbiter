"""
最小测试：验证 execution_audit 符合契约。TICKET_20260314_009
"""
import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parent.parent / "impl"
SCRIPT = IMPL_DIR / "execution_audit.py"


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
    """合法输入返回 audit_report 符合契约."""
    inp = {
        "order_plan": {
            "plan_id": "plan_test",
            "total_orders": 2,
            "total_value": 4000,
            "orders": [
                {"order_id": "ord_1", "symbol": "AAPL", "side": "BUY", "quantity": 10, "estimated_price": 150, "estimated_value": 1500},
                {"order_id": "ord_2", "symbol": "TSLA", "side": "SELL", "quantity": 5, "estimated_price": 500, "estimated_value": 2500},
            ],
        },
        "execution_report": {
            "report_id": "exec_test",
            "plan_id": "plan_test",
            "orders": [
                {"order_id": "ord_1", "symbol": "AAPL", "side": "BUY", "quantity": 10, "filled_qty": 7, "avg_fill_price": 150.1, "status": "partial", "slippage": 0.7},
                {"order_id": "ord_2", "symbol": "TSLA", "side": "SELL", "quantity": 5, "filled_qty": 5, "avg_fill_price": 499.5, "status": "filled", "slippage": 2.5},
            ],
            "summary": {"total_orders": 2, "filled_orders": 1, "partial_orders": 1, "total_slippage": 3.2},
        },
    }
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    r = out.get("audit_report")
    assert r is not None
    assert "audit_id" in r
    assert r.get("plan_id") == "plan_test"
    assert "consistency_check" in r
    assert "execution_summary" in r
    assert "anomalies" in r
    assert "audit_trail" in r
    assert "recommendations" in r


def test_anomaly_detection():
    """部分成交和高滑点被正确标记."""
    inp = {
        "order_plan": {"plan_id": "p", "orders": [{"order_id": "o1", "symbol": "A", "quantity": 10, "estimated_value": 1000}]},
        "execution_report": {
            "report_id": "e",
            "orders": [{"order_id": "o1", "symbol": "A", "filled_qty": 5, "quantity": 10, "avg_fill_price": 100, "status": "partial", "slippage": 2.0}],
            "summary": {},
        },
        "audit_config": {"flag_high_slippage": 1.0},
    }
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    anomalies = out["audit_report"]["anomalies"]
    types = [a["type"] for a in anomalies]
    assert "partial_fill" in types
    assert "high_slippage" in types
