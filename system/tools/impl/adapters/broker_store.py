"""
Broker connection store for paper/live mode.
Stores connection state in system/state/broker_connections.json.
TICKET_20250314_002
"""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

# system/state relative to impl/
STATE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "state"
CONNECTIONS_FILE = STATE_DIR / "broker_connections.json"
MOCK_ACCOUNT = {
    "account_id": "PAPER_001",
    "cash_balance": 100000.0,
    "buying_power": 100000.0,
    "currency": "USD",
}
MOCK_POSITIONS = [
    {"symbol": "SPY", "quantity": 10.0, "avg_cost": 450.0, "market_price": 455.0, "unrealized_pnl": 50.0},
]


def is_us_equity_market_open() -> tuple[bool, str]:
    """
    美股常规交易时间检查 (ET 09:30-16:00, Mon-Fri)。
    TICKET_NT_LIVE_EXECUTION_001_FOLLOWUP_001: 休市时快速返回，避免 IB 提交超时。
    Returns (is_open, message).
    """
    try:
        et = ZoneInfo("America/New_York")
        now = datetime.now(et)
        wd = now.weekday()  # 0=Mon, 6=Sun
        if wd >= 5:
            return False, "Market closed: US equities trade Mon-Fri 09:30-16:00 ET"
        t = now.time()
        from datetime import time as dt_time
        open_t = dt_time(9, 30)
        close_t = dt_time(16, 0)
        if t < open_t:
            return False, "Market closed: US equities open 09:30 ET"
        if t >= close_t:
            return False, "Market closed: US equities close 16:00 ET"
        return True, "Market open"
    except Exception as e:
        return True, ""  # 检查失败时放行，不阻塞


def _ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _load_connections() -> dict:
    _ensure_state_dir()
    if not CONNECTIONS_FILE.exists():
        return {}
    try:
        with open(CONNECTIONS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_connections(data: dict) -> None:
    _ensure_state_dir()
    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _get_ib_managed_accounts(host: str, port: int, client_id: int, timeout_sec: float = 10.0) -> tuple[list[str], str]:
    """查询 IB 当前连接的账户列表。Returns (account_ids, error). error 非空表示失败。"""
    import subprocess
    import sys

    impl_dir = Path(__file__).resolve().parent.parent
    code = f"""
import sys, json
sys.path.insert(0, {repr(str(impl_dir))})
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass
try:
    from ib_insync import IB
    ib = IB()
    ib.connect({repr(host)}, {port}, clientId={client_id}, timeout={timeout_sec})
    accounts = list(ib.managedAccounts()) if ib.managedAccounts() else []
    ib.disconnect()
    print(json.dumps({{"ok": True, "accounts": accounts}}))
except Exception as e:
    print(json.dumps({{"ok": False, "error": str(e)}}))
"""
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=int(timeout_sec) + 5,
            cwd=str(impl_dir),
        )
        raw = (r.stdout or "").strip() or (r.stderr or "").strip()
        try:
            out = json.loads(raw)
        except json.JSONDecodeError:
            return [], raw or "Invalid output"
        if not out.get("ok"):
            return [], out.get("error", "Unknown error")
        return out.get("accounts", []), ""
    except subprocess.TimeoutExpired:
        return [], "Connection timeout"
    except Exception as e:
        return [], str(e)


def _do_connect_in_subprocess(
    host: str, port: int, client_id: int, timeout_sec: float
) -> tuple[bool, str | None]:
    """在独立 subprocess 中执行 IB 连接，避免 Python 3.11+ asyncio 兼容性问题。"""
    import subprocess
    import sys

    impl_dir = Path(__file__).resolve().parent.parent
    code = f"""
import sys
sys.path.insert(0, {repr(str(impl_dir))})
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass
from ib_insync import IB
ib = IB()
ib.connect({repr(host)}, {port}, clientId={client_id}, timeout={timeout_sec})
ib.disconnect()
print("OK")
"""
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout_sec + 10,
            cwd=str(impl_dir),
        )
        if r.returncode == 0 and "OK" in (r.stdout or ""):
            return True, None
        err = (r.stderr or r.stdout or str(r.returncode)).strip().split("\n")[-1] if (r.stderr or r.stdout) else f"exit {r.returncode}"
        return False, err
    except subprocess.TimeoutExpired:
        return False, "Connection timeout"
    except Exception as e:
        return False, str(e)


def _create_ib_connection(
    broker: str,
    host: str,
    port: int,
    client_id: int,
    timeout_ms: int,
    mode: str,
    expected_account_id: str | None = None,
) -> tuple[str, int, str | None]:
    """Connect to IB (live or paper), verify, then disconnect. Returns (connection_id, latency_ms, error)."""
    conn_id = str(uuid.uuid4())
    start = time.perf_counter()
    timeout_sec = timeout_ms / 1000.0

    try:
        ok, err = _do_connect_in_subprocess(host, port, client_id, timeout_sec)
        latency_ms = int((time.perf_counter() - start) * 1000)
        if not ok:
            return "", latency_ms, err or "Connection failed"

        account_ids: list[str] = []
        if mode == "live":
            account_ids, err = _get_ib_managed_accounts(host, port, client_id, timeout_sec)
            if err and expected_account_id:
                return "", latency_ms, f"Could not fetch accounts: {err}"
            if expected_account_id:
                expected = str(expected_account_id).strip()
                if expected and (not account_ids or expected not in account_ids):
                    return "", latency_ms, (
                        f"Account mismatch: expected {expected}, "
                        f"Gateway has {account_ids or 'no accounts'}. "
                        "Ensure IB Gateway is logged into the correct account."
                    )

        data = _load_connections()
        data[conn_id] = {
            "broker": broker,
            "mode": mode,
            "host": host,
            "port": port,
            "client_id": client_id,
            "account_ids": account_ids,
            "verified_account_id": str(expected_account_id).strip() if expected_account_id else None,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        _save_connections(data)
        return conn_id, latency_ms, None
    except ImportError as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return "", latency_ms, f"ib_insync not installed: {e}"
    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        err = str(e)
        if "Connection refused" in err or "connect" in err.lower():
            return "", latency_ms, f"Connection refused: TWS/Gateway not running on {host}:{port}"
        return "", latency_ms, err


def create_live_connection(
    broker: str,
    host: str,
    port: int,
    client_id: int,
    timeout_ms: int,
    expected_account_id: str | None = None,
) -> tuple[str, int, str | None]:
    """Create live IB connection (实盘). expected_account_id 用于验证 Gateway 登录的账户。"""
    return _create_ib_connection(broker, host, port, client_id, timeout_ms, "live", expected_account_id)


def create_paper_connection(
    broker: str,
    host: str,
    port: int,
    client_id: int,
    timeout_ms: int,
) -> tuple[str, int, str | None]:
    """Create IB Paper 账户连接（模拟盘，连 IB Gateway/TWS Paper 端口）. Returns (connection_id, latency_ms, error)."""
    return _create_ib_connection(broker, host, port, client_id, timeout_ms, "paper")


def get_connection(connection_id: str) -> dict | None:
    """Get connection by id, or None if not found."""
    data = _load_connections()
    return data.get(connection_id)


def get_latest_ib_connection() -> dict | None:
    """Get the most recently created IB connection config, or None. For use when connection_id not provided."""
    data = _load_connections()
    candidates = [(cid, cfg) for cid, cfg in data.items() if cfg.get("broker") == "ib"]
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1].get("created_at", ""), reverse=True)
    return candidates[0][1]


def get_mock_account() -> dict:
    return MOCK_ACCOUNT.copy()


def get_mock_positions() -> list:
    return [p.copy() for p in MOCK_POSITIONS]


# --- Order management (TICKET_20250314_003) ---
# TICKET_NT_LIVE_EXECUTION_001: Live 订单持久化
ORDERS_FILE = STATE_DIR / "broker_orders.json"
LIVE_ORDERS_FILE = STATE_DIR / "live_orders.json"


def _load_orders() -> dict:
    _ensure_state_dir()
    if not ORDERS_FILE.exists():
        return {}
    try:
        with open(ORDERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_orders(data: dict) -> None:
    _ensure_state_dir()
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_order(
    connection_id: str,
    symbol: str,
    side: str,
    quantity: float,
    order_type: str,
    limit_price: float | None = None,
    stop_price: float | None = None,
) -> tuple[str, str, float, float]:
    """Create order. Returns (order_id, status, filled_qty, avg_fill_price)."""
    conn = get_connection(connection_id)
    if not conn:
        raise ValueError("connection_id not found")
    order_id = str(uuid.uuid4())
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # Paper: MKT fills immediately at mock price
    mock_price = 450.0
    if order_type == "MKT":
        status, filled_qty, avg_fill = "filled", quantity, mock_price
    else:
        status, filled_qty, avg_fill = "pending", 0.0, 0.0
    orders = _load_orders()
    orders[order_id] = {
        "connection_id": connection_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
        "limit_price": limit_price,
        "stop_price": stop_price,
        "status": status,
        "filled_qty": filled_qty,
        "remaining_qty": quantity - filled_qty,
        "avg_fill_price": avg_fill,
        "created_at": now,
        "last_update": now,
    }
    _save_orders(orders)
    return order_id, status, filled_qty, avg_fill


def _load_live_orders() -> dict:
    _ensure_state_dir()
    if not LIVE_ORDERS_FILE.exists():
        return {}
    try:
        with open(LIVE_ORDERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_live_orders(data: dict) -> None:
    _ensure_state_dir()
    with open(LIVE_ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _place_live_order_subprocess(
    host: str,
    port: int,
    client_id: int,
    symbol: str,
    side: str,
    quantity: float,
    order_type: str,
    limit_price: float | None,
    stop_price: float | None,
) -> str:
    """在 subprocess 中提交 IB 实盘订单，返回 JSON 结果。TICKET_NT_LIVE_EXECUTION_001"""
    import subprocess
    import sys

    impl_dir = Path(__file__).resolve().parent.parent
    params = {
        "host": host,
        "port": port,
        "client_id": client_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
        "limit_price": limit_price,
        "stop_price": stop_price,
    }
    code = f'''
import sys, json
sys.path.insert(0, {repr(str(impl_dir))})
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass
params = {repr(params)}
try:
    from ib_insync import IB, Stock, MarketOrder, LimitOrder, Order
    ib = IB()
    ib.connect(params["host"], params["port"], clientId=params["client_id"], timeout=10)
    contract = Stock(params["symbol"], "SMART", "USD")
    ib.qualifyContracts(contract)
    qty = int(params["quantity"]) if params["quantity"] == int(params["quantity"]) else params["quantity"]
    if params["order_type"] == "MKT":
        order = MarketOrder(params["side"], qty)
    elif params["order_type"] == "LMT":
        order = LimitOrder(params["side"], qty, float(params["limit_price"] or 0))
    else:
        order = Order()
        order.action = params["side"]
        order.orderType = "STP"
        order.totalQuantity = qty
        order.auxPrice = float(params["stop_price"] or 0)
    trade = ib.placeOrder(contract, order)
    ib.run(timeout=5)
    st = trade.orderStatus
    status = getattr(st, "status", "Unknown") or "Unknown"
    filled = float(getattr(st, "filled", 0) or 0)
    avg_fill = float(getattr(st, "avgFillPrice", 0) or 0)
    perm_id = str(trade.order.permId) if trade.order.permId else ""
    order_id = str(trade.order.orderId) if trade.order.orderId else perm_id
    ib.disconnect()
    out = {{"ok": True, "order_id": order_id, "ib_order_id": perm_id, "status": status,
            "filled_qty": filled, "avg_fill_price": avg_fill}}
except Exception as e:
    out = {{"ok": False, "error": str(e)}}
print(json.dumps(out))
'''
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(impl_dir),
        )
        return (r.stdout or "").strip() or (r.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return json.dumps({"ok": False, "error": "Order submission timeout"})
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


def place_live_order(
    connection_id: str,
    symbol: str,
    side: str,
    quantity: float,
    order_type: str,
    limit_price: float | None = None,
    stop_price: float | None = None,
) -> tuple[str, str, str, float, float, str]:
    """
    提交 IB 实盘订单。Returns (order_id, ib_order_id, status, filled_qty, avg_fill_price, error).
    error 非空表示失败。
    """
    conn = get_connection(connection_id)
    if not conn:
        return "", "", "rejected", 0.0, 0.0, "connection_id not found"
    if conn.get("mode") != "live":
        return "", "", "rejected", 0.0, 0.0, "connection is not live mode"
    # 若连接时验证过账户，提交前再次确认 Gateway 仍为该账户（防止中途切换）
    verified = conn.get("verified_account_id")
    if verified:
        host = str(conn.get("host", "127.0.0.1"))
        port = int(conn.get("port", 4001))
        client_id = int(conn.get("client_id", 1))
        accounts, err = _get_ib_managed_accounts(host, port, client_id, 10.0)
        if err:
            return "", "", "rejected", 0.0, 0.0, f"Cannot verify account: {err}"
        if verified not in accounts:
            return "", "", "rejected", 0.0, 0.0, (
                f"Account mismatch: expected {verified}, Gateway has {accounts}. "
                "Ensure IB Gateway is logged into the correct account."
            )
    is_open, msg = is_us_equity_market_open()
    if not is_open:
        return "", "", "rejected", 0.0, 0.0, msg
    host = str(conn.get("host", "127.0.0.1"))
    port = int(conn.get("port", 4001))
    client_id = int(conn.get("client_id", 1))
    raw = _place_live_order_subprocess(
        host, port, client_id, symbol, side, quantity,
        order_type, limit_price, stop_price,
    )
    try:
        res = json.loads(raw)
    except json.JSONDecodeError:
        return "", "", "rejected", 0.0, 0.0, raw or "Invalid subprocess output"
    if not res.get("ok"):
        return "", "", "rejected", 0.0, 0.0, res.get("error", "Unknown error")
    order_id = str(uuid.uuid4())
    ib_order_id = res.get("ib_order_id", "")
    status = res.get("status", "submitted")
    filled_qty = float(res.get("filled_qty", 0))
    avg_fill = float(res.get("avg_fill_price", 0))
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # 映射 IB 状态到统一格式
    ib_to_status = {
        "Submitted": "submitted",
        "PreSubmitted": "submitted",
        "ApiSubmitted": "submitted",
        "Filled": "filled",
        "Cancelled": "cancelled",
        "Canceled": "cancelled",
        "Rejected": "rejected",
        "Inactive": "rejected",
    }
    status = ib_to_status.get(status, status.lower() if status else "submitted")
    orders = _load_live_orders()
    orders[order_id] = {
        "connection_id": connection_id,
        "ib_order_id": ib_order_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
        "limit_price": limit_price,
        "stop_price": stop_price,
        "status": status,
        "filled_qty": filled_qty,
        "remaining_qty": quantity - filled_qty,
        "avg_fill_price": avg_fill,
        "created_at": now,
        "last_update": now,
    }
    _save_live_orders(orders)
    return order_id, ib_order_id, status, filled_qty, avg_fill, ""


def get_order(connection_id: str, order_id: str) -> dict | None:
    conn = get_connection(connection_id)
    if conn and conn.get("mode") == "live":
        orders = _load_live_orders()
        o = orders.get(order_id)
        if o and o.get("connection_id") == connection_id:
            return o
    orders = _load_orders()
    o = orders.get(order_id)
    if not o or o.get("connection_id") != connection_id:
        return None
    return o


def cancel_order_record(connection_id: str, order_id: str) -> str:
    """Cancel order. Returns status: cancelled, already_filled, or rejected."""
    orders = _load_orders()
    o = orders.get(order_id)
    if not o or o.get("connection_id") != connection_id:
        return "rejected"
    if o.get("status") == "filled":
        return "already_filled"
    o["status"] = "cancelled"
    o["last_update"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    orders[order_id] = o
    _save_orders(orders)
    return "cancelled"
