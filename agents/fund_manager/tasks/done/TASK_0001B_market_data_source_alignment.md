
Task ID
TASK_0001B

Title
Market data source alignment

Objective
审查当前 get_market_bars_batch 的 provider 实现与长期目标架构（NautilusTrader / IB）之间的差距，并产出对齐报告。

Business Context
当前 market data 使用 yfinance 作为临时 provider。本任务用于确认未来生产系统的数据来源路径：
- NautilusTrader 数据接口
- IB 数据能力
- 临时 provider 的替代策略

Key Questions
1 当前 get_market_bars_batch 的 schema 是否与 NT bar schema 兼容
2 provider 是否需要标准化字段
3 是否需要 provider adapter 层
4 registry 和 contract 是否需要扩展 metadata

Steps
1 审查 system/tools/contracts/get_market_bars_batch
2 审查 system/tools/registry.yaml
3 对比 NautilusTrader bar schema
4 记录差异
5 提出 contract 调整建议
6 如有必要创建 ticket

Expected Output
market_data_source_alignment_report.md

Priority
P0

Status
done (analysis only)

Execution_Notes
- 本任务为分析任务，产出 schema 对比报告
- 未涉及真实 IB/NT 连接或数据获取
- 实际集成验证见 TASK_0021_IB_CONNECTION_VALIDATION, TASK_0022_NT_BACKTEST_VALIDATION
