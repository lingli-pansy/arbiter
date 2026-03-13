#!/usr/bin/env python3
"""
create_portfolio: 创建模型组合并持久化到 system/state/portfolios/。
契约: system/tools/contracts/create_portfolio.yaml
输入: JSON 从 stdin 或第一个命令行参数读取。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# 定位 system/state/portfolios
_impl_dir = Path(__file__).resolve().parent
_system_dir = _impl_dir.parent.parent
STATE_DIR = _system_dir / "state" / "portfolios"

WEIGHT_TOLERANCE = 0.001  # 权重总和允许误差


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _validate(params: dict) -> str | None:
    if not params.get("portfolio_id") or not str(params["portfolio_id"]).strip():
        return "portfolio_id is required"
    if not params.get("name") or not str(params["name"]).strip():
        return "name is required"
    assets = params.get("assets")
    if not isinstance(assets, list):
        return "assets must be an array"
    if not assets:
        return "assets must not be empty"
    total = 0.0
    for i, a in enumerate(assets):
        if not isinstance(a, dict):
            return f"assets[{i}] must be an object"
        if not a.get("symbol") or not str(a["symbol"]).strip():
            return f"assets[{i}].symbol is required"
        w = a.get("weight")
        if w is None:
            return f"assets[{i}].weight is required"
        try:
            total += float(w)
        except (TypeError, ValueError):
            return f"assets[{i}].weight must be a number"
    if abs(total - 1.0) > WEIGHT_TOLERANCE:
        return f"total weight must be 1.0, got {total}"
    return None


def _sanitize_id(pid: str) -> str:
    """将 portfolio_id 转为安全文件名"""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(pid))


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "portfolio": {}, "errors": [params["_error"]]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    err = _validate(params)
    if err:
        out = {"success": False, "portfolio": {}, "errors": [err]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    pid = str(params["portfolio_id"]).strip()
    name = str(params["name"]).strip()
    assets = [
        {"symbol": str(a["symbol"]).strip(), "weight": float(a["weight"])}
        for a in params["assets"]
    ]
    total_weight = sum(a["weight"] for a in assets)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    portfolio = {
        "portfolio_id": pid,
        "name": name,
        "created_at": now,
        "updated_at": now,
        "initial_capital": float(params.get("initial_capital", 100000)),
        "strategy": str(params.get("strategy", "")),
        "notes": str(params.get("notes", "")),
        "assets": assets,
        "total_weight": round(total_weight, 4),
        "status": "active",
    }

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = _sanitize_id(pid)
    state_path = STATE_DIR / f"{safe_id}.json"
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(portfolio, f, ensure_ascii=False, indent=2)
    except OSError as e:
        out = {"success": False, "portfolio": {}, "errors": [str(e)]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    try:
        rel_path = str(state_path.relative_to(_system_dir.parent))
    except ValueError:
        rel_path = str(state_path)
    portfolio["state_path"] = rel_path
    out = {"success": True, "portfolio": portfolio, "errors": []}
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
