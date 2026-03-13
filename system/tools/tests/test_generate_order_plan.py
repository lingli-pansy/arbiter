"""
最小测试：验证 generate_order_plan 输出符合契约（TICKET_20260314_001）。
"""
import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parent.parent / "impl"
SCRIPT = IMPL_DIR / "generate_order_plan.py"


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


def test_ticket_case():
    """TICKET_20260314_001 测试用例：2 个订单，risk_limits 通过，validations 全部通过."""
    payload = {
        "rebalance_proposal": {
            "trades": [
                {
                    "symbol": "AAPL",
                    "action": "buy",
                    "delta_weight": 0.33,
                    "estimated_shares": 16,
                    "estimated_value": 3333.33,
                },
                {
                    "symbol": "NVDA",
                    "action": "sell",
                    "delta_weight": -0.33,
                    "estimated_shares": -20,
                    "estimated_value": -3333.33,
                },
            ]
        },
        "portfolio_value": 10000,
        "execution_strategy": "market",
        "risk_limits": {
            "max_order_value": 5000,
            "max_single_order_pct": 0.5,
        },
    }
    code, out = _run([json.dumps(payload)])
    assert code == 0
    assert out.get("success") is True
    plan = out.get("order_plan", {})
    assert plan.get("total_orders") == 2
    orders = plan.get("orders", [])
    assert len(orders) == 2
    sides = {o["symbol"]: o["side"] for o in orders}
    assert sides.get("AAPL") == "BUY"
    assert sides.get("NVDA") == "SELL"
    qty = {o["symbol"]: o["quantity"] for o in orders}
    assert qty.get("AAPL") == 16
    assert qty.get("NVDA") == 20
    validations = out.get("validations", [])
    assert all(v.get("passed") for v in validations)
    assert "plan_id" in plan
    assert "created_at" in plan


def test_simulate_rebalance_output_format():
    """支持 simulate_rebalance 输出格式（trades 在 rebalance 下）."""
    payload = {
        "rebalance_proposal": {
            "rebalance": {
                "trades": [
                    {"symbol": "MSFT", "action": "BUY", "delta_weight": 0.1, "estimated_shares": 5, "estimated_value": 2000},
                ]
            }
        },
        "portfolio_value": 20000,
    }
    code, out = _run([json.dumps(payload)])
    assert code == 0
    assert out.get("success") is True
    assert out["order_plan"]["total_orders"] == 1
    assert out["order_plan"]["orders"][0]["symbol"] == "MSFT"
    assert out["order_plan"]["orders"][0]["quantity"] == 5


def test_validation_missing_params():
    """缺少 rebalance_proposal 或 portfolio_value 时返回错误."""
    code1, out1 = _run([json.dumps({"portfolio_value": 10000})])
    assert code1 != 0 or out1.get("success") is False
    assert "rebalance_proposal" in (out1.get("errors", [""])[0] or "").lower()

    code2, out2 = _run([json.dumps({"rebalance_proposal": {"trades": []}})])
    assert code2 != 0 or out2.get("success") is False
    assert "portfolio_value" in (out2.get("errors", [""])[0] or "").lower()
