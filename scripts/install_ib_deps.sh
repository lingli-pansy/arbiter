#!/usr/bin/env bash
# 安装 IB live/paper 连接所需依赖，统一使用项目 .venv
# 用法: ./scripts/install_ib_deps.sh [--recreate]
# --recreate: 删除现有 .venv 并重建（解决 Python 版本或依赖问题）
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${ROOT}/.venv"

# 优先使用 Python 3.13（与 ib_insync 兼容），否则 3.12 / 3.11
PYTHON=""
for p in python3.13 python3.12 python3.11 python3; do
  if command -v "$p" &>/dev/null; then
    v=$("$p" -c "import sys; print(sys.version_info[:2])" 2>/dev/null || true)
    if [[ "$v" == "(3, 13)" || "$v" == "(3, 12)" || "$v" == "(3, 11)" ]]; then
      PYTHON="$p"
      break
    fi
  fi
done
# Homebrew 路径
[[ -z "$PYTHON" ]] && [[ -x /opt/homebrew/opt/python@3.13/bin/python3.13 ]] && PYTHON=/opt/homebrew/opt/python@3.13/bin/python3.13
[[ -z "$PYTHON" ]] && [[ -x /opt/homebrew/opt/python@3.12/bin/python3.12 ]] && PYTHON=/opt/homebrew/opt/python@3.12/bin/python3.12
[[ -z "$PYTHON" ]] && PYTHON=python3

if [[ "$1" == "--recreate" ]] && [[ -d "$VENV" ]]; then
  echo "Removing existing .venv ..."
  rm -rf "$VENV"
fi

if [[ ! -d "$VENV" ]]; then
  echo "Creating .venv with $PYTHON ..."
  "$PYTHON" -m venv "$VENV"
fi

echo "Installing dependencies ..."
"${VENV}/bin/pip" install -r "${ROOT}/system/tools/impl/requirements.txt" -q

echo "Verifying IB deps ..."
"${VENV}/bin/python" "${ROOT}/system/tools/impl/verify_ib_deps.py"
echo "OK. Use .venv/bin/python for broker tools."
