# TICKET_20250314_BACKTEST_001_FOLLOWUP_003

## Source Task
TICKET_20250314_BACKTEST_001

## Source Validation
VALIDATION_20250314_BACKTEST_001

## Blocking Issue
Yahoo Finance API 对批量请求有限流，20 只股票的 batch download 触发 `YFRateLimitError: Too Many Requests`。

当前代码虽然有 2 秒延迟，但仍被限流：
```python
YAHOO_DELAY_SEC = 2.0  # 避免 Yahoo 限流 (~20 symbols/min)
```

## Requested Capability
实现更健壮的 Yahoo Finance 请求机制，包括：
1. 指数退避重试
2. 更合理的请求间隔
3. 分批请求避免触发限流

## Why Existing Tools Are Insufficient
当前实现：
- 固定 2 秒延迟不足
- 限流后没有有效重试机制
- 批量请求 20 只股票过于激进

## Input Contract
不变

## Output Contract
不变，但应提高成功率

## Acceptance Criteria
- [x] 实现重试机制（当前：固定 10s 延迟，3 次重试）
- [ ] 指数退避重试（1s, 2s, 4s, 8s...）
- [ ] 批量请求分批进行（如每批 5 只）
- [ ] 添加缓存机制避免重复请求相同日期
- [x] 在受限流后能够成功获取数据（可能需要多次尝试）

## Implementation Note
已实现基础重试机制（RATE_LIMIT_RETRIES=3，固定 10s 退避），但指数退避和缓存机制尚未实现。建议保留此 ticket 跟踪剩余改进项，或关闭并创建新的优化 ticket。

## Test Case
连续运行 3 次：
```bash
for i in 1 2 3; do
  echo '{"date": "2024-03-31", "top_n": 5, "source": "yahoo"}' | python3 get_market_cap_ranking.py
done
```
预期至少 2/3 成功返回非空 ranking。

## Priority
P1

## Status
Open
