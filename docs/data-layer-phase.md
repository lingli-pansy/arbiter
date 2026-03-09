# Data Layer Phase Plan

## Phase 0：冻结设计（当前阶段）

目标：
- 冻结终局架构
- 冻结核心协议
- 冻结技术选型

交付：
- data-layer-target.md
- data-protocol v0.2
- capability list v0.1

完成标准：
- 后续开发不再反复摇摆 SQLite / DuckDB / Postgres / mock
- 不再讨论是否用 mock 推进主线

---

## Phase 1：数据库与协议落地

目标：
- 落 PostgreSQL
- 落 Alembic
- 落 SQLAlchemy models
- 落 Pydantic domain models

范围：
- instruments
- market_bars
- refresh_state

交付：
- docker-compose 或本地 PostgreSQL 启动方式
- 初始 migration
- model / schema / repository 基础代码

完成标准：
- 能初始化数据库
- 能写入并查询 market_bars
- 能记录 refresh_state

---

## Phase 2：Market Data 正式化

目标：
- 用真实 provider 替换 stub
- 打通 bootstrap / incremental refresh
- 支持 checkpoint
- 支持 refresh state 查询

范围：
- market provider interface
- market refresh pipeline
- market query service

交付：
- refresh_market_data
- get_market_bars
- get_refresh_state
- CLI / script for refresh

完成标准：
- 不再依赖 mock bar
- 有一段真实历史数据
- 可以持续增量更新

---

## Phase 3：News / Event Data

目标：
- 建立 news/event 协议和存储
- 支持增量抓取、去重、按 symbol 查询

范围：
- news_events
- event refresh state
- NewsService

交付：
- get_news_events
- refresh_news_events

完成标准：
- 能按 symbol + time window 查询新闻
- 有稳定的去重和增量策略

---

## Phase 4：Portfolio / Execution Truth

目标：
- 接 broker/account truth
- 记录 portfolio snapshots / orders / fills

范围：
- portfolio_snapshots
- orders
- trade_fills
- execution_results

交付：
- get_portfolio_snapshot
- get_recent_orders
- get_recent_fills

完成标准：
- 账户真相不再是临时查询结果
- 执行历史可落盘可查询

---

## Phase 5：MCP 只读能力暴露

目标：
- 把数据层暴露成可被 agent / OpenClaw 使用的原子能力

范围：
- get_market_bars
- get_refresh_state
- get_news_events
- get_portfolio_snapshot

交付：
- MCP server v0
- Python MCP SDK 集成

完成标准：
- OpenClaw 可开始最基础的数据能力实验
- 但仍不承载交易工作流

---

## Phase 6：Research 输入准备完成

目标：
- 为 scanner / candidate engine 提供稳定输入

范围：
- market + news + snapshot query ready

交付：
- Research engine 的输入服务层

完成标准：
- 可以开始做第一版 opportunity scan
- 不需要再回头补数据底座

## 实现方式（必须遵守）

### 不再使用 mock 数据推进主线

从本阶段开始：
- provider 必须接真实数据源
- 写入真实 PostgreSQL
- 所有 refresh 走真实更新流程

### 第一阶段数据库与框架

必须落地：
- PostgreSQL
- SQLAlchemy 2
- Alembic
- Pydantic v2

### 第一阶段优先数据域

优先顺序：
1. instruments
2. market_bars
3. refresh_state
4. news_events
5. portfolio_snapshots

### 实现原则

- provider 只负责取数，不负责业务表写入
- service 统一编排 refresh/query
- repository 负责数据库读写
- MCP 之后只调 service，不直连数据库