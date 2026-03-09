# Arbiter Roadmap

## Phase 1: Protocol First

Goal:
- define stable protocols
- create repository skeleton
- lock system boundaries

Deliverables:
- architecture.md
- data_protocol.md
- mcp_capabilities.md
- code skeleton

---

## Phase 2: Data Layer

Goal:
- market data ingestion
- news/event ingestion
- portfolio snapshot adapters

Deliverables:
- market provider interfaces
- storage adapters
- first refresh pipeline

---

## Phase 3: Execution + Backtest Kernel

Goal:
- integrate execution engine
- integrate backtest engine
- unify runtime contracts

Deliverables:
- broker adapters
- execution result protocol
- backtest runner

---

## Phase 4: MCP Tools

Goal:
- expose atomic capabilities
- make agents consume tools instead of internals

---

## Phase 5: Agent Layer

Goal:
- build thin research / portfolio / trader agents
- OpenClaw becomes a natural language UI, not a workflow engine