# 安装说明 (TICKET_20250314_BACKTEST_001_FOLLOWUP_001)

## Python 依赖

工具（如 `get_market_cap_ranking`、`run_market_cap_rotation_backtest`）依赖以下包：

| 包 | 版本 | 用途 |
|----|------|------|
| yfinance | >=0.2.0 | Yahoo Finance 数据 |
| pandas | >=2.0.0 | 数据处理 |
| ib_insync | >=0.9.86 | Interactive Brokers 连接 |
| nautilus_trader | >=1.200.0 | 回测引擎 |
| nest_asyncio | >=1.6.0 | 异步事件循环兼容 |

## 安装步骤

### 1. 使用项目 venv（推荐）

```bash
./scripts/install_ib_deps.sh
# 或重建 venv
./scripts/install_ib_deps.sh --recreate
```

### 2. 使用 pip 直接安装

```bash
pip install -r system/tools/impl/requirements.txt
# 或从仓库根目录
pip install yfinance>=0.2.0 pandas>=2.0.0 nautilus_trader>=1.200.0 ib_insync>=0.9.86 nest_asyncio>=1.6.0
```

### 3. 验证

```bash
# mock 模式（无需外部 API）
echo '{"date":"2024-03-31","top_n":5,"source":"static"}' | .venv/bin/python system/tools/impl/get_market_cap_ranking.py

# 或使用 mock_mode
echo '{"date":"2024-03-31","top_n":5,"mock_mode":true}' | .venv/bin/python system/tools/impl/get_market_cap_ranking.py
```

不应出现 `ModuleNotFoundError`。
