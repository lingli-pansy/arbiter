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
import os
import sys

# 抑制 NT 日志，避免污染 stdout（工具输出 JSON）
logging.getLogger("nautilus_trader").setLevel(logging.WARNING)
from datetime import datetime, timezone
from decimal import Decimal

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
