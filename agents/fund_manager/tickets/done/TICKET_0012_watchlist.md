# TICKET_0012: Watchlist Management Capability

**Status:** done  
**Created:** 2026-03-14  
**Completed:** 2026-03-14  
**Source Task:** TASK_0019 (Daily research routine)  
**Blocking Issue:** `missing_tool`

---

## Resolution

实现 get_watchlist 与 update_watchlist 工具。
- get_watchlist: 读取 system/state/watchlists/，可选 include_quotes 调用 get_market_bars_batch
- update_watchlist: add/remove/create/delete，默认 watchlist 含 tech stocks
- 修改: impl, contracts, registry, test_watchlist.py

---

## Blocking Issue

每日研究流程需要管理观察列表（watchlist），但系统当前没有 watchlist 管理工具。

当前可用工具：
- ✅ `get_market_bars_batch` - 市场数据
- ❌ `get_watchlist` - **缺失**
- ❌ `update_watchlist` - **缺失**

## Requested Capability

提供观察列表管理工具，支持：
1. 创建/读取/更新/删除 watchlist
2. 添加/移除 symbol
3. 设置 alert/notes
4. 批量获取 watchlist 行情

## Implementation Specification

### Create get_watchlist Tool

```yaml
name: get_watchlist
description: 获取观察列表及其行情数据
inputs:
  watchlist_id:
    type: string
    required: false
    default: "default"
    description: 观察列表ID
  include_quotes:
    type: boolean
    required: false
    default: true
    description: 是否包含实时行情
  lookback_days:
    type: integer
    required: false
    default: 5
    description: 历史数据天数

output:
  type: object
  properties:
    success: { type: boolean }
    watchlist:
      type: object
      properties:
        watchlist_id: { type: string }
        name: { type: string }
        created_at: { type: string }
        symbols:
          type: array
          items:
            type: object
            properties:
              symbol: { type: string }
              added_at: { type: string }
              notes: { type: string }
              alerts: { type: array }
        quotes:
          type: object
          description: symbol -> price data
    errors: { type: array }
```

### Create update_watchlist Tool

```yaml
name: update_watchlist
description: 更新观察列表（添加/移除 symbol）
inputs:
  watchlist_id:
    type: string
    required: false
    default: "default"
  action:
    type: string
    required: true
    enum: ["add", "remove", "create", "delete"]
  symbols:
    type: array[string]
    required: false
    description: 要添加/移除的 symbols
  name:
    type: string
    required: false
    description: 观察列表名称（create 时）

output:
  type: object
  properties:
    success: { type: boolean }
    watchlist: { type: object }
    errors: { type: array }
```

## Storage Format

**Location:** `system/state/watchlists/{watchlist_id}.json`

```json
{
  "watchlist_id": "default",
  "name": "Default Watchlist",
  "created_at": "2026-03-14T00:00:00Z",
  "updated_at": "2026-03-14T00:00:00Z",
  "symbols": [
    {
      "symbol": "AAPL",
      "added_at": "2026-03-14T00:00:00Z",
      "notes": "Tech leader",
      "alerts": [
        {"type": "price_above", "value": 200}
      ]
    }
  ]
}
```

## Acceptance Criteria

1. [x] `get_watchlist` 工具可用
2. [x] `update_watchlist` 工具可用
3. [x] 支持多个 watchlist
4. [x] 支持 symbol 的增删改查
5. [x] 可选行情数据获取
6. [x] 结构化 JSON 输出

## Related Tasks

- TASK_0019: Daily research routine (blocked by this)
- TASK_0004: News digest (also needed)

## Notes

**Default Watchlist:**
建议默认创建包含主要 tech stocks 的 watchlist：
```json
{
  "symbols": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]
}
```

**Implementation Files:**
- `system/tools/impl/get_watchlist.py`
- `system/tools/impl/update_watchlist.py`
- `system/tools/contracts/get_watchlist.yaml`
- `system/tools/contracts/update_watchlist.yaml`
