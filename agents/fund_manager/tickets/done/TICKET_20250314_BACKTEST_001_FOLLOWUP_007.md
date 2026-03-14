# TICKET_20250314_BACKTEST_001_FOLLOWUP_007

## Source Task
TICKET_20250314_BACKTEST_001 (原阻塞任务重执行)

## Source Validation
VALIDATION_20250314_FOLLOWUP_005_006

## Blocking Issue
`run_market_cap_rotation_backtest` 完整链路执行超时。

调用链分析：
```
run_market_cap_rotation_backtest(mock_mode=true)
    ├── get_market_cap_ranking(mock_mode=true) ✅ 支持，快速返回
    └── get_market_bars_batch(source=yahoo) ❌ 不支持 mock_mode
        └── 尝试连接 Yahoo 获取 1 年历史数据 → 超时 (2min+)
```

即使上层传入 `mock_mode=true`，`get_market_bars_batch` 仍会尝试真实 API 调用，导致：
1. 完整链路测试无法快速完成
2. 无法离线演示/测试回测功能
3. Yahoo 限流风险

## Requested Capability
让 `run_market_cap_rotation_backtest` 的完整链路支持 `mock_mode`。

**方案 A** (推荐): 为 `get_market_bars_batch` 添加 `mock_mode` 支持
- 当 `mock_mode=true` 时返回模拟的价格数据
- 保持与原数据格式一致

**方案 B**: `run_market_cap_rotation_backtest` 内部使用模拟价格
- 当 `mock_mode=true` 时跳过 `get_market_bars_batch` 调用
- 内部生成模拟价格序列

## Why Existing Tools Are Insufficient
`get_market_bars_batch` 不支持 `mock_mode`，导致依赖它的工具链无法快速测试。

## Input Contract
新增参数：
```yaml
mock_mode:
  type: boolean
  required: false
  default: false
  description: 使用模拟数据，不调用真实 API
```

## Output Contract
与正常模式相同，但数据来源为模拟生成。

## Acceptance Criteria
- [x] `get_market_bars_batch` 支持 `mock_mode=true` 参数
- [x] 模拟数据格式与真实数据一致
- [x] 能在 10 秒内返回结果
- [x] `run_market_cap_rotation_backtest` + `mock_mode` 能在 10 秒内完成执行
- [x] 能生成完整的回测报告（含 equity_curve 和 metrics）
- [ ] report.rebalances 有 4 个季度调仓记录 (注: 实际只有 2 个，见 FOLLOWUP_008)

## Validation Report
VALIDATION_20250314_FOLLOWUP_007.md

## Follow-up
TICKET_20250314_BACKTEST_001_FOLLOWUP_008 (rebalance 计数修复)

## Test Case
```bash
echo '{
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "symbols": ["AAPL", "MSFT"],
  "mock_mode": true
}' | python3 get_market_bars_batch.py
```
预期：10 秒内返回模拟的 OHLCV 数据

## Priority
P0 (阻塞 MVP 演示)

## Status
Done (2025-03-14)

## Implementation Notes
- `get_market_bars_batch`: 添加 `mock_mode` 及 `ARBITER_MOCK_MODE` 环境变量，mock 时生成 `_generate_mock_bars` 模拟 OHLCV
- `run_market_cap_rotation_backtest`: 接收 `mock_mode` 并传递给 `_call_ranking` 与 `_call_bars`
- 契约: `get_market_bars_batch.yaml`、`run_market_cap_rotation_backtest.yaml` 新增 `mock_mode` 参数
- 验证: `scripts/validate_mock_backtest.sh` — 全链路 116ms 完成，<10s ✓
