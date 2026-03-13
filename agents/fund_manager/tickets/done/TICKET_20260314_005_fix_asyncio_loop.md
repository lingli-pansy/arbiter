# Ticket: Fix Asyncio Event Loop Issue in IB Live Connection

**Ticket ID:** TICKET_20260314_005  
**Created:** 2026-03-14  
**Status:** Open  
**Priority:** P1 (阻塞真实交易)

---

## Source Task
- **Task ID:** TICKET_20260314_004 validation
- **Task Title:** Implement Real IB Gateway Connection for connect_broker

---

## Blocking Issue
TICKET_20260314_004 实现已部署，但 live 模式出现 asyncio 事件循环错误：

```
error_message: "This event loop is already running"
```

根因：`create_live_connection` 使用 `asyncio.run()` 在已经运行的事件循环中创建新循环。

---

## Requested Capability
修复 IB live 连接的异步事件循环处理：

1. **正确处理嵌套事件循环**
   - 使用 `asyncio.get_event_loop()` 检测现有循环
   - 或使用 `nest_asyncio` 允许嵌套循环
   - 或改用同步连接方法

2. **保持现有功能**
   - 支持 host/port/client_id 配置
   - 返回真实 latency_ms
   - 保存连接状态到 JSON

---

## Why Existing Implementation Fails

**当前代码 (broker_store.py):**
```python
async def _connect_and_verify():
    from ib_insync import IB
    ib = IB()
    await ib.connectAsync(host, port, clientId=client_id, timeout=timeout_ms / 1000.0)
    ...

try:
    asyncio.run(_connect_and_verify())  # ❌ 在已有循环中调用
```

**错误输出:**
```json
{
  "success": false,
  "error_message": "This event loop is already running",
  "timestamp": "2026-03-13T19:54:33Z",
  "status": "failed",
  "latency_ms": 5194
}
```

---

## Suggested Fixes

**方案 1: 使用 nest_asyncio**
```python
import nest_asyncio
nest_asyncio.apply()
# 然后 asyncio.run() 可以嵌套
```

**方案 2: 使用同步连接**
```python
from ib_insync import IB
ib = IB()
ib.connect(host, port, clientId=client_id, timeout=timeout_ms/1000)
# 不使用 async/await
```

**方案 3: 检测现有循环**
```python
try:
    loop = asyncio.get_running_loop()
    # 使用现有循环
except RuntimeError:
    loop = None
    # 创建新循环
```

---

## Acceptance Criteria

1. [ ] live 模式在 TWS/Gateway 运行时成功连接
2. [ ] 不再抛出 "Event loop is already running" 错误
3. [ ] 支持自定义 host, port, client_id
4. [ ] 返回正确的 latency_ms
5. [ ] paper 模式保持兼容

## Test Case

**输入:**
```json
{
  "broker": "ib",
  "mode": "live",
  "host": "127.0.0.1",
  "port": 7497,
  "client_id": 1,
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
  "error_message": "Connection refused: TWS/Gateway not running on 127.0.0.1:7497",
  "timestamp": "2026-03-14T...",
  "status": "failed",
  "latency_ms": 50
}
```

## Related
- Implementation: `system/tools/impl/adapters/broker_store.py`
- Caller: `system/tools/impl/connect_broker.py`
- Parent Ticket: TICKET_20260314_004
