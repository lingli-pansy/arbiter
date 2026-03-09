# Data Protocol v0.1

## Goal

Define stable internal domain protocols for Arbiter.

All layers must rely on these protocols:
- data ingestion
- research
- portfolio
- execution
- backtest
- MCP tools
- agents

---

## 1. Instrument

Represents a tradable asset.

Fields:
- symbol: str
- asset_type: str
- exchange: str
- currency: str
- tick_size: float
- lot_size: float
- price_precision: int
- size_precision: int

---

## 2. MarketBar

Represents OHLCV bar data.

Fields:
- symbol: str
- timestamp: datetime
- timeframe: str
- open: float
- high: float
- low: float
- close: float
- volume: float
- source: str

Notes:
- timeframe examples: 1m, 5m, 1h, 1d
- this is the minimum viable market time-series protocol

---

## 3. NewsEvent

Represents a normalized news/event item.

Fields:
- event_id: str
- timestamp: datetime
- symbols: list[str]
- headline: str
- summary: str
- source: str
- url: str | None
- sentiment: float | None
- entities: list[str]

---

## 4. PortfolioPosition

Represents one position in a portfolio snapshot.

Fields:
- symbol: str
- quantity: float
- market_value: float
- weight: float
- average_cost: float | None
- unrealized_pnl: float | None

---

## 5. PortfolioSnapshot

Represents the latest account or portfolio truth.

Fields:
- timestamp: datetime
- equity: float
- cash: float
- buying_power: float | None
- positions: list[PortfolioPosition]
- source: str

Source examples:
- broker_live
- broker_paper
- backtest
- derived

---

## 6. Order

Represents an order intent submitted to a broker or simulator.

Fields:
- order_id: str
- symbol: str
- side: str
- order_type: str
- quantity: float
- limit_price: float | None
- stop_price: float | None
- timestamp: datetime
- status: str
- source: str

Status examples:
- pending
- submitted
- partially_filled
- filled
- cancelled
- rejected

---

## 7. TradeFill

Represents an execution fill.

Fields:
- fill_id: str
- order_id: str
- symbol: str
- side: str
- price: float
- quantity: float
- timestamp: datetime
- fee: float | None
- venue: str | None

---

## 8. ProposalItem

Represents one candidate portfolio action.

Fields:
- symbol: str
- current_weight: float
- target_weight: float
- delta_weight: float
- action_type: str
- reason: str
- confidence: str

Action examples:
- open
- add
- trim
- close
- hold

---

## 9. Proposal

Represents a portfolio-level proposal.

Fields:
- proposal_id: str
- timestamp: datetime
- items: list[ProposalItem]
- summary: list[str]
- no_trade_reason: str | None

---

## 10. Recommendation

Represents runtime recommendation for approval.

Fields:
- recommendation: str
- confidence: str
- reasons: list[str]
- selected_symbols: list[str]
- blocked_symbols: list[str]
- risk_flags: list[str]

Recommendation examples:
- approve
- reject
- defer

---

## 11. ApprovalDecision

Represents a final approval decision.

Fields:
- decision_id: str
- timestamp: datetime
- proposal_id: str
- decision: str
- reviewer: str
- reason: str | None

Decision examples:
- approve
- reject
- defer

---

## 12. ExecutionResult

Represents execution outcome.

Fields:
- timestamp: datetime
- order_count: int
- executed_order_count: int
- trade_count: int
- execution_status: str
- fills: list[TradeFill]
- notes: str | None

Execution status examples:
- executed
- no_fills
- skipped
- error

---

## Protocol Rules

1. Protocols should be stable and versioned.
2. Agents do not invent new protocol fields.
3. MCP tools must return protocol-compliant objects.
4. Runtime and backtest should use the same protocol contracts.