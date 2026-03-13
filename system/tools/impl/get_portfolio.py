#!/usr/bin/env python3
"""
get_portfolio: 从 system/state/portfolios/ 读取模型组合。
契约: system/tools/contracts/get_portfolio.yaml
输入: JSON 从 stdin 或第一个命令行参数读取。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_impl_dir = Path(__file__).resolve().parent
_system_dir = _impl_dir.parent.parent
STATE_DIR = _system_dir / "state" / "portfolios"


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _sanitize_id(pid: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(pid))


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "portfolio": None, "errors": [params["_error"]]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    pid = params.get("portfolio_id")
    if not pid or not str(pid).strip():
        out = {"success": False, "portfolio": None, "errors": ["portfolio_id is required"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    safe_id = _sanitize_id(str(pid).strip())
    state_path = STATE_DIR / f"{safe_id}.json"
    if not state_path.exists():
        out = {"success": False, "portfolio": None, "errors": [f"Portfolio not found: {pid}"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            portfolio = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        out = {"success": False, "portfolio": None, "errors": [str(e)]}
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
