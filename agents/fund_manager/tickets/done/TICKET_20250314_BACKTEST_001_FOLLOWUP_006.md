# TICKET_20250314_BACKTEST_001_FOLLOWUP_006

## Source Task
TICKET_20250314_BACKTEST_001

## Source Validation
VALIDATION_20250314_BACKTEST_001

## Blocking Issue
**Contract-Implementation Mismatch**

Contract 定义了 `equal_weight` 参数（boolean），但实现中：
1. 未读取该参数
2. 硬编码为等权分配
3. 用户无法使用市值加权等其他策略

代码位置：`run_market_cap_rotation_backtest.py:81-90`
```python
if d == dates[0] and not positions:
    per = investable / len(syms) if syms else 0  # 硬编码等权
    prices = {s: ps.get(s, {}).get(...) or 0 for s in syms}
    for s in syms:
        if prices.get(s) and prices[s] > 0:
            positions[s] = per / prices[s]  # 等权计算
```

## Requested Capability
实现 `equal_weight` 参数：
- `true`: 等权分配（当前实现）
- `false`: 市值加权分配（根据排名权重）

## Why Existing Tools Are Insufficient
Contract 承诺了 equal_weight 配置能力，但实现只支持等权，构成契约违背。

## Input Contract
新增/修复参数：
```yaml
equal_weight:
  type: boolean
  required: false
  default: true
```

## Output Contract
不变

## Acceptance Criteria
- [x] 当 `equal_weight=true` 时，每个持仓分配相同资金
- [x] 当 `equal_weight=false` 时，按市值排名加权（排名越高权重越大）
- [x] Contract 与实际实现一致

## Validation Report
VALIDATION_20250314_FOLLOWUP_005_006.md

## Status
Done

## Test Case
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "equal_weight": false,
  "top_n": 3
}
```
预期：权重分配为 第1名 50%、第2名 33%、第3名 17%（或其他合理的市值加权方案）

## Priority
P0

## Status
Open
