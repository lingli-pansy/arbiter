# TICKET_0001: Implement get_market_bars_batch Tool

**Status:** done  
**Created:** 2026-03-12  
**Closed:** 2026-03-13  
**Source Task:** TASK_0001 (Initial Watchlist Review)  

---

## Blocking Issue
基金经理需要批量获取多标的市场行情数据以执行 watchlist review，但工具层未提供 `get_market_bars_batch` 能力。

## Requested Capability
实现一个批量获取市场 K 线/Bar 数据的工具，支持同时查询多个 symbol 的 OHLCV 数据。

## Why Existing Tools Are Insufficient
- system/tools/registry.yaml 当前为空
- 无任何市场数据相关工具已注册
- 无法实现多标的批量查询（减少 API 调用次数）

## Input Contract
```yaml
name: get_market_bars_batch
description: 批量获取多标的市场行情数据（OHLCV）
inputs:
  symbols:
    type: array[string]
    required: true
    description: 标的代码列表，如 ["AAPL", "MSFT"]
    example: ["AAPL", "MSFT", "NVDA", "AMZN", "META"]
  lookback_days:
    type: integer
    required: true
    description: 回溯天数
    default: 20
    min: 1
    max: 252
  timeframe:
    type: string
    required: false
    description: K线周期
    default: "1d"
    enum: ["1m", "5m", "15m", "1h", "4h", "1d"]
  provider:
    type: string
    required: false
    description: 数据源提供商
    default: "yahoo"
    enum: ["yahoo", "ibkr", "polygon"]
```

## Output Contract
```yaml
output:
  type: object
  properties:
    success:
      type: boolean
      description: 查询是否成功
    data:
      type: object
      description: 按 symbol 分组的数据
      properties:
        [symbol]:
          type: array
          items:
            type: object
            properties:
              timestamp: { type: string, format: datetime }
              open: { type: number }
              high: { type: number }
              low: { type: number }
              close: { type: number }
              volume: { type: integer }
    errors:
      type: array
      items:
        type: object
        properties:
          symbol: { type: string }
          error: { type: string }
    meta:
      type: object
      properties:
        requested_symbols: { type: integer }
        returned_symbols: { type: integer }
        timeframe: { type: string }
        provider: { type: string }
```

## Acceptance Criteria
1. [x] 工具在 registry.yaml 中注册，status = active
2. [x] 支持同时查询 1-10 个 symbol
3. [x] 返回数据包含完整 OHLCV 字段
4. [x] 部分失败时返回成功 symbol 数据 + 失败 symbol 错误信息
5. [x] 输入验证失败返回清晰错误（如 symbol 格式错误、lookback_days 越界）
6. [x] 包含至少一个测试用例验证契约

## Test Case
**输入:**
```json
{
  "symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "META"],
  "lookback_days": 20,
  "timeframe": "1d"
}
```

**期望输出:**
```json
{
  "success": true,
  "data": {
    "AAPL": [{"timestamp": "2026-02-20T00:00:00Z", "open": 185.0, "high": 187.5, "low": 184.2, "close": 186.8, "volume": 52000000}, ...],
    "MSFT": [...],
    "NVDA": [...],
    "AMZN": [...],
    "META": [...]
  },
  "errors": [],
  "meta": {
    "requested_symbols": 5,
    "returned_symbols": 5,
    "timeframe": "1d",
    "provider": "yahoo"
  }
}
```

## Implementation Notes
- 底层可使用 yfinance、IB API 或 Polygon
- 建议先用 yfinance 快速实现（无需认证）
- 后续可扩展支持 IBKR 实盘数据源

---

## Implementation Summary (2026-03-13)

- **Contract:** `system/tools/contracts/get_market_bars_batch.yaml`
- **Registry:** `system/tools/registry.yaml` — `get_market_bars_batch` 已注册，status = active
- **Impl:** `system/tools/impl/get_market_bars_batch.py` — 从 stdin 或首参读 JSON，写 JSON 到 stdout；底层 yfinance，provider 仅实现 yahoo
- **Tests:** `system/tools/tests/test_get_market_bars_batch.py` — 4 个用例：非法 JSON、symbols 超 10、lookback_days 越界、输出结构符合契约
- **Run:** `python system/tools/impl/get_market_bars_batch.py '{"symbols":["AAPL","MSFT"],"lookback_days":20,"timeframe":"1d"}'`（需安装 yfinance，建议使用仓库根目录 `.venv`）
