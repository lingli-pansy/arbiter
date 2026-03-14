"""
IB Fundamental Data 适配器：通过 reqFundamentalData 获取市值。
Tick 165 (Miscellaneous Stats) 方案：TICKET_20250314_003_TICK165_IMPLEMENTATION
"""
from __future__ import annotations

import math
import re
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ib_insync import IB, Stock


def _extract_mcap_from_ticker(ticker) -> float | None:
    """
    从 Ticker 对象提取市值。Tick 165 可能在不同 IB 环境中使用不同字段。
    尝试: marketCap, mktCap, fundamentalRatios, ticks 中的 generic 值。
    """
    # 直接属性
    for attr in ("marketCap", "mktCap", "lastMarketCap", "market_cap"):
        v = getattr(ticker, attr, None)
        if v is not None:
            try:
                f = float(v)
                if f > 0 and not math.isnan(f):
                    return f
            except (TypeError, ValueError):
                pass
    # info 字典（若存在）
    if hasattr(ticker, "info") and isinstance(ticker.info, dict):
        for k in ("marketCap", "mktCap", "market_cap"):
            v = ticker.info.get(k)
            if v is not None:
                try:
                    f = float(v)
                    if f > 0:
                        return f
                except (TypeError, ValueError):
                    pass
    # fundamentalRatios
    fr = getattr(ticker, "fundamentalRatios", None)
    if fr is not None:
        for attr in ("marketCap", "mktCap", "market_cap"):
            v = getattr(fr, attr, None) if hasattr(fr, attr) else None
            if v is None and isinstance(fr, dict):
                v = fr.get(attr)
            if v is not None:
                try:
                    f = float(v)
                    if f > 0:
                        return f
                except (TypeError, ValueError):
                    pass
    # ticks 中的 generic tick（部分环境可能通过 tickGeneric 传递）
    ticks = getattr(ticker, "ticks", None) or []
    for t in ticks:
        tick_type = getattr(t, "tickType", None)
        value = getattr(t, "value", None)
        if value is not None:
            try:
                f = float(value)
                if f > 1e9:  # 市值通常 > 1B
                    return f
            except (TypeError, ValueError):
                pass
    return None


def get_market_caps_tick165(
    symbols: list[str],
    host: str,
    port: int,
    client_id: int,
    timeout_sec: float = 10.0,
) -> tuple[dict[str, float], list[str]]:
    """
    通过 IB Generic Tick 165 (Miscellaneous Stats) 获取市值。
    Paper Trading 兼容（不依赖 reqFundamentalData，避免 10358）。
    Returns: ({symbol: market_cap}, [errors])
    """
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass
    from ib_insync import IB, Stock

    ib = IB()
    result: dict[str, float] = {}
    errors: list[str] = []
    tickers: list[tuple[str, object]] = []
    all_tickers: list[object] = []

    try:
        ib.connect(host, port, clientId=client_id, timeout=5.0)
        # TICKET_20250314_003_FOLLOWUP_001: 优先请求延时数据 (3=15–20min, 免费)
        # Error 10089 提示 "Delayed market data is available"
        try:
            ib.reqMarketDataType(3)  # 3=Delayed, 4=Delayed-Frozen
        except Exception:
            pass
        for sym in symbols:
            try:
                contract = Stock(sym, "SMART", "USD")
                ticker = ib.reqMktData(contract, genericTickList="165")
                tickers.append((sym, ticker))
                all_tickers.append(ticker)
            except Exception as e:
                errors.append(f"{sym}: reqMktData failed - {e}")

        poll_interval = 0.1
        max_polls = int(timeout_sec / poll_interval)
        for _ in range(max_polls):
            ib.sleep(poll_interval)
            pending = []
            for sym, ticker in tickers:
                if sym in result:
                    continue
                mcap = _extract_mcap_from_ticker(ticker)
                if mcap and mcap > 0:
                    result[sym] = mcap
                else:
                    pending.append((sym, ticker))
            tickers = pending
            if not tickers:
                break

        for sym, _ in tickers:
            errors.append(f"{sym}: timeout waiting for tick 165 data")

        # TICKET_20250314_003_FOLLOWUP_001: 流式无结果时尝试 snapshot 模式
        missing = [s for s in symbols if s not in result]
        if missing and hasattr(ib, "reqMktData"):
            for sym in missing:
                try:
                    contract = Stock(sym, "SMART", "USD")
                    ticker = ib.reqMktData(contract, genericTickList="165", snapshot=True)
                    ib.sleep(3.0)
                    mcap = _extract_mcap_from_ticker(ticker)
                    if mcap and mcap > 0:
                        result[sym] = mcap
                        errors[:] = [e for e in errors if f"{sym}:" not in e]
                    try:
                        ib.cancelMktData(ticker)
                    except Exception:
                        pass
                except Exception as e:
                    pass
    except Exception as e:
        errors.append(f"IB connection: {e}")
    finally:
        for ticker in all_tickers:
            try:
                ib.cancelMktData(ticker)
            except Exception:
                pass
        try:
            ib.disconnect()
        except Exception:
            pass
    return result, errors


def _parse_market_cap_from_xml(xml: str) -> float | None:
    """
    从 IB ReportSnapshot/ReportsFinSummary XML 中解析市值。
    尝试的标签：MKTCAP, MarketCapitalization, MarketCap
    """
    if not xml or not isinstance(xml, str):
        return None
    # 尝试多种可能的标签格式
    for tag in ("MKTCAP", "MarketCapitalization", "MarketCap"):
        m = re.search(rf"<{tag}[^>]*>([^<]+)</{tag}>", xml, re.IGNORECASE)
        if m:
            try:
                v = float(m.group(1).strip().replace(",", ""))
                if v > 0:
                    return v
            except (ValueError, TypeError):
                continue
    return None


def get_market_caps(
    symbols: list[str],
    host: str,
    port: int,
    client_id: int,
    timeout_sec: float = 10.0,
) -> tuple[dict[str, float], list[str]]:
    """
    通过 IB 连接获取多标的市值。
    Returns: ({symbol: market_cap}, [errors])
    """
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass
    from ib_insync import IB, Stock

    ib = IB()
    result: dict[str, float] = {}
    errors: list[str] = []
    try:
        ib.connect(host, port, clientId=client_id, timeout=timeout_sec)
        for sym in symbols:
            try:
                contract = Stock(sym, "SMART", "USD")
                for report_type in ("ReportSnapshot", "ReportsFinSummary"):
                    xml = ib.reqFundamentalData(contract, reportType=report_type)
                    if not xml:
                        continue
                    mcap = _parse_market_cap_from_xml(xml)
                    if mcap and mcap > 0:
                        result[sym] = mcap
                        break
                if sym not in result:
                    errors.append(f"{sym}: no market cap in IB fundamental data")
            except Exception as e:
                errors.append(f"{sym}: {e}")
    except Exception as e:
        errors.append(f"IB connection: {e}")
    finally:
        try:
            ib.disconnect()
        except Exception:
            pass
    return result, errors
