---
id: TICKET_20250314_001
source_task: TASK_0001D
title: Add data source parameter to get_market_bars_batch
status: done
created: 2025-03-14
updated: 2025-03-14
closed: 2025-03-14
---

## Blocking Issue
TASK_0001D (IB data path validation) requires fetching market data from Interactive Brokers specifically, but `get_market_bars_batch` does not accept a `source` parameter to specify the data provider.

## Resolution (2025-03-14)
- Contract: `source` 为主参数，`provider` 标记 deprecated 保持向后兼容
- Enum: `["yahoo", "ib", "polygon", "alpaca"]`
- meta 增加 `latency_ms`、`data_quality_score`
- 实现：`source` 优先，`provider` 别名，`ib` 映射内部 `ibkr`
- 测试：6 个用例全部通过

## Acceptance Criteria
- [x] Parameter renamed from `provider` to `source`
- [x] Enum updated: `["yahoo", "ib", "polygon", "alpaca"]` ("ibkr" → "ib")
- [x] Response includes `latency_ms`
- [x] Response includes `data_quality_score`
- [x] Backward compatible (accept `provider` as alias)
- [x] All tests pass
