#!/usr/bin/env python3
"""
cancel_order: 撤销订单。
契约: system/tools/contracts/cancel_order.yaml
TICKET_20250314_003
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters.broker_store import cancel_order_record


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
    status = cancel_order_record(conn_id, order_id)
    if status == "rejected":
        out = _std_response(False, error_message=f"order not found or wrong connection: {order_id}", order_id=order_id, status=status)
        print(json.dumps(out))
        sys.exit(1)

    out = _std_response(True, order_id=order_id, status=status)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
