# 仓库级协作规则（Repository-Level Collaboration Rules）

本文件面向**所有在本仓库工作的参与者和工具**（包括 OpenClaw、Cursor、人工开发者），只约束协作方式与工作流，不定义具体人格。

---

## 零、路径约定（Critical）

**仓库根目录**: `/Users/xiaoyu/arbiter-2`

所有任务、报告、工单必须写入以下**绝对路径**，严禁写入 `workspace` 子目录：

| 类型 | 正确路径 | 错误路径（已废弃） |
|------|----------|-------------------|
| 待办任务 | `/Users/xiaoyu/arbiter-2/agents/fund_manager/tasks/pending/` | `~/arbiter-2/workspace/agents/fund_manager/tasks/pending/` |
| 执行中任务 | `/Users/xiaoyu/arbiter-2/agents/fund_manager/tasks/running/` | `~/arbiter-2/workspace/...` |
| 已完成任务 | `/Users/xiaoyu/arbiter-2/agents/fund_manager/tasks/done/` | `~/arbiter-2/workspace/...` |
| 执行报告 | `/Users/xiaoyu/arbiter-2/agents/fund_manager/reports/task_runs/` | `~/arbiter-2/workspace/...` |
| 能力验收 | `/Users/xiaoyu/arbiter-2/agents/fund_manager/reports/capability_validation/` | `~/arbiter-2/workspace/...` |
| Open Tickets | `/Users/xiaoyu/arbiter-2/agents/fund_manager/tickets/open/` | `~/arbiter-2/workspace/...` |
| 已完成 Tickets | `/Users/xiaoyu/arbiter-2/agents/fund_manager/tickets/done/` | `~/arbiter-2/workspace/...` |
| 工具注册表 | `/Users/xiaoyu/arbiter-2/system/tools/registry.yaml` | `~/arbiter-2/workspace/system/tools/...` |

**注意**: 旧路径 `/Users/xiaoyu/arbiter-2/workspace/agents/**` 已废弃，相关文件已合并到正确路径。所有未来操作必须使用绝对路径 `/Users/xiaoyu/arbiter-2/agents/**`。

---

## 一、文档驱动开发（Doc-Driven Development）

- **一切以文档为入口**：  
  - 业务目标与阶段性规划 → `workspace/USER.md`  
  - 长期约束与验收标准 → `workspace/MEMORY.md`  
  - 基金经理 agent 人格与工作流 → `workspace/AGENTS.md`  
  - 工具注册与契约 → `workspace/TOOLS.md`、`system/tools/registry.yaml`、`system/tools/contracts/`
- **先读后改**：在修改代码、配置或 contracts 之前，必须先阅读相关任务、ticket 与约束文档。

---

## 二、Task → Ticket → Implementation → Review → Rerun 闭环

- **Task 来源**：  
  - 所有基金经理任务统一存放在 `agents/fund_manager/tasks/**`。  
  - 新任务应按模板创建，保持结构化（目标、依赖、Inputs Required、Expected Output 等）。

- **Ticket 规则**：  
  - 任何能力缺口、工具契约不足、实现不稳定，都应通过 `agents/fund_manager/tickets/**` 记录。  
  - Ticket 必须包含：Source Task、Blocking Issue、Requested Capability、Why Existing Tools Are Insufficient、Input/Output Contract、Acceptance Criteria、Test Case。

- **Implementation 规则**：  
  - 实现/修改能力时，以 ticket 中的契约为基准。  
  - 不在没有 ticket 的情况下大幅改动系统行为。  
  - 代码与工具实现应落在约定的目录结构内（如 `system/tools/**` 等）。

- **Review 与 Rerun**：  
  - 能力实现后，由基金经理 agent 通过重新执行原 Task 进行验收。  
  - 验收结果与关键发现应写入 `agents/fund_manager/reports/**`，形成审计链路。

---

## 三、Contract / Registry 更新要求

- **唯一可信注册表**：  
  - 所有交易辅助工具必须通过 `system/tools/registry.yaml` 注册后，方可被视为“可用能力”。  
  - 仓库中存在但未在 registry 中登记的脚本，一律视为内部实现细节，不对基金经理 agent 暴露。

- **契约优先**：  
  - 每个对外暴露的工具都应在 `system/tools/contracts/` 下拥有明确的 Input/Output Contract。  
  - 任何超出契约的隐式行为，都不应被上层依赖；如确有需要，应通过 ticket 更新契约。

- **变更流程**：  
  - 修改工具行为时，先检查并更新对应 contract；  
  - 然后更新 `registry.yaml` 与实现代码；  
  - 最后通过任务重跑与 report 完成验收。

---

## 四、测试与验收要求

- **最小可用能力（MVP Capability）**：  
  - 每次实现以“满足当前阻塞任务的最小闭环”为目标，而不是追求过度通用化。  
  - 至少提供一个可复现的测试用例（输入 + 期望输出结构），便于自动或半自动验证。

- **验收标准**（来自 `workspace/MEMORY.md`）：  
  - 新能力接入后，基金经理 agent 是否能在不依赖人工拆解的前提下完成原任务。  
  - 失败时是否能产出结构化、可实现的 ticket。  
  - 成功时是否留下足够的 report / review 证据。

---

## 五、业务目标与边界

- **不擅自改动业务目标**：  
  - 仓库的业务愿景和阶段性重点由 `workspace/USER.md` 与相关文档定义。  
  - 技术实现方不得单方面更改业务目标或优先级，如有建议，应通过文档说明或新任务提出。

- **角色定义的归属**：  
  - 具体 agent 的人格与边界（如基金经理 agent、研究 agent 等），统一在 `workspace/AGENTS.md` 中定义和扩展。  
  - 根目录不再直接约束“谁可以/不可以改代码”，而只约束协作方式与工作流。

---

## 六、OpenClaw 与 Cursor 的分工（高层约定）

- **OpenClaw / arbiter**：  
  - 作为基金经理类 agent，遵守 `workspace/AGENTS.md` 与 `workspace/TOOLS.md` 的规则；  
  - 只通过工具与文档使用系统，不直接改动实现代码。

- **Cursor / 实现方**：  
  - 作为工程实现者，遵守本文件与 `docs/CURSOR_IMPLEMENTER.md`；  
  - 根据 tasks 与 tickets 实现或改进能力，并把所有变更显式落回仓库（代码、contracts、registry、文档）。

如需扩展新的协作规则或工作流，请优先补充本文件和 `docs/**`，保持整个仓库的协作逻辑清晰一致。
