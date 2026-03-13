# TICKET_0006: Backtest Metrics Calculation Capability

**Status:** done  
**Created:** 2026-03-13  
**Completed:** 2026-03-13  
**Source Task:** TASK_0009 (Backtest metrics review)  
**Blocking Issue:** `insufficient_output_contract`

---

## Resolution

在 `run_backtest` 输出中扩展 `report.metrics` 字段，提供结构化回测指标。

**实现方式:** Option A - 扩展 run_backtest

**已实现指标:**
- sharpe_ratio
- max_drawdown_pct
- cagr_pct
- win_rate_pct (需 positions 含 PnL)
- avg_trade_pnl
- total_trades
- profit_factor
- calmar_ratio
- volatility_pct

**修改文件:**
- system/tools/impl/run_backtest.py: _calculate_metrics(), 集成到 report
- system/tools/contracts/run_backtest.yaml: metrics 契约
- system/tools/tests/test_run_backtest.py: 验证 metrics 结构
