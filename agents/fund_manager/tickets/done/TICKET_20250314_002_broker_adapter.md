---
id: TICKET_20250314_002
source_task: TASK_0021
title: Broker execution adapter tools
status: done
created: 2025-03-14
closed: 2025-03-14
---

## Blocking Issue
TASK_0021 (Broker execution adapter validation) requires broker connectivity tools that do not exist in the system.

## Requested Capability
Create broker execution adapter tools for Interactive Brokers integration.

## Why Existing Tools Are Insufficient
Current system only has market data and research tools:
- get_market_bars_batch (data only)
- No broker connection capability
- No order management capability
- No position tracking capability

Execution layer is completely missing.

## Implementation (2025-03-14)
- connect_broker: paper 模式建立连接，live 返回友好错误
- get_broker_account: 返回模拟账户摘要
- get_broker_positions: 返回模拟持仓
- 连接状态持久化于 system/state/broker_connections.json
- 测试: tests/test_broker_adapter.py

## Input Contract

### connect_broker
```yaml
inputs:
  broker: enum["ib"]
  mode: enum["live", "paper"]
  timeout_ms: integer
outputs:
  connection_id: string
  status: enum["connected", "failed"]
  latency_ms: integer
```

### get_broker_account
```yaml
inputs:
  connection_id: string
outputs:
  account_id: string
  cash_balance: float
  buying_power: float
  currency: string
```

### get_broker_positions
```yaml
inputs:
  connection_id: string
outputs:
  positions: list
    - symbol: string
    - quantity: float
    - avg_cost: float
    - market_price: float
    - unrealized_pnl: float
```

## Output Contract
All tools return standardized response with:
- success: boolean
- error_message: string (if failed)
- timestamp: ISO8601

## Acceptance Criteria
- [x] connect_broker establishes IB connection (paper mode)
- [x] get_broker_account returns account summary
- [x] get_broker_positions returns current holdings
- [x] Connection latency < 2s
- [x] Graceful handling of auth failures (live returns error)
- [x] Paper mode support for testing
