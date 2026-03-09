from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from arbiter.agent.market_overview import run_market_overview


def run_market_scan() -> Dict[str, Any]:
    """Execute a minimal market scan using the data assistant stack.

    This serves as an OpenClaw-compatible task entrypoint:
    - Uses Arbiter's default universe via run_market_overview.
    - Produces a structured summary that can be logged or forwarded.
    """
    generated_at = datetime.now(tz=timezone.utc).isoformat()
    overview = run_market_overview()

    universe_summary: List[Dict[str, Any]] = overview.get("universe_summary", [])
    news_summary: Dict[str, List[str]] = overview.get("news_summary", {})

    # 主要指数（从 universe_summary 中筛选）
    major_indices = {"SPY", "QQQ", "DIA", "IWM"}
    major_index_status = [
        entry
        for entry in universe_summary
        if entry.get("symbol") in major_indices
    ]

    # 有最近新闻的标的
    symbols_with_news = [
        symbol for symbol, headlines in news_summary.items() if headlines
    ]

    # 最近刷新过行情数据的标的（有 latest_bar_timestamp 的）
    recently_refreshed = [
        entry["symbol"]
        for entry in universe_summary
        if entry.get("latest_bar_timestamp")
    ]

    text_lines: List[str] = []
    text_lines.append(f"Market scan generated at {generated_at}.")
    if major_index_status:
        idx_symbols = ", ".join(e["symbol"] for e in major_index_status)
        text_lines.append(f"Major indices in universe: {idx_symbols}.")
    if symbols_with_news:
        text_lines.append(
            f"Symbols with recent headlines: {', '.join(symbols_with_news[:10])}."
        )
    if recently_refreshed:
        text_lines.append(
            f"Symbols with recently refreshed market data: {', '.join(recently_refreshed[:10])}."
        )

    summary = {
        "generated_at": generated_at,
        "timeframe": overview.get("timeframe"),
        "symbols": overview.get("symbols"),
        "universe_summary": universe_summary,
        "news_summary": news_summary,
        "major_index_status": major_index_status,
        "symbols_with_recent_news": symbols_with_news,
        "recently_refreshed_symbols": recently_refreshed,
        "text_summary": " ".join(text_lines),
    }
    return summary


def main() -> None:
    """CLI entrypoint for running a single market scan.

    Usage:
        python -m arbiter.openclaw.market_scan_task
    """
    result = run_market_scan()

    # 写入最新扫描结果文件
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = logs_dir / f"market_scan_{ts}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 同时打印到 stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

