本文件是 **OpenClaw / arbiter 基金经理 agent 的关键规则兜底文件**。  
无论 skills 或其他文档如何扩展，以下规则始终优先生效。

**⚠️ 路径约定（Critical）**
所有文件必须使用**绝对路径**：
- 任务: `/Users/xiaoyu/arbiter-2/agents/fund_manager/tasks/**`
- 报告: `/Users/xiaoyu/arbiter-2/agents/fund_manager/reports/**`
- 工单: `/Users/xiaoyu/arbiter-2/agents/fund_manager/tickets/**`
- 注册表: `/Users/xiaoyu/arbiter-2/system/tools/registry.yaml`

**禁止**使用相对路径或 `workspace` 子目录路径。

---

## 一、任务选择与入口

- 所有待办任务位于：`agents/fund_manager/tasks/pending/`。  
- 基金经理 agent 应：
  - 优先读取 `tasks/pending/` 中的任务列表；  
  - 按任务文件中的 Priority 字段（如 P0、P1）选择当前**最高优先级**的一个任务开始；  
  - 将正在处理的任务在文档或目录结构中标记为 running（例如移动到 `tasks/running/` 或在文件中更新 Status）。

---

## 二、工具注册表（registry）的唯一性

本工作区的交易辅助系统工具必须统一通过 `system/tools/registry.yaml` 暴露与登记。

基金经理 agent 只把 registry 里的工具视为“可用能力”。
如果某个脚本存在但未登记，视为不可用。

当前工具分层：
1. 市场数据：如 get_market_bars、get_market_bars_batch。
2. 新闻数据：如 get_news_digest。
3. 研究执行：如 run_backtest。
4. 组合与观察列表：如 get_watchlist、update_watchlist、simulate_rebalance。
5. 状态与日志：如 refresh_state、job_state、portfolio_state。

---

## 三、执行任务时的标准流程

当基金经理 agent 准备执行某个任务时，应遵守以下顺序：

1. **读取任务**：  
   - 从 `agents/fund_manager/tasks/pending/` 或 `tasks/running/` 中打开目标任务文件；  
   - 明确该任务的 Objective、Dependencies、Inputs Required 与 Expected Output。
2. **检查工具可用性**：  
   - 查看 `system/tools/registry.yaml`，确认任务依赖的工具是否存在且 `status: active`；  
   - 如有 contracts，则同时参考 `system/tools/contracts/**` 中对应工具的 Input/Output Contract。
3. **判断是否需要写 ticket**：  
   - 若发现：
     - 工具不存在，或  
     - 工具未 active，或  
     - 契约不足以支持当前任务，或  
     - 数据尚未 ready，或  
     - 工具返回错误且无法通过重试解决，  
   则应在 `agents/fund_manager/tickets/open/` 下创建/补充 ticket，记录 Blocking Issue 与所需能力。
4. **工具可用时执行任务并写 report**：  
   - 当依赖工具存在、已注册且契约满足需求时，使用这些工具完成任务；  
   - 将执行过程中的关键发现、结果与剩余疑问写入：
     - `agents/fund_manager/reports/task_runs/`（任务执行报告），以及/或  
     - `agents/fund_manager/reports/capability_validation/`（能力验收报告）。
5. **更新任务状态**：  
   - 任务因能力缺口被阻塞时，将任务状态标记为 blocked，并链接相关 ticket；  
   - 任务成功完成时，将状态标记为 done，并在 report 中引用所用工具与版本。

---

## 四、工具使用与契约遵守

工具使用规则：
1. 先查 `registry.yaml`，再使用工具。
2. 只信任 contracts 与 registry 中声明的 Input/Output Contract。
3. 任何超出契约的期望都必须通过 ticket 请求，而不是在调用时假设额外行为。
4. 如果工具结果不满足任务要求，先确认是：
   - 工具不存在
   - 工具未 active
   - contract 不足
   - 数据未 ready
   - 返回错误
   然后再写 ticket。
5. 不假设底层引擎实现细节。底层可能是 NautilusTrader、IBKR adapter 或其他实现，但对基金经理 agent 来说都属于系统内部。

特别重要的一点：

- **OpenClaw / 基金经理 agent 不直接修改 `system/tools` 的实现代码**。  
  - 如果工具行为需要调整，应通过 ticket 让实现方（如 Cursor）修改 contracts、registry 与实现；  
  - 基金经理只通过工具与文档与系统交互。

---

## 五、常见读取与产出路径

基金经理 agent 常见读取路径：
- ./agents/fund_manager/tasks/
- ./agents/fund_manager/tickets/
- ./agents/fund_manager/reports/
- ./system/tools/registry.yaml
- ./system/tools/contracts/
- ./system/state/

产出路径约定：
- task 执行结果 → agents/fund_manager/reports/task_runs/
- 能力验收结果 → agents/fund_manager/reports/capability_validation/
- 能力缺口 → agents/fund_manager/tickets/open/

文件命名建议：
- TASK_YYYYMMDD_XXXX.md
- TICKET_YYYYMMDD_XXXX.md
- REPORT_YYYYMMDD_XXXX.md
- REVIEW_YYYYMMDD_XXXX.md

---

## 六、验收优先级与当前阶段策略

验收优先级：
1. 市场数据链路
2. 新闻数据链路
3. 回测链路
4. 模拟调仓链路
5. 真实执行链路

当前开发阶段策略：
- 先验收 research 与 paper workflow。
- 先不要求真实自动下单。
- 只要任务被真实阻塞，就优先写 ticket，推动 Cursor 交付最小能力。

---

### 与 `arbiter-dev` agent 的关系

- `arbiter-dev` agent（见 `openclaw.json` 与 `workspace/AGENTS.md`）在本地运行时：
  - 完全以 `system/tools/registry.yaml` 作为“可用能力”的唯一来源；
  - 只在 registry 中存在且 `status: active` 的工具上做决策与执行；
  - 当工具缺失或契约不足时，通过 `agents/fund_manager/tickets/open/` 写 ticket，而不是直接假设新能力已存在。

- 若你为 arbiter 系统新增能力，**必须先更新 `system/tools/registry.yaml` 与（如需要）`system/tools/contracts/`**，这样 `arbiter-dev` 才会把它视为可用工具。
