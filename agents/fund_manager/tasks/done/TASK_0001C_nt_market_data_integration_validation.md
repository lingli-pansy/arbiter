
Task ID
TASK_0001C

Title
NautilusTrader market data integration validation

Objective
验证当前 market data tool 与 NautilusTrader 的集成路径，并识别需要的 adapter 或 contract 调整。

Business Context
系统计划使用 NautilusTrader 作为回测与研究核心。本任务用于确认当前数据工具是否可以作为 NT 的输入源。

Key Questions
1 NT bar schema 与当前 tool 输出是否兼容
2 是否需要 NT adapter
3 数据频率与 NT timeframe 是否匹配
4 数据字段是否完整

Steps
1 查看 NautilusTrader bar schema
2 对比 get_market_bars_batch 输出
3 识别字段差异
4 输出 integration note
5 如必要创建 adapter ticket

Expected Output
nt_market_data_integration_report.md

Priority
P0

Status
pending
