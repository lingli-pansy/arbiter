# Ticket: Fix Momentum20d Strategy - Use Correct NT API

**Ticket ID:** TICKET_20260314_003  
**Created:** 2026-03-14  
**Status:** Done  
**Priority:** P0 (阻塞回测验证)

---

## Source Task
- **Task ID:** TASK_0008B_REVALIDATION
- **Task Title:** Re-validate 2-year momentum backtest after TICKET_0005 fix

---

## Blocking Issue
TICKET_0005 声称修复了策略代码，但实际使用了错误的 API：

```python
# TICKET_0005 修复后代码 (仍然错误)
position_exists = self.portfolio.position_exists(self._instrument_id)  # ❌ 不存在
```

实际错误：
```
'nautilus_trader.portfolio.portfolio.Portfolio' object has no attribute 'position_exists'
```

---

## Root Cause Analysis

NT 1.224.0 Portfolio 实际 API：
- ❌ `position(instrument_id)` - 不存在
- ❌ `position_exists(instrument_id)` - 不存在
- ✅ `net_position(instrument_id)` - 返回净持仓量 (Quantity 或 0)

---

## Fix Required

修改 `/Users/xiaoyu/arbiter-2/system/tools/impl/strategies/momentum_20d.py`:

```python
# 修复前 (第52行)
position_exists = self.portfolio.position_exists(self._instrument_id)
position = None
if position_exists and self.cache:
    pos_list = self.cache.positions(instrument_id=self._instrument_id)
    position = pos_list[0] if pos_list else None

# 修复后
net_pos = self.portfolio.net_position(self._instrument_id)
position_exists = net_pos is not None and net_pos.as_decimal() != 0
position = None
if position_exists:
    # 从 cache 获取完整 position 对象用于平仓
    pos_list = self.cache.positions(instrument_id=self._instrument_id) if self.cache else []
    position = pos_list[0] if pos_list else None
```

---

## Acceptance Criteria

1. [ ] 策略代码修复后不再抛出 AttributeError
2. [ ] 回测能正常生成订单
3. [ ] 回测能正常生成持仓变化
4. [ ] 2年历史数据回测能完整运行

---

## Test Case

**输入:**
```json
{
  "strategy_id": "momentum_20d",
  "nt_bars": {"data": {"AAPL": [...173 bars...]}, "meta": {}},
  "symbols": ["AAPL"],
  "config": {"lookback_period": 20, "trade_size": 100}
}
```

**期望输出:**
```json
{
  "success": true,
  "report": {
    "account_summary": "DataFrame[...]",
    "order_fills": "DataFrame[...]",  // 包含订单
    "positions": "DataFrame[...]",    // 包含持仓
    "metrics": {...}
  },
  "meta": {"status": "completed", "bars_loaded": 173}
}
```

---

## Related

- Original Issue: TICKET_0005 (claimed fixed but incorrect)
- Blocked Task: TASK_0008B_REVALIDATION
- Strategy File: `system/tools/impl/strategies/momentum_20d.py`
