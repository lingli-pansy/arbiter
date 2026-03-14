#!/usr/bin/env bash
# 验证 get_market_cap_ranking / run_market_cap_rotation_backtest 依赖与基本可用性
# TICKET_20250314_BACKTEST_001_FOLLOWUP_001
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/.venv/bin/python"
IMPL="${ROOT}/system/tools/impl"

# 检查 yfinance 是否可导入
"$PY" -c "import yfinance as yf; print('yfinance: OK')"

# 最小 smoke test：调用 get_market_cap_ranking（source=yahoo 无需 IB），校验 JSON 结构
OUT=$("$PY" "$IMPL/get_market_cap_ranking.py" <<< '{"date": "2024-01-02", "top_n": 5, "source": "yahoo"}' 2>/dev/null)
if echo "$OUT" | "$PY" -c "import json,sys; d=json.load(sys.stdin); exit(0 if d.get('success') and 'ranking' in d else 1)" 2>/dev/null; then
  echo "get_market_cap_ranking: OK (valid output structure)"
else
  echo "get_market_cap_ranking: FAIL (invalid or missing success/ranking)" >&2
  exit 1
fi

echo "Market cap tools verified."
