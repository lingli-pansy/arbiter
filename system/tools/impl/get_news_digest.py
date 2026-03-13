#!/usr/bin/env python3
"""
get_news_digest: 获取新闻并生成摘要。
契约: system/tools/contracts/get_news_digest.yaml
输入: JSON 从 stdin 或第一个命令行参数读取。
输出: JSON 写入 stdout。
使用 yfinance 获取 Yahoo Finance 新闻。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_impl_dir = Path(__file__).resolve().parent

DATE_RANGE_DAYS = {"1d": 1, "3d": 3, "7d": 7, "30d": 30}
SENTIMENT_KEYWORDS_POS = ("surge", "gain", "rise", "beat", "growth", "upgrade", "bullish", "record", "strong")
SENTIMENT_KEYWORDS_NEG = ("fall", "drop", "decline", "miss", "cut", "downgrade", "bearish", "weak", "loss")


def _parse_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"_error": f"Invalid JSON: {e}"}


def _simple_sentiment(text: str) -> str:
    """简单关键词情感分析"""
    if not text:
        return "neutral"
    t = text.lower()
    pos = sum(1 for k in SENTIMENT_KEYWORDS_POS if k in t)
    neg = sum(1 for k in SENTIMENT_KEYWORDS_NEG if k in t)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def _ts_to_iso(ts: int | None) -> str:
    if ts is None:
        return ""
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return str(ts) if ts else ""


def _fetch_news(symbols: list[str], max_articles: int) -> list[dict]:
    """通过 yfinance 获取多标的新闻，去重合并"""
    try:
        import yfinance as yf
    except ImportError:
        return []

    seen_urls: set[str] = set()
    all_articles: list[dict] = []

    for sym in (symbols or [])[:10]:
        try:
            ticker = yf.Ticker(sym)
            raw = ticker.news
            if not isinstance(raw, list):
                continue
            for item in raw:
                if not isinstance(item, dict):
                    continue
                url = item.get("link") or item.get("url") or ""
                if url and url in seen_urls:
                    continue
                seen_urls.add(url or str(id(item)))
                title = item.get("title") or ""
                publisher = item.get("publisher") or item.get("source") or item.get("provider") or ""
                summary = item.get("summary") or item.get("description") or title
                ts = item.get("providerPublishTime") or item.get("published_at") or item.get("timestamp")
                related = item.get("relatedTickers") or item.get("related_symbols") or [sym]
                if sym not in related:
                    related = [sym] + [r for r in related if r != sym]
                all_articles.append({
                    "title": title,
                    "source": publisher,
                    "published_at": _ts_to_iso(ts),
                    "url": url,
                    "symbols": [str(r) for r in related[:5]],
                    "summary": summary[:500] if summary else "",
                    "_raw": item,
                })
                if len(all_articles) >= max_articles:
                    break
        except Exception:
            continue
        if len(all_articles) >= max_articles:
            break

    return all_articles[:max_articles]


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    params = _parse_input(raw)
    if "_error" in params:
        out = {"success": False, "digest": {}, "errors": [params["_error"]]}
        print(json.dumps(out, ensure_ascii=False, default=str))
        sys.exit(1)

    symbols = params.get("symbols") or []
    if not isinstance(symbols, list):
        symbols = []
    symbols = [str(s).strip() for s in symbols if s][:10]
    if not symbols:
        symbols = ["SPY"]

    date_range = str(params.get("date_range", "1d"))
    max_articles = int(params.get("max_articles", 10))
    include_sentiment = params.get("include_sentiment", False)

    articles = _fetch_news(symbols, max_articles)

    for a in articles:
        a["sentiment"] = _simple_sentiment((a.get("summary") or "") + " " + (a.get("title") or "")) if include_sentiment else "neutral"
        a.pop("_raw", None)

    by_symbol: dict[str, list] = {s: [] for s in symbols}
    for a in articles:
        for sym in a.get("symbols", []):
            if sym in by_symbol:
                by_symbol[sym].append(a)
                break
        if not any(s in a.get("symbols", []) for s in symbols):
            by_symbol[symbols[0]].append(a)

    summary_parts = []
    for a in articles[:5]:
        t = a.get("title") or ""
        if t:
            summary_parts.append(t[:80] + ("..." if len(t) > 80 else ""))
    summary = "；".join(summary_parts) if summary_parts else "暂无新闻摘要"

    digest = {
        "query": {
            "symbols": symbols,
            "date_range": date_range,
            "total_articles": len(articles),
        },
        "summary": summary,
        "articles": articles,
        "by_symbol": by_symbol,
    }

    out = {"success": True, "digest": digest, "errors": []}
    print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
