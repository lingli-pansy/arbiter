# TICKET_0009: Portfolio Exposure Analysis Capability

**Status:** done  
**Created:** 2026-03-14  
**Completed:** 2026-03-14  
**Source Task:** TASK_0012 (Portfolio exposure analysis)  
**Blocking Issue:** `missing_tool`

---

## Resolution

实现 analyze_exposure 工具，支持行业分布与集中度分析。

**实现:**
- sector: 静态 sector 映射，行业 breakdown，concentration_risk
- concentration: max_position, top_3_weight, hhi, effective_positions
- 输入: portfolio 对象或 portfolio_id（从 state 加载）

**修改文件:**
- system/tools/impl/analyze_exposure.py
- system/tools/impl/adapters/sector_mapper.py
- system/tools/contracts/analyze_exposure.yaml
- system/tools/registry.yaml
- system/tools/tests/test_analyze_exposure.py
