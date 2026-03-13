Task ID
TASK_0016

Title
Paper execution simulation

Objective
模拟订单执行。

Business Context
用于验证 execution simulation 与执行日志能力。

Inputs Required
simulate_execution

Steps
1 读取订单列表
2 执行 paper simulation
3 输出执行结果

Expected Output
execution simulation report

Dependencies
simulate_execution
order plan

Priority
P2

Status
done

Blockers
None - TICKET_20260314_002 resolved

Notes
不要在这一阶段连接真实 IB 下单，只做 simulation。
