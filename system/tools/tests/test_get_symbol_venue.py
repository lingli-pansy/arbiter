"""Minimal tests for get_symbol_venue (TICKET_0004)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"
SCRIPT = IMPL_DIR / "get_symbol_venue.py"


def _run(args: dict) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(args),
        capture_output=True,
        text=True,
        cwd=str(IMPL_DIR),
    )
    return json.loads(result.stdout if result.returncode == 0 else "{}")


def test_contract_output_structure() -> None:
    """Output has success, data, errors, meta per contract."""
    out = _run({"symbols": ["AAPL", "MSFT", "JPM"]})
    assert "success" in out
    assert "data" in out
    assert "errors" in out
    assert "meta" in out
    assert isinstance(out["data"], dict)
    assert out["data"]["AAPL"] == "NASDAQ"
    assert out["data"]["MSFT"] == "NASDAQ"
    assert out["data"]["JPM"] == "NYSE"
    assert out["meta"]["requested_symbols"] == 3
    assert out["meta"]["resolved_symbols"] == 3


def test_validation_empty_symbols() -> None:
    """Empty symbols returns validation error."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps({"symbols": []}),
        capture_output=True,
        text=True,
        cwd=str(IMPL_DIR),
    )
    out = json.loads(result.stdout)
    assert out["success"] is False
    assert "symbols" in out.get("errors", [""])[0].lower() or "error" in str(out).lower()
