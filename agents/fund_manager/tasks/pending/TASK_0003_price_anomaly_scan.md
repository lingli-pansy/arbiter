Task ID
TASK_0003

Title
Price anomaly scan

Objective
识别过去60天单日涨跌超过8%的事件。

Business Context
用于验证长区间行情读取与异常事件扫描能力。

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
60 trading days

Steps
1 获取60天数据
2 检测单日变化
3 输出异常列表

Expected Output
price anomaly report

Dependencies
get_market_bars_batch

Priority
P0

Status
pending

Blockers
none

Notes
如果返回数据缺少完整时间序列，需生成 ticket。
