#!/usr/bin/env python3
"""
run_backtest: 执行 NautilusTrader 回测。
契约: system/tools/contracts/run_backtest.yaml
输入: nt_bars (convert_bars_to_nt 输出), strategy_id, symbols, start, end, config。
兼容 convert_bars_to_nt 链路，以 adapter pattern 实现。
"""
from __future__ import annotations

import json
import logging
import math
import os
import sys

# 抑制 NT 日志，避免污染 stdout（工具输出 JSON）
logging.getLogger("nautilus_trader").setLevel(logging.WARNING)
from datetime import datetime, timezone
from decimal import Decimal

try:
    import pandas as pd
except ImportError:
    pd = None

# 确保 impl 在 path 中
_impl_dir = os.path.dirname(os.path.abspath(__file__))
if _impl_dir not in sys.path:
    sys.path.insert(0, _impl_dir)

# 抑制 NT 日志，保证 stdout 只输出 JSON
import logging
logging.getLogger("nautilus_trader").setLevel(logging.WARNING)
logging.getLogger().setLevel(logging.WARNING)

# Venue 标准化: convert_bars_to_nt 用 NASDAQ/NYSE，NT 需要 XNAS/XNYS
VENUE_TO_NT = {"NASDAQ": "XNAS", "NYSE": "XNYS", "ARCA": "ARCA", "UNKNOWN": "XNAS"}


def _calculate_metrics(
    account_summary, order_fills, positions, starting_balance: float = 1_000_000.0
) -> dict:
    """从 NT report DataFrames 计算结构化回测指标 (TICKET_0006)"""
    metrics: dict = {
        "sharpe_ratio": None,
        "max_drawdown_pct": None,
        "cagr_pct": None,
        "win_rate_pct": None,
        "avg_trade_pnl": None,
        "total_trades": 0,
        "profit_factor": None,
        "calmar_ratio": None,
        "volatility_pct": None,
    }
    if pd is None:
        return metrics

    # 从 account_summary 提取 equity curve
    equity = None
    if hasattr(account_summary, "columns") and "total" in account_summary.columns:
        equity = pd.to_numeric(account_summary["total"], errors="coerce").dropna()
    if equity is None or len(equity) < 2:
        return metrics

    # Total trades
    if hasattr(order_fills, "index") and len(order_fills) > 0:
        metrics["total_trades"] = int(len(order_fills))
    elif hasattr(positions, "columns") and hasattr(positions, "index") and len(positions) > 0:
        if "ts_closed" in positions.columns:
            closed = positions[positions["ts_closed"].notna()]
            metrics["total_trades"] = int(len(closed))
        else:
            metrics["total_trades"] = int(len(positions))

    # Returns & Sharpe
    returns = equity.pct_change().dropna()
    if len(returns) > 0 and returns.std() > 0:
        ann_factor = math.sqrt(252)  # 日频
        metrics["sharpe_ratio"] = round(float(returns.mean() / returns.std() * ann_factor), 4)
    if len(returns) > 0:
        metrics["volatility_pct"] = round(float(returns.std() * math.sqrt(252) * 100), 2)

    # Max Drawdown
    cummax = equity.cummax()
    dd = (equity - cummax) / cummax.replace(0, 1)
    if len(dd) > 0:
        metrics["max_drawdown_pct"] = round(float(dd.min() * 100), 2)

    # CAGR
    start_val = float(equity.iloc[0])
    end_val = float(equity.iloc[-1])
    if start_val > 0 and len(equity) > 1:
        try:
            delta = equity.index[-1] - equity.index[0]
            days = delta.total_seconds() / 86400
        except Exception:
            days = float(len(equity))
        years = max(days / 365.25, 1 / 365.25)
        cagr = (end_val / start_val) ** (1 / years) - 1
        metrics["cagr_pct"] = round(float(cagr * 100), 2)

    # Calmar (CAGR / |MaxDD|)
    if metrics["cagr_pct"] is not None and metrics["max_drawdown_pct"] is not None and metrics["max_drawdown_pct"] != 0:
        metrics["calmar_ratio"] = round(metrics["cagr_pct"] / abs(metrics["max_drawdown_pct"]), 4)

    # Win rate, avg PnL, profit factor (from positions or order_fills)
    pnl_col = None
    if hasattr(positions, "columns"):
        for c in ("realized_pnl", "pnl", "realized_pnl_settled"):
            if c in positions.columns:
                pnl_col = c
                break
    if pnl_col and len(positions) > 0:
        pnls = pd.to_numeric(positions[pnl_col], errors="coerce").dropna()
        if len(pnls) > 0:
            wins = (pnls > 0).sum()
            metrics["win_rate_pct"] = round(float(wins / len(pnls) * 100), 2)
            metrics["avg_trade_pnl"] = round(float(pnls.mean()), 2)
            gross_profit = pnls[pnls > 0].sum()
            gross_loss = abs(pnls[pnls < 0].sum())
            if gross_loss > 0:
                metrics["profit_factor"] = round(float(gross_profit / gross_loss), 4)
            else:
                metrics["profit_factor"] = float("inf") if gross_profit > 0 else None

    return metrics


def _normalize_bar_type(bar_type: str) -> str:
    """将 convert_bars_to_nt 的 bar_type 转为 NT 可解析格式（-EXTERNAL 后缀，venue 标准化）"""
    if not bar_type or "-EXTERNAL" in bar_type or "-INTERNAL" in bar_type:
        return bar_type
    # AAPL.NASDAQ-1-DAY-LAST -> AAPL.XNAS-1-DAY-LAST-EXTERNAL
    parts = bar_type.split("-")
    if len(parts) < 2:
        return bar_type + "-EXTERNAL"
    symbol_venue = parts[0]  # AAPL.NASDAQ
    if "." in symbol_venue:
        sym, venue = symbol_venue.rsplit(".", 1)
        nt_venue = VENUE_TO_NT.get(venue.upper(), "XNAS")
        new_sv = f"{sym}.{nt_venue}"
        spec = "-".join(parts[1:])
        return f"{new_sv}-{spec}-EXTERNAL"
    return bar_type + "-EXTERNAL"


def _dict_to_nt_bar(d: dict) -> "Bar | None":
    """将 convert_bars_to_nt 的 bar dict 转为 NT Bar 对象"""
    try:
        from nautilus_trader.model.data import Bar, BarType
        from nautilus_trader.model.objects import Price, Quantity
    except ImportError:
        return None

    bar_type_str = d.get("bar_type")
    if not bar_type_str:
        return None
    bar_type_str = _normalize_bar_type(bar_type_str)
    try:
        bt = BarType.from_str(bar_type_str)
    except Exception:
        return None

    def _p(v) -> str:
        if v is None:
            return "0"
        return str(v) if isinstance(v, str) else str(float(v))

    def _price(v) -> str:
        """确保价格至少 2 位小数，满足 NT Equity price_precision=2"""
        s = _p(v)
        if "." not in s:
            return s + ".00"
        a, b = s.split(".", 1)
        if len(b) < 2:
            return f"{a}.{b}{'0' * (2 - len(b))}"
        return f"{a}.{b[:2]}" if len(b) > 2 else s

    try:
        return Bar(
            bar_type=bt,
            open=Price.from_str(_price(d.get("open"))),
            high=Price.from_str(_price(d.get("high"))),
            low=Price.from_str(_price(d.get("low"))),
            close=Price.from_str(_price(d.get("close"))),
            volume=Quantity.from_str(_p(d.get("volume"))),
            ts_event=int(d.get("ts_event", 0)),
            ts_init=int(d.get("ts_init", 0)),
            is_revision=bool(d.get("is_revision", False)),
        )
    except Exception:
        return None


def _run_engine(nt_bars_list: list, strategy_id: str, symbols: list[str], config: dict) -> dict:
    """运行 NT BacktestEngine，返回 report。全程重定向 stdout 避免 NT 日志污染工具 JSON 输出"""
    try:
        from nautilus_trader.backtest.config import BacktestEngineConfig
        from nautilus_trader.model.data import BarType
        from nautilus_trader.backtest.engine import BacktestEngine
        from nautilus_trader.model.currencies import USD
        from nautilus_trader.model.enums import AccountType, OmsType
        from nautilus_trader.model.identifiers import TraderId, Venue
        from nautilus_trader.model.objects import Money
        from nautilus_trader.test_kit.providers import TestInstrumentProvider
    except ImportError as e:
        return {"_error": f"nautilus_trader not available: {e}"}

    if not nt_bars_list:
        return {"_error": "No bars to run"}

    devnull = open(os.devnull, "w")
    old_stdout = sys.stdout
    try:
        sys.stdout = devnull
        return _run_engine_impl(nt_bars_list, strategy_id, symbols, config)
    finally:
        sys.stdout = old_stdout
        devnull.close()


def _run_engine_impl(nt_bars_list: list, strategy_id: str, symbols: list[str], config: dict) -> dict:
    """_run_engine 内部实现，调用时 stdout 已重定向"""
    from nautilus_trader.backtest.config import BacktestEngineConfig
    from nautilus_trader.model.data import BarType
    from nautilus_trader.backtest.engine import BacktestEngine
    from nautilus_trader.model.currencies import USD
    from nautilus_trader.model.enums import AccountType, OmsType
    from nautilus_trader.model.identifiers import TraderId, Venue
    from nautilus_trader.model.objects import Money
    from nautilus_trader.test_kit.providers import TestInstrumentProvider

    engine_config = BacktestEngineConfig(trader_id=TraderId("ARBITER-BACKTEST-001"))
    engine = BacktestEngine(config=engine_config)

    venue = Venue("XNAS")
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        base_currency=None,
        starting_balances=[Money(1_000_000, USD)],
    )

    seen_instruments = set()
    for bar in nt_bars_list:
        bt = bar.bar_type
        iid = bt.instrument_id
        key = str(iid)
        if key not in seen_instruments:
            seen_instruments.add(key)
            sym = iid.symbol.value
            inst = TestInstrumentProvider.equity(symbol=sym, venue="XNAS")
            engine.add_instrument(inst)

    engine.add_data(nt_bars_list, sort=True)

    if strategy_id == "momentum_20d":
        from strategies.momentum_20d import Momentum20d, Momentum20dConfig
        from nautilus_trader.model.identifiers import InstrumentId

        bt = nt_bars_list[0].bar_type
        instrument_id = str(bt.instrument_id)
        cfg = Momentum20dConfig(
            instrument_id=instrument_id,
            bar_type=str(bt),
            lookback_period=config.get("lookback_period", 20),
            trade_size=Decimal(str(config.get("trade_size", 100))),
        )
        strategy = Momentum20d(config=cfg)
    elif strategy_id == "ema_cross":
        from nautilus_trader.config import ImportableStrategyConfig

        instrument_id = str(nt_bars_list[0].bar_type.instrument_id)
        bar_type_str = str(nt_bars_list[0].bar_type)
        strategies = [
            ImportableStrategyConfig(
                strategy_path="nautilus_trader.examples.strategies.ema_cross:EMACross",
                config_path="nautilus_trader.examples.strategies.ema_cross:EMACrossConfig",
                config={
                    "instrument_id": instrument_id,
                    "bar_type": bar_type_str,
                    "trade_size": Decimal(1_000_000),
                    "fast_ema_period": 10,
                    "slow_ema_period": 20,
                },
            ),
        ]
        for sc in strategies:
            s = sc.create_strategy()
            engine.add_strategy(s)
    else:
        from strategies.momentum_20d import Momentum20d, Momentum20dConfig

        bt = nt_bars_list[0].bar_type
        instrument_id = str(bt.instrument_id)
        cfg = Momentum20dConfig(
            instrument_id=instrument_id,
            bar_type=str(bt),
            lookback_period=config.get("lookback_period", 20),
            trade_size=Decimal(str(config.get("trade_size", 100))),
        )
        strategy = Momentum20d(config=cfg)

    if strategy_id == "ema_cross":
        pass
    else:
        engine.add_strategy(strategy)

    engine.run()
    report = {}
    try:
        report["account_summary"] = engine.trader.generate_account_report(venue)
    except Exception as e:
        report["account_summary"] = str(e)
    try:
        report["order_fills"] = engine.trader.generate_order_fills_report()
    except Exception as e:
        report["order_fills"] = str(e)
    try:
        report["positions"] = engine.trader.generate_positions_report()
    except Exception as e:
        report["positions"] = str(e)

    # TICKET_0006: 计算结构化回测指标
    try:
        report["metrics"] = _calculate_metrics(
            report.get("account_summary"),
            report.get("order_fills"),
            report.get("positions"),
        )
    except Exception:
        report["metrics"] = {}

    engine.dispose()
    return report


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _validate(params: dict) -> str | None:
    if not params.get("strategy_id"):
        return "strategy_id is required"
    nb = params.get("nt_bars")
    if not nb:
        return "nt_bars is required"
    if not isinstance(nb, dict):
        return "nt_bars must be object"
    data = nb.get("data")
    if not isinstance(data, dict):
        return "nt_bars must contain data (symbol -> bars)"
    total = sum(len(b) for b in data.values() if isinstance(b, list))
    if total == 0:
        return "nt_bars.data must contain at least one bar"
    return None


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "report": {}, "errors": [params["_error"]], "meta": {}}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    err = _validate(params)
    if err:
        out = {"success": False, "report": {}, "errors": [err], "meta": {}}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    nb = params["nt_bars"]
    data = nb.get("data", {})
    meta = nb.get("meta", {})
    strategy_id = params["strategy_id"]
    symbols = params.get("symbols") or list(data.keys())
    config = params.get("config") or {}

    all_bars = []
    for symbol, bars in data.items():
        if not isinstance(bars, list):
            continue
        for b in bars:
            if not isinstance(b, dict):
                continue
            bar = _dict_to_nt_bar(b)
            if bar:
                all_bars.append(bar)

    if not all_bars:
        out = {"success": False, "report": {}, "errors": ["No valid bars after conversion"], "meta": {}}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    all_bars.sort(key=lambda x: x.ts_init)

    result = _run_engine(all_bars, strategy_id, symbols, config)
    if "_error" in result:
        out = {
            "success": False,
            "report": {},
            "errors": [result["_error"]],
            "meta": {"strategy_id": strategy_id, "symbols": symbols, "bars_loaded": len(all_bars), "status": "failed"},
        }
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    out = {
        "success": True,
        "report": result,
        "errors": [],
        "meta": {
            "strategy_id": strategy_id,
            "symbols": symbols,
            "bars_loaded": len(all_bars),
            "status": "completed",
        },
    }
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        out = {"success": False, "report": {}, "errors": [str(e)], "meta": {"status": "crashed"}}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)
