# TICKET_0013: News Digest Capability

**Status:** done  
**Created:** 2026-03-14  
**Completed:** 2026-03-14  
**Source Task:** TASK_0019 (Daily research routine), TASK_0004 (News digest)  
**Blocking Issue:** `missing_tool`

---

## Resolution

实现 get_news_digest 工具，使用 yfinance 获取 Yahoo Finance 新闻。
- 支持按 symbol 查询，缺省 SPY
- 支持 date_range、max_articles、include_sentiment
- 输出 query、summary、articles、by_symbol
- 修改: impl, contract, registry, test_get_news_digest.py

---

## Blocking Issue

每日研究流程需要获取新闻摘要，但系统当前没有新闻数据工具。

当前可用工具：
- ✅ `get_market_bars_batch` - 市场数据
- ❌ `get_news_digest` - **缺失**

## Requested Capability

提供新闻获取和摘要工具，支持：
1. 按 symbol 获取新闻
2. 按 sector/theme 获取新闻
3. 生成新闻摘要
4. 情感分析（可选）

## Implementation Specification

### Create get_news_digest Tool

```yaml
name: get_news_digest
description: 获取新闻并生成摘要
inputs:
  symbols:
    type: array[string]
    required: false
    description: 标的列表
  sectors:
    type: array[string]
    required: false
    description: 行业列表
  themes:
    type: array[string]
    required: false
    description: 主题（如 earnings, M&A）
  date_range:
    type: string
    required: false
    default: "1d"
    enum: ["1d", "3d", "7d", "30d"]
    description: 时间范围
  max_articles:
    type: integer
    required: false
    default: 10
    description: 最大文章数
  include_sentiment:
    type: boolean
    required: false
    default: false
    description: 是否包含情感分析

output:
  type: object
  properties:
    success: { type: boolean }
    digest:
      type: object
      properties:
        query:
          type: object
          properties:
            symbols: { type: array }
            date_range: { type: string }
            total_articles: { type: integer }
        summary:
          type: string
          description: AI 生成的新闻摘要
        articles:
          type: array
          items:
            type: object
            properties:
              title: { type: string }
              source: { type: string }
              published_at: { type: string }
              url: { type: string }
              symbols: { type: array }
              summary: { type: string }
              sentiment: { type: string }  # positive/negative/neutral
        by_symbol:
          type: object
          description: symbol -> articles mapping
    errors: { type: array }
```

## Data Sources

**Options:**
1. **Yahoo Finance News** - 通过 yfinance (free)
2. **NewsAPI** - 需要 API key
3. **Polygon.io** - 需要 API key
4. **Bing News / Google News** - 需要 API key

**Recommended:** Yahoo Finance via yfinance (already used for market data)

## Example Output

```json
{
  "success": true,
  "digest": {
    "query": {
      "symbols": ["AAPL", "NVDA"],
      "date_range": "1d",
      "total_articles": 5
    },
    "summary": "AAPL 发布新产品，NVDA 宣布 AI 芯片进展，整体 tech sector 正面",
    "articles": [
      {
        "title": "Apple announces new AI features",
        "source": "TechCrunch",
        "published_at": "2026-03-14T10:00:00Z",
        "symbols": ["AAPL"],
        "summary": "Apple unveiled new AI capabilities...",
        "sentiment": "positive"
      },
      {
        "title": "NVIDIA chips power new data centers",
        "source": "Reuters",
        "published_at": "2026-03-14T09:30:00Z",
        "symbols": ["NVDA"],
        "summary": "NVIDIA's latest chips...",
        "sentiment": "positive"
      }
    ],
    "by_symbol": {
      "AAPL": [...],
      "NVDA": [...]
    }
  }
}
```

## Acceptance Criteria

1. [x] `get_news_digest` 工具可用
2. [x] 支持按 symbol 查询新闻
3. [x] 支持时间范围筛选
4. [x] 生成新闻摘要
5. [x] 按 symbol 分组返回
6. [x] 结构化 JSON 输出

## Related Tasks

- TASK_0019: Daily research routine (blocked by this)
- TASK_0004: News digest (blocked by this)
- TASK_0005: News-price correlation (blocked by this)

## Implementation Notes

**Using yfinance for news:**
```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
news = ticker.news  # Returns recent news articles
```

**News Article Structure:**
```python
{
    "title": str,
    "publisher": str,
    "published_at": str,  # ISO timestamp
    "summary": str,
    "url": str,
    "related_symbols": list[str]
}
```

**Implementation Files:**
- `system/tools/impl/get_news_digest.py`
- `system/tools/contracts/get_news_digest.yaml`
- `system/tools/tests/test_get_news_digest.py`
