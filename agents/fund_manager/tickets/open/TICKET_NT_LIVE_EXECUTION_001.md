# TICKET_NT_LIVE_EXECUTION_001

## Source Task
实盘交易能力验证 - 打通从 NautilusTrader 策略信号到 IB 真实订单执行的完整链路

## Status
**Partial - Implementation Complete, Validation Pending** - P1

**Update 2026-03-14:**
- ✅ 代码实现完成 (submit_order live 模式已实现)
- ✅ Python 3.14 兼容性解决 (使用 venv Python 3.13)
- ✅ IB Gateway 连接验证通过
- ⏳ 实盘订单提交待交易时间验证 (见 TICKET_NT_LIVE_EXECUTION_001_FOLLOWUP_001)

## Blocking Issue
当前系统已实现：
- ✅ `run_backtest` - 回测引擎（仅模拟模式）
- ✅ `submit_order` - 订单提交（仅 paper 模式，本地 JSON 存储）
- ✅ `connect_broker` - IB 连接（live 模式已可用）

**缺失关键链路**：NautilusTrader 实盘策略无法将交易信号转换为真实 IB 订单并执行。

具体问题：
1. `run_backtest` 工具仅在历史数据上运行，不支持实时/实盘模式
2. `submit_order` 在 live 模式下未对接真实 IB API，仅返回 mock 响应
3. 缺乏策略信号 → 订单转换的中间层
4. 没有实盘运行的状态管理和监控机制

## Requested Capability
构建 NT 实盘交易执行链路，实现：

1. **策略实盘运行模式**
   - 扩展 `run_backtest` 或创建 `run_strategy_live`
   - 支持实时数据输入（而非历史数据）
   - 支持生成交易信号但不自动执行（需确认）

2. **信号到订单的转换层**
   - 创建 `signal_to_order` 工具
   - 将 NT 的 Order/Position 对象转换为 IB 订单格式
   - 支持市价/限价/止损订单类型映射

3. **真实订单执行**
   - 扩展 `submit_order` 支持 live 模式真实 IB 提交
   - 使用 `ib_insync` 对接 IB Gateway/TWS
   - 返回真实订单 ID 和状态

4. **实盘监控与状态**
   - 创建 `get_strategy_state` 工具
   - 监控实盘策略运行状态
   - 持久化实盘运行日志

## Why Existing Tools Are Insufficient

| 工具 | 当前能力 | 缺失能力 |
|------|----------|----------|
| `run_backtest` | 仅历史数据回测 | 不支持实时数据流；不生成可执行的实时信号 |
| `submit_order` | Paper 模式本地存储 | Live 模式未实现真实 IB 提交；无错误重试机制 |
| `connect_broker` | 连接管理 | 未与策略执行层集成 |
| `get_order_status` | 查询本地状态 | 未对接 IB 真实订单状态查询 |

**架构缺口图示**：
```
当前架构:
NT Strategy → run_backtest (历史数据) → 回测报告
                         ↓
              submit_order (paper/mock) → 本地 JSON

目标架构:
NT Strategy → run_strategy_live (实时数据) → Signal
                    ↓
            signal_to_order → IB Order Format
                    ↓
            submit_order (live) → IB Gateway → 真实交易所
                    ↓
            get_order_status ← IB 真实状态
                    ↓
            execution_audit → 实盘执行报告
```

## Input Contract

### run_strategy_live (新工具)
```yaml
inputs:
  strategy_id:
    type: string
    required: true
    description: 策略标识 (如 "momentum_20d")
  symbols:
    type: array[string]
    required: true
    description: 交易标的列表
  mode:
    type: enum["paper", "live"]
    required: true
    default: "paper"
  data_source:
    type: enum["ib", "yahoo"]
    required: false
    default: "ib"
    description: 实时数据源
  execution_mode:
    type: enum["auto", "confirm"]
    required: false
    default: "confirm"
    description: auto=自动执行，confirm=生成信号待确认
  capital:
    type: number
    required: true
    description: 初始资金
  
outputs:
  success: boolean
  session_id: string
  status: enum["running", "stopped", "error"]
  signals:
    type: array[object]
    properties:
      timestamp: ISO8601
      symbol: string
      signal: enum["BUY", "SELL", "HOLD"]
      size: number
      price: number
```

### signal_to_order (新工具)
```yaml
inputs:
  session_id: string
  signal:
    type: object
    properties:
      symbol: string
      side: enum["BUY", "SELL"]
      size: number
      price: number
      order_type: enum["MKT", "LMT", "STP"]
  risk_check:
    type: boolean
    default: true
    description: 是否执行风险检查

outputs:
  success: boolean
  order_plan:
    type: object
    properties:
      symbol: string
      side: string
      quantity: number
      order_type: string
      limit_price: number (optional)
      estimated_value: number
```

### submit_order (扩展)
```yaml
inputs:
  connection_id: string
  symbol: string
  side: enum["BUY", "SELL"]
  quantity: number
  order_type: enum["MKT", "LMT", "STP"]
  limit_price: number (optional)
  stop_price: number (optional)
  mode: enum["paper", "live"]  # 新增
  
outputs:
  success: boolean
  order_id: string
  status: enum["submitted", "filled", "rejected", "pending"]
  filled_qty: number
  avg_fill_price: number
  ib_order_id: string  # IB 返回的真实订单 ID
  error_message: string
```

## Output Contract

所有工具返回标准响应格式：
```yaml
success: boolean
error_message: string (if failed)
timestamp: ISO8601
metadata:
  session_id: string
  tool_version: string
```

## Acceptance Criteria

### 必需 (Must Have)
- [ ] `submit_order` live 模式能成功提交订单到 IB Gateway
- [ ] 返回真实的 IB 订单 ID (permId)
- [ ] `get_order_status` 能查询 IB 真实订单状态
- [ ] 市价单能在 5 秒内成交 (正常市场条件下)
- [ ] 限价单能正确挂在 IB 订单簿上
- [ ] 错误处理：网络中断、IB 拒绝、资金不足等场景有明确错误码
- [ ] 订单持久化：所有订单记录保存到 `system/state/live_orders.json`

### 期望 (Should Have)
 [ ] `run_strategy_live` 工具能生成交易信号
- [ ] `signal_to_order` 能正确转换 NT 信号到 IB 订单格式
- [ ] 风险检查：单笔订单不超过总资金的 10%
- [ ] 费率模型：支持配置佣金和滑点
- [ ] 实时监控：每 30 秒刷新订单状态

### 可选 (Nice to Have)
- [ ] 支持止损单 (STP) 和止盈单
- [ ] 支持盘后交易 (Extended Hours)
- [ ] 支持组合订单 (OCO, Bracket)

## Test Case

### 基础验收测试
```bash
# 1. 连接 IB Gateway (Live 模式)
cd /Users/xiaoyu/arbiter-2/system/tools/impl
python3 -c "
from connect_broker import main
import json
result = main(json.dumps({
    'broker': 'ib',
    'mode': 'live',
    'timeout_ms': 10000
}))
print(result)
"
# 期望: success=true, status=connected, latency_ms>0

# 2. 提交真实市价单 (最小数量 1 股)
python3 -c "
from submit_order import main
import json
result = main(json.dumps({
    'connection_id': '<from_step_1>',
    'symbol': 'AAPL',
    'side': 'BUY',
    'quantity': 1,
    'order_type': 'MKT',
    'mode': 'live'
}))
print(result)
"
# 期望: success=true, status=submitted/filled, ib_order_id 不为空

# 3. 查询订单状态
python3 -c "
from get_order_status import main
import json
result = main(json.dumps({
    'connection_id': '<from_step_1>',
    'order_id': '<from_step_2>'
}))
print(result)
"
# 期望: 返回 IB 真实订单状态，包含 filled_qty, avg_fill_price

# 4. 验证订单记录在 IB TWS/Gateway 中可见
# 人工检查：打开 TWS，查看订单簿中是否有对应订单
```

### 完整链路测试
```bash
# 运行策略生成信号 → 转换为订单 → 提交 IB
python3 tests/test_live_execution_chain.py \
  --strategy momentum_20d \
  --symbols AAPL \
  --mode paper \
  --execution_mode confirm

# 期望输出:
# - 策略信号生成成功
# - 订单计划创建成功
# - submit_order 返回 IB 订单 ID
# - 最终状态可在 TWS 中查看
```

## Dependencies

### 前置依赖
- ✅ TICKET_20260314_004 - IB Live Connection (已完成)
- ✅ TICKET_20250314_003 - Order Management (已完成，但需扩展)

### 并行依赖
- TICKET_20250314_003_FOLLOWUP_001 - IB 实时行情订阅 (可选，可用 Yahoo 替代)

## Risk Assessment

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| IB API 限流 | 订单提交被拒绝 | 实现指数退避重试 |
| 网络中断 | 订单状态丢失 | 本地持久化 + 重连恢复 |
| 资金不足 | 订单被拒绝 | 前置余额检查 |
| 市场关闭 | 订单无法成交 | 交易时间检查 + 预提交验证 |

## Implementation Notes

### 技术方案建议

**方案 A: 直接扩展 submit_order (推荐)**
```python
# submit_order.py
if mode == "live":
    from ib_insync import IB, Stock, MarketOrder
    ib = get_connection(connection_id)  # 从 connect_broker 获取
    contract = Stock(symbol, 'SMART', 'USD')
    order = MarketOrder(side, quantity)
    trade = ib.placeOrder(contract, order)
    return {
        "success": True,
        "order_id": str(trade.order.orderId),
        "ib_order_id": str(trade.order.permId),
        "status": trade.orderStatus.status
    }
```

**方案 B: 创建独立的 live_execution 模块**
- 更清晰的架构分离
- 但增加维护复杂度

### 参考实现
- `adapters/ib_fundamental.py` - 已有 ib_insync 使用示例
- `adapters/broker_store.py` - 连接管理参考

## Related

- TICKET_20260314_004_ib_live_connection.md - IB 连接实现
- TICKET_20250314_003_order_management.md - 订单管理基础
- REPORT_20260314_TASK0021_ib_connection.md - 连接验证报告

## Priority
P1 - 阻塞实盘交易能力

## Created
2026-03-14

## Assigned To
Cursor (Implementation)

## ETA
建议 2-3 天完成基础链路 (submit_order live 模式)
建议 1 周完成完整链路 (signal_to_order + 监控)
