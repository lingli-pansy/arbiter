from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from dataclasses import dataclass
from typing import Iterable, List, Optional

from arbiter.protocols.market import MarketBar


@dataclass(slots=True)
class RefreshState:
    symbol: str
    timeframe: str
    last_bar_timestamp: datetime
    last_refresh_at: datetime
    source: str
    total_rows: int


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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_refresh_state (
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    last_bar_timestamp TEXT NOT NULL,
                    last_refresh_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    total_rows INTEGER NOT NULL,
                    PRIMARY KEY (symbol, timeframe)
                )
                """
            )

    def write_bars(self, bars: Iterable[MarketBar]) -> int:
        """将一组 `MarketBar` 写入本地存储。

        已存在的记录会被自动忽略（按 symbol/timeframe/timestamp 去重）。
        返回实际插入的记录数。
        """
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
            return 0

        with self._get_conn() as conn:
            before = conn.total_changes
            conn.executemany(
                """
                INSERT OR IGNORE INTO market_bars (
                    symbol, timestamp, timeframe,
                    open, high, low, close,
                    volume, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            after = conn.total_changes

        return after - before

    def append_bars(self, bars: Iterable[MarketBar]) -> int:
        """仅追加新 `MarketBar`，跳过已存在记录。

        语义上等同于 `write_bars`，单独暴露便于调用方表达“append 模式”。
        """
        return self.write_bars(bars)

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

    def get_last_bar_timestamp(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[datetime]:
        """获取指定 symbol/timeframe 的最新一条 K 线时间戳。"""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT MAX(timestamp) FROM market_bars
                WHERE symbol = ? AND timeframe = ?
                """,
                (symbol, timeframe),
            ).fetchone()

        if not row or row[0] is None:
            return None
        return datetime.fromisoformat(row[0])

    def get_total_rows(self, symbol: str, timeframe: str) -> int:
        """获取指定 symbol/timeframe 在 store 中的总行数。"""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) FROM market_bars
                WHERE symbol = ? AND timeframe = ?
                """,
                (symbol, timeframe),
            ).fetchone()

        return int(row[0]) if row and row[0] is not None else 0

    def update_refresh_state(
        self,
        symbol: str,
        timeframe: str,
        last_bar_timestamp: datetime,
        last_refresh_at: datetime,
        source: str,
        total_rows: int,
    ) -> None:
        """更新或创建指定 symbol/timeframe 的 refresh metadata。"""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO market_refresh_state (
                    symbol, timeframe,
                    last_bar_timestamp, last_refresh_at,
                    source, total_rows
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, timeframe) DO UPDATE SET
                    last_bar_timestamp = excluded.last_bar_timestamp,
                    last_refresh_at = excluded.last_refresh_at,
                    source = excluded.source,
                    total_rows = excluded.total_rows
                """,
                (
                    symbol,
                    timeframe,
                    last_bar_timestamp.isoformat(),
                    last_refresh_at.isoformat(),
                    source,
                    total_rows,
                ),
            )

    def get_refresh_state(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[RefreshState]:
        """查询指定 symbol/timeframe 的 refresh metadata。"""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT last_bar_timestamp,
                       last_refresh_at,
                       source,
                       total_rows
                FROM market_refresh_state
                WHERE symbol = ? AND timeframe = ?
                """,
                (symbol, timeframe),
            ).fetchone()

        if not row:
            return None

        last_bar_ts_s, last_refresh_at_s, source, total_rows = row
        return RefreshState(
            symbol=symbol,
            timeframe=timeframe,
            last_bar_timestamp=datetime.fromisoformat(last_bar_ts_s),
            last_refresh_at=datetime.fromisoformat(last_refresh_at_s),
            source=source,
            total_rows=int(total_rows),
        )


