#!/usr/bin/env python3
"""
get_broker_account: 获取券商账户摘要。
契约: system/tools/contracts/get_broker_account.yaml
TICKET_20250314_002
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters.broker_store import get_connection, get_mock_account


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _validate(params: dict) -> str | None:
    conn_id = params.get("connection_id")
    if not conn_id or not isinstance(conn_id, str) or not conn_id.strip():
        return "connection_id is required and must be non-empty"
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

    conn_id = params["connection_id"].strip()
    conn = get_connection(conn_id)
    if not conn:
        out = _std_response(False, error_message=f"connection_id not found: {conn_id}")
        print(json.dumps(out))
        sys.exit(1)

    if conn.get("mode") == "live" and conn.get("account_ids"):
        # Live 连接返回实际账户（连接时获取的 account_ids）
        acc_id = conn.get("verified_account_id") or (conn["account_ids"][0] if conn["account_ids"] else "unknown")
        out = _std_response(
            True,
            account_id=acc_id,
            account_ids=conn.get("account_ids", []),
            cash_balance=None,  # 需 reqAccountSummary 获取，暂不实现
            buying_power=None,
            currency="USD",
        )
    else:
        acc = get_mock_account()
        out = _std_response(
            True,
            account_id=acc["account_id"],
            cash_balance=acc["cash_balance"],
            buying_power=acc["buying_power"],
            currency=acc["currency"],
        )
    print(json.dumps(out))


if __name__ == "__main__":
    main()
