#!/usr/bin/env python3
"""
Live 订单提交验证脚本。TICKET_NT_LIVE_EXECUTION_001
验证：connect_broker (live) → submit_order (mode=live) → get_order_status

用法:
  python validate_live_submit.py           # Paper 模式全链路（无需 IB）
  python validate_live_submit.py --live    # Live 模式（需 IB Gateway 4001）
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
IMPL_DIR = SCRIPTS_DIR.parent / "impl"
VENV_PY = Path(__file__).resolve().parents[3] / ".venv" / "bin" / "python3"


def _check_market_hours() -> tuple[bool, str]:
    """美股交易时间预检。Returns (is_open, message)."""
    sys.path.insert(0, str(IMPL_DIR))
    from adapters.broker_store import is_us_equity_market_open
    return is_us_equity_market_open()


def _run(script: Path, payload: dict) -> tuple[int, dict]:
    python = str(VENV_PY) if VENV_PY.exists() else sys.executable
    r = subprocess.run(
        [python, str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=IMPL_DIR,
        timeout=60,
    )
    out = {}
    if r.stdout:
        try:
            out = json.loads(r.stdout)
        except json.JSONDecodeError:
            out = {"_raw": r.stdout[:500]}
    return r.returncode, out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="Use live mode (requires IB Gateway on 4001)")
    args = ap.parse_args()
    mode = "live" if args.live else "paper"
    port = 4001 if args.live else 4002

    # Live 模式预检：休市时快速返回，避免超时 (TICKET_NT_LIVE_EXECUTION_001_FOLLOWUP_001)
    if args.live:
        sys.path.insert(0, str(IMPL_DIR))
        from adapters.broker_store import is_us_equity_market_open
        is_open, msg = is_us_equity_market_open()
        if not is_open:
            print(json.dumps({
                "ok": False,
                "step": "pre_check",
                "message": msg,
                "hint": "US equities trade Mon-Fri 09:30-16:00 ET",
            }, indent=2))
            sys.exit(1)

    connect_script = IMPL_DIR / "connect_broker.py"
    submit_script = IMPL_DIR / "submit_order.py"
    status_script = IMPL_DIR / "get_order_status.py"
    for s in (connect_script, submit_script, status_script):
        if not s.exists():
            print(json.dumps({"ok": False, "error": f"script_not_found: {s}"}, indent=2))
            sys.exit(1)

    # 1. connect
    _, conn_out = _run(connect_script, {"broker": "ib", "mode": mode, "host": "127.0.0.1", "port": port})
    if not conn_out.get("success"):
        print(json.dumps({
            "ok": False,
            "step": "connect",
            "message": conn_out.get("error_message", "Connect failed"),
            "hint": "Ensure IB Gateway/TWS is running" if args.live else None,
        }, indent=2))
        sys.exit(1)
    conn_id = conn_out["connection_id"]

    # 2. submit (paper: mock fill; live: real IB)
    submit_payload = {
        "connection_id": conn_id,
        "symbol": "AAPL",
        "side": "BUY",
        "quantity": 1,
        "order_type": "MKT",
        "mode": mode,
    }
    _, submit_out = _run(submit_script, submit_payload)
    if not submit_out.get("success"):
        print(json.dumps({
            "ok": False,
            "step": "submit_order",
            "message": submit_out.get("error_message", "Submit failed"),
            "connection_id": conn_id,
        }, indent=2))
        sys.exit(1)
    order_id = submit_out["order_id"]
    ib_order_id = submit_out.get("ib_order_id", "")

    # 3. get_order_status
    _, status_out = _run(status_script, {"connection_id": conn_id, "order_id": order_id})
    if not status_out.get("success"):
        print(json.dumps({
            "ok": False,
            "step": "get_order_status",
            "message": status_out.get("error_message", "Status lookup failed"),
            "order_id": order_id,
        }, indent=2))
        sys.exit(1)

    report = {
        "ok": True,
        "mode": mode,
        "connection_id": conn_id,
        "order_id": order_id,
        "ib_order_id": ib_order_id if mode == "live" else None,
        "status": status_out.get("status"),
        "filled_qty": status_out.get("filled_qty"),
        "avg_fill_price": status_out.get("avg_fill_price"),
        "message": "Live execution chain verified" if mode == "live" else "Paper execution chain verified",
    }
    print(json.dumps(report, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
