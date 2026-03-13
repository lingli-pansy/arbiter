# Ticket: Missing simulate_execution Tool

**Ticket ID:** TICKET_20260314_002  
**Created:** 2026-03-14  
**Status:** Done  
**Priority:** P1 (阻塞执行链路)

---

## Source Task
- **Task ID:** TASK_0016, TASK_0017, TASK_0018
- **Task Title:** Paper execution simulation, Slippage analysis, Execution audit

---

## Blocking Issue
执行链路 (0015 → 0016 → 0017 → 0018) 依赖 `simulate_execution` 工具来模拟订单执行并生成执行报告。但该工具未在 `system/tools/registry.yaml` 中注册。

---

## Requested Capability
新增工具 `simulate_execution`，用于模拟订单执行并生成执行结果。

---

## Why Existing Tools Are Insufficient

| 现有工具 | 功能 | 为何不足 |
|---------|------|---------|
| `generate_order_plan` | 生成订单计划 | 只生成计划，不模拟执行 |
| `submit_order` | 提交真实订单 | 需要真实券商连接，不适合 paper simulation |
| `run_backtest` | 回测 | 用于策略验证，不是订单执行模拟 |

当前链路缺口：
```
generate_order_plan (order plan)
    → [缺少: simulate_execution]
    → execution report → slippage analysis → audit
```

---

## Input Contract

```yaml
name: simulate_execution
input:
  order_plan:
    type: object
    required: true
    description: generate_order_plan 的输出
  simulation_config:
    type: object
    required: false
    properties:
      fill_model:
        type: string
        enum: [immediate, partial, random_delay]
        default: immediate
      slippage_model:
        type: string
        enum: [none, fixed, percentage]
        default: none
      slippage_value:
        type: number
        default: 0
      market_impact:
        type: boolean
        default: false
```

---

## Output Contract

```yaml
output:
  type: object
  properties:
    success: boolean
    execution_report:
      type: object
      properties:
        report_id: string
        plan_id: string
        executed_at: string (ISO8601)
        orders:
          type: array
          items:
            order_id: string
            symbol: string
            side: string
            quantity: integer
            filled_qty: integer
            avg_fill_price: number
            status: string (filled|partial|rejected)
            slippage: number
            timestamp: string
        summary:
          total_orders: integer
          filled_orders: integer
          partial_orders: integer
          rejected_orders: integer
          total_slippage: number
    errors: array
```

---

## Acceptance Criteria

1. 工具成功注册到 `system/tools/registry.yaml`，status: active
2. Contract 文档写入 `system/tools/contracts/simulate_execution.yaml`
3. 实现脚本写入 `system/tools/impl/simulate_execution.py`
4. 支持多种 fill model (immediate, partial, random_delay)
5. 支持 slippage 模拟
6. 输出与 TASK_0017 (slippage analysis) 兼容

---

## Related
- Blocked Tasks: TASK_0016, TASK_0017, TASK_0018
- Upstream: TASK_0015 (order plan)
