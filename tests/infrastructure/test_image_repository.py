"""ImageRepository tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdfsplitter.domain.document.document import Document
from pdfsplitter.infrastructure.image_repository import ImageRepository

_RESOURCES = Path(__file__).resolve().parent.parent.parent / "resources"
_READY_PNG = _RESOURCES / "images" / "ready.png"


class TestImageRepository:
    """ImageRepository 测试套件."""

    def setup_method(self) -> None:
        self._repo = ImageRepository()

    def test_supports_image_extensions(self) -> None:
        for ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
            assert self._repo.supports(Path(f"test{ext}"))

    def test_rejects_pdf(self) -> None:
        assert not self._repo.supports(Path("test.pdf"))

    def test_rejects_unknown(self) -> None:
        assert not self._repo.supports(Path("test.gif"))
        assert not self._repo.supports(Path("test.txt"))

    def test_load_image_returns_single_page_document(self) -> None:
        if not _READY_PNG.exists():
            pytest.skip("ready.png not found")
        doc = self._repo.load(_READY_PNG)
        assert isinstance(doc, Document)
        assert doc.page_count == 1
        assert doc.pages[0].index == 0
        assert doc.pages[0].width > 0
        assert doc.pages[0].height > 0
        assert doc.path == _READY_PNG

    def test_load_image_has_empty_source_paths(self) -> None:
        if not _READY_PNG.exists():
            pytest.skip("ready.png not found")
        doc = self._repo.load(_READY_PNG)
        assert doc.source_paths == ()

    def test_load_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            self._repo.load(Path("nonexistent_image.png"))

    def test_load_unsupported_format_raises(self) -> None:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not an image")
            tmp = Path(f.name)
        try:
            with pytest.raises(ValueError, match="不支持的图片格式"):
                self._repo.load(tmp)
        finally:
            tmp.unlink(missing_ok=True)
