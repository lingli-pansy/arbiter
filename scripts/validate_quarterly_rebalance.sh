#!/usr/bin/env bash
# TICKET_20250314_BACKTEST_001_FOLLOWUP_008: 验证 quarterly 调仓产生 4 条记录

set -e
cd "$(dirname "$0")/.."
IMPL=system/tools/impl

payload='{"start_date":"2024-01-01","end_date":"2025-01-01","rebalance_frequency":"quarterly","mock_mode":true}'
out=$(echo "$payload" | python3 "$IMPL/run_market_cap_rotation_backtest.py")
count=$(echo "$out" | python3 -c "import json,sys; r=json.load(sys.stdin); print(len(r.get('report',{}).get('rebalances',[])))")

if [ "$count" -eq 4 ]; then
  echo "OK: quarterly rebalance produces 4 records"
  echo "$out" | python3 -c "
import json,sys
r=json.load(sys.stdin)
for rb in r.get('report',{}).get('rebalances',[]):
  print(' ', rb.get('date'))
"
  exit 0
else
  echo "FAIL: expected 4 rebalances, got $count"
  exit 1
fi
