#!/usr/bin/env python3
"""
calculate_portfolio_performance: 计算组合表现指标（收益、回撤、波动率等）。
契约: system/tools/contracts/calculate_portfolio_performance.yaml
输入: portfolio_id 或 portfolio，可选 market_data、start_date、end_date、benchmark。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
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


def _load_portfolio(params: dict) -> dict | None:
    portfolio = params.get("portfolio")
    if isinstance(portfolio, dict) and portfolio.get("assets"):
        return portfolio
    pid = params.get("portfolio_id") or (portfolio if isinstance(portfolio, str) else None)
    if not pid or not str(pid).strip():
        return None
    safe_id = _sanitize_id(str(pid).strip())
    path = STATE_DIR / f"{safe_id}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _fetch_market_data(symbols: list[str], start_date: str, end_date: str) -> dict:
    """调用 get_market_bars_batch 获取市场数据"""
    lookback = max(1, (datetime.fromisoformat(end_date.replace("Z", "+00:00")) -
                       datetime.fromisoformat(start_date.replace("Z", "+00:00"))).days + 5)
    req = {
        "symbols": symbols,
        "lookback_days": min(lookback, 252),
        "timeframe": "1d",
        "provider": "yahoo",
    }
    try:
        r = subprocess.run(
            [sys.executable, str(_impl_dir / "get_market_bars_batch.py")],
            input=json.dumps(req).encode(),
            capture_output=True,
            timeout=30,
            cwd=str(_impl_dir),
        )
        if r.returncode != 0 or not r.stdout:
            return {}
        out = json.loads(r.stdout.decode())
        return out.get("data", {}) if out.get("success") else {}
    except Exception:
        return {}


def _build_price_series(data: dict) -> dict[str, dict[str, float]]:
    """data[symbol] = [{timestamp, close}, ...] -> dates[symbol][date] = close"""
    dates: dict[str, dict[str, float]] = defaultdict(dict)
    for symbol, rows in (data or {}).items():
        if not isinstance(rows, list):
            continue
        for r in rows:
            ts = r.get("timestamp") or r.get("date")
            close = r.get("close")
            if ts is None or close is None:
                continue
            try:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            except Exception:
                continue
            date_key = dt.strftime("%Y-%m-%d")
            try:
                dates[symbol][date_key] = float(close)
            except (TypeError, ValueError):
                pass
    return dict(dates)


def _align_dates(price_series: dict) -> list[str]:
    """所有标的共有的交易日，按日期排序"""
    if not price_series:
        return []
    common = None
    for sym, dates in price_series.items():
        s = set(dates.keys())
        common = s if common is None else common & s
    return sorted(common or [])


def _portfolio_value_series(
    assets: list[dict],
    price_series: dict[str, dict[str, float]],
    dates: list[str],
    initial_capital: float,
) -> list[tuple[str, float]]:
    """计算每日组合净值序列"""
    weights = {str(a.get("symbol", "")).strip(): float(a.get("weight", 0)) for a in assets}
    if not dates or not weights:
        return []

    values = []
    first_prices = {}
    for d in dates:
        total = 0.0
        for sym, w in weights.items():
            prices = price_series.get(sym, {})
            p = prices.get(d)
            if p is None:
                continue
            if d == dates[0]:
                first_prices[sym] = p
            fp = first_prices.get(sym)
            if fp and fp > 0:
                total += w * (p / fp)
        if total > 0:
            values.append((d, initial_capital * total))
        elif values:
            values.append((d, values[-1][1]))
    return values


def _benchmark_value_series(
    symbol: str,
    price_series: dict[str, dict[str, float]],
    dates: list[str],
    initial: float = 100.0,
) -> list[tuple[str, float]]:
    """基准净值序列"""
    prices = price_series.get(symbol, {})
    if not dates or symbol not in price_series:
        return []
    p0 = prices.get(dates[0])
    if not p0 or p0 <= 0:
        return []
    return [(d, initial * (prices.get(d, p0) / p0)) for d in dates]


def _compute_returns(values: list[tuple[str, float]]) -> tuple[list[float], float]:
    v = [x[1] for x in values]
    if len(v) < 2:
        return [], 0.0
    total_return = (v[-1] / v[0]) - 1.0 if v[0] else 0.0
    returns = []
    for i in range(1, len(v)):
        if v[i - 1] and v[i - 1] > 0:
            returns.append((v[i] - v[i - 1]) / v[i - 1])
        else:
            returns.append(0.0)
    return returns, total_return


def _compute_drawdown(values: list[tuple[str, float]]) -> tuple[float, str | None, float]:
    v = [x[1] for x in values]
    d = [x[0] for x in values]
    if not v:
        return 0.0, None, 0.0
    peak = v[0]
    max_dd = 0.0
    max_dd_date = None
    dd_sum = 0.0
    dd_count = 0
    for i, val in enumerate(v):
        if val > peak:
            peak = val
        if peak > 0:
            dd = (val - peak) / peak
            dd_sum += dd
            dd_count += 1
            if dd < max_dd:
                max_dd = dd
                max_dd_date = d[i] if i < len(d) else None
    avg_dd = dd_sum / dd_count if dd_count else 0.0
    return max_dd, max_dd_date, avg_dd


def _compute_volatility(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(var * 252) * 100 if var >= 0 else 0.0


def _compute_sharpe(returns: list[float], risk_free: float = 0.0) -> float | None:
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(var)
    if std <= 0:
        return None
    excess = (mean - risk_free / 252) * 252
    return round(excess / (std * math.sqrt(252)), 4)


def _compute_sortino(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    neg = [r for r in returns if r < 0]
    if not neg:
        return None
    downside = math.sqrt(sum(r ** 2 for r in neg) / len(neg))
    if downside <= 0:
        return None
    return round(mean * 252 / (downside * math.sqrt(252)), 4)


def _compute_alpha_beta(
    port_returns: list[float],
    bench_returns: list[float],
    port_total: float,
    bench_total: float,
) -> tuple[float | None, float | None]:
    if len(port_returns) < 2 or len(bench_returns) < 2 or len(port_returns) != len(bench_returns):
        return None, None
    n = len(port_returns)
    mean_p = sum(port_returns) / n
    mean_b = sum(bench_returns) / n
    cov = sum((p - mean_p) * (b - mean_b) for p, b in zip(port_returns, bench_returns)) / (n - 1)
    var_b = sum((b - mean_b) ** 2 for b in bench_returns) / (n - 1)
    if var_b <= 0:
        return None, None
    beta = cov / var_b
    alpha = (port_total - bench_total) * 100
    return round(alpha, 4), round(beta, 4)


def _compute_tracking_error(port_returns: list[float], bench_returns: list[float]) -> float | None:
    if len(port_returns) < 2 or len(port_returns) != len(bench_returns):
        return None
    diff = [p - b for p, b in zip(port_returns, bench_returns)]
    mean = sum(diff) / len(diff)
    var = sum((d - mean) ** 2 for d in diff) / (len(diff) - 1)
    return round(math.sqrt(var * 252) * 100, 4) if var >= 0 else None


def _compute_info_ratio(port_returns: list[float], bench_returns: list[float]) -> float | None:
    te = _compute_tracking_error(port_returns, bench_returns)
    if te is None or te <= 0:
        return None
    diff = [p - b for p, b in zip(port_returns, bench_returns)]
    mean = sum(diff) / len(diff) * 252 * 100
    return round(mean / te, 4)


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "performance": {}, "errors": [params["_error"]]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    portfolio = _load_portfolio(params)
    if not portfolio:
        out = {"success": False, "performance": {}, "errors": ["portfolio or portfolio_id required"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    assets = portfolio.get("assets", [])
    if not assets:
        out = {"success": False, "performance": {}, "errors": ["portfolio has no assets"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    initial_capital = float(portfolio.get("initial_capital", 100000))
    benchmark = str(params.get("benchmark", "SPY")).strip()
    start_date = params.get("start_date") or portfolio.get("created_at", "")[:10]
    end_date = params.get("end_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    symbols = [str(a.get("symbol", "")).strip() for a in assets]
    all_symbols = sorted(set(symbols) | {benchmark})

    market_data = params.get("market_data") or params.get("data")
    if not market_data or not isinstance(market_data, dict):
        market_data = _fetch_market_data(all_symbols, start_date, end_date)
    raw_data = market_data.get("data", market_data) if isinstance(market_data, dict) else {}

    price_series = _build_price_series(raw_data)
    if not price_series:
        out = {"success": False, "performance": {}, "errors": ["No market data available"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    dates = _align_dates(price_series)
    if len(dates) < 2:
        out = {"success": False, "performance": {}, "errors": ["Insufficient aligned price data"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    values = _portfolio_value_series(assets, price_series, dates, initial_capital)
    if len(values) < 2:
        out = {"success": False, "performance": {}, "errors": ["Could not compute portfolio values"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    returns, total_return = _compute_returns(values)
    max_dd, max_dd_date, avg_dd = _compute_drawdown(values)
    volatility = _compute_volatility(returns)
    sharpe = _compute_sharpe(returns)
    sortino = _compute_sortino(returns)
    cagr = 0.0
    if values[0][1] and values[0][1] > 0 and len(dates) >= 1:
        try:
            days = (datetime.fromisoformat(dates[-1]) - datetime.fromisoformat(dates[0])).days
            years = max(days / 365.25, 1 / 365.25)
            cagr = ((values[-1][1] / values[0][1]) ** (1 / years) - 1) * 100
        except Exception:
            pass
    calmar = (cagr / abs(max_dd * 100)) if max_dd and max_dd != 0 else None

    bench_values = _benchmark_value_series(benchmark, price_series, dates)
    bench_returns, bench_total = _compute_returns(bench_values) if bench_values else ([], 0.0)
    min_len = min(len(returns), len(bench_returns))
    pr = returns[:min_len] if min_len else []
    br = bench_returns[:min_len] if min_len else []
    alpha, beta = _compute_alpha_beta(pr, br, total_return, bench_total)
    tracking_error = _compute_tracking_error(pr, br)
    info_ratio = _compute_info_ratio(pr, br)

    performance = {
        "period": {
            "start": dates[0],
            "end": dates[-1],
            "days": len(dates),
        },
        "returns": {
            "total_return_pct": round(total_return * 100, 2),
            "cagr_pct": round(cagr, 2),
        },
        "drawdown": {
            "max_drawdown_pct": round(max_dd * 100, 2),
            "max_drawdown_date": max_dd_date,
            "current_drawdown_pct": round(
                ((values[-1][1] - max(v[1] for v in values)) / max(v[1] for v in values) * 100)
                if values and max(v[1] for v in values) > 0 else 0,
                2,
            ),
            "avg_drawdown_pct": round(avg_dd * 100, 2),
        },
        "risk": {
            "volatility_annual_pct": round(volatility, 2),
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": round(calmar, 4) if calmar is not None else None,
        },
        "benchmark": {
            "symbol": benchmark,
            "benchmark_return_pct": round(bench_total * 100, 2) if bench_values else None,
            "alpha": alpha,
            "beta": beta,
            "tracking_error": tracking_error,
            "information_ratio": info_ratio,
        },
    }

    out = {"success": True, "performance": performance, "errors": []}
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
