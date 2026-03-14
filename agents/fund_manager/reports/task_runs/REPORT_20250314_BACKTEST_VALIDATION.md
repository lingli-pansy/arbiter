# REPORT_20250314_BACKTEST_VALIDATION.md

## 任务描述
验证回测能力：执行市值轮动策略（2024-01-01 至 2025-01-01，每季度调仓，美股市值 Top 5 等金额投资，对比纳斯达克）。

## 状态
**BLOCKED** - 能力缺口，已开 ticket

## Tools Used

| 工具 | 用途 | 结果 |
|------|------|------|
| `registry.yaml` | 查看可用工具清单 | ✅ 已扫描 21 个工具 |
| `run_backtest` contract | 检查回测策略支持 | ⚠️ 仅支持技术指标策略，无市值轮动 |
| `get_market_bars_batch` contract | 检查市场数据能力 | ✅ OHLCV 数据可用 |
| `simulate_rebalance` contract | 检查调仓模拟能力 | ⚠️ 单次调仓，无周期循环 |
| `calculate_portfolio_performance` contract | 检查基准对比能力 | ✅ 支持 QQQ 对比 |

## Key Findings

### 1. 现有能力可复用部分
- **市场数据**: `get_market_bars_batch` 可获取历史价格
- **基准对比**: `calculate_portfolio_performance` 支持 `benchmark: "QQQ"`，可生成阿尔法/贝塔/跟踪误差
- **组合管理**: `create_portfolio` 支持初始资金和持仓管理

### 2. 缺失的关键能力
| 缺口 | 影响 | 紧迫性 |
|------|------|--------|
| 市值数据获取 | 无法确定每季度买哪 5 只股票 | P0 |
| 市值轮动策略 | `run_backtest` 不支持基本面选股策略 | P0 |
| 多周期回测框架 | 无法自动执行 4 次季度调仓 | P1 |

### 3. 策略复杂度评估
这个需求比表面看起来更复杂：
- 需要**历史市值数据**（雅虎财经 fundamentals 或 Polygon.io）
- 需要**动态选股逻辑**（每季度重新计算排名）
- 需要**资金池管理**（50万投资 + 5万池子多退少补）
- 需要**换仓执行**（卖出旧持仓 + 买入新 Top 5）

现有 `run_backtest` 框架假设策略是固定的（如 EMA 金叉），不支持这种调仓日重新选股的逻辑。

## Remaining Gaps

1. **短期（本 ticket）**:
   - 市值数据接口
   - 轮动回测引擎
   - 季度调仓循环

2. **中期（后续优化）**:
   - 处理退市/停牌股票
   - 滑点与交易成本模型
   - 资金池不足时的降级策略

3. **长期（策略扩展）**:
   - 支持其他轮动因子（如 PE、ROE）
   - 多市场支持（A股、港股）
   - 动态权重（非等金额）

## Next Action

1. **Cursor 实现** `TICKET_20250314_BACKTEST_001`:
   - 工具: `get_market_cap_ranking`
   - 工具: `run_market_cap_rotation_backtest`

2. **实现完成后**，我将重新执行验证:
   - 运行完整回测
   - 对比 QQQ 买入持有收益
   - 检查每次调仓记录合理性
   - 生成验收报告

## 参考数据

**用户指定参数**:
- 回测周期: 2024-01-01 至 2025-01-01
- 初始本金: $500,000
- 流动资金池: $50,000
- 调仓频率: 每季度
- 选股数量: 市值 Top 5
- 配置方式: 等金额
- 对比基准: 纳斯达克 (QQQ)

**预期对比结果（待验证）**:
- QQQ 在 2024 年收益约 +28%
- 市值轮动策略理论上应接近或略逊于 QQQ（因大盘股集中度高）

---

**Created**: 2026-03-14  
**Ticket**: TICKET_20250314_BACKTEST_001.md  
**Status**: 等待实现
