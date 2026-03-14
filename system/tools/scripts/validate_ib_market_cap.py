#!/usr/bin/env python3
"""
IB Paper 市值验证脚本。TICKET_20250314_003_FOLLOWUP_001
验证 IB 连接与 Tick 165 / Fundamental 能否获取至少 1 只股票市值。
用法: python validate_ib_market_cap.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
IMPL_DIR = SCRIPTS_DIR.parent / "impl"
SCRIPT = IMPL_DIR / "get_market_cap_ranking.py"
VENV = Path(__file__).resolve().parents[3] / ".venv" / "bin" / "python3"


def main() -> None:
    if not SCRIPT.exists():
        print(json.dumps({"ok": False, "reason": "script_not_found", "message": str(SCRIPT)}, indent=2))
        sys.exit(1)

    python = str(VENV) if VENV.exists() else sys.executable
    inp = {"date": "2024-03-31", "top_n": 5, "source": "ib"}

    try:
        proc = subprocess.run(
            [python, str(SCRIPT)],
            input=json.dumps(inp),
            capture_output=True,
            text=True,
            cwd=IMPL_DIR,
            timeout=60,
        )
        out = {}
        if proc.stdout:
            try:
                out = json.loads(proc.stdout)
            except json.JSONDecodeError:
                out = {"_raw": proc.stdout[:500]}
    except subprocess.TimeoutExpired:
        out = {"success": False, "errors": ["timeout"]}
    except Exception as e:
        out = {"success": False, "errors": [str(e)]}

    ok = bool(out.get("success") and out.get("ranking") and len(out["ranking"]) >= 1 and out.get("source") == "ib")
    report = {
        "ok": ok,
        "source": out.get("source"),
        "ranking_count": len(out.get("ranking", [])),
        "errors": out.get("errors", [])[:5],
        "message": "IB returned market cap (source=ib)" if ok else "IB could not return market cap; use source=static or check docs/IB_PAPER_MARKET_CAP_CONFIG.md",
    }
    print(json.dumps(report, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
