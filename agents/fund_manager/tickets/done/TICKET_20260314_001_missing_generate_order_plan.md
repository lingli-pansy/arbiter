---
id: TICKET_20260314_001
source_task: TASK_0015
title: Missing generate_order_plan Tool
status: done
created: 2026-03-14
closed: 2026-03-14
---

## Blocking Issue
Task TASK_0015 依赖 `generate_order_plan` 工具将 `simulate_rebalance` 的输出转换为可执行的订单计划，但该工具未注册。

## Resolution (2026-03-14)
- Contract: `system/tools/contracts/generate_order_plan.yaml`
- Implementation: `system/tools/impl/generate_order_plan.py`
- Registry: generate_order_plan 已注册，status: active
- 支持 rebalance_proposal.trades 及 rebalance_proposal.rebalance.trades（simulate_rebalance 输出）
- risk_limits: max_order_value, max_single_order_pct, max_position_size
- validations 报告每笔订单风险校验及现金流
- 测试：3 个用例全部通过
