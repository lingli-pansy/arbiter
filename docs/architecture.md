# Arbiter Architecture

## Project Positioning

Arbiter is an autonomous trading decision system.

It is not a chat-first trading bot.
It is a data-first, protocol-first, execution-aware trading system with agents as the user-facing layer.

The system is built in five layers:

1. Data Layer
2. Domain Protocol Layer
3. Trading Runtime Layer
4. MCP Capability Layer
5. Agent Interaction Layer

---

## Layer 1: Data Layer

The data layer is responsible for stable ingestion, storage, retrieval, and refresh of:

- market data
- news/event data
- portfolio/account snapshots
- orders and fills
- backtest inputs

This layer must be stable before higher-level agent workflows.

---

## Layer 2: Domain Protocol Layer

All internal communication should rely on typed protocols, not ad-hoc JSON blobs.

Core protocols include:

- Instrument
- MarketBar
- NewsEvent
- PortfolioSnapshot
- Order
- TradeFill
- Proposal
- Recommendation
- ApprovalDecision
- ExecutionResult

These protocols are the source of truth for runtime, backtest, MCP tools, and agents.

---

## Layer 3: Trading Runtime Layer

The runtime layer is responsible for:

- opportunity scanning
- research ranking
- portfolio generation
- risk checks
- proposal creation
- execution routing
- execution result tracking

The runtime is thick.
It owns the trading logic.

Agents must not reimplement runtime logic.

---

## Layer 4: MCP Capability Layer

The MCP layer exposes atomic capabilities to agents and external systems.

Examples:

- get_market_bars
- get_news_events
- scan_opportunities
- generate_portfolio
- get_portfolio_snapshot
- submit_order
- run_backtest

Agents consume these tools.
They do not directly access storage or hidden runtime internals.

---

## Layer 5: Agent Interaction Layer

Agents are thin.

Their role is:

- understand user intent
- invoke MCP capabilities
- explain system outputs
- request confirmation when needed

Agents do not:

- invent trading logic
- bypass runtime
- manage execution directly
- own portfolio truth

---

## Target Interaction Model

User
-> Agent
-> MCP capability
-> Trading runtime
-> Structured result
-> Agent response

This means the user interacts with a natural language interface,
while the system itself remains protocol-driven and deterministic.

---

## Development Principle

Runtime is thick.
Agent is thin.
OpenClaw integration is thinner.