## 仓库规则域拆分与 OpenClaw 工作区收敛说明

本文件简要记录 2026-03-12 对本仓库进行的“规则域拆分 + OpenClaw 工作区收敛”改造。

### 目标

1. 让 OpenClaw 只读取 `workspace/` 下的 agent 规则与技能。  
2. 让根目录只保留仓库级通用协作规则。  
3. 让 Cursor 拥有单独的实现者说明文档，避免把自己当成基金经理 agent。  
4. 清理重复或冲突的 `USER.md` / `TOOLS.md` / `MEMORY.md` / `AGENTS.md`。  
5. 检查并更新 `openclaw.json`，使其贴合当前目录结构。

### 核心调整

- 根目录：
  - `AGENTS.md` 改写为仓库级协作规则（Doc-Driven、task→ticket→implementation→review→rerun 闭环、contract/registry 要求等）。  
  - 根目录 `USER.md` / `TOOLS.md` / `MEMORY.md` 归档到 `docs/archive/`，避免与 `workspace/` 下的版本冲突。

- `workspace/`：
  - 保持 `AGENTS.md` / `USER.md` / `TOOLS.md` / `MEMORY.md` 作为 OpenClaw / arbiter 基金经理 agent 的主要规则与上下文来源。  
  - 将 `workspace/TOOLS.md` 强化为“关键规则兜底文件”，明确任务选择、registry 使用、ticket 写作、report 输出以及“OpenClaw 不直接改 system/tools 实现代码”等。

- `docs/`：
  - 新增/更新：
    - `docs/CURSOR_IMPLEMENTER.md`：Cursor 实现方角色说明与默认执行策略。  
    - `docs/cursor_bootstrap.md`：在本仓库中启动 Cursor 工作流的步骤。  
    - `docs/archive/ROOT_USER.md` / `ROOT_TOOLS.md` / `ROOT_MEMORY.md`：旧根级规则的归档副本。

- `openclaw.json`：
  - 保持以仓库根作为 workspace，技能加载路径指向 `workspace/skills`，并在描述中指明人格定义见 `workspace/AGENTS.md`。

如需进一步调整规则域或 agent 架构，请在本文件基础上追加变更记录，保持演进过程可追踪。

