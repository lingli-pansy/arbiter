#!/usr/bin/env python3
"""
run_market_cap_rotation_backtest: 市值 Top N 轮动策略回测。TICKET_20250314_BACKTEST_001
"""
from __future__ import annotations
import json
import math
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
_impl = Path(__file__).resolve().parent

def _call_ranking(date: str, top_n: int, source: str = "yahoo", mock_mode: bool = False):
    """source=yahoo 用于历史回测（无 IB 可运行）；source=ib 需先 connect_broker。返回 symbols 列表（按市值排名顺序）。"""
    payload = {"date": date, "top_n": top_n, "source": source}
    if mock_mode:
        payload["mock_mode"] = True
    r = subprocess.run([sys.executable, str(_impl / "get_market_cap_ranking.py")],
        input=json.dumps(payload).encode(),
        capture_output=True, timeout=15 if mock_mode else 90, cwd=str(_impl))
    out = json.loads(r.stdout.decode()) if r.returncode == 0 else {}
    return [x["symbol"] for x in out.get("ranking", [])] if out.get("success") else []

def _call_bars(symbols: list, start: str, end: str, mock_mode: bool = False) -> dict:
    payload = {
        "symbols": symbols,
        "start_date": start,
        "end_date": end,
        "timeframe": "1d",
        "provider": "yahoo",
    }
    if mock_mode:
        payload["mock_mode"] = True
    r = subprocess.run(
        [sys.executable, str(_impl / "get_market_bars_batch.py")],
        input=json.dumps(payload).encode(),
        capture_output=True,
        timeout=15 if mock_mode else 120,
        cwd=str(_impl),
    )
    out = json.loads(r.stdout.decode()) if r.returncode == 0 else {}
    return out.get("data", {}) if out.get("success") else {}

def _price_series(data: dict) -> dict:
    ps = defaultdict(dict)
    for sym, rows in (data or {}).items():
        for r in (rows or []):
            ts = r.get("timestamp") or r.get("date")
            c = r.get("close")
            if ts and c is not None:
                try:
                    d = datetime.fromisoformat(str(ts).replace("Z", "")).strftime("%Y-%m-%d")
                    ps[sym][d] = float(c)
                except: pass
    return dict(ps)

def _nearest_date(ps: dict, target: str) -> str | None:
    dates = sorted(ps.keys())
    if not dates: return None
    for d in dates:
        if d >= target: return d
    return dates[-1]

def _alloc_weights(syms: list, equal_weight: bool) -> dict[str, float]:
    """返回 symbol -> 分配权重。等权时均分；市值加权时 rank 越高权重越大 (3,2,1 -> 50%,33%,17%)"""
    if not syms:
        return {}
    n = len(syms)
    if equal_weight:
        return {s: 1.0 / n for s in syms}
    # 市值加权: rank 1 权重最大，w_i = (n - i + 1) / sum(1..n)
    total = n * (n + 1) / 2
    return {syms[i]: (n - i) / total for i in range(n)}


def _quarterly_dates(start: str, end: str) -> list[str]:
    """季度末调仓日：3/6/9/12 月末。"""
    out = []
    sy, sm, sd = map(int, start.split("-"))
    ey, em, ed = map(int, end.split("-"))
    for y in range(sy, ey + 1):
        for m in (3, 6, 9, 12):
            d = (datetime(y, m + 1, 1) - timedelta(days=1)) if m < 12 else datetime(y, 12, 31)
            ds = d.strftime("%Y-%m-%d")
            if start <= ds <= end:
                out.append(ds)
    return sorted(set(out))


def _monthly_dates(start: str, end: str) -> list[str]:
    """每月末调仓日。TICKET_20250314_BACKTEST_001_FOLLOWUP_005"""
    out = []
    sy, sm, sd = map(int, start.split("-"))
    ey, em, ed = map(int, end.split("-"))
    for y in range(sy, ey + 1):
        for m in range(1, 13):
            if y == sy and m < sm:
                continue
            if y == ey and m > em:
                break
            d = (datetime(y, m + 1, 1) - timedelta(days=1)) if m < 12 else datetime(y, 12, 31)
            ds = d.strftime("%Y-%m-%d")
            if start <= ds <= end:
                out.append(ds)
    return sorted(set(out))

def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    try:
        params = json.loads(raw)
    except: params = {}
    start_date = params.get("start_date", "2024-01-01")
    end_date = params.get("end_date", "2025-01-01")
    initial_capital = float(params.get("initial_capital", 500000))
    cash_pool = float(params.get("cash_pool", 50000))
    top_n = int(params.get("top_n", 5))
    benchmark = params.get("benchmark", "QQQ")
    equal_weight = params.get("equal_weight", True)  # TICKET_20250314_BACKTEST_001_FOLLOWUP_006
    investable = initial_capital - cash_pool
    source = params.get("source", "yahoo")
    rebalance_freq = params.get("rebalance_frequency", "quarterly")  # TICKET_20250314_BACKTEST_001_FOLLOWUP_005
    mock_mode = params.get("mock_mode") is True  # TICKET_20250314_BACKTEST_001_FOLLOWUP_007
    rebalance_dates = _monthly_dates(start_date, end_date) if rebalance_freq == "monthly" else _quarterly_dates(start_date, end_date)
    all_symbols = set()
    for d in rebalance_dates:
        syms = _call_ranking(d, top_n + 5, source, mock_mode)
        all_symbols.update(syms[:top_n])
    if not all_symbols:
        syms = _call_ranking(start_date, top_n, source, mock_mode)
        all_symbols.update(syms)
    all_symbols.add(benchmark)
    symbols = [benchmark] + [s for s in all_symbols if s != benchmark][:9]
    data = _call_bars(symbols, start_date, end_date, mock_mode)
    ps = _price_series(data)
    if not ps:
        print(json.dumps({"success": False, "report": None, "errors": ["No price data"]}))
        sys.exit(1)
    dates = sorted(set().union(*[set(ps[s].keys()) for s in ps if ps[s]]))
    if not dates:
        print(json.dumps({"success": False, "report": None, "errors": ["No dates"]}))
        sys.exit(1)
    dates = [d for d in dates if start_date <= d <= end_date]
    # TICKET_20250314_BACKTEST_001_FOLLOWUP_008: 季度末可能为周末，映射为最近的下一个交易日
    effective_rb_dates = []
    for rb in rebalance_dates:
        for d in dates:
            if d >= rb:
                effective_rb_dates.append(d)
                break
    rb_set = set(effective_rb_dates)
    positions = {}
    cash = cash_pool
    equity_curve = []
    rebalances = []
    for d in dates:
        if d == dates[0] or d in rb_set:
            nd = _nearest_date(ps.get(list(ps.keys())[0], {}), d) if ps else d
            syms = _call_ranking(nd, top_n, source, mock_mode) if (d == dates[0] or d in rb_set) else list(positions.keys())
            if not syms:
                syms = list(positions.keys())[:top_n] if positions else []
            if d == dates[0] and not positions:
                prices = {s: ps.get(s, {}).get(_nearest_date(ps.get(s, {}), d) or d) or 0 for s in syms}
                if equal_weight:
                    per = (investable / len(syms)) if syms else 0
                    for s in syms:
                        if prices.get(s) and prices[s] > 0:
                            positions[s] = per / prices[s]
                else:
                    # 市值加权: 排名越高权重越大，rank1=3/6, rank2=2/6, rank3=1/6 (top_n=3)
                    n = len(syms)
                    denom = n * (n + 1) // 2
                    for i, s in enumerate(syms):
                        if prices.get(s) and prices[s] > 0:
                            w = (n - i) / denom
                            positions[s] = (investable * w) / prices[s]
                cash = cash_pool
            elif d in rb_set and syms:
                pv = sum(positions.get(s, 0) * (ps.get(s, {}).get(d) or ps.get(s, {}).get(_nearest_date(ps.get(s, {}), d)) or 0) for s in positions)
                cash = cash + pv
                positions = {}
                investable_rb = cash - cash_pool
                weights = _alloc_weights(syms, equal_weight)
                prices = {s: ps.get(s, {}).get(d) or ps.get(s, {}).get(_nearest_date(ps.get(s, {}), d)) for s in syms}
                for s in syms:
                    if prices.get(s) and prices[s] and prices[s] > 0:
                        w = weights.get(s, 1.0 / len(syms))
                        positions[s] = (investable_rb * w) / prices[s]
                cash = cash_pool
                rebalances.append({"date": d, "selected_symbols": syms, "portfolio_value": round(pv + cash, 2), "cash_position": round(cash, 2)})
        pv = sum(positions.get(s, 0) * (ps.get(s, {}).get(d) or 0) for s in positions)
        bm = ps.get(benchmark, {})
        bv = (bm.get(d) or 0) / (bm.get(dates[0]) or 1) * investable if bm else 0
        equity_curve.append({"date": d, "portfolio_value": round(pv + cash, 2), "benchmark_value": round(bv, 2)})
    total_ret = (equity_curve[-1]["portfolio_value"] - initial_capital) / initial_capital * 100 if equity_curve else 0
    bench_ret = (equity_curve[-1]["benchmark_value"] - investable) / investable * 100 if equity_curve else 0
    peak = initial_capital
    mdd = 0
    for e in equity_curve:
        v = e["portfolio_value"]
        if v > peak: peak = v
        if peak > 0: mdd = min(mdd, (v - peak) / peak * 100)
    days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
    cagr = ((equity_curve[-1]["portfolio_value"] / initial_capital) ** (365 / max(days, 1)) - 1) * 100 if equity_curve and days else 0
    report = {
        "strategy_name": "US Large Cap Rotation",
        "period": {"start": start_date, "end": end_date},
        "initial_capital": initial_capital,
        "cash_pool": cash_pool,
        "rebalances": rebalances,
        "equity_curve": equity_curve,
        "metrics": {
            "total_return_pct": round(total_ret, 2),
            "cagr_pct": round(cagr, 2),
            "max_drawdown_pct": round(mdd, 2),
            "benchmark_return_pct": round(bench_ret, 2),
            "alpha": round(total_ret - bench_ret, 2),
        },
    }
    print(json.dumps({"success": True, "report": report, "errors": []}, default=str))
if __name__ == "__main__": main()
