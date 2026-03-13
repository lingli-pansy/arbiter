"""
最小测试：验证 broker adapter 工具输出符合契约（TICKET_20250314_002）。
- connect_broker: paper 模式建立连接，返回 connection_id、status=connected、latency_ms<2000
- get_broker_account: 返回 account_id、cash_balance、buying_power、currency
- get_broker_positions: 返回 positions 数组
"""
import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parent.parent / "impl"
CONNECT_SCRIPT = IMPL_DIR / "connect_broker.py"
ACCOUNT_SCRIPT = IMPL_DIR / "get_broker_account.py"
POSITIONS_SCRIPT = IMPL_DIR / "get_broker_positions.py"


def _run(script: Path, payload: dict, stdin: str | None = None) -> tuple[int, dict]:
    args = [json.dumps(payload)] if payload else []
    cmd = [sys.executable, str(script)] + args
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=IMPL_DIR, input=stdin)
    out = {}
    if r.stdout:
        try:
            out = json.loads(r.stdout)
        except json.JSONDecodeError:
            out = {"_raw": r.stdout, "_stderr": r.stderr}
    return r.returncode, out


def test_connect_broker_paper():
    """connect_broker paper 模式应返回 connected 且 latency_ms < 2000."""
    payload = {"broker": "ib", "mode": "paper"}
    code, out = _run(CONNECT_SCRIPT, payload)
    assert out.get("success") is True
    assert out.get("status") == "connected"
    assert "connection_id" in out and len(out["connection_id"]) > 0
    assert out.get("latency_ms", 9999) < 2000
    assert "timestamp" in out
    return out.get("connection_id")


def test_get_broker_account(connection_id: str):
    """get_broker_account 应返回账户摘要."""
    payload = {"connection_id": connection_id}
    code, out = _run(ACCOUNT_SCRIPT, payload)
    assert out.get("success") is True
    assert "account_id" in out
    assert "cash_balance" in out and out["cash_balance"] >= 0
    assert "buying_power" in out
    assert "currency" in out


def test_get_broker_positions(connection_id: str):
    """get_broker_positions 应返回 positions 数组."""
    payload = {"connection_id": connection_id}
    code, out = _run(POSITIONS_SCRIPT, payload)
    assert out.get("success") is True
    assert "positions" in out and isinstance(out["positions"], list)
    for p in out["positions"][:1]:
        assert "symbol" in p and "quantity" in p and "avg_cost" in p


def test_connect_broker_live_returns_failed():
    """live 模式应返回 failed（未实现实盘连接）."""
    payload = {"broker": "ib", "mode": "live"}
    code, out = _run(CONNECT_SCRIPT, payload)
    assert out.get("success") is False
    assert out.get("status") == "failed"
    assert "error_message" in out


def test_get_broker_account_invalid_connection():
    """无效 connection_id 应返回错误."""
    payload = {"connection_id": "invalid-uuid-xxx"}
    code, out = _run(ACCOUNT_SCRIPT, payload)
    assert out.get("success") is False
    assert "error_message" in out


# --- Order management (TICKET_20250314_003) ---
SUBMIT_SCRIPT = IMPL_DIR / "submit_order.py"
STATUS_SCRIPT = IMPL_DIR / "get_order_status.py"
CANCEL_SCRIPT = IMPL_DIR / "cancel_order.py"


def test_submit_order_mkt(connection_id: str):
    """MKT 订单在 paper 模式应立即成交."""
    payload = {
        "connection_id": connection_id,
        "symbol": "SPY",
        "side": "BUY",
        "quantity": 10,
        "order_type": "MKT",
    }
    code, out = _run(SUBMIT_SCRIPT, payload)
    assert out.get("success") is True
    assert "order_id" in out and len(out["order_id"]) > 0
    assert out.get("status") == "filled"
    assert out.get("filled_qty") == 10
    assert out.get("avg_fill_price") > 0
    return out.get("order_id")


def test_get_order_status(connection_id: str, order_id: str):
    """get_order_status 应返回订单详情."""
    payload = {"connection_id": connection_id, "order_id": order_id}
    code, out = _run(STATUS_SCRIPT, payload)
    assert out.get("success") is True
    assert out.get("order_id") == order_id
    assert out.get("status") == "filled"
    assert "last_update" in out


def test_submit_order_lmt_and_cancel(connection_id: str):
    """LMT 订单可提交，cancel_order 可撤销."""
    payload = {
        "connection_id": connection_id,
        "symbol": "SPY",
        "side": "BUY",
        "quantity": 5,
        "order_type": "LMT",
        "limit_price": 440,
    }
    code, out = _run(SUBMIT_SCRIPT, payload)
    assert out.get("success") is True
    oid = out.get("order_id")
    cancel_payload = {"connection_id": connection_id, "order_id": oid}
    code2, out2 = _run(CANCEL_SCRIPT, cancel_payload)
    assert out2.get("success") is True
    assert out2.get("status") == "cancelled"


if __name__ == "__main__":
    conn_id = test_connect_broker_paper()
    test_get_broker_account(conn_id)
    test_get_broker_positions(conn_id)
    test_connect_broker_live_returns_failed()
    test_get_broker_account_invalid_connection()
    order_id = test_submit_order_mkt(conn_id)
    test_get_order_status(conn_id, order_id)
    test_submit_order_lmt_and_cancel(conn_id)
    print("All broker adapter and order management tests passed.")
