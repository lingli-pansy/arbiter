# IB Gateway / TWS 配置指南

TICKET_20250314_003_FOLLOWUP_001 | 市值数据  
账户验证 | 实盘交易

## 实盘账户验证（指定交易账户）

为确保实盘订单在**指定账户**执行，`connect_broker` 支持 `expected_account_id`：

```bash
# 连接时指定并验证账户
echo '{
  "broker": "ib",
  "mode": "live",
  "expected_account_id": "U12345678"
}' | .venv/bin/python3 system/tools/impl/connect_broker.py
```

- 成功：返回 `account_ids`、`verified_account_id`，后续 `submit_order` 会二次校验
- 失败：若 Gateway 当前登录账户与 `expected_account_id` 不符，连接被拒绝

**不指定时**：连接仍会获取 `account_ids` 供 `get_broker_account` 查询，但不会强制校验。

---

## 问题摘要（市值数据）

IB Paper Trading 账户在获取市值数据时可能遇到：
- **Error 10089**: 需要市场数据订阅
- **Error 10358**: Fundamentals Data 不可用（Paper 账户通常不支持）

## 配置检查清单

### 1. IB Gateway / TWS 启动

- Paper 端口: **4002** (Gateway) / 7497 (TWS)
- Live 端口: **4001** (Gateway) / 7496 (TWS)
- 确认 Gateway 已启动且 API 已启用

### 2. API 设置

路径: **Edit > Global Configuration > API > Settings**

| 项 | 建议值 |
|----|--------|
| Enable ActiveX and Socket Clients | ✓ |
| Socket port | 4002 (Paper) |
| Allow connections from localhost only | ✓ |
| Read-Only API | 按需 |
| Create API message log | 可选（调试用） |

### 3. Market Data 订阅

路径: **Configure > Market Data Connections** 或 **Account > Market Data Subscriptions**

- 检查 Paper 账户的**延迟数据**订阅状态
- 美股延迟数据（15–20 分钟）通常免费
- 实时数据需要额外订阅

### 4. Use Account Subscription

部分版本支持 **Use Account Subscription** 选项，用于复用账户级别的数据权限。若可见，可尝试启用。

## 验证步骤

1. **建立连接**
   - Paper (Gateway 4002):
     ```bash
     echo '{"broker":"ib","mode":"paper"}' | python system/tools/impl/connect_broker.py
     ```
   - Live (Gateway 4001，默认端口):
     ```bash
     echo '{"broker":"ib","mode":"live"}' | python system/tools/impl/connect_broker.py
     ```

2. **运行市值验证**
   ```bash
   python system/tools/scripts/validate_ib_market_cap.py
   ```

3. **成功标准**
   - 至少 1 只股票（如 AAPL）返回市值
   - 输出 `"ok": true`

## 已知限制

| 数据类型 | Paper 支持 | 说明 |
|----------|------------|------|
| reqFundamentalData | ❌ 10358 | Paper 一般不提供 |
| reqMktData Tick 165 | ⚠️ 需订阅 | 10089 表示需市场数据权限 |
| Snapshot 模式 | ⚠️ 可能收费 | 已在代码中作为 fallback |

## Live 账户调研结论 (2026-03-14)

**环境**: IB Gateway 4001 + 用户已有「美国非整合实时报价」订阅（费用免除）

| 数据途径 | 结果 | 说明 |
|----------|------|------|
| connect_broker | ✅ | 需用 `.venv/bin/python`（Python 3.11–3.13） |
| Tick 165 流式 | ❌ 10089 | 需 API-specific streaming 订阅 |
| Tick 165 Snapshot | ❌ 321 | Snapshot 不适用于 generic ticks |
| reqMarketDataType(3) 延时 | ❌ | Historical Data Farm: Inactive |
| Gateway 日志 SNAPSHOT_NO_API | — | 无 API Snapshot 权限 |

**结论**: 当前订阅下 Live 也无法获取市值。需通过 Gateway 蓝字链接订阅「API-specific market data packages」，或开通 US Equity and Options Add-On Streaming Bundle（约 4.50 USD/月）。

---

## 备选方案

若 IB Paper/Live 无法获取市值：

1. **Static 数据**（当前默认 fallback）
   - `source=static` 使用 `system/data/market_cap_snapshots.json`
   - 适合回测与离线验证，MVP 已验证

2. **付费 API-specific 订阅**
   - Gateway: "Click here to subscribe to API-specific market data packages"
   - 前置：US Securities Snapshot and Futures Value Bundle (NP)
   - 推荐：US Equity and Options Add-On Streaming Bundle (NP)

3. **Polygon / 其他数据源**
   - 可作为未来扩展

## 参考资料

- [IB TWS API - Market Data](https://interactivebrokers.github.io/tws-api/market_data.html)
- [IB Tick Types](https://interactivebrokers.github.io/tws-api/tick_types.html)
- [Error 10089](https://www.interactivebrokers.com/en/trading/error-codes.php)
