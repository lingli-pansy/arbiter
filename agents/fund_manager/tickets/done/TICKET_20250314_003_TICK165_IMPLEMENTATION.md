# TICKET_20250314_003_TICK165_IMPLEMENTATION

## Source Task
TASK_20250314_003_IB_MKTDATA_TICK165 - 实现 IB Tick 165 方案获取市值

## Blocking Issue
当前 `ib_fundamental.py` 仅实现 `reqFundamentalData` 方案，该方案在 IB Paper Trading 账户返回错误 10358（Fundamental Data 不可用）。

任务003要求实现 **IB Generic Tick 165** 方案作为替代，但当前代码库中**完全缺失**该实现。

## Requested Capability
实现 `get_market_cap_ranking` 的 IB Tick 165 数据源支持，使 Paper Trading 账户能够获取市值数据。

### 技术规格

#### IB Tick 165 背景
- Tick Type: 165 = Miscellaneous Stats
- API: `ib.reqMktData(contract, genericTickList='165')`
- 返回字段: 包含市值 (marketCap)、PE、EPS 等统计数据

#### 实现文件
1. **修改**: `system/tools/impl/adapters/ib_fundamental.py`
   - 添加 `get_market_caps_tick165()` 函数
   
2. **修改**: `system/tools/impl/get_market_cap_ranking.py`
   - 在 source="ib" 逻辑中优先尝试 Tick 165
   - Tick 165 失败时回退到 reqFundamentalData（Live 账户）

### 建议实现代码

```python
# system/tools/impl/adapters/ib_fundamental.py

def get_market_caps_tick165(
    symbols: list[str],
    host: str,
    port: int,
    client_id: int,
    timeout_sec: float = 10.0,
) -> tuple[dict[str, float], list[str]]:
    """
    通过 IB Generic Tick 165 获取市值。
    Tick 165 = Miscellaneous Stats，包含 marketCap 字段。
    
    Returns: ({symbol: market_cap}, [errors])
    """
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass
    from ib_insync import IB, Stock

    ib = IB()
    result: dict[str, float] = {}
    errors: list[str] = []
    tickers: list = []
    
    try:
        ib.connect(host, port, clientId=client_id, timeout=5.0)
        
        # 批量请求 Tick 165
        for sym in symbols:
            try:
                contract = Stock(sym, "SMART", "USD")
                ticker = ib.reqMktData(contract, genericTickList='165')
                tickers.append((sym, ticker))
            except Exception as e:
                errors.append(f"{sym}: reqMktData failed - {e}")
        
        # 等待数据返回（轮询方式）
        poll_interval = 0.1
        max_polls = int(timeout_sec / poll_interval)
        
        for _ in range(max_polls):
            ib.sleep(poll_interval)
            pending = []
            for sym, ticker in tickers:
                if sym in result:
                    continue
                # Tick 165 市值字段名需确认，可能是以下之一:
                # - ticker.marketCap
                # - ticker.mktCap
                # - ticker.lastMarketCap
                # - ticker.info.get('marketCap')
                mcap = getattr(ticker, 'marketCap', None)
                if mcap is None:
                    mcap = getattr(ticker, 'mktCap', None)
                if mcap is None and hasattr(ticker, 'info'):
                    mcap = ticker.info.get('marketCap')
                
                if mcap and float(mcap) > 0:
                    result[sym] = float(mcap)
                else:
                    pending.append((sym, ticker))
            
            tickers = pending
            if not tickers:
                break
        
        # 记录超时未返回的数据
        for sym, _ in tickers:
            errors.append(f"{sym}: timeout waiting for tick 165 data")
            
    except Exception as e:
        errors.append(f"IB connection: {e}")
    finally:
        # 取消所有市场数据订阅
        for _, ticker in tickers:
            try:
                ib.cancelMktData(ticker)
            except:
                pass
        try:
            ib.disconnect()
        except:
            pass
    
    return result, errors
```

### 修改 get_market_cap_ranking.py 的建议

```python
def _get_ranking_ib(
    symbols: list[str],
    connection_id: str | None,
    top_n: int,
    min_mcap: float | None,
) -> tuple[list[dict], list[str]]:
    """通过 IB 获取市值排名。优先尝试 Tick 165，失败后回退到 Fundamental Data。"""
    import os
    _impl = os.path.dirname(os.path.abspath(__file__))
    if _impl not in __import__("sys").path:
        __import__("sys").path.insert(0, _impl)
    from adapters.ib_fundamental import get_market_caps_tick165, get_market_caps
    from adapters.broker_store import get_connection, get_latest_ib_connection
    
    conn = get_connection(connection_id) if connection_id else None
    if not conn:
        conn = get_latest_ib_connection()
    if not conn:
        return [], ["connection_id required when source=ib; call connect_broker first"]
    
    host = conn.get("host", "127.0.0.1")
    port = int(conn.get("port", 4002))
    client_id = int(conn.get("client_id", 1))
    
    # 优先尝试 Tick 165 (Paper Trading 兼容)
    sym_to_mcap, errs = get_market_caps_tick165(symbols, host, port, client_id)
    
    # 如果 Tick 165 失败或数据不足，尝试 Fundamental Data
    if len(sym_to_mcap) < len(symbols):
        missing = [s for s in symbols if s not in sym_to_mcap]
        fd_mcap, fd_errs = get_market_caps(missing, host, port, client_id)
        sym_to_mcap.update(fd_mcap)
        errs.extend([f"[fd] {e}" for e in fd_errs])
    
    ranking = []
    for sym, mc in sym_to_mcap.items():
        if min_mcap and mc < min_mcap * 1e6:
            continue
        ranking.append({
            "symbol": sym,
            "market_cap": mc,
            "market_cap_millions": round(mc / 1e6, 1)
        })
    
    ranking.sort(key=lambda x: x["market_cap"], reverse=True)
    for i, r in enumerate(ranking[:top_n], 1):
        r["rank"] = i
    return ranking[:top_n], errs
```

## Why Existing Tools Are Insufficient

| 现有方案 | 问题 |
|---------|------|
| `reqFundamentalData` | IB Paper Trading 返回错误 10358，完全不可用 |
| Yahoo Finance | 需要外部 API，不符合 MVP 架构（应优先 IB） |
| Static 数据 | 仅用于测试，无法获取实时/历史市值 |
| Mock 模式 | 仅用于开发测试，非真实数据 |

**Tick 165 是唯一能在 Paper Trading 环境下获取真实市值的 IB 原生方案。**

## Input Contract
沿用现有 `get_market_cap_ranking` 契约：
```yaml
input:
  date: string          # YYYY-MM-DD
  top_n: integer        # 默认 5
  source: "ib"          # 启用 Tick 165 实现
  connection_id: string # 可选，复用已有 IB 连接
```

## Output Contract
沿用现有契约，新增 `meta.tick165_attempted` 标记：
```yaml
output:
  success: boolean
  ranking: array
  source: "ib"          # 实际使用 IB
  errors: array
  meta:
    latency_ms: number
    tick165_attempted: boolean   # 新增：是否尝试了 Tick 165
    tick165_success: boolean     # 新增：Tick 165 是否成功
```

## Acceptance Criteria

### 必需
- [ ] `get_market_caps_tick165()` 函数实现并可通过 IB Paper 获取市值
- [ ] 能成功获取 AAPL, MSFT, NVDA, AMZN, GOOGL 的市值数据
- [ ] 延迟 < 15 秒获取 20 只股票市值
- [ ] source="ib" 时优先使用 Tick 165 方案
- [ ] Tick 165 失败时回退到 Fundamental Data（不报错给上层）
- [ ] Paper Trading 账户可正常使用，不再返回 10358 错误

### 期望
- [ ] 延迟 < 8 秒获取 20 只股票市值
- [ ] 数据准确性：与 Yahoo 市值差异 < 3%
- [ ] 支持复用已有 IB 连接（不重复创建）

## Test Case

```bash
# 测试 Tick 165 方案
cd /Users/xiaoyu/arbiter-2/system/tools/impl

# 1. 确保 IB 连接可用
echo '{"broker": "ib", "mode": "paper"}' | \
  /Users/xiaoyu/arbiter-2/.venv/bin/python3 connect_broker.py

# 2. 测试市值排名 (source=ib，应自动使用 Tick 165)
echo '{"date": "2024-01-02", "top_n": 5, "source": "ib"}' | \
  /Users/xiaoyu/arbiter-2/.venv/bin/python3 get_market_cap_ranking.py

# 期望输出:
{
  "success": true,
  "ranking": [
    {"rank": 1, "symbol": "AAPL", "market_cap": 3000000000000, "market_cap_millions": 3000000},
    {"rank": 2, "symbol": "MSFT", "market_cap": 2800000000000, "market_cap_millions": 2800000},
    ...
  ],
  "source": "ib",
  "errors": [],
  "meta": {
    "latency_ms": 8000,
    "tick165_attempted": true,
    "tick165_success": true
  }
}
```

## Implementation Notes

### Tick 165 字段调研
需要确认 IB Tick 165 的确切字段名：
```python
# 调试用代码：打印 ticker 所有属性
ticker = ib.reqMktData(contract, genericTickList='165')
ib.sleep(2)
print([attr for attr in dir(ticker) if not attr.startswith('_')])
print(ticker.__dict__ if hasattr(ticker, '__dict__') else 'no __dict__')
```

### 并发优化（可选）
如果 20 只股票串行请求太慢，可考虑：
- 批量请求后统一等待
- 使用 `ib.pendingTickersEvent` 异步回调

### 参考资料
- ib_insync docs: https://ib-insync.readthedocs.io/
- IB API Tick Types: https://interactivebrokers.github.io/tws-api/tick_types.html

## Related
- Source Task: TASK_20250314_003_IB_MKTDATA_TICK165
- Parent Ticket: TICKET_20250314_001_FOLLOWUP_005
- Blocked By: 无（这是实现类 ticket）
- Blocks: TASK_20250314_001_IB_MARKET_CAP_ARCH_FIX 验收

## Priority
P0 - 阻塞市值轮动回测在 Paper 环境下的验收

## Status
Done - 2026-03-14 由 Cursor 实现

## Created
2026-03-14

## Assigned To
Cursor (实现方)

## ETA
待确认（预计 2-4 小时实现 + 测试）
