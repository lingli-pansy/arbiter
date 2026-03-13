#!/usr/bin/env bash
# 统一入口：调用 install_ib_deps.sh
# 用法: ./scripts/setup_venv.sh [--recreate]
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${SCRIPT_DIR}/install_ib_deps.sh" "$@"
