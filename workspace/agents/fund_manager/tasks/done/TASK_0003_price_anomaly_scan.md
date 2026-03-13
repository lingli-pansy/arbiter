---
id: TASK_0003
title: Price anomaly scan
type: research
priority: P1
status: pending
created: 2025-03-12
---

## Objective
Scan for price anomalies across watchlist in last 20 days, identify +5% or -5% daily moves.

## Dependencies
- get_watchlist
- get_market_bars_batch

## Inputs Required
- watchlist_id: "default"
- lookback_days: 20
- threshold_pct: 5.0

## Expected Output
- List of anomalies with symbol, date, move %, volume context
- Summary statistics

## Acceptance Criteria
- [ ] Detect all +/-5% daily moves
- [ ] Include volume vs average comparison
- [ ] Rank by magnitude
