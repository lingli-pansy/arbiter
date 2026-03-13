Task ID
TASK_0008B

Title
Historical momentum backtest with 2-year data

Objective
使用2年真实历史数据执行momentum_20d策略回测，验证订单生成、持仓变化和完整的回测结果。

Business Context
TASK_0008仅用mock数据验证了回测链路。本任务使用真实历史数据验证策略实际表现。

Inputs Required
get_market_bars_batch, convert_bars_to_nt, run_backtest

Symbols
AAPL
NVDA
TSLA

Period
2 years (2023-01-01 to 2024-12-31)
Warmup: 20 trading days

Steps
1 获取2年历史数据(约500+ bars per symbol)
2 转换为NT格式
3 执行momentum_20d回测
4 验证订单生成
5 验证持仓变化
6 输出完整回测报告

Expected Output
完整回测报告（含订单、持仓、收益曲线）

Dependencies
get_market_bars_batch, convert_bars_to_nt, run_backtest

Priority
P0

Status
pending

Blockers
none

Notes
需要验证: 1) 数据量是否足够 2) 策略是否生成信号 3) metrics是否完整
