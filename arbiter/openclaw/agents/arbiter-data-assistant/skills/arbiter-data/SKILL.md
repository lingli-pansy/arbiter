---
name: arbiter-data
description: 使用 Arbiter MCP 数据工具进行市场数据与新闻查询、刷新和巡视的技能。
---

## 场景概览

该技能用于指导 agent 如何使用 Arbiter 的 MCP 工具完成以下数据助手场景：

- 查询单个标的的行情与新闻；
- 手动刷新单个或一小批标的的行情/新闻数据；
- 对一个 symbol universe 做「市场巡视」，了解数据新鲜度与最近新闻情况。

## 可用 MCP Tools（只读与刷新）

### 1. get_market_bars

- **用途**：查询某个标的在指定时间区间内的历史 K 线数据。
- **典型调用时机**：
  - 用户希望看某个标的在特定时间段的走势，而不仅仅是最近 N 根。
- **参数**：
  - `symbol`: 股票代码（如 `"NVDA"`）。
  - `timeframe`: 周期字符串（当前以 `"1d"` 为主）。
  - `start`: ISO8601 时间字符串，如 `"2025-01-01T00:00:00+00:00"`。
  - `end`: ISO8601 时间字符串。
- **注意**：适合时间段明确的问题，例如“看过去一年的日线情况”。

### 2. get_latest_bars

- **用途**：查询某标的最新 N 根 K 线。
- **典型调用时机**：
  - 用户问“看 NVDA 最近 20 根 1d bars”。
  - 做盘前/盘中快速浏览最近一段走势。
- **参数**：
  - `symbol`: 股票代码。
  - `timeframe`: 如 `"1d"`。
  - `limit`: 返回条数上限（默认 20）。
- **内部行为**：
  - 在数据层使用 `ORDER BY timestamp DESC LIMIT N` 查询，而非全表扫描。

### 3. get_news

- **用途**：查询某标的最新新闻。
- **典型调用时机**：
  - 用户问“最近 NVDA 有什么新闻？”。
  - 市场巡视场景中，为 universe 中的每个 symbol 抓取若干 headline。
- **参数**：
  - `symbol`: 股票代码。
  - `limit`: 返回新闻条数上限（可用 3~10）。

### 4. get_refresh_state

- **用途**：查询 refresh_state 中记录的数据刷新状态。
- **典型调用时机**：
  - 需要解释“数据更新到哪里了”、“最近一次成功刷新是什么时候”。
- **参数**：
  - `dataset_type`: `"market_bars"` 或 `"news_events"`。
  - `dataset_key`:  
    - 行情：`"{symbol}:{timeframe}"`（如 `"NVDA:1d"`）  
    - 新闻：`"{symbol}"`（如 `"NVDA"`）

### 5. get_universe_data_summary

- **用途**：对多个 symbol 一次性获取数据新鲜度概览。
- **典型调用时机**：
  - 盘前/盘中做「市场巡视」，需要知道：
    - 哪些标的有最新的行情 bar；
    - 哪些标的最近有新闻；
    - 各自的 refresh 状态。
- **参数**：
  - `symbols`（可选）：symbol 列表；若为空则使用 Arbiter 默认 universe。
  - `timeframe`：如 `"1d"`。
  - `limit`（可选）：仅对默认 universe 生效，用于截取前 N 个 symbol。

## 刷新相关 Tools

### 6. refresh_market_data

- **用途**：刷新单个标的的行情数据，并返回刷新结果与最新 refresh_state。
- **适用场景**：
  - 用户明确请求“刷新 NVDA 的行情数据”。
  - 在做任何较重的分析前，先确保单标的数据是最新的。

### 7. refresh_news

- **用途**：刷新单个标的的新闻数据，并返回刷新结果与最新 refresh_state。
- **适用场景**：
  - 用户请求“刷新 NVDA 的新闻”；
  - 检查某个标的是否有新的新闻出现。

### 8. refresh_market_batch

- **用途**：依次刷新一组 symbol 的行情数据。
- **典型调用时机**：
  - 盘前对一组重点标的（如默认 universe 的子集）做一次集中的行情刷新。
- **建议使用方式**：
  - 接受用户提供的 symbol 列表，或基于默认 universe 截取一小批（例如前 10~20 个）。
  - 刷新结果可配合 `get_universe_data_summary` 一起总结。

### 9. refresh_news_batch

- **用途**：依次刷新一组 symbol 的新闻数据。
- **典型调用时机**：
  - 市场开盘前/收盘后，对重点标的的新闻做一轮刷新。

## 使用建议（数据助手视角）

### 触发规则（如何选择工具）

- **整体市场 / 美股今天怎么样 / 市场整体如何**：
  - 优先调用 `get_universe_data_summary`（不自己生成结论）。
  - 根据返回的主要指数与关注标的的时间戳和状态，整理一段简短的市场概览。
- **单标的行情（如「NVDA 最近行情」「NVDA 最近日线」）**：
  - 调用 `get_latest_bars(symbol, timeframe="1d", limit=20)` 或在需要指定时间范围时调用 `get_market_bars`。
  - 根据返回的 bar 数据，描述最近一段时间的趋势与大致价格区间。
- **单标的新闻（如「NVDA 最近新闻」）**：
  - 调用 `get_news(symbol, limit=3~10)`。
  - 只使用返回的新闻条目生成新闻摘要，不从模型知识中虚构 headline。

### 使用建议（数据助手视角）

- **单标的查询**：
  - 一律先用 `get_latest_bars` / `get_market_bars` / `get_news` 获取真实数据；
  - 如用户关心“数据是否最新”，可以同时查 `get_refresh_state`。
- **小批量刷新 + 巡视**：
  - 使用 `refresh_market_batch` / `refresh_news_batch` 对一组 symbol 预先刷新；
  - 然后用 `get_universe_data_summary` 获取汇总信息，再结合 `get_news` 抽取 headline 做文字总结。
- **注意避免（强约束）**：
  - 不通过这些工具执行任何交易指令；
  - 不从工具以外的模型知识推导或猜测具体价格、指数点位、涨跌幅或当日市场表现；
  - 不在用户回复中提到「技能说明」「工具列表」「加载数据工具」「读取 skill 文件」等内部过程，这些步骤一律在内部静默完成；
  - 不向用户展示 HTTP 细节、错误栈或任何 MCP 内部结构（如 server 名称、transport 类型、工具枚举等）。
- **当工具不可用或返回空数据时**：
  - 向用户返回固定文案：**「当前无法获取市场数据，请稍后再试。」**
  - 不得根据模型自身知识继续生成任何行情数字或市场总结。

