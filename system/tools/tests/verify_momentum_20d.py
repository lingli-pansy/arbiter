#!/usr/bin/env python3
"""TICKET_0005 验收：momentum_20d 策略能完整运行"""
import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"
SCRIPT = IMPL_DIR / "run_backtest.py"

nt_bars = {
    "data": {
        "AAPL": [
            {
                "bar_type": "AAPL.NASDAQ-1-DAY-LAST",
                "open": "185.0",
                "high": "187.5",
                "low": "184.2",
                "close": str(186.8 + i * 0.5),
                "volume": "52000000",
                "ts_event": 1704067200000000000 + i * 86400 * 1_000_000_000,
                "ts_init": 1704067200000000000 + i * 86400 * 1_000_000_000,
                "is_revision": False,
            }
            for i in range(27)
        ],
    },
    "meta": {"timeframe": "1d", "timeframe_nt": "1-DAY"},
}

params = {
    "strategy_id": "momentum_20d",
    "nt_bars": nt_bars,
    "symbols": ["AAPL"],
    "config": {"trade_size": 10},
}

raw = json.dumps(params)
r = subprocess.run(
    [sys.executable, str(SCRIPT)],
    input=raw.encode(),
    capture_output=True,
    timeout=60,
    cwd=str(IMPL_DIR),
)
print("returncode:", r.returncode)
if r.stderr:
    print("stderr:", r.stderr.decode()[:1500])
text = r.stdout.decode()
for line in reversed(text.strip().split("\n")):
    if line.strip().startswith("{"):
        try:
            out = json.loads(line)
            print("success:", out.get("success"))
            print("meta:", out.get("meta"))
            if out.get("report"):
                rpt = out["report"]
                print("report keys:", list(rpt.keys()))
            sys.exit(0 if out.get("success") else 1)
        except Exception:
            pass
sys.exit(1)
