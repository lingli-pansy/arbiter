# Capability Validation Report: Momentum20d Strategy Fix (TICKET_0005)

**Validation Date:** 2026-03-13  
**Ticket ID:** TICKET_0005  
**Source Task:** TASK_0008B (2-year historical momentum backtest)  
**Validator:** OpenClaw Fund Manager (Dev)

---

## Capability Tested

`Momentum20d` 策略修复 - 修复 Portfolio API 调用错误

## Ticket ID

TICKET_0005: Fix Momentum20d Strategy Portfolio API

## Test Inputs

```json
{
  "strategy_id": "momentum_20d",
  "nt_bars": {
    "data": {
      "AAPL": [
        {"bar_type": "AAPL.XNAS-1-DAY-LAST-EXTERNAL", "open": "169.5", "high": "171.0", "low": "169.0", "close": "170.0", "volume": "1000000", "ts_event": 1672531200000000000, "ts_init": 1672531200000000000, "is_revision": False},
        // ... 30 bars total, price trending 170.0 -> 213.5
      ]
    },
    "meta": {"timeframe": "1d"}
  },
  "symbols": ["AAPL"],
  "config": {"trade_size": 10}
}
```

**Test Data Characteristics:**
- 30 bars (20 warmup + 10 trading days)
- Clear upward momentum: 170.0 → 213.5 (+25.6%)
- Daily interval, XNAS venue

## Observed Result

| Test Item | Expected | Observed | Status |
|-----------|----------|----------|--------|
| Backtest execution | No crash | ✅ Success | PASS |
| Bars loaded | 30 | ✅ 30 | PASS |
| Order generation | At least 1 | ✅ 1 order | PASS |
| Position tracking | Position created | ✅ Position | PASS |

### Key Outputs

**Backtest Status:**
```json
{
  "success": true,
  "meta": {
    "strategy_id": "momentum_20d",
    "symbols": ["AAPL"],
    "bars_loaded": 30,
    "status": "completed"
  }
}
```

**Order Generated:**
- Client Order ID: `O-20230121-000000-001-000-1`
- Trader ID: `ARBITER-BACKTEST-001`
- Side: BUY (market order)
- Quantity: 10 shares

**Position Created:**
- Position tracked in portfolio
- Net qty: 10 (after buy)

## Pass/Fail

**PASS** ✅

所有验收标准满足：
- [x] 策略代码修复后不再抛出 AttributeError
- [x] 回测能正常生成订单
- [x] 回测能正常生成持仓
- [x] 完整回测能运行完成

## Code Changes Verified

修复前 (bug):
```python
position = self.portfolio.position(self._instrument_id)  # ❌ 不存在
```

修复后 (working):
```python
net_qty = self.portfolio.net_position(self._instrument_id)  # ✅
positions = self.cache.positions(instrument_id=self._instrument_id)  # ✅
position = positions[0] if positions else None
```

## Issues Found

None. 策略修复成功。

## Follow-up Tickets

None required for this fix.

---

**Conclusion:**  
TICKET_0005 修复验证通过。`Momentum20d` 策略现在可以正确执行，生成订单和持仓。TASK_0008B 可以解除阻塞并重新执行。
