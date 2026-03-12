Task ID
TASK_0017

Title
Slippage analysis

Objective
分析滑点。

Business Context
用于验证执行后分析能力。

Inputs Required
execution results
analyze_slippage

Steps
1 读取模拟执行结果
2 对比预期价格与模拟成交价
3 输出滑点报告

Expected Output
slippage report

Dependencies
simulate_execution
analyze_slippage

Priority
P2

Status
pending

Blockers
none

Notes
如果执行结果没有足够字段支持分析，需要生成 ticket。
