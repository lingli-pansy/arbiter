# Task Run Report: TASK_0008B - 2-Year Historical Momentum Backtest

**Task ID:** TASK_0008B  
**Title:** Historical momentum backtest with 2-year data  
**Executed Date:** 2026-03-13  
**Status:** 🚫 BLOCKED  
**Executor:** OpenClaw Fund Manager (Dev)

---

## Tools Used

| Tool | Status | Notes |
|------|--------|-------|
| `get_market_bars_batch` | ✅ | 成功获取 2 年数据 |
| `get_symbol_venue` | ✅ | Venue 映射成功 |
| `convert_bars_to_nt` | ✅ | 格式转换成功 |
| `run_backtest` | ❌ | 策略崩溃 |

---

## Task Objective

使用 2 年真实历史数据执行 momentum_20d 策略回测，验证订单生成、持仓变化和完整回测结果。

## Execution Attempt

### Step 1: Data Fetching ✅

成功获取 2 年数据：
- AAPL: 501 bars (2023-01-03 to 2024-12-30)
- NVDA: 501 bars (2023-01-03 to 2024-12-30)
- TSLA: 501 bars (2023-01-03 to 2024-12-30)

**Total:** ~1,500 bars across 3 symbols

### Step 2: Venue Mapping ✅

```json
{"AAPL": "NASDAQ", "NVDA": "NASDAQ", "TSLA": "NASDAQ"}
```

### Step 3: Format Conversion ✅

成功转换为 NT Bar 格式：
- ISO timestamp → int64 nanoseconds
- float prices → string (Price)
- int volume → string (Quantity)
- bar_type: `AAPL.XNAS-1-DAY-LAST-EXTERNAL`

### Step 4: Backtest Execution ❌

**Status:** Crashed

**Error:**
```
AttributeError: 'nautilus_trader.portfolio.portfolio.Portfolio' object has no attribute 'position'
```

**Location:** `strategies/momentum_20d.py:49`

**Root Cause:**
策略代码使用了错误的 NT API：
```python
position = self.portfolio.position(self._instrument_id)  # ❌ 不存在
```

正确的 API 应该是：
```python
position_exists = self.portfolio.position_exists(self._instrument_id)  # ✅
```

---

## What Worked

| Component | Status |
|-----------|--------|
| 2-year data fetching | ✅ |
| Venue resolution | ✅ |
| NT format conversion | ✅ |
| Backtest engine startup | ✅ |
| Bar data loading | ✅ |
| Strategy registration | ✅ |

## What Failed

| Component | Status | Issue |
|-----------|--------|-------|
| Strategy execution | ❌ | API mismatch |
| Order generation | ❌ | 策略崩溃 |
| Position tracking | ❌ | 策略崩溃 |
| Report generation | ❌ | 无数据 |

---

## Tickets Created

| Ticket ID | Title | Status |
|-----------|-------|--------|
| TICKET_0005 | Fix Momentum20d Strategy Portfolio API | open |

---

## Next Action

1. **等待 TICKET_0005 修复** - 策略代码需要修改

2. **修复后重新执行 TASK_0008B**

3. **验证清单:**
   - [ ] 策略执行无错误
   - [ ] 订单生成正常
   - [ ] 持仓变化正常
   - [ ] 回测报告完整

---

## Conclusion

2 年数据获取链路完全可用，但策略实现存在 bug。这是一个实现错误，不是系统设计问题。等待修复后可重新执行。

**数据链路:** ✅ 已验证  
**策略实现:** ❌ 需修复
