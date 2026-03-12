Task ID
TASK_0009

Title
Backtest metrics review

Objective
分析回测指标。

Business Context
用于验证回测结果是否足够支持研究判断。

Inputs Required
run_backtest output

Symbols
AAPL
NVDA
TSLA

Period
2 years

Steps
1 读取回测结果
2 检查 Sharpe、Drawdown、CAGR
3 输出策略评估

Expected Output
strategy evaluation report

Dependencies
run_backtest

Priority
P1

Status
pending

Blockers
none

Notes
如果回测结果没有结构化 summary_metrics，需要生成 ticket。
