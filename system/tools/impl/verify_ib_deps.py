#!/usr/bin/env python3
"""
验证 IB 连接所需依赖 (ib_insync, nest_asyncio)。
TICKET_20260314_006
Usage: python verify_ib_deps.py
Exit: 0 on success, 1 on failure.
"""
from __future__ import annotations

import sys


def main() -> int:
    errors = []
    # nest_asyncio must be applied before ib_insync (eventkit needs event loop)
    try:
        import nest_asyncio
        nest_asyncio.apply()
        print("nest_asyncio: installed")
    except ImportError as e:
        errors.append(f"nest_asyncio: {e}")
        # Cannot import ib_insync without nest_asyncio in some environments
        if errors:
            for err in errors:
                print(f"FAIL: {err}", file=sys.stderr)
            return 1

    try:
        import ib_insync
        print(f"ib_insync: {ib_insync.__version__}")
    except ImportError as e:
        errors.append(f"ib_insync: {e}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
