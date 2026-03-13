# OpenClaw Validation Report

**Validation Date:** 2026-03-14  
**Ticket ID:** TICKET_20260314_003  
**Capability Tested:** Fix Momentum20d Strategy - Use Correct NT API

---

## Test Summary

| Field | Value |
|-------|-------|
| Capability Tested | Momentum20d Strategy - NT API Fix |
| Ticket ID | TICKET_20260314_003 |
| Test Inputs | AAPL, NVDA, TSLA (252 days of data) |
| Observed Result | ✅ Backtest completed successfully |
| Pass/Fail | **PASS** |

---

## Detailed Test Results

### 1. Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 策略代码修复后不再抛出 AttributeError | ✅ PASS | No `position_exists` AttributeError in logs |
| 回测能正常生成订单 | ✅ PASS | 8 orders generated (4 BUY, 4 SELL) |
| 回测能正常生成持仓变化 | ✅ PASS | 4 positions opened and closed |
| 历史数据回测能完整运行 | ✅ PASS | 519 bars processed, status=completed |

### 2. Input/Output Contract Compliance

**Input Contract (run_backtest):**
- ✅ `strategy_id`: "momentum_20d" (string)
- ✅ `nt_bars`: convert_bars_to_nt output format
- ✅ `symbols`: ["AAPL", "NVDA", "TSLA"] (array)
- ✅ `config`: {"lookback_period": 20, "trade_size": 100} (object)

**Output Contract:**
- ✅ `success`: true (boolean)
- ✅ `report.account_summary`: DataFrame with 9 rows
- ✅ `report.order_fills`: DataFrame with 8 orders
- ✅ `report.positions`: DataFrame with 4 positions
- ✅ `report.metrics`: Structured metrics object
- ✅ `meta.bars_loaded`: 519
- ✅ `meta.status`: "completed"

### 3. Performance Metrics

| Metric | Value |
|--------|-------|
| Total PnL | $3,659.00 (0.37%) |
| Sharpe Ratio | 0.4557 |
| Max Drawdown | -2.76% |
| Total Orders | 8 |
| Total Positions | 4 |
| Win Rate | 50% |

### 4. Strategy Code Verification

The fix in `momentum_20d.py` correctly uses `net_position()` instead of the non-existent `position_exists()`:

```python
# Line 47-48: Fixed API usage
net_pos = self.portfolio.net_position(self._instrument_id)
position_exists = net_pos is not None and net_pos != 0
```

This aligns with NT 1.224.0 Portfolio API:
- ❌ `position(instrument_id)` - does not exist
- ❌ `position_exists(instrument_id)` - does not exist  
- ✅ `net_position(instrument_id)` - returns net position quantity

---

## Issues Found

**None.** All acceptance criteria met.

---

## Follow-up Tickets

**None required.**

---

## Conclusion

TICKET_20260314_003 has been successfully implemented and validated. The momentum_20d strategy now correctly uses the NautilusTrader 1.224.0 API and can execute backtests without errors.

**Next Action:** Move TASK_0008B_REVALIDATION to done status and close related blockers.

---

## Validation Artifacts

- Input Data: `/tmp/market_data.json`
- NT Bars: `/tmp/nt_bars.json`
- Strategy File: `/Users/xiaoyu/arbiter-2/system/tools/impl/strategies/momentum_20d.py`
