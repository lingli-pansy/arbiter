# TICKET_20250314_BACKTEST_001_ARCH_FIX

## Source Task
VALIDATION_20250314_BACKTEST_001 - 市值轮动回测能力验收

## Blocking Issue
架构合规性问题：`get_market_cap_ranking` 实现使用 Yahoo Finance (yfinance) 获取市值数据，但项目 MVP 阶段已确定数据源为 **NautilusTrader + Interactive Brokers**。

当前实现代码：
```python
# get_market_cap_ranking.py line 24
import yfinance as yf
...
info = t.info  # Yahoo Finance API
mcap = info.get("marketCap") or info.get("enterpriseValue")
```

## Requested Capability
重新实现 `get_market_cap_ranking`，使用 **Interactive Brokers Fundamental Data API** 获取市值数据。

## Why Current Implementation Violates Architecture

根据项目文档 `USER.md` 和 `AGENTS.md`：
> "当前已经确定的底层选型：NautilusTrader 用于回测引擎，IB 用于券商执行"

使用 Yahoo Finance 的问题：
1. **数据一致性**：生产环境使用 IB，研发/回测使用 Yahoo，数据源不一致
2. **合规风险**：Yahoo Finance API 有使用限制，不适合生产级回测
3. **架构偏离**：MVP 明确约束数据源，不应引入额外依赖

## IB Fundamental Data API 参考

IB API 提供以下方式获取市值数据：

```python
from ib_insync import *

# 方法1: 通过 reqFundamentalData 获取财务报表数据
# reportType: "ReportsFinSummary" 包含市值信息

# 方法2: 通过 reqMktData 的 generic tick 获取
# genericTickList="165" (Misc. Stats) 包含市值

# 方法3: 通过 reqContractDetails 获取基本合约信息
```

## Proposed Implementation

### 方案 A: 新增工具 `get_ib_fundamental_data`
```yaml
name: get_ib_fundamental_data
description: 通过 IB 获取股票基本面数据（市值、PE等）
input:
  symbols: array[string]  # 股票代码列表
  field: string          # "market_cap" | "pe_ratio" | "all"
  connection_id: string  # IB 连接ID（从 connect_broker 获取）
output:
  data: object           # symbol -> fundamental data
```

### 方案 B: 修改 `get_market_cap_ranking`
- 添加 `source` 参数，支持 `"ib"` | `"yahoo"`
- 默认 `"ib"` 以符合架构
- 通过 IB 连接获取市值数据

## Acceptance Criteria

1. `get_market_cap_ranking` 支持通过 IB 获取市值数据
2. 默认使用 IB 数据源（符合 MVP 架构）
3. 需要 IB 连接时，工具自动复用已有连接或提示用户先调用 `connect_broker`
4. 输出格式与当前契约兼容（不破坏已有接口）
5. 移除或可选化 yfinance 依赖

## Test Case

```bash
# 1. 先建立 IB 连接
echo '{"broker": "ib", "mode": "paper"}' | python3 connect_broker.py

# 2. 通过 IB 获取市值排名
echo '{"date": "2024-01-02", "top_n": 5, "source": "ib"}' | python3 get_market_cap_ranking.py
```

**Expected Output**:
```json
{
  "success": true,
  "ranking": [
    {"rank": 1, "symbol": "AAPL", "market_cap": 3000000000000, "market_cap_millions": 3000000},
    ...
  ],
  "as_of_date": "2024-01-02",
  "source": "ib",
  "errors": []
}
```

## Impact

- **阻塞**: TICKET_20250314_BACKTEST_001_FOLLOWUP_001 (yfinance 安装) 应该被废弃
- **依赖**: 需要 IB TWS/Gateway 运行才能测试
- **优先级**: P0 - 架构合规性问题

## Related

- Original Ticket: TICKET_20250314_BACKTEST_001
- Validation Report: VALIDATION_20250314_BACKTEST_001.md
- Architecture Decision: USER.md (IB as data source)

## Priority
P0 - 架构合规性阻塞

## Status
Open

## Created
2026-03-14
