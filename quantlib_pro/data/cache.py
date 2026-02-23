"""
Redis-backed cache layer with in-memory L1 and file-based L3.

Tier layout:
  L1 – process-local dict  (sub-millisecond)
  L2 – Redis               (1–5 ms)
  L3 – Parquet files       (10–50 ms)
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd

log = logging.getLogger(__name__)

_L1: dict[str, dict] = {}           # {key: {"data": ..., "expires": float}}
_CACHE_DIR = os.path.join("cache", "parquet")


# ------------------------------------------------------------------ L1 memory


def l1_get(key: str) -> Optional[Any]:
    entry = _L1.get(key)
    if entry is None:
        return None
    if time.time() > entry["expires"]:
        del _L1[key]
        return None
    return entry["data"]


def l1_set(key: str, data: Any, ttl_seconds: int = 3600) -> None:
    _L1[key] = {"data": data, "expires": time.time() + ttl_seconds}


def l1_delete(key: str) -> None:
    _L1.pop(key, None)


def l1_clear() -> None:
    _L1.clear()


# ------------------------------------------------------------------ L2 redis


def l2_get(redis_client: Any, key: str) -> Optional[pd.DataFrame]:
    """Return a DataFrame from Redis or None if missing/error."""
    if redis_client is None:
        return None
    try:
        raw = redis_client.get(f"qlp:{key}")
        if raw is None:
            return None
        return pd.read_json(raw)
    except Exception as exc:
        log.warning("Redis GET failed for %s: %s", key, exc)
        return None


def l2_set(redis_client: Any, key: str, df: pd.DataFrame, ttl_seconds: int = 3600) -> None:
    """Write a DataFrame to Redis; swallow errors so cache is always non-critical."""
    if redis_client is None:
        return
    try:
        redis_client.setex(f"qlp:{key}", ttl_seconds, df.to_json())
    except Exception as exc:
        log.warning("Redis SET failed for %s: %s", key, exc)


def l2_delete(redis_client: Any, key: str) -> None:
    if redis_client is None:
        return
    try:
        redis_client.delete(f"qlp:{key}")
    except Exception:
        pass


# ------------------------------------------------------------------ L3 file


def _l3_path(key: str) -> str:
    safe_key = key.replace(":", "_").replace("/", "_")
    return os.path.join(_CACHE_DIR, f"{safe_key}.parquet")


def l3_get(key: str, max_age_hours: int = 24) -> Optional[pd.DataFrame]:
    path = _l3_path(key)
    if not os.path.exists(path):
        return None
    age_hours = (time.time() - os.path.getmtime(path)) / 3600
    if age_hours > max_age_hours:
        return None
    try:
        return pd.read_parquet(path)
    except Exception as exc:
        log.warning("Parquet read failed for %s: %s", key, exc)
        return None


def l3_set(key: str, df: pd.DataFrame) -> None:
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        df.to_parquet(_l3_path(key), index=True)
    except Exception as exc:
        log.warning("Parquet write failed for %s: %s", key, exc)


# ------------------------------------------------------------------ unified


def get_dataframe(
    key: str,
    redis_client: Any = None,
    max_age_hours: int = 24,
) -> tuple[Optional[pd.DataFrame], str]:
    """
    Try L1 → L2 → L3.  Returns (DataFrame | None, source_label).
    """
    # L1
    data = l1_get(key)
    if data is not None:
        return data, "memory_cache"

    # L2
    df = l2_get(redis_client, key)
    if df is not None and not df.empty:
        l1_set(key, df)
        return df, "redis_cache"

    # L3
    df = l3_get(key, max_age_hours=max_age_hours)
    if df is not None and not df.empty:
        l2_set(redis_client, key, df)
        l1_set(key, df)
        return df, "file_cache"

    return None, "miss"


def set_dataframe(
    key: str,
    df: pd.DataFrame,
    redis_client: Any = None,
    ttl_seconds: int = 3600,
) -> None:
    """Write a DataFrame to all cache tiers."""
    l1_set(key, df, ttl_seconds=ttl_seconds)
    l2_set(redis_client, key, df, ttl_seconds=ttl_seconds)
    l3_set(key, df)
