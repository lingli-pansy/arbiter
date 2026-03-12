Task ID
TASK_0008

Title
Run first backtest

Objective
回测20日动量策略。

Business Context
用于验证 NautilusTrader 回测链路与 job 产物输出。

Inputs Required
run_backtest

Symbols
AAPL
NVDA
TSLA

Period
2 years

Steps
1 选择策略定义
2 调用 run_backtest
3 记录 job 状态
4 输出回测报告

Expected Output
backtest report

Dependencies
run_backtest

Priority
P1

Status
pending

Blockers
none

Notes
如果缺少 metrics output、job state 或结果路径，需生成 ticket。
