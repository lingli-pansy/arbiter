---
id: TICKET_20250314_003
source_task: TASK_0022
title: Order management tools
status: done
created: 2025-03-14
closed: 2025-03-14
---

## Blocking Issue
TASK_0022 (Paper trading integration test) requires order submission and management tools that do not exist in the system.

Depends on: TICKET_20250314_002 (broker connection)

## Requested Capability
Create order management tools for submitting, tracking, and canceling orders.

## Why Existing Tools Are Insufficient
No order execution capability exists in the system.

## Implementation (2025-03-14)
- submit_order: MKT 立即成交，LMT/STP 为 pending
- get_order_status: 查询订单状态
- cancel_order: 撤销未成交订单
- 订单持久化于 system/state/broker_orders.json
- 测试: tests/test_broker_adapter.py

## Input Contract

### submit_order
```yaml
inputs:
  connection_id: string
  symbol: string
  side: enum["BUY", "SELL"]
  quantity: float
  order_type: enum["MKT", "LMT", "STP"]
  limit_price: float (optional)
  stop_price: float (optional)
outputs:
  order_id: string
  status: enum["submitted", "rejected", "filled"]
  filled_qty: float
  avg_fill_price: float
```

### get_order_status
```yaml
inputs:
  connection_id: string
  order_id: string
outputs:
  order_id: string
  status: enum["pending", "partial", "filled", "cancelled", "rejected"]
  filled_qty: float
  remaining_qty: float
  avg_fill_price: float
  last_update: ISO8601
```

### cancel_order
```yaml
inputs:
  connection_id: string
  order_id: string
outputs:
  order_id: string
  status: enum["cancelled", "rejected", "already_filled"]
```

## Output Contract
All tools return standardized response with:
- success: boolean
- error_message: string (if failed)
- timestamp: ISO8601

## Acceptance Criteria
- [x] submit_order creates order and returns ID
- [x] get_order_status tracks order lifecycle
- [x] cancel_order works for unfilled orders
- [x] Market orders fill immediately in paper mode
- [x] Proper error handling for invalid orders
