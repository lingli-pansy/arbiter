#!/usr/bin/env python3
"""
execution_audit: 汇总执行全流程数据，验证一致性，生成审计报告。
契约: system/tools/contracts/execution_audit.yaml
TICKET_20260314_009
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


def _extract_order_plan(params: dict) -> dict | None:
    op = params.get("order_plan")
    if isinstance(op, dict) and op.get("orders") is not None:
        return op
    if isinstance(op, dict) and "order_plan" in op:
        return op.get("order_plan")
    return None


def _extract_execution_report(params: dict) -> dict | None:
    er = params.get("execution_report")
    if isinstance(er, dict) and er.get("orders") is not None:
        return er
    out = params.get("execution_report")
    if isinstance(out, dict) and "execution_report" in out:
        return out["execution_report"]
    return None


def _extract_slippage_report(params: dict) -> dict | None:
    sr = params.get("slippage_report")
    if isinstance(sr, dict):
        return sr
    out = params.get("slippage_report")
    if isinstance(out, dict) and "slippage_report" in out:
        return out["slippage_report"]
    return None


def _audit(
    order_plan: dict,
    execution_report: dict,
    slippage_report: dict | None,
    check_consistency: bool,
    flag_partial_fills: bool,
    flag_high_slippage: float,
) -> dict:
    plan_orders = order_plan.get("orders") or []
    plan_id = order_plan.get("plan_id", "unknown")
    exec_orders = execution_report.get("orders") or []
    exec_id = execution_report.get("report_id", "unknown")
    exec_summary = execution_report.get("summary") or {}

    plan_by_id = {o.get("order_id"): o for o in plan_orders}
    exec_by_id = {o.get("order_id"): o for o in exec_orders}

    total_planned_value = sum(float(o.get("estimated_value", 0) or 0) for o in plan_orders)
    total_executed_value = sum(
        int(o.get("filled_qty", 0)) * float(o.get("avg_fill_price", 0))
        for o in exec_orders
    )
    total_planned_qty = sum(int(o.get("quantity", 0)) for o in plan_orders)
    total_filled_qty = sum(int(o.get("filled_qty", 0)) for o in exec_orders)
    fill_quantity_rate = total_filled_qty / total_planned_qty if total_planned_qty else 0

    plan_orders_match = len(plan_orders) == len(exec_orders)
    plan_value_match = abs(total_planned_value - total_executed_value) < 0.01
    all_orders_accounted = set(plan_by_id) == set(exec_by_id)
    discrepancies = []
    if not plan_orders_match:
        discrepancies.append("Order count mismatch: plan vs execution")
    if not plan_value_match:
        discrepancies.append("Executed value differs from planned")
    if not all_orders_accounted:
        missing = set(plan_by_id) - set(exec_by_id)
        extra = set(exec_by_id) - set(plan_by_id)
        if missing:
            discrepancies.append(f"Unmatched plan orders: {list(missing)}")
        if extra:
            discrepancies.append(f"Unexpected execution orders: {list(extra)}")

    anomalies = []
    for o in exec_orders:
        oid = o.get("order_id", "")
        symbol = str(o.get("symbol", ""))
        status = str(o.get("status", "")).lower()
        filled = int(o.get("filled_qty", 0))
        qty = int(o.get("quantity", 0))
        slip = float(o.get("slippage", 0))

        if flag_partial_fills and status == "partial":
            anomalies.append({
                "type": "partial_fill",
                "order_id": oid,
                "symbol": symbol,
                "description": f"Partial fill: {filled}/{qty}",
                "severity": "medium",
            })
        if status == "rejected":
            anomalies.append({
                "type": "rejected",
                "order_id": oid,
                "symbol": symbol,
                "description": "Order rejected",
                "severity": "high",
            })
        if flag_high_slippage and slip >= flag_high_slippage:
            anomalies.append({
                "type": "high_slippage",
                "order_id": oid,
                "symbol": symbol,
                "description": f"Slippage {slip:.2f} >= threshold {flag_high_slippage}",
                "severity": "low" if slip < 5 else "medium",
            })

    trail = []
    created_at = order_plan.get("created_at", "")
    executed_at = execution_report.get("executed_at", "")
    trail.append({"timestamp": created_at, "stage": "plan", "entity_id": plan_id, "description": f"Order plan created ({len(plan_orders)} orders)"})
    trail.append({"timestamp": executed_at, "stage": "execution", "entity_id": exec_id, "description": f"Execution completed ({len(exec_orders)} orders)"})
    if slippage_report:
        trail.append({"timestamp": slippage_report.get("analyzed_at", ""), "stage": "analysis", "entity_id": slippage_report.get("report_id", ""), "description": "Slippage analysis completed"})
    audited_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    trail.append({"timestamp": audited_at, "stage": "audit", "entity_id": f"audit_{uuid.uuid4().hex[:12]}", "description": "Audit report generated"})

    recommendations = []
    if anomalies:
        rec = "Review " + ", ".join(a["type"] for a in anomalies[:3])
        if len(anomalies) > 3:
            rec += f" and {len(anomalies) - 3} more"
        recommendations.append(rec)
    if not plan_value_match:
        recommendations.append("Verify execution prices vs planned estimates")
    if total_filled_qty < total_planned_qty:
        recommendations.append(f"Fill rate {fill_quantity_rate:.1%} - consider partial fill strategy")

    return {
        "audit_id": f"audit_{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "execution_report_id": exec_id,
        "audited_at": audited_at,
        "consistency_check": {
            "plan_orders_match": plan_orders_match,
            "plan_value_match": plan_value_match,
            "all_orders_accounted": all_orders_accounted,
            "discrepancies": discrepancies,
        },
        "execution_summary": {
            "total_planned_orders": len(plan_orders),
            "total_executed_orders": len(exec_orders),
            "fill_rate": len(exec_orders) / len(plan_orders) if plan_orders else 0,
            "fill_quantity_rate": round(fill_quantity_rate, 4),
            "total_planned_value": round(total_planned_value, 2),
            "total_executed_value": round(total_executed_value, 2),
            "value_completion_rate": round(total_executed_value / total_planned_value, 4) if total_planned_value else 0,
        },
        "anomalies": anomalies,
        "audit_trail": trail,
        "recommendations": recommendations,
    }


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)

    if "_error" in params:
        out = {"success": False, "audit_report": None, "errors": [params["_error"]]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    op = _extract_order_plan(params)
    er = _extract_execution_report(params)
    if not op or not er:
        out = {"success": False, "audit_report": None, "errors": ["order_plan and execution_report required"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    sr = _extract_slippage_report(params)
    cfg = params.get("audit_config") or {}
    check_consistency = cfg.get("check_consistency", True)
    flag_partial_fills = cfg.get("flag_partial_fills", True)
    flag_high_slippage = float(cfg.get("flag_high_slippage", 1.0))

    report = _audit(op, er, sr, check_consistency, flag_partial_fills, flag_high_slippage)
    out = {"success": True, "audit_report": report, "errors": []}
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
