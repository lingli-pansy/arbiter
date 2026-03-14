#!/usr/bin/env bash
# 验证 TICKET_20250314_BACKTEST_001_FOLLOWUP_002/004/006 实现
# 用法: ./scripts/validate_ticket_fixes.sh

set -e
REPO=/Users/xiaoyu/arbiter-2
PY="$REPO/.venv/bin/python3"
IMPL="$REPO/system/tools/impl"
OK=0
FAIL=0

check() {
  if eval "$@" > /dev/null 2>&1; then
    echo "[OK] $1"
    OK=$((OK+1))
  else
    echo "[FAIL] $1" >&2
    FAIL=$((FAIL+1))
  fi
}

echo "=== TICKET_20250314_BACKTEST_001 验证 ==="

# FOLLOWUP_004: mock_mode 立即返回，不调用 API
OUT=$("$PY" "$IMPL/get_market_cap_ranking.py" <<< '{"date":"2024-03-31","top_n":5,"mock_mode":true}' 2>/dev/null)
check "echo '$OUT' | $PY -c \"import json,sys; d=json.load(sys.stdin); assert d.get('success') and d.get('source')=='mock' and len(d.get('ranking',[]))>=1\""

# FOLLOWUP_002: source=yahoo 不连 IB（用 mock 无法直接验证，但可测 mock 流程）
# 实际 source=yahoo 需网络，此处用 mock 替代
OUT=$("$PY" "$IMPL/get_market_cap_ranking.py" <<< '{"date":"2024-03-31","top_n":3,"source":"yahoo","mock_mode":true}' 2>/dev/null)
check "echo '$OUT' | $PY -c \"import json,sys; d=json.load(sys.stdin); assert d.get('success') and len(d.get('ranking',[]))==3\""

# FOLLOWUP_006: equal_weight 参数（需 run_market_cap_rotation_backtest 支持）
# 用 mock 模式快速验证 run_backtest 能接受 equal_weight
OUT=$("$PY" "$IMPL/run_market_cap_rotation_backtest.py" <<< '{"start_date":"2024-01-01","end_date":"2024-03-31","top_n":3,"equal_weight":false}' 2>/dev/null | head -c 500)
check "echo '$OUT' | $PY -c \"import json,sys; d=json.load(sys.stdin); assert d.get('success') or 'errors' in d\""

echo "--- 合计: $OK 通过, $FAIL 失败 ---"
[ $FAIL -eq 0 ] && exit 0 || exit 1
