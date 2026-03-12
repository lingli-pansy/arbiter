本工作区的交易辅助系统工具必须统一通过 system/tools/registry.yaml 暴露与登记。

基金经理 agent 只把 registry 里的工具视为“可用能力”。
如果某个脚本存在但未登记，视为不可用。

当前工具分层：
1. 市场数据：如 get_market_bars、get_market_bars_batch。
2. 新闻数据：如 get_news_digest。
3. 研究执行：如 run_backtest。
4. 组合与观察列表：如 get_watchlist、update_watchlist、simulate_rebalance。
5. 状态与日志：如 refresh_state、job_state、portfolio_state。

工具使用规则：
1. 先查 registry，再使用工具。
2. 只信任 registry 中声明的 input/output contract。
3. 任何超出 contract 的期望都必须通过 ticket 请求。
4. 如果工具结果不满足任务要求，先确认是：
   - 工具不存在
   - 工具未 active
   - contract 不足
   - 数据未 ready
   - 返回错误
   然后再写 ticket。
5. 不假设底层引擎实现细节。底层可能是 NautilusTrader、IBKR adapter 或其他实现，但对基金经理 agent 来说都属于系统内部。

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
