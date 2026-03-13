Task ID
TASK_0006

Title
Event watchlist creation

Objective
创建事件驱动 watchlist。

Business Context
用于验证事件筛选与 watchlist 产物生成能力。

Inputs Required
get_market_bars_batch
get_news_digest
get_watchlist
update_watchlist

Symbols
NVDA
AAPL
TSLA
AMZN
META
GOOGL
MSFT

Period
20 trading days / 7 days news

Steps
1 分析新闻
2 分析价格变化
3 生成候选事件清单
4 更新事件驱动 watchlist

Expected Output
event_watchlist.md

Dependencies
get_market_bars_batch
get_news_digest
get_watchlist
update_watchlist

Priority
P1

Status
pending

Blockers
none

Notes
如果 watchlist state 还不存在，可以先写 ticket。
