"""Infrastructure layer tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from pdfsplitter.infrastructure.config import ConfigService


class TestConfigService:
    """ConfigService 测试套件."""

    def test_defaults(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            f.write(b"{}")
            tmp_path = Path(f.name)
        try:
            cfg = ConfigService(config_path=tmp_path)
            assert cfg.get("version") == 1
            assert cfg.get("nonexistent", "default") == "default"
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_set_and_get(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            f.write(b"{}")
            tmp_path = Path(f.name)
        try:
            cfg = ConfigService(config_path=tmp_path)
            cfg.set("test_key", "test_value")
            assert cfg.get("test_key") == "test_value"
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_save_and_load(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = Path(f.name)
        try:
            cfg = ConfigService(config_path=tmp_path)
            cfg.set("saved_key", 42)
            cfg.save()

            cfg2 = ConfigService(config_path=tmp_path)
            assert cfg2.get("saved_key") == 42
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_missing_file_uses_defaults(self) -> None:
        cfg = ConfigService(config_path=Path("nonexistent_file.json"))
        assert cfg.get("version") == 1

    def test_corrupted_file_falls_back(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("this is not json")
            tmp_path = Path(f.name)
        try:
            cfg = ConfigService(config_path=tmp_path)
            assert cfg.get("version") == 1
        finally:
            tmp_path.unlink(missing_ok=True)
