# TICKET_20250314_BACKTEST_001_FOLLOWUP_008

## Source Task
TICKET_20250314_BACKTEST_001 (原阻塞任务重执行)

## Source Validation
VALIDATION_20250314_FOLLOWUP_007

## Blocking Issue
`rebalance_frequency=quarterly` 参数未正确产生 4 个季度调仓记录。

测试输入:
```json
{
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "rebalance_frequency": "quarterly",
  ...
}
```

预期调仓日期:
- 2024-03-31 (Q1)
- 2024-06-30 (Q2)
- 2024-09-30 (Q3)
- 2024-12-31 (Q4)

实际调仓日期:
- 2024-09-30 (Q3) ✅
- 2024-12-31 (Q4) ✅
- **缺失 Q1 和 Q2**

可能原因:
1. `_quarterly_dates()` 函数未正确生成 3/31 和 6/30
2. 调仓逻辑在年初跳过前两个季度
3. rebalances 数组只在调仓发生变动时才记录

## Requested Capability
修复 `rebalance_frequency=quarterly` 以产生完整的 4 个季度调仓记录。

## Why Existing Tools Are Insufficient
当前实现返回的 rebalances 数组不完整，影响回测策略准确性。

## Input Contract
不变

## Output Contract
`report.rebalances` 应包含所有季度末调仓记录。

## Acceptance Criteria
- [x] `rebalance_frequency=quarterly` 时产生 4 条调仓记录
- [x] 调仓日期为 3/31、6/30、9/30、12/31 (在日期范围内)；若为周末则用下一交易日 04-01、07-01
- [x] 与 `_quarterly_dates()` 函数生成的日期一致

## Test Case
```bash
echo '{
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "rebalance_frequency": "quarterly",
  "mock_mode": true
}' | python3 run_market_cap_rotation_backtest.py
```

预期: `report.rebalances` 长度为 4

## Priority
P1 (影响策略准确性但核心链路已通)

## Status
Done (2025-03-14)

## Implementation Notes
- 根因：2024-03-31、2024-06-30 为周末，价格数据无这些日期，主循环 `for d in dates` 永远不会触发
- 修复：将调仓日映射为「首个 >= 该日的交易日」，使用 `effective_rb_set` 触发调仓
- 验证：`scripts/validate_quarterly_rebalance.sh` — report.rebalances 长度为 4 ✓
