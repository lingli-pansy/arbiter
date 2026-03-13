#!/usr/bin/env python3
"""
simulate_rebalance: 模拟组合调仓，生成调仓建议。
契约: system/tools/contracts/simulate_rebalance.yaml
输入: portfolio 或 portfolio_id，target_weights。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_impl_dir = Path(__file__).resolve().parent
_system_dir = _impl_dir.parent.parent
STATE_DIR = _system_dir / "state" / "portfolios"


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _sanitize_id(pid: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(pid))


def _load_portfolio(params: dict) -> dict | None:
    portfolio = params.get("portfolio")
    if isinstance(portfolio, dict) and portfolio.get("assets"):
        return portfolio
    pid = params.get("portfolio_id") or (portfolio if isinstance(portfolio, str) else None)
    if not pid or not str(pid).strip():
        return None
    safe_id = _sanitize_id(str(pid).strip())
    path = STATE_DIR / f"{safe_id}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _get_target_weights(assets: list[dict], target_cfg: dict) -> dict[str, float]:
    tw = target_cfg or {}
    t = tw.get("type", "equal")
    if t == "equal":
        n = len(assets)
        return {str(a.get("symbol", "")).strip(): round(1.0 / n, 4) for a in assets}
    if t == "custom":
        w = tw.get("weights", {})
        return {str(k): float(v) for k, v in w.items()}
    return {}


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "rebalance": {}, "errors": [params["_error"]]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    portfolio = _load_portfolio(params)
    if not portfolio:
        out = {"success": False, "rebalance": {}, "errors": ["portfolio or portfolio_id required"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    assets = portfolio.get("assets", [])
    if not assets:
        out = {"success": False, "rebalance": {}, "errors": ["portfolio has no assets"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    target_cfg = params.get("target_weights")
    if not target_cfg:
        out = {"success": False, "rebalance": {}, "errors": ["target_weights is required"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    target_weights = _get_target_weights(assets, target_cfg)
    if not target_weights:
        out = {"success": False, "rebalance": {}, "errors": ["target_weights must be type equal or custom"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    current_weights = {str(a.get("symbol", "")).strip(): float(a.get("weight", 0)) for a in assets}
    capital = float(portfolio.get("initial_capital", 100000))
    market_prices = params.get("market_prices") or {}

    all_symbols = sorted(set(current_weights.keys()) | set(target_weights.keys()))
    differences = {}
    for s in all_symbols:
        cw = current_weights.get(s, 0)
        tw = target_weights.get(s, 0)
        differences[s] = round(tw - cw, 4)

    trades = []
    cash_required = 0.0
    cash_generated = 0.0
    for s in all_symbols:
        delta = differences[s]
        cw = current_weights.get(s, 0)
        tw = target_weights.get(s, 0)
        if delta > 0:
            action = "BUY"
        elif delta < 0:
            action = "SELL"
        else:
            action = "HOLD"
        price = float(market_prices.get(s, 1.0)) if market_prices else 1.0
        est_value = delta * capital
        est_shares = est_value / price if price > 0 else 0
        if action == "BUY":
            cash_required += est_value
        elif action == "SELL":
            cash_generated += abs(est_value)
        trades.append({
            "symbol": s,
            "action": action,
            "current_weight": round(cw, 4),
            "target_weight": round(tw, 4),
            "delta_weight": round(delta, 4),
            "estimated_shares": round(est_shares, 2),
            "estimated_value": round(est_value, 2),
        })

    net_cash = round(cash_generated - cash_required, 2)
    turnover = sum(abs(t["delta_weight"]) for t in trades) / 2

    rebalance = {
        "current_weights": {k: round(v, 4) for k, v in current_weights.items()},
        "target_weights": {k: round(v, 4) for k, v in target_weights.items()},
        "differences": differences,
        "trades": trades,
        "cash_required": round(cash_required, 2),
        "cash_generated": round(cash_generated, 2),
        "net_cash_flow": net_cash,
        "transaction_costs": 0,
        "expected_turnover": round(turnover, 4),
    }

    out = {"success": True, "rebalance": rebalance, "errors": []}
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
