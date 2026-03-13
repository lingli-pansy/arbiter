#!/usr/bin/env python3
"""get_news_digest 最小测试 (TICKET_0013)"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parents[1] / "impl"
SCRIPT = (IMPL_DIR / "get_news_digest.py").resolve()


def _run(params: dict) -> tuple[int, dict]:
    raw = json.dumps(params)
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=raw.encode(),
        capture_output=True,
        timeout=30,
        cwd=str(IMPL_DIR.resolve()),
    )
    out = json.loads(r.stdout.decode()) if r.stdout else {}
    return r.returncode, out


def test_output_structure() -> None:
    """有效输入应返回符合契约的输出结构"""
    code, out = _run({"symbols": ["AAPL"], "max_articles": 5})
    assert code == 0
    assert out.get("success") is True
    digest = out.get("digest", {})
    assert "query" in digest
    assert "summary" in digest
    assert "articles" in digest
    assert "by_symbol" in digest
    assert digest["query"].get("symbols") == ["AAPL"]
    assert "total_articles" in digest["query"]


def test_default_symbols() -> None:
    """无 symbols 时默认使用 SPY"""
    code, out = _run({})
    assert code == 0
    assert out.get("success") is True
    assert out.get("digest", {}).get("query", {}).get("symbols") == ["SPY"]


def test_include_sentiment() -> None:
    """include_sentiment 时文章含 sentiment 字段"""
    code, out = _run({"symbols": ["AAPL"], "max_articles": 3, "include_sentiment": True})
    assert code == 0
    for a in out.get("digest", {}).get("articles", []):
        assert "sentiment" in a
        assert a["sentiment"] in ("positive", "negative", "neutral")


if __name__ == "__main__":
    test_output_structure()
    test_default_symbols()
    test_include_sentiment()
    print("All tests passed.")
