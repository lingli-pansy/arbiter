---
id: TICKET_20260314_008
status: done
resolved: 2026-03-14
---

# Ticket: Missing analyze_slippage Tool

**Resolution:** 已实现。新增 contract、impl、registry 注册、测试脚本。

**Implemented:**
- `system/tools/contracts/analyze_slippage.yaml`
- `system/tools/impl/analyze_slippage.py`
- `system/tools/registry.yaml` 已注册 analyze_slippage
- `system/tools/tests/test_analyze_slippage.py`

**Capability:** 接收 simulate_execution 输出，按 symbol/side 汇总滑点，支持高滑点阈值检测、基点(bps)计算。
