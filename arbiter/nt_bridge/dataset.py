from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from arbiter.data.repositories.db import get_session
from arbiter.market_store.queries import get_market_bars
from arbiter.market_store.schema import CanonicalBar


@dataclass(slots=True)
class NtDatasetConfig:
    """
    Minimal configuration for generating an NT-compatible dataset.

    This does not expose any NT internals; it only controls how we
    export canonical bars to disk for later NT consumption.
    """

    output_dir: Path
    symbols: list[str]
    timeframe: str = "1d"
    start: datetime | None = None
    end: datetime | None = None


def _bars_to_csv(path: Path, bars: list[CanonicalBar]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "symbol",
                "venue",
                "timeframe",
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "currency",
                "source",
                "status",
                "version",
                "priority",
                "quality_flag",
            ]
        )
        for b in bars:
            writer.writerow(
                [
                    b.symbol,
                    b.venue,
                    b.timeframe,
                    b.timestamp.isoformat(),
                    b.open,
                    b.high,
                    b.low,
                    b.close,
                    b.volume,
                    b.currency,
                    b.source,
                    b.status,
                    b.version,
                    b.priority,
                    b.quality_flag,
                ]
            )


def prepare_nt_dataset(config: NtDatasetConfig) -> dict:
    """
    Export canonical bars into a simple CSV-based dataset that can be
    ingested by NautilusTrader tooling.

    This function intentionally does not import or depend on NT packages;
    it only prepares files on disk.
    """

    with get_session() as session:
        _do_prepare_dataset(session, config)
    return {"output_dir": str(config.output_dir), "symbols": config.symbols, "timeframe": config.timeframe}


def _do_prepare_dataset(session: Session, config: NtDatasetConfig) -> None:
    if config.end is None:
        end = datetime.utcnow()
    else:
        end = config.end
    if config.start is None:
        start = end.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = config.start

    for symbol in config.symbols:
        bars = get_market_bars(
            session,
            symbol=symbol,
            timeframe=config.timeframe,
            start=start,
            end=end,
        )
        path = config.output_dir / f"{symbol}_{config.timeframe}.csv"
        _bars_to_csv(path, bars)


def run_backtest(config: NtDatasetConfig) -> dict:
    """
    Stub for triggering an NT backtest based on the prepared dataset.

    In this phase, we only ensure the dataset can be created; actual NT
    backtest wiring can be added in a later phase.
    """

    info = prepare_nt_dataset(config)
    # In a real implementation, this is where we would invoke NT's
    # backtest CLI or Python API.
    return {"status": "queued", "dataset": info}


def get_backtest_status(backtest_id: str) -> dict:
    """
    Minimal stub returning a static status. Hook for future expansion.
    """

    return {"backtest_id": backtest_id, "status": "not_implemented"}


def get_backtest_result(backtest_id: str) -> dict:
    """
    Minimal stub returning a static result. Hook for future expansion.
    """

    return {"backtest_id": backtest_id, "result": None}


def main() -> None:
    from arbiter.config.universe import MARKET_SYMBOLS

    out_dir = Path("nt_datasets/default")
    cfg = NtDatasetConfig(output_dir=out_dir, symbols=MARKET_SYMBOLS[:5], timeframe="1d")
    info = prepare_nt_dataset(cfg)
    print("Prepared NT dataset:", info)


if __name__ == "__main__":
    main()

