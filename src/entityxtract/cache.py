"""
Global LLM response cache (exact-match, not semantic).

Caches OpenRouter / OpenAI-compatible chat completion calls via LangChain's
global LLM cache. The cache key is derived from the full serialized prompt
(including multimodal parts) and the model's llm_string (model name,
temperature, model_kwargs, base URL, etc.), so only bit-for-bit identical
requests hit the cache.

Configuration (all via .env / environment variables):
    LLM_CACHE_ENABLED          -- "true"/"false" (default: "false")
    LLM_CACHE_BACKEND          -- "sqlite" | "memory"  (default: "sqlite")
    LLM_CACHE_PATH             -- sqlite db path (default: ".cache/llm_cache.db")
    LLM_CACHE_MAX_SIZE_MB      -- max db size in MB before auto-clear (default: 500)
    LLM_CACHE_HIT_THRESHOLD_S  -- invoke() wall-time (s) under which we treat
                                  a call as a cache hit (default: 0.5)
"""

import os
import threading
from pathlib import Path
from typing import Optional

from .config import get_config
from .logging_config import get_logger

logger = get_logger(__name__)

_initialized = False
_enabled = False
_backend: Optional[str] = None
_db_path: Optional[str] = None
_max_size_bytes: Optional[int] = None
_hit_threshold_s: float = 0.5

# Serializes destructive operations on the cache DB (size-limit eviction and
# manual clear) so that concurrent workers in `extract_objects()` don't race
# on check→delete→reinstall.
_cache_lock = threading.Lock()


def _env_bool(key: str, default: bool = False) -> bool:
    val = get_config(key)
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")


def _install_sqlite_cache(path: str) -> None:
    from langchain_core.globals import set_llm_cache
    from langchain_community.cache import SQLiteCache

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    set_llm_cache(SQLiteCache(database_path=path))


def setup_cache() -> None:
    """Configure the global LangChain LLM cache based on env vars.

    Idempotent: safe to call multiple times; only the first call does work.
    """
    global _initialized, _enabled, _backend, _db_path, _max_size_bytes, _hit_threshold_s
    if _initialized:
        return
    _initialized = True

    _enabled = _env_bool("LLM_CACHE_ENABLED", default=False)
    if not _enabled:
        logger.info("LLM cache disabled (set LLM_CACHE_ENABLED=true to enable).")
        return

    _backend = (get_config("LLM_CACHE_BACKEND") or "sqlite").strip().lower()

    try:
        _hit_threshold_s = float(get_config("LLM_CACHE_HIT_THRESHOLD_S") or 0.5)
    except (TypeError, ValueError):
        _hit_threshold_s = 0.5

    try:
        max_mb = float(get_config("LLM_CACHE_MAX_SIZE_MB") or 500)
    except (TypeError, ValueError):
        max_mb = 500.0
    _max_size_bytes = int(max_mb * 1024 * 1024)

    if _backend == "sqlite":
        _db_path = get_config("LLM_CACHE_PATH") or ".cache/llm_cache.db"
        _install_sqlite_cache(_db_path)
        logger.info(
            f"LLM cache enabled: SQLite at '{_db_path}' "
            f"(max {max_mb:.0f} MB, hit-threshold {_hit_threshold_s}s)"
        )
    elif _backend == "memory":
        from langchain_core.globals import set_llm_cache
        from langchain_core.caches import InMemoryCache

        set_llm_cache(InMemoryCache())
        logger.info(
            f"LLM cache enabled: in-memory (hit-threshold {_hit_threshold_s}s)"
        )
    else:
        logger.warning(
            f"Unknown LLM_CACHE_BACKEND='{_backend}'; LLM cache NOT enabled."
        )
        _enabled = False


def is_cache_enabled() -> bool:
    """Return True if the LLM cache has been successfully initialized."""
    return _enabled


def get_hit_threshold_s() -> float:
    """Wall-clock threshold (seconds) below which an invoke() is treated as a cache hit."""
    return _hit_threshold_s


def enforce_cache_size_limit() -> None:
    """If the SQLite cache DB exceeds the configured size, delete and recreate it.

    Cheap to call (one stat syscall on the fast path). No-op for non-sqlite
    backends or when caching is disabled. The destructive path (delete +
    reinstall) is serialized via `_cache_lock` so concurrent workers from
    `extract_objects()` don't race.

    Note: on POSIX systems, `os.remove()` is safe even if another thread has
    an open SQLAlchemy connection to the DB — the inode survives until the
    last FD is closed. On Windows this could fail; not addressed here.
    """
    if not _enabled or _backend != "sqlite" or not _db_path or not _max_size_bytes:
        return
    try:
        if not os.path.exists(_db_path):
            return
        # Fast path: if we're under the limit, don't bother taking the lock.
        if os.path.getsize(_db_path) <= _max_size_bytes:
            return

        with _cache_lock:
            # Re-check under the lock; another thread may have already evicted.
            if not os.path.exists(_db_path):
                return
            size = os.path.getsize(_db_path)
            if size <= _max_size_bytes:
                return
            logger.warning(
                f"LLM cache size {size / (1024 * 1024):.1f} MB exceeds limit "
                f"{_max_size_bytes / (1024 * 1024):.0f} MB; clearing '{_db_path}'."
            )
            try:
                os.remove(_db_path)
            except OSError as e:
                logger.warning(f"Failed to remove cache db '{_db_path}': {e}")
                return
            # Re-install a fresh SQLiteCache so subsequent calls keep working.
            _install_sqlite_cache(_db_path)
    except Exception as e:
        logger.warning(f"Error enforcing cache size limit: {e}")


def clear_cache() -> None:
    """Manually clear the cache (useful for tests / scripts). Thread-safe."""
    if not _enabled:
        return
    with _cache_lock:
        if _backend == "sqlite" and _db_path and os.path.exists(_db_path):
            try:
                os.remove(_db_path)
                _install_sqlite_cache(_db_path)
                logger.info(f"LLM cache cleared: '{_db_path}'")
            except OSError as e:
                logger.warning(f"Failed to clear cache db: {e}")
        elif _backend == "memory":
            from langchain_core.globals import set_llm_cache
            from langchain_core.caches import InMemoryCache

            set_llm_cache(InMemoryCache())
            logger.info("LLM in-memory cache cleared.")
