Task ID
TASK_0005

Title
News price correlation

Objective
识别新闻与价格波动的关联。

Business Context
用于验证 market + news 联合分析链路。

Inputs Required
get_market_bars_batch
get_news_digest

Symbols
NVDA
AAPL
TSLA
AMZN
META

Period
20 trading days / 7 days news

Steps
1 获取价格数据
2 获取新闻数据
3 对比波动
4 输出候选事件

Expected Output
event candidate list

Dependencies
get_market_bars_batch
get_news_digest

Priority
P1

Status
pending

Blockers
none

Notes
重点看 price spike 与 news spike 是否能在同一任务中关联。
