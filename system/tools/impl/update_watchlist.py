#!/usr/bin/env python3
"""
update_watchlist: 更新观察列表（添加/移除 symbol，创建/删除）。
契约: system/tools/contracts/update_watchlist.yaml
输入: JSON 从 stdin 或第一个命令行参数读取。
输出: JSON 写入 stdout。
"""
from __future__ import annotations

import json
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


def _load_watchlist(watchlist_id: str) -> dict | None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = _sanitize_id(watchlist_id or "default")
    path = STATE_DIR / f"{safe_id}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _save_watchlist(wl: dict) -> bool:
    wid = wl.get("watchlist_id", "default")
    safe_id = _sanitize_id(wid)
    path = STATE_DIR / f"{safe_id}.json"
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(wl, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "watchlist": None, "errors": [params["_error"]]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    watchlist_id = str(params.get("watchlist_id", "default")).strip() or "default"
    action = str(params.get("action", "")).strip().lower()
    symbols = params.get("symbols") or []
    name = params.get("name") or ""

    if action not in ("add", "remove", "create", "delete"):
        out = {"success": False, "watchlist": None, "errors": ["action must be add, remove, create, or delete"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if action == "create":
        safe_id = _sanitize_id(watchlist_id)
        if (STATE_DIR / f"{safe_id}.json").exists():
            out = {"success": False, "watchlist": None, "errors": [f"Watchlist already exists: {watchlist_id}"]}
            print(json.dumps(out, ensure_ascii=False, default=str))
            sys.exit(1)
        syms = [s for s in symbols if isinstance(s, str) and s.strip()] if symbols else DEFAULT_SYMBOLS
        wl = {
            "watchlist_id": watchlist_id,
            "name": name or watchlist_id,
            "created_at": now,
            "updated_at": now,
            "symbols": [{"symbol": s.strip(), "added_at": now, "notes": "", "alerts": []} for s in syms],
        }
        if not _save_watchlist(wl):
            out = {"success": False, "watchlist": None, "errors": ["Failed to save watchlist"]}
            print(json.dumps(out, ensure_ascii=False, default=str))
            sys.exit(1)
        out = {"success": True, "watchlist": wl, "errors": []}
        print(json.dumps(out, ensure_ascii=False, default=str))
        return

    if action == "delete":
        safe_id = _sanitize_id(watchlist_id)
        path = STATE_DIR / f"{safe_id}.json"
        if not path.exists():
            out = {"success": False, "watchlist": None, "errors": [f"Watchlist not found: {watchlist_id}"]}
            print(json.dumps(out, ensure_ascii=False, default=str))
            sys.exit(1)
        try:
            path.unlink()
        except OSError:
            out = {"success": False, "watchlist": None, "errors": ["Failed to delete watchlist"]}
            print(json.dumps(out, ensure_ascii=False, default=str))
            sys.exit(1)
        out = {"success": True, "watchlist": {"watchlist_id": watchlist_id, "deleted": True}, "errors": []}
        print(json.dumps(out, ensure_ascii=False, default=str))
        return

    wl = _load_watchlist(watchlist_id)
    if not wl:
        out = {"success": False, "watchlist": None, "errors": [f"Watchlist not found: {watchlist_id}"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    sym_list = [str(s).strip() for s in symbols if s] if isinstance(symbols, list) else []
    entries = wl.get("symbols", [])

    if action == "add":
        existing = {e.get("symbol", "").upper() for e in entries}
        for s in sym_list:
            if s and s.upper() not in existing:
                entries.append({"symbol": s, "added_at": now, "notes": "", "alerts": []})
                existing.add(s.upper())
    elif action == "remove":
        to_remove = {s.upper() for s in sym_list}
        entries = [e for e in entries if (e.get("symbol") or "").upper() not in to_remove]

    wl["symbols"] = entries
    wl["updated_at"] = now
    if name:
        wl["name"] = name

    if not _save_watchlist(wl):
        out = {"success": False, "watchlist": None, "errors": ["Failed to save watchlist"]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    out = {"success": True, "watchlist": wl, "errors": []}
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
