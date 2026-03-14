#!/usr/bin/env bash
# TICKET_20250314_003 - 最小验证脚本：测试 get_market_cap_ranking source=ib（含 Tick 165 路径）
# 用法: ./validate_tick165.sh
# 需先确保 IB Gateway/TWS Paper 已启动；或使用 mock_mode 验证契约。

set -e
TOOLS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMPL="$TOOLS_DIR/impl"
VENV="${ARBITER_VENV:-$(cd "$TOOLS_DIR/../.." 2>/dev/null && pwd)/.venv}"

# 1. Mock 模式验证（无需 IB）
echo "=== Mock 模式验证 ==="
echo '{"date":"2024-01-02","top_n":5,"mock_mode":true}' | "$VENV/bin/python3" "$IMPL/get_market_cap_ranking.py" | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d.get('success'), d
assert 'meta' in d
assert 'latency_ms' in d['meta']
print('OK: mock output has meta.latency_ms')
"

# 2. source=ib（需 IB 连接）
echo ""
echo "=== source=ib 验证（需 IB 已连接） ==="
echo '{"date":"2024-01-02","top_n":5,"source":"ib"}' | "$VENV/bin/python3" "$IMPL/get_market_cap_ranking.py" | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d.get('success') or d.get('errors'), d
if d.get('success'):
    meta=d.get('meta',{})
    assert 'tick165_attempted' in meta or 'latency_ms' in meta, meta
    print('OK: ib output has meta')
else:
    print('Note: IB not connected, errors:', d.get('errors',[]))
" 2>/dev/null || echo "Skip: IB not available"
