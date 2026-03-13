# TICKET_0007: Mean Reversion Strategy Implementation

**Status:** done  
**Created:** 2026-03-14  
**Completed:** 2026-03-14  
**Source Task:** TASK_0010 (Strategy comparison)  
**Blocking Issue:** `missing_tool`

---

## Resolution

实现 mean_reversion 均值回归策略，支持与 momentum_20d 对比。

**实现:**
- `system/tools/impl/strategies/mean_reversion.py`: MeanReversion 策略
- 逻辑：价格低于 N 日均线 X% 时做多，回归均线时平仓
- 参数：lookback_period=20, deviation_threshold=0.02, trade_size=100
- run_backtest 已注册 strategy_id="mean_reversion"

**修改文件:**
- system/tools/impl/run_backtest.py: 添加 mean_reversion 分支
- system/tools/contracts/run_backtest.yaml: 更新 strategy_id/config 描述
- system/tools/tests/test_run_backtest.py: test_mean_reversion_strategy
