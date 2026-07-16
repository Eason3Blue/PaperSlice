"""Logging configuration - 统一日志配置."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_dir: str | Path = "logs",
    level: int = logging.INFO,
    console_enabled: bool = True,
    file_enabled: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """配置全局日志系统.

    Args:
        log_dir: 日志目录.
        level: 日志级别.
        console_enabled: 是否启用控制台输出.
        file_enabled: 是否启用文件输出.
        max_bytes: 日志文件最大大小.
        backup_count: 保留的历史日志文件数.
    """
    root = logging.getLogger()
    root.setLevel(level)

    if root.handlers:
        root.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    if console_enabled:
        try:
            from rich.logging import RichHandler

            rich_handler = RichHandler(
                rich_tracebacks=True,
                show_time=True,
                show_path=False,
            )
            rich_handler.setLevel(level)
            root.addHandler(rich_handler)
        except ImportError:
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(level)
            console.setFormatter(fmt)
            root.addHandler(console)

    if file_enabled:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path / "pdfsplitter.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)

    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("fitz").setLevel(logging.WARNING)

    root.info("Logging configured: level=%s", logging.getLevelName(level))
