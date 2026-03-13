# Task Run Report: TASK_0008B_REVALIDATION

**Task ID:** TASK_0008B_REVALIDATION  
**Title:** Re-validate 2-year momentum backtest after TICKET_0005 fix  
**Executed:** 2026-03-14  
**Status:** 🚫 BLOCKED

---

## Objective
验证 TICKET_0005 修复后，momentum_20d 策略能否正常执行2年历史数据回测。

---

## Tools Used

| Tool | Purpose | Status |
|------|---------|--------|
| `get_market_bars_batch` | 获取历史数据 | ✅ Success |
| `convert_bars_to_nt` | 格式转换 | ✅ Success |
| `run_backtest` | 执行回测 | ❌ Failed |

---

## Execution Attempt

### Step 1: Data Fetching ✅
- **Symbols:** AAPL, NVDA, TSLA
- **Requested Period:** 252 days (最大允许值)
- **Actual Data:** 173 bars per symbol
- **Source:** Yahoo Finance

### Step 2: Format Conversion ✅
- **Tool:** convert_bars_to_nt
- **Output:** NT-compatible format
- **Bars Converted:** 173 per symbol

### Step 3: Backtest Execution ❌

**Error:**
```
'nautilus_trader.portfolio.portfolio.Portfolio' object has no attribute 'position_exists'
```

**Root Cause:**
TICKET_0005 声称修复了策略代码，但使用了错误的 API：
- 声称修复: `position_exists()` - **实际不存在**
- 正确 API: `net_position()` - 返回净持仓量

---

## NT API Investigation

NT 1.224.0 Portfolio 实际方法：
- ✅ `net_position(instrument_id)` - 返回净持仓量
- ❌ `position(instrument_id)` - 不存在 (TICKET_0005 之前使用的)
- ❌ `position_exists(instrument_id)` - 不存在 (TICKET_0005 修复后使用的)

---

## Conclusion

**TICKET_0005 修复不正确。**

策略代码仍然使用不存在的 API，导致回测无法执行。

需要重新修复：`system/tools/impl/strategies/momentum_20d.py`

---

## Next Action

1. **等待 TICKET_20260314_003 修复**
2. **修复后重新执行 TASK_0008B_REVALIDATION**

---

## Tickets

| Ticket | Title | Status |
|--------|-------|--------|
| TICKET_0005 | Original fix (incorrect) | done (superseded) |
| TICKET_20260314_003 | Correct API fix | open |
