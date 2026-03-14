"""
Static Fundamental 适配器：从预存 JSON 获取市值。TICKET_20250314_001_FOLLOWUP_005 方案4
用于回测，无需外部 API。
"""
from __future__ import annotations

import json
from pathlib import Path

# adapters->impl; impl.parent.parent = system; system/data
_IMPL = Path(__file__).resolve().parent.parent
_DATA_DIR = _IMPL.parent.parent / "data"
_SNAPSHOTS_FILE = _DATA_DIR / "market_cap_snapshots.json"


def get_ranking_from_static(
    date_str: str,
    universe: list[str] | None,
    top_n: int,
    min_mcap: float | None,
) -> tuple[list[dict], list[str]]:
    """
    从 market_cap_snapshots.json 获取指定日期的市值排名。
    若无精确日期，取最近的历史快照。
    Returns: (ranking, errors)
    """
    syms = universe or [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "JPM", "V", "UNH",
        "JNJ", "XOM", "PG", "HD", "MA", "DIS", "BAC", "WMT", "CVX", "PEP",
    ]
    errors: list[str] = []
    if not _SNAPSHOTS_FILE.exists():
        return [], [f"Static data not found: {_SNAPSHOTS_FILE}"]

    try:
        data = json.loads(_SNAPSHOTS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return [], [f"Failed to load static data: {e}"]

    # 找 date 当天或之前最近的快照
    avail_dates = sorted(d for d in data if isinstance(data[d], dict) and d <= date_str)
    if not avail_dates:
        return [], [f"No snapshot for date <= {date_str}"]

    snapshot_date = avail_dates[-1]
    by_sym: dict[str, float] = data[snapshot_date]

    ranking = []
    for sym in syms:
        mc = by_sym.get(sym) if isinstance(by_sym.get(sym), (int, float)) else None
        if mc is None or mc <= 0:
            continue
        if min_mcap and mc < min_mcap * 1e6:
            continue
        ranking.append({
            "symbol": sym,
            "market_cap": float(mc),
            "market_cap_millions": round(float(mc) / 1e6, 1),
        })
    ranking.sort(key=lambda x: x["market_cap"], reverse=True)
    for i, r in enumerate(ranking[:top_n], 1):
        r["rank"] = i
    return ranking[:top_n], errors
