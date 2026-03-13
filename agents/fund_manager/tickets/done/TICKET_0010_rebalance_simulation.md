# TICKET_0010: Rebalance Simulation Capability

**Status:** done  
**Created:** 2026-03-14  
**Completed:** 2026-03-14  
**Source Task:** TASK_0013 (Simulate rebalance)  
**Blocking Issue:** `missing_tool`

---

## Resolution

实现 simulate_rebalance 工具，支持等权与自定义目标权重调仓模拟。

**实现:**
- 输入: portfolio 或 portfolio_id，target_weights (type: equal/custom)
- 输出: current_weights, target_weights, differences, trades (BUY/SELL/HOLD), cash_required, cash_generated, net_cash_flow, expected_turnover

**修改文件:**
- system/tools/impl/simulate_rebalance.py
- system/tools/contracts/simulate_rebalance.yaml
- system/tools/registry.yaml
- system/tools/tests/test_simulate_rebalance.py
