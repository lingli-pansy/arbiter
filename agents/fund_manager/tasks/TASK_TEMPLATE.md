Task ID
TASK_YYYYMMDD_XXXX

Title
一句话描述任务。

Objective
说明这个任务最终要产出什么业务结果。

Business Context
说明为什么要做这件事，它属于哪一类任务，例如：watchlist review / news monitoring / strategy research / backtest / portfolio review / rebalance / execution review。

Inputs Required
列出本任务依赖的工具名称。
例如：
- get_market_bars_batch
- get_news_digest
- run_backtest

Symbols
如果任务涉及标的，在这里列出。
例如：
AAPL
MSFT
NVDA

Period
如果任务涉及时间范围，在这里写清楚。
例如：
20 trading days
2 years
7 days

Steps
1. 写清第一步动作
2. 写清第二步动作
3. 写清第三步动作

Expected Output
写清任务产物，例如：
- watchlist review report
- news digest report
- backtest report
- rebalance proposal

Dependencies
列出明确依赖的 system tool。
例如：
get_market_bars_batch
get_news_digest

Priority
P0 | P1 | P2 | P3

Status
pending | running | blocked | done

Blockers
如果当前被阻塞，在这里写清阻塞原因。
如果没有，写 none。

Notes
补充说明。没有可写 none。
