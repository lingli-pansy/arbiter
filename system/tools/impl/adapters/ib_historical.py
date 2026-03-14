"""
IB Historical Data 适配器：通过 reqHistoricalData 获取 OHLCV。
用于 get_market_bars_batch 和 get_market_cap_ranking 的价格部分。
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

# timeframe -> IB barSizeSetting
TIMEFRAME_TO_BAR_SIZE = {
    "1m": "1 min",
    "5m": "5 mins",
    "15m": "15 mins",
    "1h": "1 hour",
    "4h": "1 hour",
    "1d": "1 day",
}


def get_historical_bars(
    symbols: list[str],
    start_str: str,
    end_str: str,
    timeframe: str,
    host: str,
    port: int,
    client_id: int,
    timeout_sec: float = 30.0,
) -> tuple[dict, list[dict]]:
    """
    通过 IB reqHistoricalData 获取多标的 OHLCV。
    start_str/end_str: YYYY-MM-DD
    Returns: (data: {symbol: [bar_dicts]}, errors: [{symbol, error}])
    """
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass
    from ib_insync import IB, Stock

    bar_size = TIMEFRAME_TO_BAR_SIZE.get(timeframe, "1 day")
    # IB durationStr: 如 "20 D", "1 M"
    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_str, "%Y-%m-%d")
        days = max(1, (end_dt - start_dt).days + 1)
    except ValueError:
        days = 31
    duration_str = f"{min(days, 365)} D"
    end_dt = datetime.strptime(end_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    end_datetime = end_dt.strftime("%Y%m%d-%H:%M:%S")

    data: dict = {}
    errors: list[dict] = []
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=timeout_sec)
        for sym in symbols:
            try:
                contract = Stock(sym, "SMART", "USD")
                bars = ib.reqHistoricalData(
                    contract,
                    endDateTime=end_datetime,
                    durationStr=duration_str,
                    barSizeSetting=bar_size,
                    whatToShow="TRADES",
                    useRTH=True,
                    formatDate=1,
                )
                if not bars:
                    errors.append({"symbol": sym, "error": "No bars returned"})
                    continue
                rows = []
                for bar in bars:
                    dt = bar.date
                    if hasattr(dt, "isoformat"):
                        ts_str = dt.isoformat() if getattr(dt, "tzinfo", None) else str(dt) + "Z"
                    else:
                        ts_str = str(dt)
                    rows.append({
                        "timestamp": ts_str,
                        "open": float(bar.open) if bar.open is not None else None,
                        "high": float(bar.high) if bar.high is not None else None,
                        "low": float(bar.low) if bar.low is not None else None,
                        "close": float(bar.close) if bar.close is not None else None,
                        "volume": int(bar.volume) if bar.volume is not None else 0,
                    })
                data[sym] = rows
            except Exception as e:
                errors.append({"symbol": sym, "error": str(e)})
    except Exception as e:
        for sym in symbols:
            if sym not in data:
                errors.append({"symbol": sym, "error": f"IB connection: {e}"})
    finally:
        try:
            ib.disconnect()
        except Exception:
            pass
    return data, errors


def get_close_prices_as_of(
    symbols: list[str],
    date_str: str,
    host: str,
    port: int,
    client_id: int,
    lookback_days: int = 35,
    timeout_sec: float = 30.0,
) -> tuple[dict[str, float], list[str]]:
    """
    获取指定日期（含）之前各标的最后收盘价。
    用于 get_market_cap_ranking 的价格部分。
    Returns: ({symbol: close_price}, [errors])
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return {}, [f"Invalid date: {date_str}"]
    start = (dt - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end = (dt + timedelta(days=5)).strftime("%Y-%m-%d")
    data, bar_errors = get_historical_bars(
        symbols, start, end, "1d", host, port, client_id, timeout_sec
    )
    prices: dict[str, float] = {}
    errs: list[str] = []
    for d in bar_errors:
        errs.append(f"{d['symbol']}: {d['error']}")
    for sym, rows in data.items():
        if not rows:
            continue
        # 取 date 之前最后一条的 close
        target_date = dt.date()
        valid = [r for r in rows if _parse_bar_date(r["timestamp"]) <= target_date]
        if valid:
            last = valid[-1]
            close = last.get("close")
            if close is not None and close > 0:
                prices[sym] = float(close)
    return prices, errs


def _parse_bar_date(ts_str: str):
    """从 timestamp 字符串解析 date"""
    try:
        if "T" in ts_str:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).date()
        return datetime.strptime(ts_str[:10], "%Y-%m-%d").date()
    except Exception:
        return datetime.min.date()
