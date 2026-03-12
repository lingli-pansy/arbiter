---
name: arbiter-tool-contracts
description: 将 registry 中声明的工具契约视为交易辅助系统“能做什么”的唯一可信来源。
---

文件 `system/tools/registry.yaml` 是能力可用性的唯一事实来源（source of truth）。

解释规则：
- 只有当某个工具出现在 registry 中且 `status: active` 时，才视为“可用能力”；
- `input` 定义了允许的请求结构；
- `output` 定义了最小的响应结构；
- `errors` 定义了预期的失败类型；
- `state_reads` 与 `state_writes` 定义这个工具会读取 / 写入哪些系统状态。

当某个任务无法推进时，在创建 ticket 之前，你需要先对能力缺口进行分类：
- `missing_tool`：工具本身不存在；
- `inactive_tool`：工具存在但未激活；
- `insufficient_input_contract`：输入契约不够；
- `insufficient_output_contract`：输出契约不够支撑下一步决策；
- `missing_state_dependency`：缺少必要状态依赖；
- `unstable_error_surface`：错误类型混乱、不可预期。

每一张 ticket 都必须在 `Blocking Issue` 小节中使用上述分类之一。

在验收某项能力时，请检查：
- 契约 schema 是否完整；
- 返回结果是否足够支撑下一步业务决策；
- 错误类型是否可区分；
- 是否在需要的地方提供了刷新 / 任务 / 状态等元数据。

不要从实现文件名或函数名中“脑补”任何隐含保证，只信任 registry 中声明的契约。
