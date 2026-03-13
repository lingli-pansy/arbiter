# Strategy Memo: 20-Day Momentum Strategy

**Task ID:** TASK_0007  
**Generated:** 2026-03-14  
**Status:** Complete

---

## 1. Strategy Description

### Core Hypothesis
20日动量策略基于以下假设：近期（过去20个交易日）表现强势的股票在短期内会继续跑赢大盘，体现价格动量效应。

### Rationale
- 行为金融学：投资者反应不足导致趋势延续
- 机构调仓滞后：大资金调仓需要时间，形成趋势惯性
- 信息扩散：利好消息逐步被市场消化

---

## 2. Strategy Rules

### 2.1 Universe Selection
- **Symbols:** AAPL, NVDA, TSLA
- **Asset Class:** 美股大盘股
- **Liquidity:** 日均成交额 > 10亿美元（三者均满足）

### 2.2 Signal Generation

#### Entry Signal (Long)
```
条件1: 20日收益率 > 0
条件2: 20日收益率在Universe中排名前1（即最高）
条件3: 当前无持仓该Symbol

Action: 买入信号触发
```

#### Exit Signal
```
条件1: 持有某Symbol但已不再满足Entry Signal
条件2: 或20日收益率由正转负

Action: 卖出信号触发
```

### 2.3 Position Sizing
- **Method:** 等权重配置
- **Max Positions:** 1（每次只持有表现最强的1只）
- **Cash Buffer:** 0%（全仓轮动）

### 2.4 Rebalance Frequency
- **Frequency:** 每日收盘后计算信号
- **Execution:** 次日开盘执行调仓
- **Timing:** EOD signal → next open execution

---

## 3. Backtest Requirements

### Required Data
- OHLCV bars for AAPL, NVDA, TSLA
- Period: 至少2年历史数据
- Resolution: Daily

### Metrics to Track
- Total Return
- Annualized Return
- Max Drawdown
- Sharpe Ratio
- Win Rate
- Number of Trades
- Average Holding Period

### Benchmark
- SPY (S&P 500 ETF)

---

## 4. Risk Controls

### Position Level
- 单一标的最大仓位：100%（策略本身就是集中持仓）

### Portfolio Level
- 无杠杆
- 全仓投资，不留现金

### Circuit Breakers
- 单日跌幅 > 5% 时暂停新开仓（待实现）
- 连续3次调仓亏损时触发策略审查（待实现）

---

## 5. Implementation Notes

### Pros
- 逻辑简单，易于理解和实现
- 调仓频率低，交易成本低
- 标的流动性充足，冲击成本小

### Cons
- 集中度高，单一标的风险
- 动量崩溃时回撤可能较大
- 未考虑基本面因素

### Future Enhancements
1. 加入波动率过滤（VIX > 25 时降低仓位）
2. 多时间框架确认（周线趋势过滤）
3. 动态仓位（根据波动率调整）
4. 加入止损逻辑

---

## 6. Next Steps

1. **Run Backtest** - 使用 `run_backtest` 工具验证策略历史表现
2. **Analyze Results** - 检查关键指标是否达到预期
3. **Iterate** - 根据回测结果调整参数或逻辑
4. **Paper Trade** - 通过模拟执行验证滑点和执行成本

---

**Strategy Definition Complete**  
Ready for backtest execution (TASK_0008 or similar).
