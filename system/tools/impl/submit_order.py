#!/usr/bin/env python3
"""
submit_order: 提交订单。
契约: system/tools/contracts/submit_order.yaml
TICKET_20250314_003
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters.broker_store import create_order, place_live_order

VALID_SIDES = ("BUY", "SELL")
VALID_ORDER_TYPES = ("MKT", "LMT", "STP")
VALID_MODES = ("paper", "live")


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _validate(params: dict) -> str | None:
    if not params.get("connection_id") or not str(params["connection_id"]).strip():
        return "connection_id is required"
    if not params.get("symbol") or not str(params["symbol"]).strip():
        return "symbol is required"
    side = params.get("side")
    if side not in VALID_SIDES:
        return f"side must be one of {VALID_SIDES}"
    qty = params.get("quantity")
    if not isinstance(qty, (int, float)) or qty <= 0:
        return "quantity must be positive number"
    ot = params.get("order_type")
    if ot not in VALID_ORDER_TYPES:
        return f"order_type must be one of {VALID_ORDER_TYPES}"
    mode = params.get("mode", "paper")
    if mode not in VALID_MODES:
        return f"mode must be one of {VALID_MODES}"
    if ot == "LMT" and (params.get("limit_price") is None or params.get("limit_price") <= 0):
        return "limit_price required for LMT orders"
    if ot == "STP" and (params.get("stop_price") is None or params.get("stop_price") <= 0):
        return "stop_price required for STP orders"
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
    mode = str(params.get("mode", "paper")).strip()
    try:
        if mode == "live":
            order_id, ib_order_id, status, filled_qty, avg_fill, err = place_live_order(
                connection_id=conn_id,
                symbol=str(params["symbol"]).strip(),
                side=params["side"],
                quantity=float(params["quantity"]),
                order_type=params["order_type"],
                limit_price=params.get("limit_price"),
                stop_price=params.get("stop_price"),
            )
            if err:
                out = _std_response(False, error_message=err)
                print(json.dumps(out))
                sys.exit(1)
            out = _std_response(
                True,
                order_id=order_id,
                ib_order_id=ib_order_id,
                status=status,
                filled_qty=filled_qty,
                avg_fill_price=avg_fill,
            )
        else:
            order_id, status, filled_qty, avg_fill = create_order(
                connection_id=conn_id,
                symbol=str(params["symbol"]).strip(),
                side=params["side"],
                quantity=float(params["quantity"]),
                order_type=params["order_type"],
                limit_price=params.get("limit_price"),
                stop_price=params.get("stop_price"),
            )
            out = _std_response(
                True,
                order_id=order_id,
                status=status,
                filled_qty=filled_qty,
                avg_fill_price=avg_fill,
            )
        print(json.dumps(out))
    except ValueError as e:
        out = _std_response(False, error_message=str(e))
        print(json.dumps(out))
        sys.exit(1)


if __name__ == "__main__":
    main()
