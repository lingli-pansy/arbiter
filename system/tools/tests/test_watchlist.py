#!/usr/bin/env python3
"""get_watchlist / update_watchlist 最小测试 (TICKET_0012)"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"
GET_SCRIPT = (IMPL_DIR / "get_watchlist.py").resolve()
UPD_SCRIPT = (IMPL_DIR / "update_watchlist.py").resolve()


def _run(script: Path, params: dict) -> tuple[int, dict]:
    raw = json.dumps(params)
    r = subprocess.run(
        [sys.executable, str(script)],
        input=raw.encode(),
        capture_output=True,
        timeout=15,
        cwd=str(IMPL_DIR.resolve()),
    )
    out = json.loads(r.stdout.decode()) if r.stdout else {}
    return r.returncode, out


def test_get_watchlist_default() -> None:
    """get_watchlist 默认返回 default 列表（无行情避免网络）"""
    code, out = _run(GET_SCRIPT, {"watchlist_id": "default", "include_quotes": False})
    assert code == 0
    assert out.get("success") is True
    wl = out.get("watchlist")
    assert wl is not None
    assert "watchlist_id" in wl
    assert "symbols" in wl
    assert "quotes" in wl


def test_update_watchlist_add_remove() -> None:
    """update_watchlist add/remove 可增删 symbol"""
    wid = "test_watchlist_001"
    code, out = _run(UPD_SCRIPT, {"watchlist_id": wid, "action": "create", "symbols": ["AAPL", "MSFT"]})
    assert code == 0
    assert out.get("success") is True
    wl = out.get("watchlist")
    assert wl is not None
    syms = [s.get("symbol") for s in wl.get("symbols", [])]
    assert "AAPL" in syms
    assert "MSFT" in syms

    code2, out2 = _run(UPD_SCRIPT, {"watchlist_id": wid, "action": "add", "symbols": ["NVDA"]})
    assert code2 == 0
    syms2 = [s.get("symbol") for s in out2.get("watchlist", {}).get("symbols", [])]
    assert "NVDA" in syms2

    code3, out3 = _run(UPD_SCRIPT, {"watchlist_id": wid, "action": "remove", "symbols": ["MSFT"]})
    assert code3 == 0
    syms3 = [s.get("symbol") for s in out3.get("watchlist", {}).get("symbols", [])]
    assert "MSFT" not in syms3
    assert "AAPL" in syms3

    _run(UPD_SCRIPT, {"watchlist_id": wid, "action": "delete"})


def test_update_watchlist_validation() -> None:
    """update_watchlist 无效 action 返回错误"""
    code, out = _run(UPD_SCRIPT, {"action": "invalid"})
    assert code != 0 or out.get("success") is False
    assert "action" in str(out.get("errors", [])).lower()


if __name__ == "__main__":
    test_get_watchlist_default()
    test_update_watchlist_add_remove()
    test_update_watchlist_validation()
    print("All tests passed.")
