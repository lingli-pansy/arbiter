# TICKET_20250314_BACKTEST_001

## Source Task
用户验证回测能力，需求：2024-01-01 至 2025-01-01 期间，每季度调仓一次，选择美股市值 Top 5 公司做等金额轮动，本金 50 万美元，流动资金池 5 万美元，对比纳斯达克收益率曲线。

## Blocking Issue
现有工具链无法支持市值轮动策略回测，缺少三个关键能力：
1. 无法获取历史市值数据并筛选 Top N 股票
2. 没有市值轮动策略实现
3. 没有多周期循环回测框架

## Requested Capability
构建市值轮动回测完整链路，支持动态选股 + 周期性调仓 + 基准对比。

## Resolution (2026-03-14)
- `get_market_cap_ranking`: 已实现，使用 Yahoo Finance info API 获取市值排名
- `run_market_cap_rotation_backtest`: 已实现，季度调仓、等权、基准对比
- `get_market_bars_batch`: 扩展支持 `start_date`/`end_date` 用于历史回测
- 验收报告: `agents/fund_manager/reports/capability_validation/VALIDATION_20260314_BACKTEST_001.md`

## Status
Done

## Closed
2026-03-14
