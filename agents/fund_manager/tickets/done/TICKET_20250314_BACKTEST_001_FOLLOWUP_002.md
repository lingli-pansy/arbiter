# TICKET_20250314_BACKTEST_001_FOLLOWUP_002

## Source Task
TICKET_20250314_BACKTEST_001

## Source Validation
VALIDATION_20250314_BACKTEST_001

## Blocking Issue
当 `source=yahoo` 时，代码仍尝试连接 IB 获取价格，导致：
1. 不必要的超时等待（~56秒）
2. 大量 IB 连接错误日志
3. 最终被 Yahoo 限流

代码位置：`get_market_cap_ranking.py:96`
```python
prices, price_errs = _get_prices_via_ib(syms, date_str, connection_id)
```

## Requested Capability
当 `source=yahoo` 时，完全跳过 IB 连接逻辑，直接使用 Yahoo Finance 获取价格。

## Why Existing Tools Are Insufficient
当前实现违背了 contract 中 source 参数的预期行为。用户明确指定 `source=yahoo` 时期望完全使用 Yahoo，不应有 IB 依赖。

## Input Contract
```yaml
source:
  type: string
  required: false
  default: "ib"
  enum: ["ib", "yahoo"]
  description: |
    数据源；ib=Interactive Brokers（默认），yahoo=Yahoo Finance（备用）。
    当 source=ib 且 IB 返回 10358 时，自动回退到 Yahoo。
    # 期望行为：source=yahoo 时不应尝试连接 IB
```

## Output Contract
不变，但应减少错误日志中的 IB 连接错误。

## Acceptance Criteria
- [x] 当 `source=yahoo` 时，不调用任何 IB 相关代码
- [x] 当 `source=yahoo` 时，响应时间显著缩短（<10秒）
- [x] 当 `source=yahoo` 时，错误日志中不包含 IB 连接错误
- [x] 当 `source=ib` 时，保持现有行为

## Test Case
```bash
echo '{"date": "2024-03-31", "top_n": 5, "source": "yahoo"}' | python3 get_market_cap_ranking.py
```
预期：
- 无 IB 连接错误
- 响应时间 < 10秒
- 返回 ranking 或 Yahoo 相关错误

## Priority
P0

## Status
Open
