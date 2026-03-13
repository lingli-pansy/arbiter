# TICKET_0011: Portfolio Performance Calculation Capability

**Status:** done  
**Created:** 2026-03-14  
**Completed:** 2026-03-14  
**Source Task:** TASK_0014 (Portfolio performance tracking)  
**Blocking Issue:** `missing_tool`

---

## Resolution

实现 calculate_portfolio_performance 工具，支持收益、回撤、波动率、夏普、基准对比。

**实现:**
- 输入: portfolio_id 或 portfolio，可选 market_data、start_date、end_date、benchmark
- 输出: period, returns, drawdown, risk, benchmark 结构化 JSON
- 缺省 market_data 时内部调用 get_market_bars_batch 拉取

**修改文件:**
- system/tools/impl/calculate_portfolio_performance.py
- system/tools/contracts/calculate_portfolio_performance.yaml
- system/tools/registry.yaml
- system/tools/tests/test_calculate_portfolio_performance.py

---

## Blocking Issue

基金经理需要跟踪组合表现（收益、回撤等），但系统当前没有 `calculate_portfolio_performance` 工具。

当前可用工具：
- ✅ `get_portfolio` - 读取组合
- ✅ `get_market_bars_batch` - 获取市场数据
- ❌ `calculate_portfolio_performance` - **缺失**

## Requested Capability

提供组合表现计算工具，支持：
1. 计算组合收益率（总收益、年化收益）
2. 计算回撤（最大回撤、回撤持续时间）
3. 计算波动率
4. 计算夏普比率
5. 对比基准表现

## Why Existing Tools Are Insufficient

| 所需能力 | 现有工具 | 状态 |
|---------|---------|------|
| 组合收益计算 | ❌ 缺失 | 需要 performance 工具 |
| 回撤计算 | ❌ 缺失 | 需要 performance 工具 |
| 波动率计算 | ❌ 缺失 | 需要 performance 工具 |
| 基准对比 | ❌ 缺失 | 需要 performance 工具 |

## Implementation Specification

### Create calculate_portfolio_performance Tool

```yaml
name: calculate_portfolio_performance
description: 计算组合表现指标（收益、回撤、波动率等）
inputs:
  portfolio_id:
    type: string
    required: false
    description: 组合标识
  portfolio:
    type: object
    required: false
    description: 组合对象（含 assets 和初始资本）
  start_date:
    type: string
    required: false
    description: 开始日期（ISO 8601）
  end_date:
    type: string
    required: false
    description: 结束日期（ISO 8601）
  benchmark:
    type: string
    required: false
    default: "SPY"
    description: 基准标的（如 SPY、QQQ）
  include_metrics:
    type: array[string]
    required: false
    default: ["all"]
    enum: ["returns", "drawdown", "volatility", "sharpe", "benchmark", "all"]

output:
  type: object
  properties:
    success: { type: boolean }
    performance:
      type: object
      properties:
        period:
          type: object
          properties:
            start: { type: string }
            end: { type: string }
            days: { type: integer }
        returns:
          type: object
          properties:
            total_return_pct: { type: number }
            cagr_pct: { type: number }
            daily_returns: { type: array }
            cumulative_returns: { type: array }
        drawdown:
          type: object
          properties:
            max_drawdown_pct: { type: number }
            max_drawdown_date: { type: string }
            current_drawdown_pct: { type: number }
            avg_drawdown_pct: { type: number }
        risk:
          type: object
          properties:
            volatility_annual_pct: { type: number }
            sharpe_ratio: { type: number }
            sortino_ratio: { type: number }
            calmar_ratio: { type: number }
        benchmark:
          type: object
          properties:
            symbol: { type: string }
            benchmark_return_pct: { type: number }
            alpha: { type: number }
            beta: { type: number }
            tracking_error: { type: number }
            information_ratio: { type: number }
    errors: { type: array }
```

## Required Data

**1. Portfolio History**
需要组合的历史快照来追踪表现：
```json
{
  "portfolio_id": "MODEL_TECH_001",
  "snapshots": [
    {"date": "2026-03-01", "value": 100000, "weights": {...}},
    {"date": "2026-03-14", "value": 105000, "weights": {...}}
  ]
}
```

**实现选项：**
- Option A: 从 portfolio 创建时开始追踪（简化版）
- Option B: 完整的 snapshot 历史系统（完整版）

**建议：** 先实现 Option A，从 portfolio creation date 开始计算。

**2. Market Data**
使用现有的 `get_market_bars_batch` 获取价格数据。

## Acceptance Criteria

1. [x] 工具 `calculate_portfolio_performance` 在 registry.yaml 中注册
2. [x] 支持总收益率和年化收益率计算
3. [x] 支持最大回撤和回撤分析
4. [x] 支持波动率和夏普比率计算
5. [x] 支持基准对比（alpha, beta）
6. [x] 输出为结构化 JSON

**Completed:** 2026-03-14

## Test Case

**输入:**
```json
{
  "portfolio_id": "MODEL_TECH_001",
  "start_date": "2026-03-01",
  "end_date": "2026-03-14",
  "benchmark": "QQQ"
}
```

**期望输出:**
```json
{
  "success": true,
  "performance": {
    "period": {
      "start": "2026-03-01",
      "end": "2026-03-14",
      "days": 14
    },
    "returns": {
      "total_return_pct": 5.2,
      "cagr_pct": 120.5
    },
    "drawdown": {
      "max_drawdown_pct": -2.1,
      "max_drawdown_date": "2026-03-08"
    },
    "risk": {
      "volatility_annual_pct": 18.5,
      "sharpe_ratio": 1.35
    },
    "benchmark": {
      "symbol": "QQQ",
      "benchmark_return_pct": 3.8,
      "alpha": 1.4,
      "beta": 1.15
    }
  }
}
```

## Related Tasks

- TASK_0014: Portfolio performance tracking (blocked by this)
- TASK_0011: Create portfolio (completed)
- TASK_0012: Portfolio exposure analysis (completed)
- TASK_0013: Rebalance simulation (completed)

## Implementation Path

**Phase 1: Basic Performance (MVP)**
- Total return calculation
- Simple drawdown
- Basic volatility

**Phase 2: Advanced Metrics**
- Sharpe, Sortino, Calmar ratios
- Benchmark comparison
- Rolling performance

**Implementation Files:**
- `system/tools/impl/calculate_portfolio_performance.py`
- `system/tools/contracts/calculate_portfolio_performance.yaml`
- `system/tools/tests/test_calculate_portfolio_performance.py`

## Notes

**Portfolio Value Calculation:**
```python
def calculate_portfolio_value(weights, prices):
    """Calculate portfolio value based on weights and prices"""
    return sum(
        weight * price 
        for symbol, weight in weights.items()
        for price in prices.get(symbol, 0)
    )
```

**Return Calculation:**
```python
def calculate_returns(value_series):
    """Calculate returns from value series"""
    returns = value_series.pct_change().dropna()
    total_return = (value_series[-1] / value_series[0]) - 1
    return returns, total_return
```

**Drawdown Calculation:**
```python
def calculate_drawdown(value_series):
    """Calculate drawdown from value series"""
    peak = value_series.cummax()
    drawdown = (value_series - peak) / peak
    max_drawdown = drawdown.min()
    return drawdown, max_drawdown
```

**Recommended Priority:** P1 (blocks TASK_0014)
