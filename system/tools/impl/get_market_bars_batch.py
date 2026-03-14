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


def _generate_mock_bars(
    symbols: list[str],
    start_str: str,
    end_str: str,
) -> dict:
    """生成模拟 OHLCV 数据，格式与真实数据一致。TICKET_20250314_BACKTEST_001_FOLLOWUP_007"""
    from datetime import datetime, timedelta
    data: dict = {}
    base_prices = {"AAPL": 185.0, "MSFT": 405.0, "GOOGL": 140.0, "AMZN": 155.0, "NVDA": 480.0, "META": 335.0, "QQQ": 380.0}
    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    except ValueError:
        return {}
    current = start_dt
    while current <= end_dt:
        day_str = current.strftime("%Y-%m-%d")
        if current.weekday() < 5:  # 仅工作日
            for sym in symbols:
                base = base_prices.get(sym, 100.0)
                drift = 0.0002 * (hash(sym + day_str) % 100 - 50)
                o = base
                c = o * (1 + drift)
                h = max(o, c) * 1.005
                l = min(o, c) * 0.995
                vol = 40_000_000 + (hash(sym) % 20_000_000)
                if sym not in data:
                    data[sym] = []
                data[sym].append({
                    "timestamp": day_str + "T16:00:00Z",
                    "open": round(o, 2),
                    "high": round(h, 2),
                    "low": round(l, 2),
                    "close": round(c, 2),
                    "volume": int(vol),
                })
                base_prices[sym] = c
        current += timedelta(days=1)
    return data


def _get_source(params: dict) -> tuple[str, str | None]:
    """
    获取数据源，优先使用新的 'source' 参数，兼容旧的 'provider' 参数。
    返回: (source_value, error_message) — source 为 yahoo/ib 等，不再映射 ib->ibkr
    """
    if "source" in params:
        source = params["source"]
        if source not in VALID_SOURCES:
            return "", f"source must be one of {VALID_SOURCES}"
        return source, None
    if "provider" in params:
        provider = params["provider"]
        if provider not in VALID_PROVIDERS:
            return "", f"provider must be one of {VALID_PROVIDERS}"
        return "ib" if provider == "ibkr" else provider, None
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
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    if start_date and end_date:
        try:
            sd = datetime.strptime(str(start_date), "%Y-%m-%d")
            ed = datetime.strptime(str(end_date), "%Y-%m-%d")
            if sd > ed:
                return "start_date must be <= end_date"
            if (ed - sd).days > 2520:  # ~7 years max
                return "date range must not exceed 2520 days"
        except ValueError:
            return "start_date and end_date must be YYYY-MM-DD"
    else:
        lookback = params.get("lookback_days", 20)
        if not isinstance(lookback, int) or not (LOOKBACK_DAYS_MIN <= lookback <= LOOKBACK_DAYS_MAX):
            return f"lookback_days must be an integer between {LOOKBACK_DAYS_MIN} and {LOOKBACK_DAYS_MAX}"
    tf = params.get("timeframe", "1d")
    if tf not in VALID_TIMEFRAMES:
        return f"timeframe must be one of {VALID_TIMEFRAMES}"
    
    source, error = _get_source(params)
    if error:
        return error
    
    if source not in ("yahoo", "ib"):
        return f"source '{source}' is not yet implemented, only 'yahoo' and 'ib' are available"
    
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


def _fetch_yahoo(
    symbols: list[str],
    lookback_days: int,
    timeframe: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[dict, list[dict]]:
    import yfinance as yf

    interval = TIMEFRAME_TO_INTERVAL.get(timeframe, "1d")
    if start_date and end_date:
        start_str = start_date
        end_str = end_date
    else:
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
            def _scalar(v):
                """Unwrap single-element Series to avoid FutureWarning."""
                if hasattr(v, "iloc") and hasattr(v, "size") and v.size == 1:
                    return v.iloc[0]
                return v

            def _num(key: str) -> float | None:
                for k in (key, key.lower(), key.upper()):
                    if k in row.index:
                        v = _scalar(row[k])
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
                        v = _scalar(row[k])
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


def _fetch_ib(
    symbols: list[str],
    lookback_days: int,
    timeframe: str,
    start_date: str | None,
    end_date: str | None,
    connection_id: str | None,
) -> tuple[dict, list[dict]]:
    """通过 IB reqHistoricalData 获取 OHLCV。需先 connect_broker。"""
    import os
    _impl = os.path.dirname(os.path.abspath(__file__))
    if _impl not in sys.path:
        sys.path.insert(0, _impl)
    from adapters.broker_store import get_connection, get_latest_ib_connection
    conn = get_connection(connection_id) if connection_id else None
    if not conn:
        conn = get_latest_ib_connection()
    if not conn:
        return {}, [{"symbol": "", "error": "connection_id required when source=ib; call connect_broker first"}]
    host = conn.get("host", "127.0.0.1")
    port = int(conn.get("port", 4002))
    client_id = int(conn.get("client_id", 1))
    if start_date and end_date:
        start_str, end_str = start_date, end_date
    else:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=lookback_days)
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
    from adapters.ib_historical import get_historical_bars
    return get_historical_bars(symbols, start_str, end_str, timeframe, host, port, client_id)


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

    # TICKET_20250314_BACKTEST_001_FOLLOWUP_007: mock_mode 快速返回模拟数据
    mock_mode = params.get("mock_mode") is True or (
        __import__("os").environ.get("ARBITER_MOCK_MODE", "").lower() in ("1", "true", "yes")
    )
    if mock_mode:
        syms = params.get("symbols") or ["AAPL", "MSFT", "QQQ"]
        if isinstance(syms, str):
            syms = [s.strip() for s in syms.split(",") if s.strip()]
        start_str = params.get("start_date") or "2024-01-02"
        end_str = params.get("end_date") or "2024-03-31"
        data = _generate_mock_bars(syms, start_str, end_str)
        latency_ms = int((time.time() - start_time) * 1000)
        out = {
            "success": True,
            "data": data,
            "errors": [],
            "meta": {
                "requested_symbols": len(syms),
                "returned_symbols": len(data),
                "timeframe": params.get("timeframe", "1d"),
                "source": "mock",
                "latency_ms": latency_ms,
                "data_quality_score": 1.0,
            },
        }
        print(json.dumps(out, ensure_ascii=False))
        return

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
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    connection_id = params.get("connection_id")

    if source == "ib":
        data, errors = _fetch_ib(
            symbols, lookback_days, timeframe,
            start_date=str(start_date) if start_date else None,
            end_date=str(end_date) if end_date else None,
            connection_id=connection_id,
        )
    else:
        data, errors = _fetch_yahoo(
            symbols, lookback_days, timeframe,
            start_date=str(start_date) if start_date else None,
            end_date=str(end_date) if end_date else None,
        )
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
