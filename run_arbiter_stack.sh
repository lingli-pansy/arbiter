#!/usr/bin/env bash

set -euo pipefail

# Resolve project root (directory of this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
cd "$ROOT_DIR"

echo "[arbiter] Starting Postgres via docker compose..."
docker compose up -d postgres

echo "[arbiter] Loading environment from .env (if present)..."
if [[ -f ".env" ]]; then
  # export all variables defined in .env
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

echo "[arbiter] Starting scheduler (market/news refresh + agent market scan)..."
nohup "$ROOT_DIR/.venv/bin/python" -m arbiter.scheduler.scheduler \
  >> "$LOG_DIR/scheduler.log" 2>&1 &
echo $! > "$LOG_DIR/scheduler.pid"

echo "[arbiter] Starting MCP server..."
nohup "$ROOT_DIR/.venv/bin/python" -m arbiter.mcp.server \
  >> "$LOG_DIR/mcp_server.log" 2>&1 &
echo $! > "$LOG_DIR/mcp_server.pid"

echo "[arbiter] Stack started."
echo "  - Scheduler log:     $LOG_DIR/scheduler.log"
echo "  - MCP server log:    $LOG_DIR/mcp_server.log"
echo "  - Scheduler PID:     $(cat "$LOG_DIR/scheduler.pid")"
echo "  - MCP server PID:    $(cat "$LOG_DIR/mcp_server.pid")"

