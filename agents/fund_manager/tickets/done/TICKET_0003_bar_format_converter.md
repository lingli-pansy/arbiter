# TICKET_0003: Bar Format Converter (current → NT)

**Status:** done  
**Created:** 2026-03-13  
**Source Task:** TASK_0001B (Market data source alignment)  
**Blocking Issue:** `insufficient_output_contract`  
**Priority:** P1

---

## Blocking Issue

get_market_bars_batch 输出为 native 格式（ISO 时间戳、float/int），与 NautilusTrader Bar 格式不兼容。需要 adapter 将 current output 转为 NT 格式。

## Requested Capability

将 get_market_bars_batch 输出转为 NautilusTrader 兼容格式（bar_type, ts_event/ts_init 纳秒，Price/Quantity 字符串）。

## Implementation Summary

- **工具:** `convert_bars_to_nt`
- **契约:** system/tools/contracts/convert_bars_to_nt.yaml
- **实现:** system/tools/impl/convert_bars_to_nt.py（adapter pattern，不修改 get_market_bars_batch）
- **依赖:** get_symbol_venue（venue 映射）或可选 venue_map 入参
- **测试:** system/tools/tests/test_convert_bars_to_nt.py

## Acceptance Criteria

- [x] 工具在 registry.yaml 中注册，status = active
- [x] 输入接受 get_market_bars_batch 完整输出
- [x] 输出 NT 格式：bar_type, open/high/low/close/volume 为字符串，ts_event/ts_init 纳秒
- [x] 支持可选 venue_map；缺省时使用内置 venue 解析
- [x] 时间戳 ISO → 纳秒转换正确
- [x] 包含至少一个测试用例
