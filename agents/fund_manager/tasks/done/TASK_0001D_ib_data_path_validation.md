
Task ID
TASK_0001D

Title
IB data path validation

Objective
明确 IB 在当前系统中的角色（数据源 / 执行平台），并验证最小接入条件。

Business Context
系统计划使用 IB 作为券商执行平台，同时可能提供部分 market data。本任务用于确认 IB 数据能力与接入要求。

Key Questions
1 IB 是否作为主要 market data provider
2 IB Gateway / TWS 接入条件
3 需要的 market data subscription
4 与 NautilusTrader adapter 的关系

Steps
1 调研 IB market data capability
2 确认 API 访问要求
3 记录数据订阅需求
4 输出 integration note
5 如必要创建 capability ticket

Expected Output
ib_data_path_validation_report.md

Priority
P0

Status
done (analysis only)

Execution_Notes
- 本任务为分析任务，产出 IB 能力调研报告
- 未涉及真实 IB Gateway/TWS 连接
- 实际连接验证见 TASK_0021_IB_CONNECTION_VALIDATION
