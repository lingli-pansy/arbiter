# MCP Capabilities v0.1

## Design Principle

Expose atomic capabilities.
Do not expose internal runtime workflows directly.

Agents should compose capabilities,
not reconstruct system internals.

---

## Data Capabilities

### get_market_bars
Input:
- symbol
- timeframe
- start
- end

Output:
- list[MarketBar]

### get_news_events
Input:
- symbol
- start
- end

Output:
- list[NewsEvent]

### get_portfolio_snapshot
Input:
- account_id | None

Output:
- PortfolioSnapshot

### get_recent_orders
Input:
- limit

Output:
- list[Order]

### get_recent_fills
Input:
- limit

Output:
- list[TradeFill]

---

## Research Capabilities

### scan_opportunities
Input:
- universe
- as_of

Output:
- ranked candidates

### summarize_symbol_context
Input:
- symbol
- time_window

Output:
- structured symbol context

---

## Portfolio Capabilities

### generate_portfolio
Input:
- candidates
- constraints

Output:
- Proposal

### run_risk_checks
Input:
- proposal
- portfolio_snapshot

Output:
- risk flags + filtered proposal

---

## Execution Capabilities

### submit_order
Input:
- Order

Output:
- order status

### execute_proposal
Input:
- Proposal
- ApprovalDecision

Output:
- ExecutionResult

---

## Backtest Capabilities

### run_backtest
Input:
- strategy_config
- start
- end

Output:
- BacktestResult

### replay_proposal
Input:
- proposal_id

Output:
- replay summary

---

## Agent Usage Rule

Agents should never:
- directly read hidden storage
- rebuild proposal logic in prompts
- bypass capability interfaces