"""Async persistence helper to prevent UI blocking on database calls."""
from __future__ import annotations

import logging
import threading
from typing import Any
from alerts.persistent_kv import kv_get, kv_set

def bg_kv_set(key: str, value: Any) -> None:
    """Run kv_set in a background thread."""
    def _task():
        try:
            kv_set(key, value)
        except Exception:
            logging.exception(f"Background kv_set failed for {key}")
            
    threading.Thread(target=_task, daemon=True).start()

def get_persisted_value(key: str, default: Any = None) -> Any:
    """Safe wrapper for kv_get."""
    return kv_get(key, default)
