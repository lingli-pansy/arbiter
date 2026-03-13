---
id: TICKET_20260314_007
status: done
resolved: 2026-03-14
---

# Ticket: Python 3.14 Compatibility for IB Live Connection

**Resolution:** 采用方案 4（降级 Python 版本）。项目通过 `install_ib_deps.sh` 使用 Python 3.11–3.13 创建 `.venv`，避开 Python 3.14 与 ib_insync 的兼容问题。`connect_broker` 在 Python 3.13 下正常运行。pyproject.toml 已声明 `requires-python = ">=3.11,<3.14"`。
