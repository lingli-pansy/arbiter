#!/usr/bin/env python3
"""
get_watchlist: 获取观察列表及其可选行情数据。
契约: system/tools/contracts/get_watchlist.yaml
输入: JSON 从 stdin 或第一个命令行参数读取。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_impl_dir = Path(__file__).resolve().parent
_system_dir = _impl_dir.parent.parent
STATE_DIR = _system_dir / "state" / "watchlists"

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _sanitize_id(wid: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(wid))


def _ensure_default() -> None:
    """确保 default watchlist 存在"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "default.json"
    if not path.exists():
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            "watchlist_id": "default",
            "name": "Default Watchlist",
            "created_at": now,
            "updated_at": now,
            "symbols": [{"symbol": s, "added_at": now, "notes": "", "alerts": []} for s in DEFAULT_SYMBOLS],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def _load_watchlist(watchlist_id: str) -> dict | None:
    _ensure_default()
    safe_id = _sanitize_id(watchlist_id or "default")
    path = STATE_DIR / f"{safe_id}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _fetch_quotes(symbols: list[str], lookback_days: int) -> dict:
    """调用 get_market_bars_batch 获取行情"""
    if not symbols:
        return {}
    req = {"symbols": symbols[:10], "lookback_days": lookback_days, "timeframe": "1d", "provider": "yahoo"}
    try:
        r = subprocess.run(
            [sys.executable, str(_impl_dir / "get_market_bars_batch.py")],
            input=json.dumps(req).encode(),
            capture_output=True,
            timeout=15,
            cwd=str(_impl_dir),
        )
        if r.returncode != 0 or not r.stdout:
            return {}
        out = json.loads(r.stdout.decode())
        return out.get("data", {}) if out.get("success") else {}
    except Exception:
        return {}


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "watchlist": None, "errors": [params["_error"]]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    watchlist_id = str(params.get("watchlist_id", "default")).strip() or "default"
    include_quotes = params.get("include_quotes", True)
    lookback_days = int(params.get("lookback_days", 5))

    wl = _load_watchlist(watchlist_id)
    if not wl:
        out = {"success": False, "watchlist": None, "errors": [f"Watchlist not found: {watchlist_id}"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    symbols = [s.get("symbol", "") for s in wl.get("symbols", []) if s.get("symbol")]
    quotes = {}
    if include_quotes and symbols:
        raw_data = _fetch_quotes(symbols, lookback_days)
        for sym, rows in (raw_data or {}).items():
            if rows and isinstance(rows, list):
                last = rows[-1] if rows else {}
                quotes[sym] = {"close": last.get("close"), "open": last.get("open"), "volume": last.get("volume")}

    wl["quotes"] = quotes
    out = {"success": True, "watchlist": wl, "errors": []}
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
