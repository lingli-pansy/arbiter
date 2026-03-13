"""
Momentum20d: 20日动量策略，用于 TASK_0008 run_backtest。
当 close > 20 bar 前的 close 时做多，否则平仓。
使用 order_factory 和 submit_order 与 NT API 兼容。
"""
from __future__ import annotations

from decimal import Decimal

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy


class Momentum20dConfig(StrategyConfig):
    """Momentum20d 策略配置"""
    instrument_id: str
    bar_type: str
    lookback_period: int = 20
    trade_size: Decimal = Decimal("100")


class Momentum20d(Strategy):
    """20日动量策略"""

    def __init__(self, config: Momentum20dConfig) -> None:
        super().__init__(config)
        self._config = config
        self._instrument_id = InstrumentId.from_str(config.instrument_id)
        self._lookback = config.lookback_period
        self._trade_size = config.trade_size
        self._close_history: list[Decimal] = []

    def on_start(self) -> None:
        bt = BarType.from_str(self._config.bar_type)
        self.subscribe_bars(bt)

    def on_bar(self, bar: Bar) -> None:
        self._close_history.append(bar.close.as_decimal())
        if len(self._close_history) < self._lookback + 1:
            return
        self._close_history = self._close_history[-self._lookback - 1 :]
        close_now = self._close_history[-1]
        close_past = self._close_history[0]
        momentum_positive = close_now > close_past
        # NT Portfolio API (TICKET_0005): position_exists 替代已废弃的 position()
        position_exists = self.portfolio.position_exists(self._instrument_id)
        position = None
        if position_exists and self.cache:
            pos_list = self.cache.positions(instrument_id=self._instrument_id)
            position = pos_list[0] if pos_list else None
        if self.order_factory is None:
            return
        if momentum_positive and not position_exists:
            try:
                order = self.order_factory.market(
                    instrument_id=self._instrument_id,
                    order_side=OrderSide.BUY,
                    quantity=Quantity.from_int(int(self._trade_size)),
                )
                self.submit_order(order)
            except Exception:
                pass
        elif not momentum_positive and position_exists and position is not None:
            try:
                qty = position.quantity.as_decimal() if hasattr(position, "quantity") else 0
                if qty > 0:
                    self.close_position(position)
            except Exception:
                pass
