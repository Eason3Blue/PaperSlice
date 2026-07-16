"""Export domain tests."""

from __future__ import annotations

from pathlib import Path

from pdfsplitter.domain.export.export_config import ExportConfig, ExportFormat, ExportResult


class TestExportConfig:
    """ExportConfig 测试套件."""

    def test_defaults(self) -> None:
        config = ExportConfig()
        assert config.format == ExportFormat.PDF_SINGLE
        assert str(config.output_path) == "output.pdf"
        assert config.cut_lines is False
        assert config.page_numbers is False

    def test_custom(self) -> None:
        config = ExportConfig(
            format=ExportFormat.PDF_MULTIPLE,
            output_path=Path("/tmp/test.pdf"),
            cut_lines=True,
            page_numbers=True,
        )
        assert config.format == ExportFormat.PDF_MULTIPLE
        assert config.cut_lines is True
        assert config.page_numbers is True

    def test_immutable(self) -> None:
        config = ExportConfig()
        with pytest.raises(Exception):
            config.cut_lines = True  # type: ignore[misc]


class TestExportResult:
    """ExportResult 测试套件."""

    def test_creation(self) -> None:
        paths = (Path("a.pdf"), Path("b.pdf"))
        result = ExportResult(output_paths=paths, tile_count=2)
        assert result.output_paths == paths
        assert result.tile_count == 2

    def test_immutable(self) -> None:
        result = ExportResult(output_paths=(Path("a.pdf"),), tile_count=1)
        with pytest.raises(Exception):
            result.tile_count = 5  # type: ignore[misc]


import pytest
