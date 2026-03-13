"""
MeanReversion: 均值回归策略，用于 TASK_0010 策略对比。
当价格低于 N 日均线 X% 时做多，回归均线时平仓。
"""
from __future__ import annotations

from decimal import Decimal

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy


class MeanReversionConfig(StrategyConfig):
    """MeanReversion 策略配置"""
    instrument_id: str
    bar_type: str
    lookback_period: int = 20
    deviation_threshold: float = 0.02  # 2%，价格低于 MA*(1-threshold) 时买入
    trade_size: Decimal = Decimal("100")


class MeanReversion(Strategy):
    """均值回归策略：价格偏离均线后回归时交易"""

    def __init__(self, config: MeanReversionConfig) -> None:
        super().__init__(config)
        self._config = config
        self._instrument_id = InstrumentId.from_str(config.instrument_id)
        self._lookback = config.lookback_period
        self._threshold = config.deviation_threshold
        self._trade_size = config.trade_size
        self._close_history: list[Decimal] = []

    def on_start(self) -> None:
        bt = BarType.from_str(self._config.bar_type)
        self.subscribe_bars(bt)

    def on_bar(self, bar: Bar) -> None:
        self._close_history.append(bar.close.as_decimal())
        if len(self._close_history) < self._lookback:
            return
        self._close_history = self._close_history[-self._lookback:]
        close_now = self._close_history[-1]
        ma = sum(self._close_history) / len(self._close_history)
        if ma <= 0:
            return
        deviation = float((close_now - ma) / ma)
        # NT Portfolio API (TICKET_20260314_003): net_position 替代不存在的 position_exists
        net_pos = self.portfolio.net_position(self._instrument_id)
        position_exists = net_pos is not None and net_pos != 0
        position = None
        if position_exists and self.cache:
            pos_list = self.cache.positions(instrument_id=self._instrument_id)
            position = pos_list[0] if pos_list else None
        if self.order_factory is None:
            return
        if deviation < -self._threshold and not position_exists:
            try:
                order = self.order_factory.market(
                    instrument_id=self._instrument_id,
                    order_side=OrderSide.BUY,
                    quantity=Quantity.from_int(int(self._trade_size)),
                )
                self.submit_order(order)
            except Exception:
                pass
        elif deviation >= 0 and position_exists and position is not None:
            try:
                qty = position.quantity.as_decimal() if hasattr(position, "quantity") else 0
                if qty > 0:
                    self.close_position(position)
            except Exception:
                pass
