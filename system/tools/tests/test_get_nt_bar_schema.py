#!/usr/bin/env python3
"""Minimal test for get_nt_bar_schema tool. TICKET_0002."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"
SCRIPT = IMPL_DIR / "get_nt_bar_schema.py"


def _run(inp: dict) -> dict:
    raw = json.dumps(inp)
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=raw.encode(),
        capture_output=True,
        cwd=IMPL_DIR,
    )
    out = r.stdout.decode().strip()
    err = r.stderr.decode().strip()
    if err:
        sys.stderr.write(err + "\n")
    return json.loads(out) if out else {}


def test_contract_output_structure() -> None:
    """Output matches contract: success, schema.fields, schema.example, version or meta."""
    result = _run({"format": "dict", "include_examples": True})
    assert "success" in result
    assert result["success"] is True
    assert "schema" in result
    schema = result["schema"]
    assert "fields" in schema
    fields = schema["fields"]
    assert isinstance(fields, list)
    field_names = {f["name"] for f in fields}
    required_ohlcv = {"open", "high", "low", "close", "volume"}
    assert required_ohlcv.issubset(field_names), f"Missing OHLCV: {field_names}"
    ts_fields = {"ts_event", "ts_init"}
    assert ts_fields.issubset(field_names) or "ts_event" in field_names, f"Missing ts: {field_names}"
    for f in fields:
        assert "name" in f and "type" in f
    if "example" in schema:
        ex = schema["example"]
        assert "open" in ex and "high" in ex and "low" in ex and "close" in ex and "volume" in ex


def test_format_dict_default() -> None:
    """Default format dict returns expected structure."""
    result = _run({})
    assert result["success"] is True
    assert "schema" in result
    assert "fields" in result["schema"]


def test_include_examples_false() -> None:
    """include_examples=false can omit or have empty example."""
    result = _run({"format": "dict", "include_examples": False})
    assert result["success"] is True
    # Contract allows example to be present or absent when include_examples=false
    assert "schema" in result
    assert "fields" in result["schema"]
