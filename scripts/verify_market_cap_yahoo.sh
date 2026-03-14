#!/usr/bin/env bash
# TICKET_20250314_001_FOLLOWUP_004: 验证 Yahoo 数据源在限流场景下可获取市值
# 使用小 universe 快速完成（5 只股票 ~8 秒）

set -e
REPO=/Users/xiaoyu/arbiter-2
PY="$REPO/.venv/bin/python3"
IMPL="$REPO/system/tools/impl"
INPUT='{"date":"2024-01-02","top_n":5,"source":"yahoo","universe":["AAPL","MSFT","GOOGL","AMZN","NVDA"]}'

echo "=== Yahoo 市值排名验证 (小 universe) ==="
OUT=$("$PY" "$IMPL/get_market_cap_ranking.py" <<< "$INPUT" 2>/dev/null)
if echo "$OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('success') and len(d.get('ranking',[]))>=1; print('OK')" 2>/dev/null; then
  echo "get_market_cap_ranking (yahoo): OK - 返回有效 ranking"
  echo "$OUT" | head -c 500
else
  echo "get_market_cap_ranking (yahoo): FAIL" >&2
  echo "$OUT" >&2
  exit 1
fi
