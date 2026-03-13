#!/usr/bin/env python3
"""
convert_bars_to_nt: 将 get_market_bars_batch 输出转为 NautilusTrader 兼容格式（adapter）。
契约: system/tools/contracts/convert_bars_to_nt.yaml
不修改 get_market_bars_batch，以 adapter pattern 实现。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

# 确保 impl 目录在 path 中，以便导入 adapters
_impl_dir = os.path.dirname(os.path.abspath(__file__))
if _impl_dir not in sys.path:
    sys.path.insert(0, _impl_dir)
from adapters.venue_resolver import resolve_venues

# 时间周期映射: get_market_bars_batch -> NT BarType
TIMEFRAME_TO_NT = {
    "1m": "1-MINUTE",
    "5m": "5-MINUTE",
    "15m": "15-MINUTE",
    "1h": "1-HOUR",
    "4h": "4-HOUR",
    "1d": "1-DAY",
}


def _iso_to_nanoseconds(ts_str: str) -> int | None:
    """将 ISO 8601 字符串转为纳秒时间戳"""
    if not ts_str or not isinstance(ts_str, str):
        return None
    s = ts_str.strip().replace("Z", "+00:00")
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1_000_000_000)
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1_000_000_000)
    except (ValueError, TypeError):
        return None


def _to_price(v) -> str:
    """转为 Price 字符串"""
    if v is None:
        return "0"
    if isinstance(v, str):
        return v
    return str(float(v))


def _to_quantity(v) -> str:
    """转为 Quantity 字符串"""
    if v is None:
        return "0"
    if isinstance(v, str):
        return v
    return str(int(v))


def _convert_bar(bar: dict, symbol: str, venue: str, timeframe_nt: str) -> dict | None:
    ts_ns = _iso_to_nanoseconds(bar.get("timestamp", ""))
    if ts_ns is None:
        return None
    bar_type = f"{symbol}.{venue}-{timeframe_nt}-LAST"
    return {
        "bar_type": bar_type,
        "open": _to_price(bar.get("open")),
        "high": _to_price(bar.get("high")),
        "low": _to_price(bar.get("low")),
        "close": _to_price(bar.get("close")),
        "volume": _to_quantity(bar.get("volume")),
        "ts_event": ts_ns,
        "ts_init": ts_ns,
        "is_revision": False,
    }


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _validate(params: dict) -> str | None:
    md = params.get("market_data")
    if md is None:
        return "market_data is required"
    if not isinstance(md, dict):
        return "market_data must be an object"
    data = md.get("data") if isinstance(md.get("data"), dict) else md
    if not isinstance(data, dict):
        return "market_data must contain 'data' key with symbol -> bars mapping"
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

    md = params["market_data"]
    data = md.get("data", md) if isinstance(md, dict) else {}
    meta = md.get("meta", {}) if isinstance(md, dict) else {}
    timeframe = params.get("timeframe") or meta.get("timeframe", "1d")
    timeframe_nt = TIMEFRAME_TO_NT.get(timeframe, "1-DAY")
    venue_map = params.get("venue_map")

    symbols = list(data.keys())
    if venue_map is None or not isinstance(venue_map, dict):
        venue_map = resolve_venues(symbols)

    out_data = {}
    errors = []
    for symbol, bars in data.items():
        if not isinstance(bars, list):
            errors.append({"symbol": symbol, "error": "bars must be array"})
            continue
        venue = venue_map.get(symbol, "UNKNOWN")
        converted = []
        for i, bar in enumerate(bars):
            if not isinstance(bar, dict):
                continue
            nt_bar = _convert_bar(bar, symbol, venue, timeframe_nt)
            if nt_bar:
                converted.append(nt_bar)
        out_data[symbol] = converted

    out = {
        "success": True,
        "data": out_data,
        "errors": errors,
        "meta": {
            "timeframe": timeframe,
            "timeframe_nt": timeframe_nt,
            "source_format": "get_market_bars_batch",
        },
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
