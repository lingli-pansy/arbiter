Task ID
TASK_0013

Title
Simulate rebalance

Objective
模拟等权再平衡。

Business Context
用于验证组合调仓建议能力。

Inputs Required
simulate_rebalance

Assets
NVDA
MSFT
AAPL

Steps
1 读取当前组合
2 设定目标等权
3 生成调仓建议

Expected Output
rebalance proposal

Dependencies
simulate_rebalance
portfolio state

Priority
P2

Status
pending

Blockers
none

Notes
需要明确输出目标权重、当前权重、差额与现金占用。
