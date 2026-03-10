from __future__ import annotations

"""
Canonical market data store for Arbiter.

This package defines:
- Canonical instrument and bar schemas
- Segment / ingest ledger models
- Helper functions to initialize the schema

All historical imports and realtime ingests should ultimately write into this
canonical store, using the write semantics described in
docs/arbiter_market_data_phase_guide_v1.md.
"""

from .schema import CanonicalBar, CanonicalInstrument, IngestSegment  # noqa: F401
from .schema import init_canonical_schema  # noqa: F401

