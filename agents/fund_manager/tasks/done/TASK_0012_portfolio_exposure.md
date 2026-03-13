Task ID
TASK_0012

Title
Portfolio exposure analysis

Objective
分析组合风险暴露。

Business Context
用于验证组合分析与风险报告能力。

Inputs Required
get_portfolio
analyze_exposure

Assets
NVDA
MSFT
AAPL

Steps
1 读取当前组合
2 分析行业和集中度暴露
3 输出风险报告

Expected Output
risk report

Dependencies
portfolio state
risk analysis tool

Priority
P2

Status
pending

Blockers
none

Notes
如果缺少 sector mapping 或 exposure tool，生成 ticket。
