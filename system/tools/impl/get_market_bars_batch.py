#!/usr/bin/env python3
"""
get_market_bars_batch: 批量获取多标的市场行情数据（OHLCV）。
契约: system/tools/contracts/get_market_bars_batch.yaml
输入: JSON 从 stdin 或第一个命令行参数读取。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone, timedelta

TIMEFRAME_TO_INTERVAL = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "4h": "1h",  # yfinance 无 4h，用 1h 近似
    "1d": "1d",
}

VALID_PROVIDERS = ("yahoo", "ibkr", "polygon")
VALID_TIMEFRAMES = list(TIMEFRAME_TO_INTERVAL.keys())
MAX_SYMBOLS = 10
LOOKBACK_DAYS_MIN = 1
LOOKBACK_DAYS_MAX = 252


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _validate(params: dict) -> str | None:
    if not isinstance(params.get("symbols"), list):
        return "symbols must be an array of strings"
    symbols = params["symbols"]
    if not (1 <= len(symbols) <= MAX_SYMBOLS):
        return f"symbols length must be between 1 and {MAX_SYMBOLS}"
    for s in symbols:
        if not isinstance(s, str) or not s.strip():
            return "each symbol must be a non-empty string"
    lookback = params.get("lookback_days", 20)
    if not isinstance(lookback, int) or not (LOOKBACK_DAYS_MIN <= lookback <= LOOKBACK_DAYS_MAX):
        return f"lookback_days must be an integer between {LOOKBACK_DAYS_MIN} and {LOOKBACK_DAYS_MAX}"
    tf = params.get("timeframe", "1d")
    if tf not in VALID_TIMEFRAMES:
        return f"timeframe must be one of {VALID_TIMEFRAMES}"
    prov = params.get("provider", "yahoo")
    if prov not in VALID_PROVIDERS:
        return f"provider must be one of {VALID_PROVIDERS}"
    if prov != "yahoo":
        return "only provider 'yahoo' is implemented"
    return None


def _fetch_yahoo(symbols: list[str], lookback_days: int, timeframe: str) -> tuple[dict, list[dict]]:
    import yfinance as yf

    interval = TIMEFRAME_TO_INTERVAL.get(timeframe, "1d")
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    data = {}
    errors = []

    # 按单标的拉取，保证部分失败时可区分，且列名统一为 Open/High/Low/Close/Volume
    for sym in symbols:
        try:
            df = yf.download(
                sym,
                start=start_str,
                end=end_str,
                interval=interval,
                progress=False,
                auto_adjust=False,
                prepost=False,
                threads=False,
            )
            if df is None or df.empty:
                errors.append({"symbol": sym, "error": "No data returned"})
                continue
            def _num(key: str) -> float | None:
                for k in (key, key.lower(), key.upper()):
                    if k in row.index:
                        v = row[k]
                        if v is None or (isinstance(v, float) and math.isnan(v)):
                            return None
                        try:
                            return float(v)
                        except (TypeError, ValueError):
                            return None
                return None

            def _vol() -> int:
                for k in ("Volume", "volume", "VOLUME"):
                    if k in row.index:
                        v = row[k]
                        if v is None or (isinstance(v, float) and math.isnan(v)):
                            return 0
                        try:
                            return int(v)
                        except (TypeError, ValueError):
                            return 0
                return 0

            rows = []
            for ts, row in df.iterrows():
                if hasattr(ts, "isoformat"):
                    ts_str = ts.isoformat() if getattr(ts, "tzinfo", None) else str(ts) + "Z"
                else:
                    ts_str = str(ts)
                rows.append({
                    "timestamp": ts_str,
                    "open": _num("Open"),
                    "high": _num("High"),
                    "low": _num("Low"),
                    "close": _num("Close"),
                    "volume": _vol(),
                })
            data[sym] = rows
        except Exception as e:
            errors.append({"symbol": sym, "error": str(e)})
    return data, errors


def main() -> None:
    if len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        raw = sys.stdin.read()

    params = _parse_input(raw)
    if "_error" in params:
        out = {
            "success": False,
            "data": {},
            "errors": [{"symbol": "", "error": params["_error"]}],
            "meta": {"requested_symbols": 0, "returned_symbols": 0, "timeframe": "1d", "provider": "yahoo"},
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    err = _validate(params)
    if err:
        out = {
            "success": False,
            "data": {},
            "errors": [{"symbol": "", "error": err}],
            "meta": {"requested_symbols": 0, "returned_symbols": 0, "timeframe": "1d", "provider": "yahoo"},
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    symbols = params["symbols"]
    lookback_days = int(params.get("lookback_days", 20))
    timeframe = params.get("timeframe", "1d")
    provider = params.get("provider", "yahoo")

    data, errors = _fetch_yahoo(symbols, lookback_days, timeframe)
    returned = len(data)
    out = {
        "success": returned > 0,
        "data": data,
        "errors": errors,
        "meta": {
            "requested_symbols": len(symbols),
            "returned_symbols": returned,
            "timeframe": timeframe,
            "provider": provider,
        },
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
