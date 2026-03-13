"""
最小测试：验证 get_market_bars_batch 输出符合契约（TICKET_0001）。
- 输入验证：非法参数返回 success=false 与 errors。
- 输出结构：合法请求返回 success、data、errors、meta，且 data[symbol] 为 OHLCV 数组。
"""
import json
import subprocess
import sys
from pathlib import Path

# 实现脚本与 tests 平级在 system/tools 下
IMPL_DIR = Path(__file__).resolve().parent.parent / "impl"
SCRIPT = IMPL_DIR / "get_market_bars_batch.py"


def _run(args: list[str], stdin: str | None = None) -> tuple[int, dict]:
    cmd = [sys.executable, str(SCRIPT)] + args
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=IMPL_DIR, input=stdin)
    out = {}
    if r.stdout:
        try:
            out = json.loads(r.stdout)
        except json.JSONDecodeError:
            out = {"_raw": r.stdout, "_stderr": r.stderr}
    return r.returncode, out


def test_validation_invalid_json():
    """输入非 JSON 时应返回错误."""
    code, out = _run([], stdin="not json")
    assert code != 0
    assert out.get("success") is False
    assert "errors" in out and len(out["errors"]) >= 1


def test_validation_symbols_too_many():
    """symbols 超过 10 个应返回验证错误."""
    payload = {"symbols": [f"S{i}" for i in range(15)], "lookback_days": 5}
    code, out = _run([json.dumps(payload)])
    assert code != 0 or out.get("success") is False
    errs = out.get("errors", [])
    assert any("symbols" in (e.get("error") or "").lower() or "1 and 10" in (e.get("error") or "") for e in errs)


def test_validation_lookback_out_of_range():
    """lookback_days 越界应返回验证错误."""
    payload = {"symbols": ["AAPL"], "lookback_days": 300}
    code, out = _run([json.dumps(payload)])
    assert code != 0 or out.get("success") is False
    errs = out.get("errors", [])
    assert any("lookback" in (e.get("error") or "").lower() or "252" in (e.get("error") or "") for e in errs)


def test_contract_output_structure():
    """合法请求（TICKET_0001 Test Case）返回结构符合契约."""
    payload = {
        "symbols": ["AAPL", "MSFT"],
        "lookback_days": 20,
        "timeframe": "1d",
    }
    code, out = _run([json.dumps(payload)])
    assert "success" in out
    assert "data" in out and isinstance(out["data"], dict)
    assert "errors" in out and isinstance(out["errors"], list)
    assert "meta" in out and isinstance(out["meta"], dict)
    assert out["meta"].get("requested_symbols") == 2
    assert out["meta"].get("timeframe") == "1d"
    assert out["meta"].get("source") == "yahoo"
    assert "latency_ms" in out["meta"]
    assert "data_quality_score" in out["meta"]
    if out.get("success") and out.get("data"):
        for sym, bars in out["data"].items():
            assert isinstance(bars, list)
            for bar in bars[:1]:  # 至少检查第一条
                assert "timestamp" in bar and "open" in bar and "high" in bar and "low" in bar and "close" in bar and "volume" in bar
                assert isinstance(bar["volume"], int)


def test_source_param_ib():
    """source=ib 时 meta.source 为 ib，且包含 latency_ms、data_quality_score（TICKET_20250314_001）."""
    payload = {"symbols": ["SPY", "QQQ"], "lookback_days": 20, "timeframe": "1d", "source": "ib"}
    code, out = _run([json.dumps(payload)])
    assert "meta" in out
    assert out["meta"].get("source") == "ib"
    assert "latency_ms" in out["meta"]
    assert out["meta"]["latency_ms"] < 10000  # 10s 内完成
    assert "data_quality_score" in out["meta"]


def test_backward_compat_provider():
    """provider（已弃用）作为 source 别名仍可用."""
    payload = {"symbols": ["SPY"], "lookback_days": 20, "timeframe": "1d", "provider": "yahoo"}
    code, out = _run([json.dumps(payload)])
    assert "meta" in out
    assert out["meta"].get("source") == "yahoo"
