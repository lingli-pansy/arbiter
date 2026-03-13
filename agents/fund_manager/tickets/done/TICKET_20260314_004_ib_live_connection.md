# Ticket: Implement Real IB Gateway Connection for connect_broker

**Ticket ID:** TICKET_20260314_004  
**Created:** 2026-03-14  
**Status:** Done  
**Priority:** P1 (阻塞真实交易)

---

## Source Task
- **Task ID:** TASK_0021_IB_CONNECTION_VALIDATION
- **Task Title:** Validate IB Gateway/TWS connection capability

---

## Blocking Issue
用户已配置 IB Paper 账户，但 `connect_broker` 工具的 live 模式仅返回硬编码错误，未实现真实 IB Gateway/TWS 连接：

```python
# 当前实现 (connect_broker.py line 70-75)
if mode == "live":
    out = _std_response(
        False,
        error_message="live mode requires IB Gateway/TWS running; use paper mode for testing",
        status="failed",
    )
```

---

## Requested Capability
实现真正的 Interactive Brokers 连接能力：

1. **IB Gateway/TWS 连接**
   - 使用 `ib_insync` 或官方 IB API
   - 支持 localhost:7496 (TWS) 或 7497 (Gateway)
   - 支持 Paper 和 Live 账户

2. **连接健康检查**
   - 验证连接是否活跃
   - 处理断开重连
   - 返回真实延迟 (latency_ms)

3. **配置管理**
   - 支持自定义 host/port
   - 支持 client ID 配置
   - 超时处理

---

## Why Existing Tools Are Insufficient
- `connect_broker` 当前仅支持 mock paper 连接
- live 模式硬编码返回错误，无法连接真实 IB
- 其他工具 (`get_broker_account`, `submit_order`) 依赖真实连接才能工作

---

## Input Contract (Existing)
```yaml
broker: "ib"  # required
mode: "live" | "paper"  # required  
timeout_ms: 1000-30000  # optional, default 5000
```

## Output Contract (Existing)
```yaml
success: boolean
error_message: string
timestamp: datetime
connection_id: string
status: "connected" | "failed"
latency_ms: integer
```

## Acceptance Criteria

1. [ ] live 模式能成功连接运行中的 IB Gateway/TWS - ❌ BLOCKED by asyncio issue
2. [ ] 返回真实的 connection_id 和 latency_ms - ❌ BLOCKED
3. [x] 连接失败时返回具体错误（网络/配置/权限） - ✅ PASS
4. [x] 支持配置 host, port, client_id - ✅ PASS
5. [x] 与现有 paper 模式保持兼容 - ✅ PASS

## Validation Results

**Date:** 2026-03-14
**Report:** VALIDATION_20260314_004_ib_live_connection.md
**Status:** PARTIAL

| Test | Result |
|------|--------|
| Paper mode | ✅ PASS |
| Error handling (TWS not running) | ✅ PASS |
| Custom host/port/client_id | ✅ PASS |
| Live connection with TWS | ❌ FAIL - asyncio event loop error |

**Follow-up:** TICKET_20260314_005 - Fix Asyncio Event Loop Issue

## Test Case

**输入:**
```json
{
  "broker": "ib",
  "mode": "live",
  "timeout_ms": 10000
}
```

**预期输出 (TWS running):**
```json
{
  "success": true,
  "error_message": "",
  "timestamp": "2026-03-14T...",
  "connection_id": "<uuid>",
  "status": "connected",
  "latency_ms": 150
}
```

**预期输出 (TWS not running):**
```json
{
  "success": false,
  "error_message": "Connection refused: TWS/Gateway not running on localhost:7496",
  "timestamp": "2026-03-14T...",
  "status": "failed"
}
```

## Implementation Notes

**建议方案:**
```python
# 使用 ib_insync
from ib_insync import IB, Stock

def create_live_connection(host="127.0.0.1", port=7496, client_id=1, timeout_ms=5000):
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, timeout=timeout_ms/1000)
        return ib, True
    except Exception as e:
        return None, False
```

**依赖:**
- `ib_insync` 库 (需添加到 requirements)

**配置:**
- 支持环境变量或配置文件设置 host/port
- 默认: 127.0.0.1:7496 (TWS), 127.0.0.1:7497 (Gateway)

## Related
- Current implementation: `system/tools/impl/connect_broker.py`
- Paper mode: `system/tools/impl/adapters/broker_store.py`
- Contract: `system/tools/contracts/connect_broker.yaml`
- Blocked: 真实交易执行能力
