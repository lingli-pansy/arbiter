# TICKET_20250314_BACKTEST_001_FOLLOWUP_005

## Source Task
TICKET_20250314_BACKTEST_001

## Source Validation
VALIDATION_20250314_BACKTEST_001

## Blocking Issue
**Contract-Implementation Mismatch**

Contract 定义了 `rebalance_frequency` 参数（enum: [quarterly, monthly]），但实现中：
1. 未读取该参数
2. 硬编码为 quarterly 调仓
3. 用户无法使用 monthly 调仓策略

代码位置：`run_market_cap_rotation_backtest.py:54`
```python
def _quarterly_dates(start: str, end: str) -> list[str]:
    # 只生成季度末日期
```

## Requested Capability
实现 `rebalance_frequency` 参数，支持 monthly 调仓。

## Why Existing Tools Are Insufficient
Contract 承诺了 quarterly/monthly 两种调仓频率，但实现只支持 quarterly，构成契约违背。

## Input Contract
新增/修复参数：
```yaml
rebalance_frequency:
  type: string
  required: false
  default: quarterly
  enum: [quarterly, monthly]
```

## Output Contract
不变

## Acceptance Criteria
- [x] 当 `rebalance_frequency=monthly` 时，在每月最后一个交易日调仓
- [x] 当 `rebalance_frequency=quarterly` 时，保持现有行为（3/6/9/12月末）
- [x] 返回的 `rebalances` 数组日期与配置一致
- [x] Contract 与实际实现一致

## Validation Report
VALIDATION_20250314_FOLLOWUP_005_006.md

## Status
Done

## Test Case
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "rebalance_frequency": "monthly",
  "top_n": 5
}
```
预期：rebalances 包含 1月、2月、3月、4月、5月、6月的调仓记录

## Priority
P0

## Status
Open
