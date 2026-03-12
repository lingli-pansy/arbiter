Task ID
TASK_0014

Title
Portfolio performance tracking

Objective
计算组合收益。

Business Context
用于验证 portfolio valuation 与 performance report 能力。

Inputs Required
get_portfolio
get_market_bars_batch
calculate_portfolio_performance

Assets
NVDA
MSFT
AAPL

Period
Since inception

Steps
1 读取组合持仓
2 拉取价格数据
3 计算收益与回撤
4 输出收益报告

Expected Output
performance report

Dependencies
portfolio state
market data
performance tool

Priority
P2

Status
pending

Blockers
none

Notes
如果组合快照历史不存在，需写 ticket。
