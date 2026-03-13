#!/usr/bin/env python3
"""
analyze_slippage: 分析订单执行滑点，生成滑点报告。
契约: system/tools/contracts/analyze_slippage.yaml
TICKET_20260314_008
输入: JSON 从 stdin 或第一个命令行参数读取。
"""
from __future__ import annotations

import json
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _extract_execution_report(params: dict) -> dict | None:
    """从 simulate_execution 完整输出或直接 execution_report 提取."""
    er = params.get("execution_report")
    if isinstance(er, dict) and er.get("orders") is not None:
        return er
    # 可能是 simulate_execution 的完整输出
    if isinstance(params.get("execution_report"), dict):
        return params["execution_report"]
    return None


def _analyze(
    er: dict,
    high_threshold: float,
    group_by_symbol: bool,
    include_rejected: bool,
) -> dict:
    orders = er.get("orders") or []
    source_id = er.get("report_id", "unknown")

    # 过滤 rejected（如配置）
    if not include_rejected:
        orders = [o for o in orders if str(o.get("status", "")).lower() != "rejected"]

    total_slippage = 0.0
    max_slip = 0.0
    max_slip_symbol = ""

    by_symbol: dict[str, dict] = defaultdict(lambda: {"order_count": 0, "total_slippage": 0.0, "total_value": 0.0})
    by_side: dict[str, dict] = defaultdict(lambda: {"order_count": 0, "total_slippage": 0.0})
    high_orders = []

    for o in orders:
        slip = float(o.get("slippage", 0))
        symbol = str(o.get("symbol", ""))
        side = str(o.get("side", "BUY")).upper()
        if side not in ("BUY", "SELL"):
            side = "BUY"
        filled = int(o.get("filled_qty", 0))
        avg_price = float(o.get("avg_fill_price", 0))
        value = filled * avg_price if avg_price else 0

        total_slippage += slip
        if slip > max_slip:
            max_slip = slip
            max_slip_symbol = symbol

        by_symbol[symbol]["order_count"] += 1
        by_symbol[symbol]["total_slippage"] += slip
        by_symbol[symbol]["total_value"] += value

        by_side[side]["order_count"] += 1
        by_side[side]["total_slippage"] += slip

        if slip >= high_threshold:
            high_orders.append({
                "order_id": o.get("order_id", ""),
                "symbol": symbol,
                "side": side,
                "slippage": round(slip, 4),
                "threshold": high_threshold,
            })

    n = len(orders)
    avg_slip = total_slippage / n if n else 0

    # 按 symbol 输出
    by_symbol_list = []
    for sym, d in sorted(by_symbol.items()):
        cnt = d["order_count"]
        ts = d["total_slippage"]
        tv = d["total_value"]
        avg = ts / cnt if cnt else 0
        bps = (ts / tv * 10000) if tv and tv > 0 else 0
        by_symbol_list.append({
            "symbol": sym,
            "order_count": cnt,
            "total_slippage": round(ts, 4),
            "avg_slippage": round(avg, 4),
            "total_value": round(tv, 4),
            "slippage_bps": round(bps, 2),
        })

    by_side_out = {
        "BUY": {
            "order_count": by_side["BUY"]["order_count"],
            "total_slippage": round(by_side["BUY"]["total_slippage"], 4),
            "avg_slippage": round(
                by_side["BUY"]["total_slippage"] / by_side["BUY"]["order_count"], 4
            ) if by_side["BUY"]["order_count"] else 0,
        },
        "SELL": {
            "order_count": by_side["SELL"]["order_count"],
            "total_slippage": round(by_side["SELL"]["total_slippage"], 4),
            "avg_slippage": round(
                by_side["SELL"]["total_slippage"] / by_side["SELL"]["order_count"], 4
            ) if by_side["SELL"]["order_count"] else 0,
        },
    }

    return {
        "report_id": f"slip_{uuid.uuid4().hex[:12]}",
        "source_execution_report": source_id,
        "analyzed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total_orders": len(orders),
            "analyzed_orders": n,
            "total_slippage": round(total_slippage, 4),
            "avg_slippage_per_order": round(avg_slip, 4),
            "max_slippage": round(max_slip, 4),
            "max_slippage_symbol": max_slip_symbol or "-",
        },
        "by_symbol": by_symbol_list,
        "by_side": by_side_out,
        "high_slippage_orders": high_orders,
    }


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)

    if "_error" in params:
        out = {"success": False, "slippage_report": None, "errors": [params["_error"]]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    er = _extract_execution_report(params)
    if not er or not isinstance(er.get("orders"), list):
        out = {"success": False, "slippage_report": None, "errors": ["execution_report with orders array required"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    cfg = params.get("analysis_config") or {}
    high_threshold = float(cfg.get("high_slippage_threshold", 5.0))
    group_by_symbol = cfg.get("group_by_symbol", True)
    include_rejected = cfg.get("include_rejected", False)

    report = _analyze(er, high_threshold, group_by_symbol, include_rejected)
    out = {"success": True, "slippage_report": report, "errors": []}
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
