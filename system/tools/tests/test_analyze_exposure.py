#!/usr/bin/env python3
"""analyze_exposure 最小测试"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"


def _run(params: dict) -> tuple[int, dict]:
    raw = json.dumps(params)
    r = subprocess.run(
        [sys.executable, str(IMPL_DIR / "analyze_exposure.py")],
        input=raw.encode(),
        capture_output=True,
        timeout=10,
        cwd=str(IMPL_DIR),
    )
    out = {}
    if r.stdout:
        try:
            out = json.loads(r.stdout.decode())
        except json.JSONDecodeError:
            out = {"_raw": r.stdout.decode()[:500]}
    return r.returncode, out


def test_analyze_exposure_validation() -> None:
    """缺少 portfolio 应返回错误"""
    code, out = _run({})
    assert code != 0 or out.get("success") is False


def test_analyze_exposure_portfolio_object() -> None:
    """传入 portfolio 对象应返回 sector 和 concentration"""
    params = {
        "portfolio": {
            "portfolio_id": "MODEL_TECH_001",
            "assets": [
                {"symbol": "NVDA", "weight": 0.4},
                {"symbol": "MSFT", "weight": 0.35},
                {"symbol": "AAPL", "weight": 0.25},
            ],
        },
        "analysis_type": ["sector", "concentration"],
    }
    code, out = _run(params)
    assert code == 0, f"Failed: {out}"
    assert out.get("success") is True
    assert "exposure" in out
    sector = out["exposure"].get("sector", {})
    assert "breakdown" in sector
    assert len(sector["breakdown"]) >= 1
    assert "concentration_risk" in sector
    conc = out["exposure"].get("concentration", {})
    assert "max_position" in conc
    assert conc["max_position"] == 0.4
    assert conc["top_3_weight"] == 1.0
    assert "hhi" in conc
    assert conc["hhi"] == round(0.4**2 + 0.35**2 + 0.25**2, 4)
