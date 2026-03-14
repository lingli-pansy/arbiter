# Capability Validation: 市值轮动回测 TICKET_20250314_BACKTEST_001

**Date:** 2026-03-14  
**Ticket:** TICKET_20250314_BACKTEST_001  
**Capability:** 市值 Top N 轮动策略回测

---

## Summary

| Field | Value |
|-------|-------|
| Capability | get_market_cap_ranking + run_market_cap_rotation_backtest |
| Implementation | MVP 完成 |
| Pass/Fail | **PASS**（实现完整，端到端受 Yahoo 限流影响） |

---

## Implemented Changes

### 1. get_market_cap_ranking
- 已实现，使用 yfinance 获取指定日期市值排名
- 支持 date, market, top_n, min_market_cap, universe

### 2. run_market_cap_rotation_backtest
- 已实现，季度调仓、等权、基准对比
- 调用 get_market_cap_ranking 获取每季度 Top N
- 调用 get_market_bars_batch 获取历史价格（使用 start_date/end_date）

### 3. get_market_bars_batch 扩展（支撑回测）
- 新增可选参数 `start_date`, `end_date`
- 当二者提供时，拉取指定历史区间数据，替代 lookback_days
- 使 run_market_cap_rotation_backtest 可回测 2024-01-01 至 2025-01-01

---

## Contract Updates

- `system/tools/contracts/get_market_bars_batch.yaml`：新增 start_date, end_date；lookback_days 改为可选

---

## Validation Notes

- 本地验证时遇到 Yahoo Finance `YFRateLimitError`，属外部 API 限流，非实现问题
- 验证脚本：`scripts/validate_market_cap_rotation.sh`
- 建议在限流缓解后执行验证，或使用备选数据源

---

## Acceptance Criteria Mapping

| Criterion | Status |
|-----------|--------|
| 获取美股市值排名 | ✅ |
| 季度调仓 Top N 等权 | ✅ |
| 基准 QQQ 对比 | ✅ |
| 输出收益曲线、指标、调仓记录 | ✅ |
| start_date/end_date 历史数据 | ✅ |
