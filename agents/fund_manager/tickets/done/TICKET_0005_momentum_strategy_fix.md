# TICKET_0005: Fix Momentum20d Strategy Portfolio API

**Status:** open  
**Created:** 2026-03-13  
**Source Task:** TASK_0008B (2-year historical momentum backtest)  
**Blocking Issue:** `unstable_error_surface`

---

## Blocking Issue

`momentum_20d` 策略在执行时崩溃，因为使用了错误的 NautilusTrader Portfolio API：

```
AttributeError: 'nautilus_trader.portfolio.portfolio.Portfolio' object has no attribute 'position'
```

错误位置：`strategies/momentum_20d.py:49`
```python
position = self.portfolio.position(self._instrument_id)  # ❌ 错误
```

## Requested Capability

修复 `Momentum20d` 策略代码，使用正确的 NautilusTrader API 获取持仓信息。

## Why Existing Tools Are Insufficient

策略实现存在 bug，导致回测无法完成。这不是数据或配置问题，而是代码实现错误。

## Root Cause Analysis

NautilusTrader 1.224.0 的 Portfolio API 变更：
- ❌ `portfolio.position(instrument_id)` - 不存在
- ✅ `portfolio.positions()` - 返回所有持仓
- ✅ `portfolio.position_exists(instrument_id)` - 检查持仓是否存在
- ✅ `portfolio.net_position(instrument_id)` - 获取净持仓量

## Fix Required

修改 `system/tools/impl/strategies/momentum_20d.py`:

```python
# 修复前 (第49行)
position = self.portfolio.position(self._instrument_id)
if momentum_positive and position is None:
    ...
elif not momentum_positive and position is not None and position.quantity.as_decimal() > 0:
    ...

# 修复后
position_exists = self.portfolio.position_exists(self._instrument_id)
if momentum_positive and not position_exists:
    # 买入逻辑
    ...
elif not momentum_positive and position_exists:
    # 平仓逻辑
    position = self.portfolio.positions()[self._instrument_id]
    if position.quantity.as_decimal() > 0:
        ...
```

## Acceptance Criteria

1. [ ] 策略代码修复后不再抛出 AttributeError
2. [ ] 回测能正常生成订单
3. [ ] 回测能正常生成持仓
4. [ ] 2年历史数据回测能完整运行

## Test Case

**输入:**
```json
{
  "strategy_id": "momentum_20d",
  "nt_bars": {"data": {"AAPL": [...27 bars...]}, "meta": {}},
  "symbols": ["AAPL"],
  "config": {"trade_size": 10}
}
```

**期望输出:**
```json
{
  "success": true,
  "report": {
    "account_summary": "DataFrame[...]",
    "order_fills": "DataFrame[...]",  // 包含订单
    "positions": "DataFrame[...]"     // 包含持仓
  },
  "meta": {"status": "completed", "bars_loaded": 27}
}
```

## Related Tasks

- TASK_0008B: 2-year historical momentum backtest (blocked by this)
- TASK_0008: Run first backtest (completed with mock data)

## Notes

- 这是一个实现 bug，不是工具缺失
- 需要修改 `system/tools/impl/strategies/momentum_20d.py`
- 其他策略（如 ema_cross）可能也需要检查相同问题
