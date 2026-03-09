from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ProposalItem:
    symbol: str
    current_weight: float
    target_weight: float
    delta_weight: float
    action_type: str
    reason: str
    confidence: str


@dataclass(slots=True)
class Proposal:
    proposal_id: str
    timestamp: datetime
    items: list[ProposalItem]
    summary: list[str]
    no_trade_reason: str | None = None


@dataclass(slots=True)
class Recommendation:
    recommendation: str
    confidence: str
    reasons: list[str]
    selected_symbols: list[str]
    blocked_symbols: list[str]
    risk_flags: list[str]


@dataclass(slots=True)
class ApprovalDecision:
    decision_id: str
    timestamp: datetime
    proposal_id: str
    decision: str
    reviewer: str
    reason: str | None = None


