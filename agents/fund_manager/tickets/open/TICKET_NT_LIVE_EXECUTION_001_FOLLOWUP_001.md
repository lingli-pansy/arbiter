# TICKET_NT_LIVE_EXECUTION_001_FOLLOWUP_001

## Source Task
VALIDATION_NT_LIVE_EXECUTION_001 - 实盘订单提交交易时间验证

## Status
**Open** - P1

## Blocking Issue
TICKET_NT_LIVE_EXECUTION_001 代码实现已完成，但实盘验证受市场时间限制：

**当前状态:**
- ✅ `submit_order` live 模式代码已实现 (`place_live_order()`)
- ✅ IB Gateway 连接成功 (使用 Python 3.13 venv)
- ❌ 订单提交超时 (市场关闭)

**根本原因:**
测试时间 (周六 18:19 CST = 美东 05:19) 美股市场关闭，无法验证真实订单提交。

## Requested Capability
在美股交易时间内重新验证 `submit_order` live 模式完整功能。

## Why Current Validation Is Insufficient

| 验证项 | 代码层面 | 实盘验证 |
|--------|----------|----------|
| submit_order live 实现 | ✅ 完成 | ❌ 未验证 |
| IB 订单 ID (permId) 返回 | ✅ 代码有 | ❌ 未确认 |
| 市价单 5 秒成交 | ✅ 代码有 | ❌ 未确认 |
| 订单持久化 (live_orders.json) | ✅ 代码有 | ❌ 未验证 |

**风险:** 代码实现可能未正确处理 IB API 边缘情况，需实盘验证。

## Acceptance Criteria

### 必需 (Must Have)
- [ ] `submit_order` live 模式返回 `success: true`
- [ ] 返回非空的 `ib_order_id` (IB permId)
- [ ] 返回 `status: "filled"` 或 `"submitted"`
- [ ] `system/state/live_orders.json` 包含订单记录
- [ ] 订单可在 IB TWS/Gateway 中查看

### 期望 (Should Have)
- [ ] 市价单在 5 秒内成交
- [ ] `get_order_status` 能查询到最新状态
- [ ] 成交价格和数量与实际一致

## Test Case

### 前置条件
1. IB Gateway/TWS 运行中
2. 使用 Python 3.13 venv: `/Users/xiaoyu/arbiter-2/.venv/bin/python3`
3. 美股市场交易时间 (美东 09:30-16:00)

### 执行步骤

**Step 1: 建立 Live 连接**
```bash
cd /Users/xiaoyu/arbiter-2/system/tools/impl
echo '{
  "broker": "ib",
  "mode": "live",
  "timeout_ms": 10000
}' | /Users/xiaoyu/arbiter-2/.venv/bin/python3 connect_broker.py
```
**期望:** success=true, connection_id 非空

**Step 2: 提交市价单 (最小数量)**
```bash
echo '{
  "connection_id": "<from_step_1>",
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 1,
  "order_type": "MKT",
  "mode": "live"
}' | /Users/xiaoyu/arbiter-2/.venv/bin/python3 submit_order.py
```
**期望:** 
- success=true
- status="filled" (或 "submitted")
- ib_order_id 非空字符串

**Step 3: 验证订单记录**
```bash
cat /Users/xiaoyu/arbiter-2/system/state/live_orders.json
```
**期望:** JSON 中包含刚提交的订单记录

**Step 4: 人工验证**
打开 IB TWS/Gateway，检查订单簿中是否有对应订单。

## Blocking Conditions

| 条件 | 状态 | 预计解除时间 |
|------|------|--------------|
| 美股市场开放 | ❌ 关闭中 | 周一 09:30 ET |
| IB Gateway 运行 | ✅ 可用 | - |
| Python 3.13 venv | ✅ 可用 | - |

## Input/Output Contract

同 TICKET_NT_LIVE_EXECUTION_001

## Risk Assessment

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| IB API 限流 | 低 | 订单被拒绝 | 单次测试，数量最小 |
| 资金不足 | 低 | 订单被拒绝 | 测试前检查账户余额 |
| 网络中断 | 低 | 连接失败 | 本地测试，网络稳定 |
| 价格波动 | 中 | 成交价格偏离 | 市价单，小额测试 |

## Related

- TICKET_NT_LIVE_EXECUTION_001 (母 ticket)
- VALIDATION_NT_LIVE_EXECUTION_001.md (验收报告)
- TICKET_20260314_007_py314_compatibility.md (Python 版本问题)

## Priority
P1 - 阻塞实盘交易能力完整验证

## Created
2026-03-14

## ETA
等待美股交易时间开放 (下周一 09:30 ET)

## Notes

**重要提醒:**
- 必须使用 `.venv/bin/python3`，系统 Python 3.14 不兼容
- 建议测试时间: 美东 10:00-11:00 (市场活跃，流动性好)
- 最小测试数量: 1 股 AAPL
- 测试前确认 IB 账户有足够现金
