#!/usr/bin/env python3
"""
get_nt_bar_schema: 获取 NautilusTrader Bar 数据结构的 schema 定义。
契约: system/tools/contracts/get_nt_bar_schema.yaml
输入: JSON 从 stdin 或第一个命令行参数读取。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
import sys

# NautilusTrader Bar 已知结构（官方文档），用于 nautilus_trader 未安装时的静态回退
STATIC_BAR_FIELDS = [
    {"name": "bar_type", "type": "BarType", "required": True, "description": "Bar type specification"},
    {"name": "open", "type": "Price", "required": True, "description": "Opening price"},
    {"name": "high", "type": "Price", "required": True, "description": "Highest price"},
    {"name": "low", "type": "Price", "required": True, "description": "Lowest price"},
    {"name": "close", "type": "Price", "required": True, "description": "Closing price"},
    {"name": "volume", "type": "Quantity", "required": True, "description": "Trading volume"},
    {"name": "ts_event", "type": "int64", "required": True, "description": "Event timestamp (nanoseconds)"},
    {"name": "ts_init", "type": "int64", "required": True, "description": "Initialization timestamp (nanoseconds)"},
    {"name": "is_revision", "type": "bool", "required": False, "description": "Whether bar is a revision of previous"},
]

STATIC_BAR_EXAMPLE = {
    "bar_type": "AAPL.NASDAQ-1-MINUTE-LAST",
    "open": "185.50",
    "high": "187.25",
    "low": "184.75",
    "close": "186.80",
    "volume": "52000000",
    "ts_event": 1704067200000000000,
    "ts_init": 1704067200000000000,
    "is_revision": False,
}


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _validate(params: dict) -> str | None:
    fmt = params.get("format", "dict")
    if fmt not in ("dict", "json_schema", "python_type"):
        return f"format must be one of: dict, json_schema, python_type"
    inc = params.get("include_examples", True)
    if not isinstance(inc, bool):
        return "include_examples must be a boolean"
    return None


def _introspect_nt_bar() -> tuple[list[dict], dict | None, str | None]:
    """从 nautilus_trader 内省 Bar 类，返回 (fields, example, version) 或 (None, None, None)"""
    try:
        import nautilus_trader
        from nautilus_trader.model.data import Bar
    except ImportError:
        return [], None, None

    version = getattr(nautilus_trader, "__version__", None) or "unknown"
    fields = []
    example = {}

    # 尝试从 dataclass/__init__ 获取字段
    if hasattr(Bar, "__dataclass_fields__"):
        for name, f in Bar.__dataclass_fields__.items():
            type_hint = getattr(f.type, "__name__", str(f.type))
            fields.append({
                "name": name,
                "type": type_hint,
                "required": f.default is f.default_factory if hasattr(f, "default_factory") else f.default is ...,
                "description": getattr(f, "metadata", {}) or "",
            })
        # 构建示例（仅 OHLCV 等可序列化字段）
        for fd in fields:
            n = fd["name"]
            if n in STATIC_BAR_EXAMPLE:
                example[n] = STATIC_BAR_EXAMPLE[n]
    else:
        # 回退到静态定义
        fields = STATIC_BAR_FIELDS.copy()
        example = STATIC_BAR_EXAMPLE.copy()

    return fields, example if example else None, version


def _build_schema(fields: list[dict], example: dict | None, include_examples: bool, fmt: str) -> dict:
    schema = {"fields": fields}
    if include_examples and example:
        schema["example"] = example

    if fmt == "json_schema":
        # 转为 JSON Schema 风格
        props = {}
        for f in fields:
            t = f.get("type", "string")
            props[f["name"]] = {"type": "string" if t in ("Price", "Quantity", "BarType") else t.lower()}
        schema["json_schema"] = {"type": "object", "properties": props}
    elif fmt == "python_type":
        schema["python_type"] = "nautilus_trader.model.data.Bar"

    return schema


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "error": params["_error"], "schema": None, "version": None}
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    err = _validate(params)
    if err:
        out = {"success": False, "error": err, "schema": None, "version": None}
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    fmt = params.get("format", "dict")
    include_examples = params.get("include_examples", True)
    fields, example, version = _introspect_nt_bar()

    if not fields:
        fields = STATIC_BAR_FIELDS.copy()
        example = STATIC_BAR_EXAMPLE.copy() if include_examples else None
        version = None  # 未安装时版本不可知

    schema = _build_schema(fields, example, include_examples, fmt)
    out = {
        "success": True,
        "schema": schema,
        "version": version,
    }
    if not version:
        out["meta"] = {"source": "static_fallback", "note": "nautilus_trader not installed; schema from documentation"}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
