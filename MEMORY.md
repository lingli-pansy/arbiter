长期约束：
- OpenClaw 是真实基金经理 agent，而不是虚构角色文档。
- Cursor 是实现方，不负责基金经理判断。
- 交易辅助系统是能力层，不直接代替 agent 思考。
- 每次能力建设都要回到真实 task 验收。
- task -> ticket -> implementation -> review -> rerun 是核心闭环。

当前验收标准：
- 新能力接入后，OpenClaw 能否不依赖人工拆解，独立完成原任务。
- 若失败，能否产出结构化、可实现的 ticket。
- 若成功，能否留下足够的 report / review 证据。
