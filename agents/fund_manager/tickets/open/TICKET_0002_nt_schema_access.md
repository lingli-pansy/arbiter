# TICKET_0002: NautilusTrader Schema Access Capability

**Status:** open  
**Created:** 2026-03-13  
**Source Task:** TASK_0001B (Market data source alignment)  
**Blocking Issue:** `missing_tool`

---

## Blocking Issue

基金经理需要审查 `get_market_bars_batch` 的 schema 与 NautilusTrader bar schema 的兼容性，但系统未提供访问 NautilusTrader schema 定义的工具或文档。

当前状态：
- NautilusTrader Python 包未安装
- 无 NautilusTrader bar schema 文档
- 无法完成 schema 对比任务

## Requested Capability

提供一个工具或文档路径，使基金经理能够获取 NautilusTrader 的 bar/candle schema 定义，用于与现有 tool contract 进行对比。

## Why Existing Tools Are Insufficient

| 所需能力 | 现有工具 | 状态 |
|---------|---------|------|
| 查询 NautilusTrader Bar 结构 | 无 | ❌ 缺失 |
| 对比 schema 差异 | 无 | ❌ 缺失 |
| NT DataType 映射 | 无 | ❌ 缺失 |

## Input Contract

```yaml
name: get_nt_bar_schema
description: 获取 NautilusTrader Bar 数据结构的 schema 定义
inputs:
  format:
    type: string
    required: false
    default: "dict"
    enum: ["dict", "json_schema", "python_type"]
  include_examples:
    type: boolean
    required: false
    default: true
```

## Output Contract

```yaml
output:
  type: object
  properties:
    success: { type: boolean }
    schema:
      type: object
      description: Bar 数据结构的完整定义
      properties:
        fields:
          type: array
          items:
            type: object
            properties:
              name: { type: string }
              type: { type: string }
              required: { type: boolean }
              description: { type: string }
        example:
          type: object
          description: 示例 Bar 数据
    version:
      type: string
      description: NautilusTrader 版本
```

## Acceptance Criteria

1. [ ] 工具 `get_nt_bar_schema` 在 registry.yaml 中注册，status = active
2. [ ] 能返回 Bar 类型的完整字段列表（open, high, low, close, volume, ts_event, ts_init 等）
3. [ ] 包含每个字段的 Python 类型信息
4. [ ] 提供示例 Bar 对象的数据结构
5. [ ] 版本信息与当前安装的 nautilus_trader 一致

## Test Case

**输入:**
```json
{"format": "dict", "include_examples": true}
```

**期望输出:**
```json
{
  "success": true,
  "schema": {
    "fields": [
      {"name": "open", "type": "Price", "required": true, "description": "Opening price"},
      {"name": "high", "type": "Price", "required": true, "description": "Highest price"},
      {"name": "low", "type": "Price", "required": true, "description": "Lowest price"},
      {"name": "close", "type": "Price", "required": true, "description": "Closing price"},
      {"name": "volume", "type": "Quantity", "required": true, "description": "Trading volume"},
      {"name": "ts_event", "type": "int64", "required": true, "description": "Event timestamp (nanoseconds)"},
      {"name": "ts_init", "type": "int64", "required": true, "description": "Initialization timestamp"}
    ],
    "example": {
      "open": "185.50",
      "high": "187.25",
      "low": "184.75",
      "close": "186.80",
      "volume": "52000000",
      "ts_event": 1704067200000000000,
      "ts_init": 1704067200000000000
    }
  },
  "version": "1.200.0"
}
```

## Related Tasks

- TASK_0001B: Market data source alignment (blocked by this)
- TASK_0001C: NautilusTrader market data integration validation (blocked by this)
- TASK_0008: Run backtest (likely depends on NT compatibility)

## Notes

替代方案：
1. 安装 nautilus_trader 并暴露查询接口
2. 提供离线 schema 文档
3. 提供 schema 对比工具，自动输出差异报告

推荐实现方案：安装 `nautilus_trader` 并创建 `get_nt_bar_schema` 工具，以便基金经理能独立完成 schema 对齐审查。
