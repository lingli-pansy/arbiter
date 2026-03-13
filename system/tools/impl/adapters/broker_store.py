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
from pathlib import Path

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


def create_paper_connection(broker: str, timeout_ms: int) -> tuple[str, int]:
    """Create paper connection, return (connection_id, latency_ms)."""
    conn_id = str(uuid.uuid4())
    start = time.perf_counter()
    data = _load_connections()
    data[conn_id] = {
        "broker": broker,
        "mode": "paper",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _save_connections(data)
    latency_ms = int((time.perf_counter() - start) * 1000)
    return conn_id, latency_ms


def get_connection(connection_id: str) -> dict | None:
    """Get connection by id, or None if not found."""
    data = _load_connections()
    return data.get(connection_id)


def get_mock_account() -> dict:
    return MOCK_ACCOUNT.copy()


def get_mock_positions() -> list:
    return [p.copy() for p in MOCK_POSITIONS]


# --- Order management (TICKET_20250314_003) ---
ORDERS_FILE = STATE_DIR / "broker_orders.json"


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


def get_order(connection_id: str, order_id: str) -> dict | None:
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
