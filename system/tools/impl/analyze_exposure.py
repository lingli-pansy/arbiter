#!/usr/bin/env python3
"""
analyze_exposure: 分析组合风险暴露（行业、集中度等）。
契约: system/tools/contracts/analyze_exposure.yaml
输入: portfolio 或 portfolio_id，analysis_type 可选。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_impl_dir = Path(__file__).resolve().parent
_system_dir = _impl_dir.parent.parent
STATE_DIR = _system_dir / "state" / "portfolios"

try:
    from adapters.sector_mapper import get_sector
except ImportError:
    from .adapters.sector_mapper import get_sector

HHI_DIVERSIFIED = 0.15
HHI_MODERATE = 0.25


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _load_portfolio(params: dict) -> dict | None:
    """Resolve portfolio from params: portfolio object or portfolio_id."""
    portfolio = params.get("portfolio")
    if isinstance(portfolio, dict) and portfolio.get("assets"):
        return portfolio
    pid = params.get("portfolio_id") or (portfolio if isinstance(portfolio, str) else None)
    if not pid or not str(pid).strip():
        return None
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(pid).strip())
    path = STATE_DIR / f"{safe_id}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _concentration_risk(hhi: float) -> str:
    if hhi < HHI_DIVERSIFIED:
        return "low"
    if hhi < HHI_MODERATE:
        return "medium"
    return "high"


def _analyze_sector(assets: list[dict]) -> dict:
    sector_symbols: dict[str, list[str]] = {}
    for a in assets:
        sym = str(a.get("symbol", "")).strip()
        sector = get_sector(sym)
        if sector not in sector_symbols:
            sector_symbols[sector] = []
        sector_symbols[sector].append(sym)
    breakdown = []
    for sector, syms in sector_symbols.items():
        w = sum(float(a["weight"]) for a in assets if str(a.get("symbol", "")).strip() in syms)
        breakdown.append({"sector": sector, "weight": round(w, 4), "symbols": syms})
    hhi_sector = sum(b["weight"] ** 2 for b in breakdown)
    return {
        "breakdown": breakdown,
        "concentration_risk": _concentration_risk(hhi_sector),
    }


def _analyze_concentration(assets: list[dict]) -> dict:
    weights = sorted([float(a.get("weight", 0)) for a in assets], reverse=True)
    if not weights:
        return {"max_position": 0, "top_3_weight": 0, "hhi": 0, "effective_positions": 0}
    hhi = sum(w ** 2 for w in weights)
    top3 = sum(weights[:3])
    eff = 1 / hhi if hhi > 0 else 0
    return {
        "max_position": round(weights[0], 4),
        "top_3_weight": round(top3, 4),
        "hhi": round(hhi, 4),
        "effective_positions": round(eff, 2),
    }


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "exposure": {}, "errors": [params["_error"]]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    portfolio = _load_portfolio(params)
    if not portfolio:
        out = {"success": False, "exposure": {}, "errors": ["portfolio or portfolio_id required, and must have assets"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    assets = portfolio.get("assets", [])
    if not assets:
        out = {"success": False, "exposure": {}, "errors": ["portfolio has no assets"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    analysis_types = params.get("analysis_type", ["sector", "concentration"])
    if isinstance(analysis_types, str):
        analysis_types = [analysis_types]
    if "all" in analysis_types:
        analysis_types = ["sector", "concentration"]

    exposure = {}
    if "sector" in analysis_types:
        exposure["sector"] = _analyze_sector(assets)
    if "concentration" in analysis_types:
        exposure["concentration"] = _analyze_concentration(assets)

    out = {"success": True, "exposure": exposure, "errors": []}
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
