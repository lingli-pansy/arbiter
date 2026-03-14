"""最小测试：验证 get_market_cap_ranking 符合契约。TICKET_20250314_BACKTEST_001"""
import json
import subprocess
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parent.parent / "impl"
SCRIPT = IMPL_DIR / "get_market_cap_ranking.py"


def _run(args: list[str]) -> tuple[int, dict]:
    cmd = [sys.executable, str(SCRIPT)] + args
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=IMPL_DIR)
    out = {}
    if r.stdout:
        try:
            out = json.loads(r.stdout)
        except json.JSONDecodeError:
            out = {"_raw": r.stdout}
    return r.returncode, out


def test_contract_output():
    """合法 date 返回 ranking 符合契约."""
    inp = {"date": "2024-03-31", "top_n": 5}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    ranking = out.get("ranking", [])
    assert len(ranking) <= 5
    for r in ranking:
        assert "rank" in r
        assert "symbol" in r
        assert "market_cap" in r
        assert "market_cap_millions" in r


def test_top_n():
    """top_n 参数生效."""
    inp = {"date": "2024-06-30", "top_n": 3}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    assert len(out.get("ranking", [])) <= 3


def test_static_source():
    """source=static 返回预存市值排名。TICKET_20250314_001_FOLLOWUP_005"""
    inp = {"date": "2024-03-31", "top_n": 5, "source": "static"}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    ranking = out.get("ranking", [])
    assert len(ranking) >= 1
    assert out.get("source") == "static"


def test_mock_mode_meta():
    """mock_mode 返回 meta 含 latency_ms。TICKET_20250314_003"""
    inp = {"date": "2024-01-02", "top_n": 5, "mock_mode": True}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    meta = out.get("meta", {})
    assert "latency_ms" in meta
    assert isinstance(meta["latency_ms"], (int, float))


def test_static_source():
    """source=static 返回预存市值排名。TICKET_20250314_001_FOLLOWUP_005"""
    inp = {"date": "2024-03-31", "top_n": 5, "source": "static"}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    assert out.get("source") == "static"
    ranking = out.get("ranking", [])
    assert len(ranking) >= 1
    for r in ranking:
        assert "symbol" in r and "market_cap" in r


def test_static_source():
    """source=static 从预存快照获取市值。TICKET_20250314_001_FOLLOWUP_005"""
    inp = {"date": "2024-03-31", "top_n": 5, "source": "static"}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    assert out.get("source") == "static"
    ranking = out.get("ranking", [])
    assert len(ranking) >= 1
    for r in ranking:
        assert "symbol" in r and "market_cap" in r


def test_static_source():
    """source=static 从预存快照返回排名。TICKET_20250314_001_FOLLOWUP_005"""
    inp = {"date": "2024-03-31", "top_n": 5, "source": "static"}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    assert out.get("source") == "static"
    ranking = out.get("ranking", [])
    assert len(ranking) >= 1
    for r in ranking:
        assert "rank" in r and "symbol" in r and "market_cap" in r


def test_static_source():
    """source=static 从预存快照获取市值。TICKET_20250314_001_FOLLOWUP_005"""
    inp = {"date": "2024-03-31", "top_n": 5, "source": "static"}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    assert out.get("source") == "static"
    ranking = out.get("ranking", [])
    assert len(ranking) >= 1


def test_static_source():
    """source=static 从预存快照返回市值排名。TICKET_20250314_001_FOLLOWUP_005"""
    inp = {"date": "2024-03-31", "top_n": 5, "source": "static"}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    assert out.get("source") == "static"
    ranking = out.get("ranking", [])
    assert len(ranking) >= 1
    for r in ranking:
        assert "symbol" in r and "market_cap" in r


def test_static_source():
    """source=static 返回预存市值排名。TICKET_20250314_001_FOLLOWUP_005"""
    inp = {"date": "2024-03-31", "top_n": 5, "source": "static"}
    code, out = _run([json.dumps(inp)])
    assert out.get("success") is True
    assert out.get("source") == "static"
    ranking = out.get("ranking", [])
    assert len(ranking) >= 1
