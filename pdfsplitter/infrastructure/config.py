"""Config Service - 配置管理与持久化."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "recent_files": [],
    "last_paper": "A4",
    "last_paper_category": "ISO216",
    "last_margin_mm": 10.0,
    "last_overlap_mm": 5.0,
    "cut_lines_enabled": False,
    "page_numbers_enabled": False,
    "default_dpi": 150,
    "window_geometry": None,
    "language": "zh_CN",
    "version": 1,
}


@dataclass
class ConfigService:
    """应用配置服务.

    负责配置的读取、写入与版本迁移.
    配置存储在 settings.json 中.
    """

    config_path: Path = field(default_factory=lambda: Path("settings.json"))
    _data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.load()

    def load(self) -> None:
        """从文件加载配置."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.info("ConfigService: loaded from %s", self.config_path)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("ConfigService: failed to load config: %s", e)
                self._data = dict(DEFAULT_SETTINGS)
        else:
            self._data = dict(DEFAULT_SETTINGS)
            logger.info("ConfigService: no config file, using defaults")

        self._migrate()

    def save(self) -> None:
        """保存配置到文件."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            logger.info("ConfigService: saved to %s", self.config_path)
        except OSError as e:
            logger.error("ConfigService: failed to save config: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值.

        Args:
            key: 配置键.
            default: 默认值.

        Returns:
            配置值.
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值.

        Args:
            key: 配置键.
            value: 配置值.
        """
        self._data[key] = value

    def _migrate(self) -> None:
        """配置版本迁移."""
        version = self._data.get("version", 0)
        if version < 1:
            self._data["version"] = 1
            logger.info("ConfigService: migrated config to version 1")
