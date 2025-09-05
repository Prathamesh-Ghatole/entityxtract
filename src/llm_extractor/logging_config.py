"""
Centralized logging configuration for llm_extractor.

Features:
- Console + rotating file handlers
- Configurable via environment variables:
    LLM_EXTRACTOR_LOG_LEVEL       (e.g., DEBUG, INFO, WARNING)
    LLM_EXTRACTOR_CONSOLE_LEVEL   (overrides console handler level)
    LLM_EXTRACTOR_FILE_LEVEL      (overrides file handler level)
    LLM_EXTRACTOR_LOG_DIR         (directory for log files; defaults to <CWD>/logs)
    LLM_EXTRACTOR_LOG_FILE        (filename; defaults to llm_extractor.log)
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union

_LOGGING_CONFIGURED = False


def _parse_level(value: Optional[Union[str, int]], default: int = logging.INFO) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    try:
        return getattr(logging, str(value).strip().upper())
    except Exception:
        return default


def _default_log_dir() -> Path:
    env_dir = os.environ.get("LLM_EXTRACTOR_LOG_DIR")
    if env_dir:
        return Path(env_dir)
    # Default to current working directory /logs
    return Path.cwd() / "logs"


def setup_logging(
    level: Optional[Union[int, str]] = None,
    console_level: Optional[Union[int, str]] = None,
    file_level: Optional[Union[int, str]] = None,
    log_file: Optional[Union[str, os.PathLike]] = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """
    Initialize root logging with console + rotating file handlers.

    Calling setup_logging() multiple times is safe; handlers will only be added once.
    Levels can be controlled via params or environment variables listed in module docstring.
    """
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    root = logging.getLogger()

    # Resolve levels (env overrides are supported)
    env_level = os.environ.get("LLM_EXTRACTOR_LOG_LEVEL")
    env_console = os.environ.get("LLM_EXTRACTOR_CONSOLE_LEVEL")
    env_file = os.environ.get("LLM_EXTRACTOR_FILE_LEVEL")

    root_level = _parse_level(level or env_level or logging.INFO)
    c_level = _parse_level(console_level or env_console or root_level)
    f_level = _parse_level(file_level or env_file or root_level)

    root.setLevel(root_level)

    # Console handler
    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_handler.setLevel(c_level)
    console_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(console_handler)

    # File handler (rotating)
    try:
        log_dir = _default_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        log_path = Path(log_file) if log_file else log_dir / os.environ.get(
            "LLM_EXTRACTOR_LOG_FILE", "llm_extractor.log"
        )

        file_handler = RotatingFileHandler(
            log_path, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(f_level)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(process)d - %(threadName)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        root.addHandler(file_handler)
    except Exception:
        # If file setup fails, fall back to console-only and record the failure.
        root.exception("Failed to set up file logging handler; continuing with console only.")

    _LOGGING_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
