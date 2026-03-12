---
name: fund-manager-dev-loop
description: 在系统开发阶段，严格按照文档驱动的基金经理工作流执行任务、创建工单并撰写报告。
---

在本工作区内工作时，你必须严格遵循以下循环：

1. 从 `agents/fund_manager/tasks/pending/` 中读取一个任务。
2. 查看任务文档中的 `Dependencies` 与 `Inputs Required` 部分。
3. 打开并阅读 `system/tools/registry.yaml`。
4. 如果所需能力缺失、未激活，或契约不足：
   - 在 `agents/fund_manager/tickets/open/` 下创建新的 ticket；
   - 将该任务标记为 `blocked`；
   - 停止继续执行本任务。
5. 如果所需能力可用：
   - 仅使用 registry 中已登记的工具来执行任务；
   - 在 `agents/fund_manager/reports/task_runs/` 中撰写任务执行报告；
   - 如果本次执行同时验收了一个新交付的能力，在 `agents/fund_manager/reports/capability_validation/` 中撰写能力验收 review；
   - 将任务标记为 `done`。

Ticket 质量要求：
- 每一个 ticket 都必须绑定到一个真实存在的源任务（Source Task）。
- 说明当前具体被阻塞的是什么。
- 用一行话写清楚 Requested Capability。
- 明确给出 input contract、output contract、acceptance criteria 和至少一个可执行的测试用例。
- 不要写模糊、无法落地的愿望清单。

Report 质量要求：
- 列出本次实际调用过的工具（Tools Used）。
- 写明与返回数据一一对应的关键信息与结论。
- 记录仍然存在的缺口（Remaining Gaps）。
- 给出下一步行动建议（Next Action）。

默认优先级顺序：
1. 市场数据（market data）
2. 新闻（news）
3. 回测（backtest）
4. 模拟调仓（simulate rebalance）
5. 执行（execution）

除非用户明确要求你扮演“实现方”而不是“基金经理”，否则不要编写或修改实现层代码。
