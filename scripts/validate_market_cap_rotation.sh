#!/usr/bin/env bash
# 市值轮动回测验证脚本。TICKET_20250314_BACKTEST_001
# 用法: ./scripts/validate_market_cap_rotation.sh
# 依赖: .venv 已创建且安装 yfinance；若遇 Yahoo 限流请稍后重试

set -e
REPO=/Users/xiaoyu/arbiter-2
PY="${REPO}/.venv/bin/python3"
IMPL="${REPO}/system/tools/impl"

cd "$REPO"
if [[ ! -x "$PY" ]]; then
  echo "Create venv first: python3 -m venv .venv && .venv/bin/pip install -r system/tools/impl/requirements.txt"
  exit 1
fi

echo "=== 1. get_market_cap_ranking ==="
"$PY" "$IMPL/get_market_cap_ranking.py" <<< '{"date":"2024-03-31","top_n":5}' | head -c 500
echo ""

echo ""
echo "=== 2. run_market_cap_rotation_backtest ==="
"$PY" "$IMPL/run_market_cap_rotation_backtest.py" <<< '{"start_date":"2024-01-01","end_date":"2025-01-01","initial_capital":500000,"cash_pool":50000,"top_n":5,"benchmark":"QQQ"}' | head -c 2000
echo ""
echo "=== done ==="
