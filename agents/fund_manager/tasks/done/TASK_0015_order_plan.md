Task ID
TASK_0015

Title
Generate order plan

Objective
从 rebalance proposal 生成订单列表。

Business Context
用于连接组合建议与执行计划。

Inputs Required
generate_order_plan
rebalance proposal

Steps
1 读取 rebalance proposal
2 生成订单计划
3 输出订单列表

Expected Output
order plan

Dependencies
generate_order_plan
simulate_rebalance

Priority
P2

Status
blocked

Blockers
TICKET_20260314_001 - Missing generate_order_plan tool

Notes
第一版只需要 paper / simulated order plan，不需要真实下单。
