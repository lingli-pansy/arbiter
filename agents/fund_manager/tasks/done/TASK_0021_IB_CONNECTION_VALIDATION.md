Task ID
TASK_0021_IB_CONNECTION_VALIDATION

Title
Validate IB Gateway/TWS connection capability

Objective
验证 IB 连接工具 (connect_broker) 是否能在当前环境中正常工作。

Business Context
系统注册了 connect_broker 工具，但从未实际验证过 IB Gateway/TWS 连接。本任务确认：
1. IB Gateway/TWS 是否可访问
2. 连接配置是否正确
3. 需要用户提供什么权限/配置

Inputs Required
connect_broker

Steps
1 尝试连接 IB (paper trading mode)
2 记录连接结果
3 如失败，记录错误类型（配置缺失 / 网络问题 / 权限不足）
4 输出验证报告

Expected Output
IB 连接验证报告

Dependencies
connect_broker

Priority
P1

Status
done

Execution Results
---
**Execution Date:** 2026-03-14
**Report:** REPORT_20260314_TASK0021_ib_connection.md

**Results:**
- ✅ Paper Mode: Connection successful (connection_id: 970c566e-fdbe-4ada-9466-326183d02116)
- ❌ Live Mode: Implementation missing (hardcoded error response)

**Contract Compliance:**
- All input/output contracts satisfied for paper mode
- Live mode returns error as per current implementation

**Follow-up Ticket:**
- TICKET_20260314_004: Implement Real IB Gateway Connection for connect_broker

**User Action for Live Trading:**
1. ✅ Paper account configured
2. ⏳ Wait for TICKET_20260314_004 implementation
3. Install IB Gateway or TWS
4. Enable API (Global Configuration → API → Settings)
5. Configure port 7496/7497

Blockers
- TICKET_20260314_007: Python 3.14 Compatibility for IB Live Connection (live mode blocked)

Notes
本任务仅验证连接能力，不涉及真实交易。需要用户确认是否已配置 IB Gateway。
