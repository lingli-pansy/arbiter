# TICKET_20250314_BACKTEST_001_FOLLOWUP_001

## Source Task
TICKET_20250314_BACKTEST_001

## Source Validation
VALIDATION_20250314_BACKTEST_001

## Blocking Issue
工具运行时缺少必要的 Python 依赖，导致 `ModuleNotFoundError`。

验收测试中发现以下依赖缺失：
- `yfinance` - Yahoo Finance 数据获取
- `pandas` - 数据处理
- `ib-insync` - Interactive Brokers 连接

## Requested Capability
声明并管理工具所需的所有 Python 依赖。

## Why Existing Tools Are Insufficient
当前工具没有声明依赖，导致在干净环境中无法运行。

## Input Contract
N/A (元数据文件)

## Output Contract
- requirements.txt 文件，列出所有依赖
- 或 registry.yaml 中增加 dependencies 字段
- 可选：安装脚本或虚拟环境配置

## Acceptance Criteria
- [ ] 在干净的 Python 环境中，按照文档安装依赖后，工具可以正常运行
- [ ] 依赖版本明确指定，避免兼容性问题
- [ ] 文档中包含安装步骤

## Test Case
1. 创建新的虚拟环境
2. 安装依赖
3. 运行 `get_market_cap_ranking` 和 `run_market_cap_rotation_backtest`
4. 不应出现 `ModuleNotFoundError`

## Priority
P0

## Status
Open
