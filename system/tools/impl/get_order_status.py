#!/usr/bin/env python3
"""
get_order_status: 查询订单状态。
契约: system/tools/contracts/get_order_status.yaml
TICKET_20250314_003
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters.broker_store import get_order


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _validate(params: dict) -> str | None:
    if not params.get("connection_id") or not str(params["connection_id"]).strip():
        return "connection_id is required"
    if not params.get("order_id") or not str(params["order_id"]).strip():
        return "order_id is required"
    return None


def _std_response(success: bool, **kwargs) -> dict:
    out = {
        "success": success,
        "error_message": kwargs.pop("error_message", ""),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **kwargs,
    }
    return out


def main() -> None:
    if len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        raw = sys.stdin.read()

    params = _parse_input(raw)
    if "_error" in params:
        out = _std_response(False, error_message=params["_error"])
        print(json.dumps(out))
        sys.exit(1)

    err = _validate(params)
    if err:
        out = _std_response(False, error_message=err)
        print(json.dumps(out))
        sys.exit(1)

    conn_id = str(params["connection_id"]).strip()
    order_id = str(params["order_id"]).strip()
    o = get_order(conn_id, order_id)
    if not o:
        out = _std_response(False, error_message=f"order not found: {order_id}")
        print(json.dumps(out))
        sys.exit(1)

    out = _std_response(
        True,
        order_id=order_id,
        ib_order_id=o.get("ib_order_id", ""),
        status=o["status"],
        filled_qty=o["filled_qty"],
        remaining_qty=o["remaining_qty"],
        avg_fill_price=o["avg_fill_price"],
        last_update=o["last_update"],
    )
    print(json.dumps(out))


if __name__ == "__main__":
    main()
