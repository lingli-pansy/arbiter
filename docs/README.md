This pack is a starting configuration for running OpenClaw as a real fund-manager agent during development of a private trading assistant system.

**OpenClaw 直接使用 workspace/**  
在 `openclaw.json` 中，`fund-manager-dev` 与 `arbiter-dev` 的 **workspace** 已设为 `./workspace`，Core Files（AGENTS.md、TOOLS.md、USER.md、MEMORY.md）从 **workspace/** 目录加载，无需根目录符号链接。  
实际生效的 workspace 来自 **`~/.openclaw/openclaw.json`** 里该 agent 的 `workspace` 字段。Dashboard 无法修改；CLI 无 `set-workspace` 命令，需手动编辑该文件，将 arbiter-dev 的 `workspace` 设为 **`~/arbiter-2/workspace`**，保存后重启 Gateway/TUI。  
仓库级协作规则（所有人/工具）见根目录 `AGENTS.md` 与 `docs/REPO_COLLABORATION_RULES.md`。

Included files:
- openclaw.json: minimal agent + workspace config
- workspace/AGENTS.md: role and workflow rules for the fund-manager agent
- workspace/TOOLS.md: tool usage model and contract rules
- workspace/USER.md: workspace-specific project context
- workspace/MEMORY.md: long-lived development constraints
- workspace/skills/*: two local workspace skills to reinforce the task -> ticket -> report loop

How to use:
1. Merge these files into the repo/workspace that OpenClaw will run against.
2. Ensure your existing `agents/`, `system/`, and `docs/` directories are present in the same workspace.
3. Start OpenClaw using this workspace config.
4. Give the agent an initial task file under `agents/fund_manager/tasks/pending/`.
5. Let the agent run; it should either produce a ticket or a report.
