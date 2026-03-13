# TICKET_0002: NautilusTrader Schema Access Capability

**Status:** done  
**Created:** 2026-03-13  
**Completed:** 2026-03-13  
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

1. [x] 工具 `get_nt_bar_schema` 在 registry.yaml 中注册，status = active
2. [x] 能返回 Bar 类型的完整字段列表（open, high, low, close, volume, ts_event, ts_init 等）
3. [x] 包含每个字段的 Python 类型信息
4. [x] 提供示例 Bar 对象的数据结构
5. [x] 版本信息与当前安装的 nautilus_trader 一致（或未安装时返回 static fallback）

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
    "fields": [...],
    "example": {...}
  },
  "version": "1.224.0"
}
```

## Related Tasks

- TASK_0001B: Market data source alignment (blocked by this)
- TASK_0001C: NautilusTrader market data integration validation (blocked by this)
- TASK_0008: Run backtest (likely depends on NT compatibility)

## Implementation Summary

- **Contract:** `system/tools/contracts/get_nt_bar_schema.yaml`
- **Impl:** `system/tools/impl/get_nt_bar_schema.py`
  - 优先从已安装的 `nautilus_trader` 内省 Bar 类获取 schema
  - 未安装时返回基于官方文档的静态 schema（支持 schema 对比）
  - 支持 format: dict | json_schema | python_type
  - 支持 include_examples: true | false
- **Dependency:** `system/tools/impl/requirements.txt` 新增 `nautilus_trader>=1.200.0`
- **Tests:** `system/tools/tests/test_get_nt_bar_schema.py` 3 用例通过
