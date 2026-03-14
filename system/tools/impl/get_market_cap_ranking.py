#!/usr/bin/env python3
"""
get_market_cap_ranking: 获取指定日期的市值排名。TICKET_20250314_BACKTEST_001_ARCH_FIX
支持 source=ib（默认，符合 MVP 架构）或 source=yahoo。
"""
from __future__ import annotations
import json
import sys
import time
from datetime import datetime, timedelta

# 美股大盘候选池（市值常居前列）
US_LARGE_CAP_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "JPM", "V", "UNH",
    "JNJ", "XOM", "PG", "HD", "MA", "DIS", "BAC", "WMT", "CVX", "PEP",
]

def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _get_ranking_ib(
    symbols: list[str],
    connection_id: str | None,
    top_n: int,
    min_mcap: float | None,
) -> tuple[list[dict], list[str], dict]:
    """通过 IB 获取市值排名。优先 Tick 165 (Paper 兼容)，失败后回退 Fundamental Data。
    TICKET_20250314_003_TICK165_IMPLEMENTATION
    Returns: (ranking, errors, meta) 其中 meta 含 tick165_attempted, tick165_success"""
    import os
    _impl = os.path.dirname(os.path.abspath(__file__))
    if _impl not in __import__("sys").path:
        __import__("sys").path.insert(0, _impl)
    from adapters.ib_fundamental import get_market_caps_tick165, get_market_caps
    from adapters.broker_store import get_connection, get_latest_ib_connection

    conn = get_connection(connection_id) if connection_id else None
    if not conn:
        conn = get_latest_ib_connection()
    if not conn:
        return [], ["connection_id required when source=ib; call connect_broker first"], {}

    host = conn.get("host", "127.0.0.1")
    port = int(conn.get("port", 4002))
    client_id = int(conn.get("client_id", 1))

    sym_to_mcap: dict[str, float] = {}
    errs: list[str] = []
    tick165_success = False

    sym_to_mcap, errs = get_market_caps_tick165(symbols, host, port, client_id)
    tick165_success = len(sym_to_mcap) > 0

    if len(sym_to_mcap) < len(symbols):
        missing = [s for s in symbols if s not in sym_to_mcap]
        fd_mcap, fd_errs = get_market_caps(missing, host, port, client_id)
        sym_to_mcap.update(fd_mcap)
        errs.extend([f"[fd] {e}" for e in fd_errs])

    ranking = []
    for sym, mc in sym_to_mcap.items():
        if min_mcap and mc < min_mcap * 1e6:
            continue
        ranking.append({"symbol": sym, "market_cap": mc, "market_cap_millions": round(mc / 1e6, 1)})
    ranking.sort(key=lambda x: x["market_cap"], reverse=True)
    for i, r in enumerate(ranking[:top_n], 1):
        r["rank"] = i
    meta = {"tick165_attempted": True, "tick165_success": tick165_success}
    return ranking[:top_n], errs, meta


def _get_prices_via_ib(symbols: list[str], date_str: str, connection_id: str | None) -> tuple[dict[str, float], list[str]]:
    """通过 IB reqHistoricalData 获取指定日期收盘价。无连接时返回空。"""
    import os
    _impl = os.path.dirname(os.path.abspath(__file__))
    if _impl not in __import__("sys").path:
        __import__("sys").path.insert(0, _impl)
    from adapters.broker_store import get_connection, get_latest_ib_connection
    from adapters.ib_historical import get_close_prices_as_of
    conn = get_connection(connection_id) if connection_id else None
    if not conn:
        conn = get_latest_ib_connection()
    if not conn:
        return {}, []
    host = conn.get("host", "127.0.0.1")
    port = int(conn.get("port", 4002))
    client_id = int(conn.get("client_id", 1))
    return get_close_prices_as_of(symbols, date_str, host, port, client_id)


def _get_ranking_yahoo(
    date_str: str, market: str, top_n: int, min_mcap: float | None, universe: list[str],
    connection_id: str | None = None,
    use_ib_for_price: bool = False,
) -> tuple[list[dict], list[str]]:
    """通过 Yahoo Finance 获取市值排名（备用数据源）。
    当 use_ib_for_price=True 且有 IB 连接时，价格用 IB；否则用 yf.download。
    TICKET_20250314_BACKTEST_001_FOLLOWUP_002: source=yahoo 时 use_ib_for_price=False，完全不连 IB。
    """
    import yfinance as yf
    import pandas as pd
    ranking = []
    errors = []
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    start = (dt - timedelta(days=30)).strftime("%Y-%m-%d")
    end = (dt + timedelta(days=5)).strftime("%Y-%m-%d")
    syms = universe or US_LARGE_CAP_UNIVERSE
    YAHOO_DELAY_SEC = 2.0  # 避免 Yahoo 限流 (~20 symbols/min)
    RATE_LIMIT_RETRIES = 3
    prices: dict[str, float] = {}
    # 仅当 use_ib_for_price 时尝试 IB（source=yahoo 不连 IB）
    if use_ib_for_price:
        prices, price_errs = _get_prices_via_ib(syms, date_str, connection_id)
    else:
        price_errs = []
    if price_errs:
        errors.extend(price_errs)
    if not prices or len(prices) < len(syms):
        time.sleep(2)
        for attempt in range(RATE_LIMIT_RETRIES + 1):
            try:
                data = yf.download(syms, start=start, end=end, progress=False, threads=False)
                if data.empty:
                    raise ValueError("no price data")
                closes = data["Close"] if "Close" in data.columns else data.iloc[:, 0]
                if len(syms) == 1:
                    closes = pd.DataFrame(closes, columns=[syms[0]]) if isinstance(closes, pd.Series) else closes
                if hasattr(closes.index, "date"):
                    mask = [d <= dt.date() for d in closes.index.date]
                else:
                    mask = closes.index <= pd.Timestamp(dt)
                if not any(mask):
                    raise ValueError("no data for date")
                valid = closes.loc[mask].iloc[-1]
                for sym in syms:
                    in_valid = sym in getattr(valid, "index", closes.columns) if hasattr(valid, "index") else sym in closes.columns
                    if sym not in prices and in_valid:
                        v = valid[sym] if hasattr(valid, "__getitem__") else valid
                        try:
                            prices[sym] = float(v)
                        except (TypeError, ValueError):
                            pass
                break
            except Exception as e:
                err_str = str(e)
                if "Too Many Requests" in err_str or "Rate limited" in err_str:
                    if attempt < RATE_LIMIT_RETRIES:
                        time.sleep(2 ** (attempt + 1))  # 指数退避: 2s, 4s, 8s (TICKET_20250314_BACKTEST_001_FOLLOWUP_003)
                    else:
                        errors.append("batch download: rate limited after retries")
                        return [], errors
                else:
                    errors.append(f"batch download: {e}")
                    break
    # 逐只获取 info（marketCap/shares），带延迟
    for sym in syms:
        if sym in prices:
            price = prices[sym]
        else:
            errors.append(f"{sym}: no price from download")
            time.sleep(YAHOO_DELAY_SEC)
            continue
        for attempt in range(RATE_LIMIT_RETRIES + 1):
            try:
                t = yf.Ticker(sym)
                info = t.info
                mcap = info.get("marketCap") or info.get("enterpriseValue")
                shares = info.get("sharesOutstanding")
                curr_price = info.get("regularMarketPrice") or info.get("currentPrice") or price
                if mcap and mcap > 0 and curr_price and curr_price > 0:
                    mc = mcap * (price / curr_price)
                elif shares and shares > 0 and price > 0:
                    mc = price * shares
                else:
                    errors.append(f"{sym}: no market cap in info")
                    break
                if min_mcap and mc < min_mcap * 1e6:
                    break
                ranking.append({"symbol": sym, "market_cap": mc, "market_cap_millions": round(mc / 1e6, 1)})
                break
            except Exception as e:
                err_str = str(e)
                if "Too Many Requests" in err_str or "Rate limited" in err_str:
                    if attempt < RATE_LIMIT_RETRIES:
                        time.sleep(2 ** (attempt + 1))  # 指数退避 (FOLLOWUP_003)
                    else:
                        errors.append(f"{sym}: rate limited after retries")
                else:
                    errors.append(f"{sym}: {e}")
                    break
        time.sleep(YAHOO_DELAY_SEC)
    ranking.sort(key=lambda x: x["market_cap"], reverse=True)
    for i, r in enumerate(ranking[:top_n], 1):
        r["rank"] = i
    return ranking[:top_n], errors


# TICKET_20250314_BACKTEST_001_FOLLOWUP_004: Mock 数据用于测试
MOCK_RANKING = [
    {"rank": 1, "symbol": "AAPL", "market_cap": 2800000000000, "market_cap_millions": 2800000},
    {"rank": 2, "symbol": "MSFT", "market_cap": 2700000000000, "market_cap_millions": 2700000},
    {"rank": 3, "symbol": "GOOGL", "market_cap": 1700000000000, "market_cap_millions": 1700000},
    {"rank": 4, "symbol": "AMZN", "market_cap": 1500000000000, "market_cap_millions": 1500000},
    {"rank": 5, "symbol": "NVDA", "market_cap": 1300000000000, "market_cap_millions": 1300000},
]


def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        print(json.dumps({"success": False, "ranking": [], "errors": [params["_error"]]}))
        sys.exit(1)
    # TICKET_20250314_BACKTEST_001_FOLLOWUP_004: mock_mode 或 ARBITER_MOCK_MODE
    if params.get("mock_mode") or (__import__("os").environ.get("ARBITER_MOCK_MODE") in ("1", "true", "True")):
        top_n = max(1, min(20, int(params.get("top_n", 5))))
        ranking = [dict(r, rank=i + 1) for i, r in enumerate(MOCK_RANKING[:top_n])]
        print(json.dumps({
            "success": True, "ranking": ranking,
            "as_of_date": params.get("date", "2024-03-31"),
            "source": "mock", "errors": [],
            "meta": {"latency_ms": 10},
        }, default=str))
        return
    date = params.get("date")
    if not date:
        print(json.dumps({"success": False, "ranking": [], "errors": ["date required"]}))
        sys.exit(1)
    market = params.get("market", "US")
    top_n = int(params.get("top_n", 5))
    top_n = max(1, min(20, top_n))
    min_mcap = params.get("min_market_cap")
    universe = params.get("universe")
    source = params.get("source", "ib")
    connection_id = params.get("connection_id")
    start = time.perf_counter()
    syms = universe or US_LARGE_CAP_UNIVERSE
    if source == "static":
        import os
        _impl = os.path.dirname(os.path.abspath(__file__))
        if _impl not in __import__("sys").path:
            __import__("sys").path.insert(0, _impl)
        from adapters.static_fundamental import get_ranking_from_static
        ranking, errors = get_ranking_from_static(date, universe, top_n, min_mcap)
        ib_meta = {}
    elif source == "ib":
        ranking, errors, ib_meta = _get_ranking_ib(syms, connection_id, top_n, min_mcap)
        # TICKET_20250314_001_FOLLOWUP_005: IB 失败时回退 static（不使用 Yahoo）
        errs_joined = " ".join(errors).lower()
        ib_blocked = (
            "10358" in errs_joined or "fundamentals" in errs_joined or "fundamental data" in errs_joined
            or "10089" in errs_joined or "market data" in errs_joined or "subscription" in errs_joined
        )
        if (not ranking or len(ranking) < top_n) and ib_blocked:
            ib_fallback = params.get("ib_fallback", "static")
            if ib_fallback == "static":
                errors.insert(0, "[fallback] IB data not available (Paper 10358/10089); using static")
                import os
                _impl = os.path.dirname(os.path.abspath(__file__))
                if _impl not in __import__("sys").path:
                    __import__("sys").path.insert(0, _impl)
                from adapters.static_fundamental import get_ranking_from_static
                ranking, static_errs = get_ranking_from_static(date, universe, top_n, min_mcap)
                errors.extend(static_errs)
                source = "static"
            else:
                errors.insert(0, "[fallback] IB data not available; using Yahoo")
                ranking, yahoo_errs = _get_ranking_yahoo(date, market, top_n, min_mcap, universe, connection_id, use_ib_for_price=True)
                errors.extend(yahoo_errs)
                source = "yahoo"
    else:
        ranking, errors = _get_ranking_yahoo(date, market, top_n, min_mcap, universe, None, use_ib_for_price=False)
        ib_meta = {}
    elapsed = int((time.perf_counter() - start) * 1000)
    meta = {"latency_ms": elapsed, **(ib_meta if ib_meta else {})}
    print(json.dumps({
        "success": True,
        "ranking": ranking,
        "as_of_date": date,
        "source": source,
        "errors": errors,
        "meta": meta
    }, default=str))

if __name__ == "__main__":
    main()
