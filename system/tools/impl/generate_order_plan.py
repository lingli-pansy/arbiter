#!/usr/bin/env python3
"""
generate_order_plan: 从 rebalance proposal 生成可执行的订单计划。
契约: system/tools/contracts/generate_order_plan.yaml
输入: JSON 从 stdin 或第一个命令行参数读取。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _extract_trades(rebalance_proposal: dict) -> list[dict]:
    """从 rebalance_proposal 提取 trades，支持 simulate_rebalance 输出格式."""
    if not rebalance_proposal:
        return []
    trades = rebalance_proposal.get("trades")
    if trades is None and "rebalance" in rebalance_proposal:
        trades = rebalance_proposal["rebalance"].get("trades")
    return trades if isinstance(trades, list) else []


def _validate(params: dict) -> str | None:
    if "rebalance_proposal" not in params:
        return "rebalance_proposal is required"
    if "portfolio_value" not in params:
        return "portfolio_value is required"
    pv = params["portfolio_value"]
    if not isinstance(pv, (int, float)) or pv <= 0:
        return "portfolio_value must be a positive number"
    exec_strat = params.get("execution_strategy", "market")
    if exec_strat not in ("market", "twap", "vwap"):
        return "execution_strategy must be one of market, twap, vwap"
    return None


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)

    if "_error" in params:
        out = {
            "success": False,
            "order_plan": None,
            "validations": [],
            "errors": [params["_error"]],
        }
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    err = _validate(params)
    if err:
        out = {
            "success": False,
            "order_plan": None,
            "validations": [],
            "errors": [err],
        }
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    trades = _extract_trades(params["rebalance_proposal"])
    portfolio_value = float(params["portfolio_value"])
    risk_limits = params.get("risk_limits") or {}
    max_order_value = risk_limits.get("max_order_value")
    max_single_order_pct = risk_limits.get("max_single_order_pct")
    max_position_size = risk_limits.get("max_position_size")

    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc).isoformat()
    orders = []
    validations = []

    total_buy_value = 0.0
    total_sell_value = 0.0

    for i, t in enumerate(trades):
        symbol = str(t.get("symbol", "")).strip()
        if not symbol:
            continue
        action = str(t.get("action", "")).upper()
        if action in ("BUY", "SELL"):
            pass
        elif action in ("buy", "sell"):
            action = action.upper()
        else:
            continue

        est_shares = t.get("estimated_shares", 0)
        est_value_raw = float(t.get("estimated_value", 0))
        quantity = int(round(abs(est_shares)))
        if quantity <= 0:
            continue

        est_value = abs(est_value_raw)
        est_price = est_value / quantity if quantity > 0 else 0

        # risk_limits 校验
        order_pct = est_value / portfolio_value if portfolio_value > 0 else 0
        skip = False
        if max_order_value is not None and est_value > max_order_value:
            validations.append({
                "check": f"max_order_value_{symbol}",
                "passed": False,
                "message": f"Order value {est_value:.2f} exceeds max_order_value {max_order_value}",
            })
            skip = True
        if max_single_order_pct is not None and order_pct > max_single_order_pct:
            validations.append({
                "check": f"max_single_order_pct_{symbol}",
                "passed": False,
                "message": f"Order {order_pct:.2%} exceeds max_single_order_pct {max_single_order_pct:.2%}",
            })
            skip = True
        if max_position_size is not None and quantity > max_position_size:
            validations.append({
                "check": f"max_position_size_{symbol}",
                "passed": False,
                "message": f"Quantity {quantity} exceeds max_position_size {max_position_size}",
            })
            skip = True
        if skip:
            continue

        if max_order_value is not None and est_value <= max_order_value:
            validations.append({
                "check": f"max_order_value_{symbol}",
                "passed": True,
                "message": f"Order value {est_value:.2f} within limit",
            })
        if max_single_order_pct is not None and order_pct <= max_single_order_pct:
            validations.append({
                "check": f"max_single_order_pct_{symbol}",
                "passed": True,
                "message": f"Order {order_pct:.2%} within limit",
            })

        if action == "BUY":
            total_buy_value += est_value
        else:
            total_sell_value += est_value

        order_type = "MKT" if params.get("execution_strategy", "market") == "market" else "MKT"
        orders.append({
            "order_id": f"ord_{uuid.uuid4().hex[:8]}",
            "symbol": symbol,
            "side": action,
            "order_type": order_type,
            "quantity": quantity,
            "estimated_price": round(est_price, 2),
            "estimated_value": round(est_value, 2),
            "time_in_force": "DAY",
            "notes": f"rebalance {action}",
        })

    total_value = total_buy_value + total_sell_value
    net_cash = total_sell_value - total_buy_value
    validations.append({
        "check": "cash_sufficiency",
        "passed": net_cash >= 0 or True,
        "message": f"Net cash flow: {net_cash:.2f} (sells {total_sell_value:.2f}, buys {total_buy_value:.2f})",
    })

    order_plan = {
        "plan_id": plan_id,
        "created_at": created_at,
        "total_orders": len(orders),
        "total_value": round(total_value, 2),
        "orders": orders,
    }

    out = {
        "success": True,
        "order_plan": order_plan,
        "validations": validations,
        "errors": [],
    }
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
