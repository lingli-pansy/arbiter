#!/usr/bin/env python3
"""
get_symbol_venue: 解析标的代码到交易场所的映射，用于 NT BarType 生成。
契约: system/tools/contracts/get_symbol_venue.yaml
输入: JSON 从 stdin 或第一个命令行参数读取。
输出: JSON 写入 stdout。
Adapter pattern: 不修改 get_market_bars_batch，独立工具供 convert_bars_to_nt 使用。
"""
from __future__ import annotations

import json
import os
import sys

# 确保 impl 目录在 path 中，以便 adapters 可导入
_impl_dir = os.path.dirname(os.path.abspath(__file__))
if _impl_dir not in sys.path:
    sys.path.insert(0, _impl_dir)

# 相对导入适配器逻辑
try:
    from .adapters.venue_resolver import resolve_venues
except ImportError:
    from adapters.venue_resolver import resolve_venues


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _validate(params: dict) -> str | None:
    if not isinstance(params.get("symbols"), list):
        return "symbols must be an array of strings"
    symbols = params["symbols"]
    if not symbols:
        return "symbols must not be empty"
    for s in symbols:
        if not isinstance(s, str) or not s.strip():
            return "each symbol must be a non-empty string"
    return None


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "data": {}, "errors": [params["_error"]], "meta": {}}
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    err = _validate(params)
    if err:
        out = {"success": False, "data": {}, "errors": [err], "meta": {}}
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    symbols = [s.strip() for s in params["symbols"]]
    data = resolve_venues(symbols)
    out = {
        "success": True,
        "data": data,
        "errors": [],
        "meta": {"requested_symbols": len(symbols), "resolved_symbols": len(data)},
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
