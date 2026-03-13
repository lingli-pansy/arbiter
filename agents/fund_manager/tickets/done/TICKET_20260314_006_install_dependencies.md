---
id: TICKET_20260314_006
source_task: TICKET_20260314_005 Validation
title: Install Python Dependencies for IB Live Connection
status: done
created: 2026-03-14
resolved: 2026-03-14
priority: P1
---

## Blocking Issue
TICKET_20260314_005 的实现代码和 requirements.txt 已更新，但 Python 依赖包未安装到当前环境，导致无法验证 IB live 连接功能。

**Validation Report:** VALIDATION_20260314_005_ASYNCIO_FIX.md

**Error:**
```
ModuleNotFoundError: No module named 'ib_insync'
ModuleNotFoundError: No module named 'nest_asyncio'
```

---

## Resolution (2026-03-14)

**已实现:**
1. 依赖已安装至 `.venv`（ib_insync 0.9.86, nest_asyncio 1.6.0）
2. 新增 `system/tools/impl/verify_ib_deps.py` 验证脚本
3. 新增 `scripts/install_ib_deps.sh` 安装脚本

**验证:**
```bash
.venv/bin/python system/tools/impl/verify_ib_deps.py
# Output: nest_asyncio: installed, ib_insync: 0.9.86
```

**重要:** 所有需 IB 连接的工具必须使用 `.venv` 下的 Python，否则会遇到 ImportError。OpenClaw/agent 调用时需指定 `python: .venv/bin/python`。

**待跟进:** connect_broker live 模式在 TWS 未运行时仍返回 "Timeout should be used inside a task"（Python 3.14 + ib_insync 兼容性），建议单独开 ticket 处理。ImportError 已消除。

---

## Requested Capability
安装并验证以下 Python 包：

1. **ib_insync>=0.9.86**
2. **nest_asyncio>=1.6.0**

---

## Acceptance Criteria

- [x] `ib_insync>=0.9.86` 成功安装
- [x] `nest_asyncio>=1.6.0` 成功安装
- [x] 验证导入: verify_ib_deps.py 通过
- [ ] connect_broker live 返回 "Connection refused"（见待跟进）

---

## Related
- Parent Ticket: TICKET_20260314_005
- Grandparent Ticket: TICKET_20260314_004
- Implementation: system/tools/impl/verify_ib_deps.py, scripts/install_ib_deps.sh
- Requirements: system/tools/impl/requirements.txt
