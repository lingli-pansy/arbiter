Task ID
TASK_0001

Title
Initial watchlist review

Objective
审查主要标的最近20天价格变化并生成第一份观察报告。

Business Context
系统启动后的第一次研究任务，用于验证 market data 工具链。

Inputs Required
get_market_bars_batch

Symbols
AAPL
MSFT
NVDA
AMZN
META

Period
20 trading days

Steps
1 获取最近20天日线
2 计算涨跌幅
3 输出观察结论

Expected Output
watchlist review report

Dependencies
get_market_bars_batch

Priority
P0

Status
pending

Blockers
none

Notes
第一次闭环任务，优先用于验证 tool contract 与 report 输出。
