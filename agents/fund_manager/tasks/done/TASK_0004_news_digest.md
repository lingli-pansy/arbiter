Task ID
TASK_0004

Title
Recent news digest

Objective
收集过去7天相关新闻摘要。

Business Context
用于验证 news ingestion、标准化与摘要输出能力。

Inputs Required
get_news_digest

Symbols
NVDA
AAPL
TSLA

Period
7 days

Steps
1 查询新闻
2 提取摘要
3 输出新闻报告

Expected Output
news digest report

Dependencies
get_news_digest

Priority
P1

Status
pending

Blockers
none

Notes
若新闻结果缺少 symbol tagging 或 relevance 字段，需生成 ticket。
