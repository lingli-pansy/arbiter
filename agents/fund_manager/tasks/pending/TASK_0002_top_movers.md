Task ID
TASK_0002

Title
Top movers detection

Objective
找出最近30天涨幅最大的股票。

Business Context
用于验证批量行情查询、涨跌幅计算与排序逻辑。

Inputs Required
get_market_bars_batch

Symbols
AAPL
MSFT
NVDA
AMZN
META
GOOGL
TSLA

Period
30 trading days

Steps
1 获取30天数据
2 计算涨幅
3 排序
4 输出前三

Expected Output
top movers report

Dependencies
get_market_bars_batch

Priority
P0

Status
pending

Blockers
none

Notes
如果工具层没有 percent change helper，也可以先在 report 中显式说明计算方式。
