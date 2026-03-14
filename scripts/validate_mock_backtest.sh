#!/usr/bin/env bash
# TICKET_20250314_BACKTEST_001_FOLLOWUP_007: 验证 mock_mode 下全链路回测 10 秒内完成
set -e
_IMPL="$(cd "$(dirname "$0")/../system/tools/impl" && pwd)"
cd "$_IMPL"

payload='{"start_date":"2024-01-01","end_date":"2024-03-31","top_n":3,"benchmark":"QQQ","mock_mode":true}'
start=$(python3 -c 'import time; print(int(time.time()*1000))')
out=$(echo "$payload" | python3 run_market_cap_rotation_backtest.py)
end=$(python3 -c 'import time; print(int(time.time()*1000))')
elapsed=$((end - start))

success=$(echo "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('success', False))")
if [ "$success" != "True" ]; then
  echo "FAIL: mock backtest success=$success"
  echo "$out" | python3 -m json.tool 2>/dev/null || echo "$out"
  exit 1
fi

if [ "$elapsed" -gt 10000 ]; then
  echo "FAIL: mock backtest took ${elapsed}ms (>10s)"
  exit 1
fi

echo "OK: mock backtest completed in ${elapsed}ms (<10s)"
echo "$out" | python3 -c "
import json,sys
d=json.load(sys.stdin)
r=d.get('report',{})
m=r.get('metrics',{})
print(f\"  total_return_pct: {m.get('total_return_pct')}  max_drawdown_pct: {m.get('max_drawdown_pct')}\")
"
