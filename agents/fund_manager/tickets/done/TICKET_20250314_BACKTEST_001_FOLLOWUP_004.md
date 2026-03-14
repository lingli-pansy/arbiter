# TICKET_20250314_BACKTEST_001_FOLLOWUP_004

## Source Task
TICKET_20250314_BACKTEST_001

## Source Validation
VALIDATION_20250314_BACKTEST_001

## Blocking Issue
验收测试依赖外部 API（Yahoo Finance），导致：
1. 测试不稳定（受网络、限流影响）
2. 测试不可重复（每次结果可能不同）
3. 测试速度慢（需要实际 API 调用）

## Requested Capability
提供 Mock 模式或预置测试数据，使验收测试不依赖外部 API。

## Why Existing Tools Are Insufficient
当前工具没有测试模式，每次运行都进行真实 API 调用。

## Input Contract
新增可选参数：
```yaml
mock_mode:
  type: boolean
  required: false
  default: false
  description: 使用 Mock 数据进行测试，不调用真实 API
```

或环境变量：`ARBITER_MOCK_MODE=1`

## Output Contract
当 mock_mode=true 时，返回预定义的测试数据：
```json
{
  "success": true,
  "ranking": [
    {"rank": 1, "symbol": "AAPL", "market_cap": 2800000000000, "market_cap_millions": 2800000},
    {"rank": 2, "symbol": "MSFT", "market_cap": 2700000000000, "market_cap_millions": 2700000},
    ...
  ],
  "as_of_date": "2024-03-31",
  "source": "mock",
  "errors": [],
  "meta": {"latency_ms": 10}
}
```

## Acceptance Criteria
- [x] 支持 mock_mode 参数或环境变量
- [x] Mock 数据返回格式与真实数据一致
- [ ] Mock 数据覆盖常见场景（正常、空结果、部分缺失）
- [ ] 文档说明如何使用 Mock 模式进行测试

## Test Case
```bash
# Mock 模式
echo '{"date": "2024-03-31", "top_n": 5, "source": "yahoo", "mock_mode": true}' | python3 get_market_cap_ranking.py

# 预期：立即返回预定义数据，不调用 Yahoo API
```

## Priority
P1

## Status
Open
