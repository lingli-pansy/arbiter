This pack is a starting configuration for running OpenClaw as a real fund-manager agent during development of a private trading assistant system.

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
