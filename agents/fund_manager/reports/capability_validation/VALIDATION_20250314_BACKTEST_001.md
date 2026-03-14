# OpenClaw Validation Output (Static Code Review)

## Capability Tested
市值轮动回测能力 (Market Cap Rotation Backtest)

## Ticket ID
TICKET_20250314_BACKTEST_001

## Review Date
2026-03-14

## Review Method
Static Code Review (Dynamic testing blocked by environment constraints)

---

## Tools Tested
1. `get_market_cap_ranking` - 获取指定日期市值排名
2. `run_market_cap_rotation_backtest` - 执行市值轮动回测

---

## Test 1: get_market_cap_ranking

### Contract Review

| Contract Item | Status | Notes |
|--------------|--------|-------|
| Input: date | ✅ | Required, string, YYYY-MM-DD |
| Input: source | ✅ | enum ["ib", "yahoo"], default "ib" |
| Input: top_n | ✅ | integer, min 1, max 20 |
| Input: market | ✅ | default "US" |
| Output: success | ✅ | boolean |
| Output: ranking | ✅ | array with rank, symbol, market_cap |
| Output: as_of_date | ✅ | string |
| Output: source | ✅ | actual source used |
| Output: errors | ✅ | array |

### Implementation Issues Found

1. **IB Connection Leak** (Line 96)
   ```python
   prices, price_errs = _get_prices_via_ib(syms, date_str, connection_id)
   ```
   当 `source=yahoo` 时，代码仍优先尝试 IB 连接，违背用户预期。

2. **Yahoo Rate Limiting** (Line 102-120)
   - 固定 2 秒延迟不足避免限流
   - 批量下载 20 只股票容易触发 `YFRateLimitError`
   - 重试机制仅在异常时触发，限流后没有退避策略

3. **Error Handling Gap**
   - IB 连接失败时错误信息不够清晰
   - 没有区分"连接不可用"和"数据不存在"

### Pass/Fail: ⚠️ PARTIAL
- Contract 完整 ✅
- 实现有架构缺陷 ⚠️

---

## Test 2: run_market_cap_rotation_backtest

### Contract Review

| Contract Item | Status | Notes |
|--------------|--------|-------|
| Input: start_date | ✅ | Required |
| Input: end_date | ✅ | Required |
| Input: initial_capital | ✅ | default 500000 |
| Input: cash_pool | ✅ | default 50000 |
| Input: rebalance_frequency | ❌ | **Contract 定义但未实现** |
| Input: top_n | ✅ | default 5 |
| Input: benchmark | ✅ | default "QQQ" |
| Input: equal_weight | ❌ | **Contract 定义但未实现** |
| Output: report.strategy_name | ✅ | "US Large Cap Rotation" |
| Output: report.period | ✅ | {start, end} |
| Output: report.rebalances | ✅ | array |
| Output: report.equity_curve | ✅ | array |
| Output: report.metrics | ✅ | object |

### Critical Issue: Contract-Implementation Mismatch

**Contract 定义但未实现参数：**

1. `rebalance_frequency` (contract: quarterly/monthly)
   - 实现中硬编码为 quarterly
   - 用户无法使用 monthly 调仓

2. `equal_weight` (contract: boolean)
   - 实现中硬编码为等权分配
   - 用户无法配置市值加权或其他策略

### Other Issues

1. **Subprocess Error Handling** (Line 18-22)
   ```python
   r = subprocess.run([...], capture_output=True, timeout=90, ...)
   out = json.loads(r.stdout.decode()) if r.returncode == 0 else {}
   ```
   - 不检查 stderr
   - 超时后无详细错误信息
   - 子进程失败时静默返回空 {}

2. **Cascading Failure Risk**
   - `_call_ranking` 返回空列表时，`_call_bars` 也会失败
   - 最终导致 "No price data" 错误，但根因不明

### Pass/Fail: ❌ FAIL
- Contract 与实现不一致 ❌
- 两个关键参数未实现 ❌

---

## Root Cause Summary

| Issue | Severity | Category |
|-------|----------|----------|
| Contract-Implementation Mismatch | **Critical** | insufficient_output_contract |
| IB Connection Leak | **High** | unstable_error_surface |
| Yahoo Rate Limiting | **Medium** | missing_state_dependency |
| Subprocess Error Handling | **Medium** | unstable_error_surface |
| Missing Dependencies | **Medium** | missing_state_dependency |

---

## Validation Status

| Metric | Result |
|--------|--------|
| Tools Available | ✅ 2/2 |
| Contract Compliant | ❌ NO |
| Implementation Complete | ❌ NO |
| Production Ready | ❌ NO |

**Overall Status**: ❌ **VALIDATION FAILED**

---

## Required Actions Before Production

### Must Fix (P0)
1. **实现 `rebalance_frequency` 参数**
   - 支持 monthly 调仓
   - 更新 `_quarterly_dates()` 为更通用的 `_rebalance_dates()`

2. **实现 `equal_weight` 参数**
   - true: 等权分配（当前实现）
   - false: 市值加权分配

3. **修复 `source=yahoo` 逻辑**
   - 跳过 IB 连接尝试
   - 直接使用 Yahoo Finance

### Should Fix (P1)
4. **改进错误处理**
   - 区分网络错误、数据缺失、参数错误
   - 提供详细的错误上下文

5. **声明依赖**
   - 创建 requirements.txt
   - 或更新 registry 记录依赖

---

## Follow-up Tickets

已创建以下 tickets:

1. **TICKET_20250314_BACKTEST_001_FOLLOWUP_001** - 依赖声明
2. **TICKET_20250314_BACKTEST_001_FOLLOWUP_002** - source=yahoo 跳过 IB
3. **TICKET_20250314_BACKTEST_001_FOLLOWUP_003** - Yahoo 限流处理
4. **TICKET_20250314_BACKTEST_001_FOLLOWUP_004** - Mock 数据支持

**新增 Tickets 需创建：**

5. **TICKET_20250314_BACKTEST_001_FOLLOWUP_005** - 实现 `rebalance_frequency` 参数
6. **TICKET_20250314_BACKTEST_001_FOLLOWUP_006** - 实现 `equal_weight` 参数

---

## Next Action
1. 创建 FOLLOWUP_005 和 FOLLOWUP_006
2. 等待实现方修复 Contract-Implementation 不匹配问题
3. 修复后重新运行验收测试

---

*Note: 本次验收基于静态代码审查。动态测试因环境限制（sandbox 不可用）无法完成。建议在修复上述问题后，在正确配置的环境中重新执行动态验收。*
