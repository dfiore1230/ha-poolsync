from __future__ import annotations

from typing import Any


def _g(d: dict, *path, default=None):
    cur: Any = d
    for p in path:
        if isinstance(cur, dict):
            if p not in cur:
                return default
            cur = cur[p]
            continue
        if isinstance(cur, list):
            try:
                idx = int(p)
            except (TypeError, ValueError):
                return default
            if idx < 0 or idx >= len(cur):
                return default
            cur = cur[idx]
            continue
        return default
    return cur
