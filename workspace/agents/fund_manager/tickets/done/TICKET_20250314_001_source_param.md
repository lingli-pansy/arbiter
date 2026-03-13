---
id: TICKET_20250314_001
source_task: TASK_0001D
title: Add data source parameter to get_market_bars_batch
status: done
implemented: 2025-03-14
validated: 2025-03-14
created: 2025-03-14
---

## Blocking Issue
TASK_0001D (IB data path validation) requires fetching market data from Interactive Brokers specifically, but `get_market_bars_batch` does not accept a `source` parameter to specify the data provider.

## Requested Capability
Extend `get_market_bars_batch` to support explicit data source selection.

## Why Existing Tools Are Insufficient
Current `get_market_bars_batch` only has:
- symbols, start_date, end_date, timeframe

Missing:
- source: enum["yahoo", "ib", "polygon", "alpaca"]
- No way to validate IB-specific data path
- No way to compare latency/quality across sources

## Input Contract
```yaml
source:
  type: string
  enum: ["yahoo", "ib", "polygon", "alpaca"]
  default: "yahoo"
  description: Data provider source
```

## Output Contract
Same as current, but include metadata:
```yaml
metadata:
  source: string
  latency_ms: integer
  data_quality_score: float
```

## Acceptance Criteria
- [ ] Can specify source="ib" and get IB data
- [ ] Can specify source="yahoo" and get Yahoo data
- [ ] Response includes latency_ms
- [ ] Backward compatible (default to yahoo if source not specified)

## Test Case
```python
# Test IB source
result = get_market_bars_batch(
    symbols=["SPY", "QQQ"],
    start_date="2025-03-01",
    end_date="2025-03-14",
    timeframe="1d",
    source="ib"
)
assert result.metadata.source == "ib"
assert result.metadata.latency_ms < 1000

# Test default (yahoo)
result = get_market_bars_batch(
    symbols=["SPY"],
    start_date="2025-03-01",
    end_date="2025-03-14",
    timeframe="1d"
)
assert result.metadata.source == "yahoo"
```
