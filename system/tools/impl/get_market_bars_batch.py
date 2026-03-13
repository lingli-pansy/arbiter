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
import time
from datetime import datetime, timezone, timedelta

TIMEFRAME_TO_INTERVAL = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "4h": "1h",  # yfinance 无 4h，用 1h 近似
    "1d": "1d",
}

# 新的 source 参数枚举值
VALID_SOURCES = ("yahoo", "ib", "polygon", "alpaca")
# 旧版兼容（provider 参数）
VALID_PROVIDERS = ("yahoo", "ibkr", "polygon", "alpaca")
VALID_TIMEFRAMES = list(TIMEFRAME_TO_INTERVAL.keys())
MAX_SYMBOLS = 10
LOOKBACK_DAYS_MIN = 1
LOOKBACK_DAYS_MAX = 252


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _get_source(params: dict) -> tuple[str, str | None]:
    """
    获取数据源，优先使用新的 'source' 参数，兼容旧的 'provider' 参数。
    返回: (source_value, error_message)
    """
    # 优先使用新的 source 参数
    if "source" in params:
        source = params["source"]
        if source not in VALID_SOURCES:
            return "", f"source must be one of {VALID_SOURCES}"
        # 映射 ib 到 yfinance 的 ibkr
        if source == "ib":
            return "ibkr", None
        return source, None
    
    # 兼容旧的 provider 参数
    if "provider" in params:
        provider = params["provider"]
        if provider not in VALID_PROVIDERS:
            return "", f"provider must be one of {VALID_PROVIDERS}"
        return provider, None
    
    # 默认使用 yahoo
    return "yahoo", None


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
    
    source, error = _get_source(params)
    if error:
        return error
    
    # 暂时只有 yahoo 已实现
    if source not in ("yahoo", "ibkr"):
        return f"source '{source}' is not yet implemented, only 'yahoo' is available"
    
    return None


def _calculate_data_quality(data: dict) -> float:
    """计算数据质量评分 (0-1)"""
    if not data:
        return 0.0
    
    total_points = 0
    valid_points = 0
    
    for symbol, bars in data.items():
        for bar in bars:
            total_points += 5  # open, high, low, close, volume
            # 检查每个字段是否有效
            if bar.get("open") is not None:
                valid_points += 1
            if bar.get("high") is not None:
                valid_points += 1
            if bar.get("low") is not None:
                valid_points += 1
            if bar.get("close") is not None:
                valid_points += 1
            if bar.get("volume") is not None and bar.get("volume") > 0:
                valid_points += 1
    
    return valid_points / total_points if total_points > 0 else 0.0


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
    start_time = time.time()
    
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
            "meta": {
                "requested_symbols": 0,
                "returned_symbols": 0,
                "timeframe": "1d",
                "source": "yahoo",
                "latency_ms": 0,
                "data_quality_score": 0.0,
            },
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    err = _validate(params)
    if err:
        out = {
            "success": False,
            "data": {},
            "errors": [{"symbol": "", "error": err}],
            "meta": {
                "requested_symbols": 0,
                "returned_symbols": 0,
                "timeframe": "1d",
                "source": "yahoo",
                "latency_ms": 0,
                "data_quality_score": 0.0,
            },
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    symbols = params["symbols"]
    lookback_days = int(params.get("lookback_days", 20))
    timeframe = params.get("timeframe", "1d")
    source, _ = _get_source(params)

    # 目前只支持 yahoo
    data, errors = _fetch_yahoo(symbols, lookback_days, timeframe)
    returned = len(data)
    
    # 计算延迟和数据质量
    latency_ms = int((time.time() - start_time) * 1000)
    data_quality_score = _calculate_data_quality(data)
    
    # 获取用户指定的 source 值用于返回（不是内部映射后的值）
    user_source = params.get("source", params.get("provider", "yahoo"))
    # 如果是旧版的 ibkr，返回新的 ib
    if user_source == "ibkr":
        user_source = "ib"
    
    out = {
        "success": returned > 0,
        "data": data,
        "errors": errors,
        "meta": {
            "requested_symbols": len(symbols),
            "returned_symbols": returned,
            "timeframe": timeframe,
            "source": user_source,
            "latency_ms": latency_ms,
            "data_quality_score": round(data_quality_score, 4),
        },
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
