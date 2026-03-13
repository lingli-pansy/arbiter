## 在本仓库中启动 Cursor 工作流

本仓库假定以下协作模式：

- OpenClaw / arbiter 作为 **基金经理 agent**，围绕真实任务使用系统；
- Cursor 作为 **实现方 / 工程团队**，根据任务与 ticket 持续迭代能力。

### 1. 快速了解当前状态

1. 阅读 `workspace/USER.md`：系统目标与工作偏好。  
2. 阅读 `workspace/MEMORY.md`：长期约束与验收标准。  
3. 阅读 `workspace/AGENTS.md`：Fund Manager (Dev) 的人格与工作流。  
4. 浏览：
   - `agents/fund_manager/tasks/BACKLOG.md` 与 `tasks/pending/**`  
   - `agents/fund_manager/tickets/open/**`  
   - `system/tools/registry.yaml` 与 `system/tools/contracts/**`

### 2. 选择与确认任务

1. 优先从 `agents/fund_manager/tasks/pending/` 中选一个 P0 / P1 任务。  
2. 查看该任务是否已有对应 ticket：  
   - 若已有：以 ticket 为当前实现入口。  
   - 若没有但已被实际阻塞：可以先与用户确认后补写 ticket。

### 3. 对齐工具契约与实现范围

1. 以 `system/tools/contracts/**` 中的契约为准，不擅自扩展隐式行为。  
2. 若契约不足以满足任务需求：  
   - 在 `agents/fund_manager/tickets/open/**` 中补充或新建更完整的 ticket。  
3. 实现工具时：  
   - 更新 `system/tools/registry.yaml`，把工具标记为 `status: active`（或合适状态）。  
   - 在 `system/tools/impl/**` 或项目约定位置添加实现代码。

### 4. 交付与验收

1. 实现完成后，可在本地简单验证（脚本 / 测试）。  
2. 将预期使用方式与样例输入输出写入相关 ticket 或补充文档。  
3. 由 OpenClaw Fund Manager 通过任务执行与 report 输出进行最终验收。

> 提醒：除非任务或 ticket 明确标记为仅需设计方案（如 `design_only = true`），否则默认期望 Cursor 侧**真正落地最小可用实现**，而不是只给建议。

### 5. 启动 OpenClaw TUI（arbiter-dev）

OpenClaw TUI **不支持** `-a`、`-w` 等参数；agent 与 workspace 由系统已配置的 agent 决定。

- 本仓库中 repo 内 `openclaw.json` 已将 agent 的 **workspace 设为 `./workspace`**；**实际生效**的 workspace 路径在 **`~/.openclaw/openclaw.json`** 的 `agents.list[].workspace`。Dashboard 不能改该值，CLI 也没有 `set-workspace`，需直接编辑 `~/.openclaw/openclaw.json`，将 arbiter-dev 的 `workspace` 改为 **`/Users/xiaoyu/arbiter-2/workspace`**（或 `~/arbiter-2/workspace`）。改完后重启 Gateway/TUI 即可。
- 若 `arbiter-dev` 已配置且为 default，在项目根执行：`cd ~/arbiter-2` 后 `openclaw tui`。
- 在 TUI 内切换 agent：**Ctrl+G** 或 `/agents`；切换 session：`/session agent:arbiter-dev:main`。
- 查看当前 agent 与 workspace：`openclaw agents list`。

如需为 Cursor 侧增加更细致的开发流程（例如代码风格、测试策略等），可以扩展本文件或新增专门的 `docs/**` 文档。

