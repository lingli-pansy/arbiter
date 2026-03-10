
# Arbiter Market Data & NT Integration Phase Guide (v1)

## Objective of This Phase

Build a stable market data foundation that:

- Reuses NautilusTrader (NT) capabilities wherever possible
- Uses IBKR only for realtime / incremental data ingestion
- Imports long historical data from external providers
- Stores everything in a unified **canonical market store**
- Exposes stable **MCP capabilities**
- Enables **NT research/backtest/simulation**
- Demonstrates **50 US equities realtime ingestion stability**

This phase does NOT implement live trading execution yet.

---

# Architecture Principles

## 1. Reuse NautilusTrader wherever possible

Reuse NT for:

- IBKR connection/session
- Instrument / contract resolution
- realtime market data streaming
- compatibility with future paper/live trading

Arbiter remains responsible for:

- canonical data schema
- storage and merge rules
- ingest ledger / refresh state
- repair / finalize semantics
- MCP query and control APIs
- agent-facing abstractions

---

# System Layers

Historical Importers
→ batch import long historical bars

Realtime Adapter (IBKR via NautilusTrader)
→ incremental market data ingest

Canonical Market Store
→ single internal source of truth

NT Bridge
→ converts canonical data to NT compatible datasets

MCP Layer
→ query + control interface

Agent Layer
→ OpenClaw agents consuming MCP

---

# Data Model

Canonical Bar Schema (minimum)

instrument_id
symbol
venue
timeframe
timestamp
open
high
low
close
volume
currency
source
ingest_method
ingested_at
status
version
priority
quality_flag

Optional fields

provider_symbol
ib_contract_id
session_scope
what_to_show
corporate_action_mode
raw_payload_ref
batch_id

Status values

provisional
finalized

---

# Data Write Semantics

Operations

import_market_data(segment, source, mode)

ingest_market_data(segment, source, mode)

repair_market_data(segment, source, mode)

finalize_market_data(segment)

Modes

append
upsert
replace_range
repair_range

Conflict resolution

finalized > provisional
repair > ordinary ingest
higher priority source > lower priority source
newer version > older version

---

# Milestones

## M1 – Data Model & Storage

Define:

canonical schema
segment model
write semantics
status lifecycle
conflict resolution rules

Deliverable:

schema implemented and validated

---

## M2 – Data Pipeline

Implement:

historical bulk import
IBKR realtime ingest via NT adapter
canonical storage write
query APIs for bars and coverage

Deliverable:

AAPL / MSFT / SPY / QQQ ingest working

---

## M3 – MCP Exposure

Read APIs

get_latest_bars
get_market_bars
get_data_coverage
get_refresh_state
get_universe_data_summary
get_ingest_job_status

Control APIs

ingest_market_data
repair_market_data
finalize_market_data

---

## M4 – NT Research Bridge

Implement

prepare_nt_dataset
run_backtest
get_backtest_status
get_backtest_result

Use canonical store as NT dataset source.

---

# Required Concrete Outcome

The following **must be demonstrated** for this phase to be considered successful.

1. Historical market data imported into canonical store

2. Realtime ingest from IBKR via NautilusTrader adapter

3. **50 US equities realtime bars continuously entering the canonical store**

4. Realtime ingestion remains stable for at least several hours without failure

5. MCP queries can retrieve latest bars and coverage

6. NT dataset can be prepared from canonical store

---

# Target Universe for Realtime Validation

The following universe should be used for the realtime ingestion test.

Example set (can be adjusted):

AAPL
MSFT
AMZN
GOOGL
META
NVDA
TSLA
BRK.B
AVGO
JPM
JNJ
XOM
V
PG
MA
HD
UNH
MRK
PEP
ABBV
COST
KO
BAC
PFE
CRM
ADBE
CSCO
CMCSA
ACN
ABT
TMO
NFLX
ORCL
DHR
INTC
QCOM
WMT
TXN
AMD
LIN
PM
HON
UPS
BMY
AMAT
RTX
LOW
NEE
IBM
SPY

Total ≈ 50 symbols

---

# Validation Checklist

The phase is considered successful when:

- canonical schema implemented
- historical import works
- IBKR realtime ingest works
- **50 symbols ingest stable**
- MCP queries return correct results
- NT dataset preparation works

---

# External Dependencies (must be confirmed before development)

NautilusTrader installation

NT IB integration enabled

IB Gateway or TWS available

IBKR API enabled

Market data subscriptions active

Local storage path for canonical store

Parquet / dataset storage allowed

Network access to IBKR

Environment variables for API access

---

# Future Phases (not in scope)

Strategy automation

Paper trading orchestration

Live execution routing

Risk management layer

Portfolio optimization agents

---
