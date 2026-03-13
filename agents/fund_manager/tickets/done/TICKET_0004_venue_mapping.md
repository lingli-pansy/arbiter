# TICKET_0004: Venue Mapping for Bar Type Generation

**Status:** done  
**Created:** 2026-03-13  
**Source Task:** TASK_0001B (Market data source alignment)  
**Blocking Issue:** `missing_tool`  
**Priority:** P1

---

## Blocking Issue

NautilusTrader BarType 格式为 `{symbol}.{venue}-{timeframe}-LAST`，需要 symbol → venue 映射能力。系统无此工具。

## Requested Capability

提供 symbol 到交易所 venue 的映射，用于 BarType 生成。

## Implementation Summary

- **工具:** `get_symbol_venue`
- **契约:** system/tools/contracts/get_symbol_venue.yaml
- **实现:** system/tools/impl/get_symbol_venue.py + adapters/venue_resolver.py
- **数据:** 内置 NASDAQ/NYSE 常见标的映射表，可扩展
- **测试:** system/tools/tests/test_get_symbol_venue.py

## Acceptance Criteria

- [x] 工具在 registry.yaml 中注册，status = active
- [x] 输入 symbols 数组，输出 symbol → venue 映射
- [x] 支持 NASDAQ、NYSE 等主流美股市所
- [x] 未知标的回退到默认 venue（NASDAQ）
- [x] 包含至少一个测试用例
