from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Iterable, List

from arbiter.protocols.market import MarketBar


class MarketStore:
    """使用 SQLite 的最小本地市场数据存储。

    仅针对 `MarketBar`，提供写入与按时间区间查询能力。
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_schema(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_bars (
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    source TEXT NOT NULL,
                    PRIMARY KEY (symbol, timestamp, timeframe)
                )
                """
            )

    def write_bars(self, bars: Iterable[MarketBar]) -> None:
        """将一组 `MarketBar` 写入本地存储。"""
        records = [
            (
                b.symbol,
                b.timestamp.isoformat(),
                b.timeframe,
                b.open,
                b.high,
                b.low,
                b.close,
                b.volume,
                b.source,
            )
            for b in bars
        ]
        if not records:
            return

        with self._get_conn() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO market_bars (
                    symbol, timestamp, timeframe,
                    open, high, low, close,
                    volume, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )

    def read_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> List[MarketBar]:
        """按 symbol/timeframe 和时间区间读取 `MarketBar` 列表。"""
        start_s = start.isoformat()
        end_s = end.isoformat()

        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT symbol, timestamp, timeframe,
                       open, high, low, close,
                       volume, source
                FROM market_bars
                WHERE symbol = ?
                  AND timeframe = ?
                  AND timestamp >= ?
                  AND timestamp <= ?
                ORDER BY timestamp ASC
                """,
                (symbol, timeframe, start_s, end_s),
            ).fetchall()

        bars: List[MarketBar] = []
        for (
            sym,
            ts_s,
            tf,
            open_,
            high,
            low,
            close,
            volume,
            source,
        ) in rows:
            ts = datetime.fromisoformat(ts_s)
            bars.append(
                MarketBar(
                    symbol=sym,
                    timestamp=ts,
                    timeframe=tf,
                    open=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    source=source,
                )
            )
        return bars

