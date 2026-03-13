#!/usr/bin/env python3
"""
connect_broker: 建立券商连接（IB paper/live）。
契约: system/tools/contracts/connect_broker.yaml
TICKET_20250314_002
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters.broker_store import create_paper_connection

VALID_BROKERS = ("ib",)
VALID_MODES = ("live", "paper")
TIMEOUT_MIN = 1000
TIMEOUT_MAX = 30000


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _validate(params: dict) -> str | None:
    broker = params.get("broker")
    if broker not in VALID_BROKERS:
        return f"broker must be one of {VALID_BROKERS}"
    mode = params.get("mode")
    if mode not in VALID_MODES:
        return f"mode must be one of {VALID_MODES}"
    timeout = params.get("timeout_ms", 5000)
    if not isinstance(timeout, int) or not (TIMEOUT_MIN <= timeout <= TIMEOUT_MAX):
        return f"timeout_ms must be integer between {TIMEOUT_MIN} and {TIMEOUT_MAX}"
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
        out = _std_response(False, error_message=params["_error"], status="failed")
        print(json.dumps(out))
        sys.exit(1)

    err = _validate(params)
    if err:
        out = _std_response(False, error_message=err, status="failed")
        print(json.dumps(out))
        sys.exit(1)

    broker = params["broker"]
    mode = params["mode"]
    timeout_ms = int(params.get("timeout_ms", 5000))

    if mode == "live":
        out = _std_response(
            False,
            error_message="live mode requires IB Gateway/TWS running; use paper mode for testing",
            status="failed",
        )
        print(json.dumps(out))
        sys.exit(1)

    # paper mode
    conn_id, latency_ms = create_paper_connection(broker, timeout_ms)
    out = _std_response(
        True,
        connection_id=conn_id,
        status="connected",
        latency_ms=latency_ms,
    )
    print(json.dumps(out))


if __name__ == "__main__":
    main()
