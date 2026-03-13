#!/usr/bin/env python3
"""
simulate_execution: 模拟订单执行，生成执行报告。
契约: system/tools/contracts/simulate_execution.yaml
输入: JSON 从 stdin 或第一个命令行参数读取。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
import random
import sys
import uuid
from datetime import datetime, timezone


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _extract_order_plan(params: dict) -> dict | None:
    """提取 order_plan，支持 generate_order_plan 完整输出或 order_plan 对象."""
    op = params.get("order_plan")
    if isinstance(op, dict) and op.get("orders") is not None:
        return op
    # 可能传入的是 generate_order_plan 的完整输出
    out = params.get("order_plan")
    if isinstance(out, dict) and "order_plan" in out:
        return out["order_plan"]
    return None


def _apply_slippage(estimated_price: float, side: str, slippage_model: str, slippage_value: float) -> tuple[float, float]:
    """
    计算成交价和滑点。
    返回 (avg_fill_price, slippage_per_share)
    - BUY: 滑点使成交价升高（不利）
    - SELL: 滑点使成交价降低（不利）
    """
    if slippage_model == "none" or slippage_value == 0:
        return estimated_price, 0.0

    if slippage_model == "fixed":
        slip_per_share = slippage_value
    elif slippage_model == "percentage":
        slip_per_share = estimated_price * (slippage_value / 100.0)
    else:
        slip_per_share = 0.0

    # 不利方向：BUY 时成交价更高，SELL 时成交价更低
    if side == "BUY":
        fill_price = estimated_price + slip_per_share
    else:
        fill_price = max(0.01, estimated_price - slip_per_share)

    return round(fill_price, 4), round(slip_per_share, 4)


def _simulate_fill(
    order: dict,
    fill_model: str,
    slippage_model: str,
    slippage_value: float,
) -> tuple[int, float, float, str]:
    """
    模拟单笔订单成交。
    返回 (filled_qty, avg_fill_price, slippage_total, status)
    """
    quantity = int(order.get("quantity", 0))
    est_price = float(order.get("estimated_price", 0))
    side = str(order.get("side", "BUY")).upper()

    if quantity <= 0:
        return 0, 0.0, 0.0, "rejected"

    fill_price, slip_per_share = _apply_slippage(est_price, side, slippage_model, slippage_value)

    if fill_model == "immediate":
        filled_qty = quantity
        status = "filled"
    elif fill_model == "partial":
        # 70–100% 随机成交
        pct = random.uniform(0.7, 1.0)
        filled_qty = max(1, int(quantity * pct))
        status = "partial" if filled_qty < quantity else "filled"
    elif fill_model == "random_delay":
        # 模拟延迟：仍全部成交，但滑点可能略增
        filled_qty = quantity
        status = "filled"
        if slippage_model == "none" and slippage_value == 0:
            # 随机微小滑点
            jitter = random.uniform(-0.001, 0.001) * est_price
            fill_price = max(0.01, fill_price + jitter)
            slip_per_share = abs(jitter)
    else:
        filled_qty = quantity
        status = "filled"

    slippage_total = slip_per_share * filled_qty
    return filled_qty, fill_price, round(slippage_total, 4), status


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)

    if "_error" in params:
        out = {
            "success": False,
            "execution_report": None,
            "errors": [params["_error"]],
        }
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    order_plan = _extract_order_plan(params)
    if not order_plan or not isinstance(order_plan.get("orders"), list):
        out = {
            "success": False,
            "execution_report": None,
            "errors": ["order_plan with orders array is required"],
        }
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    cfg = params.get("simulation_config") or {}
    fill_model = cfg.get("fill_model", "immediate")
    slippage_model = cfg.get("slippage_model", "none")
    slippage_value = float(cfg.get("slippage_value", 0))

    if fill_model not in ("immediate", "partial", "random_delay"):
        fill_model = "immediate"
    if slippage_model not in ("none", "fixed", "percentage"):
        slippage_model = "none"

    plan_id = order_plan.get("plan_id", "unknown")
    report_id = f"exec_{uuid.uuid4().hex[:12]}"
    executed_at = datetime.now(timezone.utc).isoformat()

    exec_orders = []
    filled_count = 0
    partial_count = 0
    rejected_count = 0
    total_slippage = 0.0

    for ord_in in order_plan["orders"]:
        filled_qty, avg_fill_price, slippage_total, status = _simulate_fill(
            ord_in, fill_model, slippage_model, slippage_value
        )
        if status == "filled":
            filled_count += 1
        elif status == "partial":
            partial_count += 1
        else:
            rejected_count += 1

        total_slippage += slippage_total

        exec_orders.append({
            "order_id": ord_in.get("order_id", ""),
            "symbol": ord_in.get("symbol", ""),
            "side": ord_in.get("side", "BUY"),
            "quantity": int(ord_in.get("quantity", 0)),
            "filled_qty": filled_qty,
            "avg_fill_price": round(avg_fill_price, 4),
            "status": status,
            "slippage": round(slippage_total, 4),
            "timestamp": executed_at,
        })

    execution_report = {
        "report_id": report_id,
        "plan_id": plan_id,
        "executed_at": executed_at,
        "orders": exec_orders,
        "summary": {
            "total_orders": len(exec_orders),
            "filled_orders": filled_count,
            "partial_orders": partial_count,
            "rejected_orders": rejected_count,
            "total_slippage": round(total_slippage, 4),
        },
    }

    out = {
        "success": True,
        "execution_report": execution_report,
        "errors": [],
    }
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
