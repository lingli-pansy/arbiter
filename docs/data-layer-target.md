# Data Layer Target Architecture

## 目标

为 Arbiter 建立一个长期可用、可积累、可刷新、可回测、可对外暴露能力的数据底座。

本层不是为某个 agent 服务。
本层是整个系统的事实底座。

---

## 一、设计原则

1. 不再使用 mock 数据推进主线。
2. 外部源只负责输入，系统内部必须有自己的 canonical store。
3. 所有上层（research / backtest / execution / MCP / agents）只消费统一协议对象。
4. 数据更新必须支持：
   - bootstrap
   - incremental refresh
   - reconcile / repair
5. 数据层先对外暴露只读能力，再逐步暴露写能力。
6. 尽量少自己写基础设施，优先复用成熟库。

---

## 二、最终分层

### 1. Source Adapters
负责对接外部数据源与券商网关：

- market data provider
- news/event provider
- broker account provider
- broker execution provider

这层不直接写业务表。

### 2. Raw Landing
保存原始响应或标准化前记录，用于追溯和修复。

推荐：
- PostgreSQL raw tables（轻量）
- Parquet archive（大对象或批量原始数据）

### 3. Canonical Store
系统统一事实库。

推荐数据库：
- PostgreSQL

主要数据域：
- instruments
- market_bars
- news_events
- portfolio_snapshots
- orders
- trade_fills
- execution_results
- refresh_state
- research_cache

### 4. Service Layer
统一查询与刷新入口：

- MarketDataService
- NewsService
- PortfolioDataService
- ExecutionDataService

上层只调 service，不直接读写数据库。

### 5. Capability Exposure Layer
通过 MCP 暴露原子能力：

- get_market_bars
- get_refresh_state
- get_news_events
- get_portfolio_snapshot
- get_recent_orders
- get_recent_fills

---

## 三、技术选型

### 核心数据库
- PostgreSQL

原因：
- 事务能力强
- schema 演进成熟
- 分区能力成熟
- COPY / INSERT / MERGE 等能力完善
- 适合长期 canonical store

### Python 数据访问
- SQLAlchemy 2
- Alembic

### 协议与校验
- Pydantic v2

### 批量处理与研究交换
- Polars
- Parquet

### MCP
- Official Python MCP SDK

### 执行/回测内核
- Nautilus Trader

---

## 四、核心协议

### Instrument
- symbol
- asset_type
- exchange
- currency
- tick_size
- lot_size
- price_precision
- size_precision

### MarketBar
- symbol
- timestamp
- timeframe
- open
- high
- low
- close
- volume
- source

### NewsEvent
- event_id
- timestamp
- symbols
- headline
- summary
- source
- url
- sentiment
- entities

### PortfolioSnapshot
- timestamp
- equity
- cash
- buying_power
- positions
- source

### Order
- order_id
- symbol
- side
- order_type
- quantity
- status
- timestamp
- source

### TradeFill
- fill_id
- order_id
- symbol
- side
- price
- quantity
- timestamp
- fee
- venue

### ExecutionResult
- timestamp
- order_count
- executed_order_count
- trade_count
- execution_status
- fills
- notes

---

## 五、刷新模型

### 1. Bootstrap
首次初始化历史数据。

### 2. Incremental Refresh
基于 checkpoint 增量拉取。

### 3. Reconcile
定期补数、修正、对账。

---

## 六、Refresh State 终局字段

每个 dataset key 至少记录：

- dataset_type
- dataset_key
- source
- last_success_at
- last_event_timestamp
- last_cursor
- refresh_status
- error_message
- row_count

---

## 七、时间语义

每个对象应明确以下时间概念：

- event_time
- ingested_at
- effective_time

不能只依赖一个 timestamp 字段。

---

## 八、对外能力边界

第一阶段只暴露只读能力：

- get_market_bars
- get_latest_bars
- get_refresh_state
- get_news_events
- get_portfolio_snapshot

第二阶段再暴露研究与执行能力。

---

## 九、明确不做的事

- 不让 agent 直接读数据库
- 不让 provider 直接写 canonical 业务表
- 不把券商网关当唯一历史数据源
- 不在 prompt 里拼工作流替代接口

## 十、数据源策略（明确选型）

### Market Data 主源

第一阶段只选一个主源，避免双源复杂度。

推荐优先级：

1. Alpaca Market Data API
2. Polygon

选择原则：
- 用于 research/backtest 的历史与实时市场数据
- 不依赖券商网关作为唯一研究数据来源
- 统一由 provider adapter 映射为 canonical protocol

说明：
- Alpaca 提供历史与实时市场数据能力，后续与 MCP/agent 结合更自然
- Polygon 提供更强的市场数据覆盖，也适合作为 research 主源
- 二者二选一，不要第一阶段双接

### News/Event 主源

第一阶段推荐：
- Finnhub Company News API

目标：
- 获取 symbol -> news events
- 增量写入
- 去重
- 后续供 research/scanner 使用

### Broker / Account Truth Source

第一阶段允许：
- IB Gateway
- Futu OpenD

但仅用于：
- portfolio snapshot
- orders
- fills
- execution truth

不作为：
- 历史 research canonical source

理由：
- 券商网关适合账户真相
- 不适合承担整个 research/backtest 历史数据底座