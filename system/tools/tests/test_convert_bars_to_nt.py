"""Minimal tests for convert_bars_to_nt (TICKET_0003)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"
SCRIPT = IMPL_DIR / "convert_bars_to_nt.py"


def _run(args: dict) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(args),
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    return json.loads(result.stdout if result.returncode == 0 else "{}")


def test_contract_output_structure() -> None:
    """Output has success, data, errors, meta; NT bars have required fields."""
    market_data = {
        "data": {
            "AAPL": [
                {
                    "timestamp": "2026-02-20T00:00:00Z",
                    "open": 185.0,
                    "high": 187.5,
                    "low": 184.2,
                    "close": 186.8,
                    "volume": 52000000,
                },
            ],
        },
        "meta": {"timeframe": "1d"},
    }
    out = _run({"market_data": market_data})
    assert out["success"] is True
    assert "data" in out
    assert "errors" in out
    assert "meta" in out
    assert "AAPL" in out["data"]
    bars = out["data"]["AAPL"]
    assert len(bars) == 1
    nt_bar = bars[0]
    for key in ("bar_type", "open", "high", "low", "close", "volume", "ts_event", "ts_init", "is_revision"):
        assert key in nt_bar, f"missing {key}"
    assert nt_bar["bar_type"] == "AAPL.NASDAQ-1-DAY-LAST"
    assert isinstance(nt_bar["ts_event"], int)
    assert nt_bar["ts_event"] > 0
    assert nt_bar["open"] == "185.0"


def test_validation_missing_market_data() -> None:
    """Missing market_data returns validation error."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps({}),
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    out = json.loads(result.stdout)
    assert out["success"] is False
    assert "market_data" in str(out.get("errors", [""])).lower()
