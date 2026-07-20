"""RepositoryRouter tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdfsplitter.application.repository import RepositoryRouter
from pdfsplitter.domain.document.document import Document
from pdfsplitter.domain.document.page import Page
from pdfsplitter.infrastructure.image_repository import ImageRepository
from pdfsplitter.infrastructure.mupdf_repository import MuPDFRepository

_RESOURCES = Path(__file__).resolve().parent.parent.parent / "resources"
_READY_PNG = _RESOURCES / "images" / "ready.png"
_SAMPLE_PNG = _RESOURCES / "images" / "sample.png"


class TestRepositoryRouter:
    """RepositoryRouter 测试套件."""

    def setup_method(self) -> None:
        self._router = RepositoryRouter([
            MuPDFRepository(),
            ImageRepository(),
        ])

    def test_routes_pdf_to_mupdf(self) -> None:
        assert self._router.supports(Path("test.pdf"))

    def test_routes_image_to_image_repo(self) -> None:
        assert self._router.supports(Path("test.png"))
        assert self._router.supports(Path("test.jpg"))

    def test_rejects_unknown_format(self) -> None:
        assert not self._router.supports(Path("test.gif"))

    def test_load_image_routes_correctly(self) -> None:
        if not _READY_PNG.exists():
            pytest.skip("ready.png not found")
        doc = self._router.load(_READY_PNG)
        assert doc.page_count == 1
        assert doc.path == _READY_PNG
        assert doc.pages[0].width > 0

    def test_load_unsupported_format_raises(self) -> None:
        with pytest.raises(ValueError, match="不支持的文件格式"):
            self._router.load(Path("test.gif"))

    def test_load_multiple_single_file(self) -> None:
        if not _READY_PNG.exists():
            pytest.skip("ready.png not found")
        doc = self._router.load_multiple([_READY_PNG])
        assert doc.page_count == 1
        assert doc.source_paths == (_READY_PNG,)
        assert doc.path == _READY_PNG

    def test_load_multiple_two_images(self) -> None:
        if not _READY_PNG.exists() or not _SAMPLE_PNG.exists():
            pytest.skip("test images not found")
        doc = self._router.load_multiple([_READY_PNG, _SAMPLE_PNG])
        assert doc.page_count == 2
        assert doc.source_paths == (_READY_PNG, _SAMPLE_PNG)
        assert doc.path == _READY_PNG
        assert doc.pages[0].index == 0
        assert doc.pages[1].index == 1

    def test_load_multiple_empty_list_raises(self) -> None:
        with pytest.raises(ValueError, match="文件列表为空"):
            self._router.load_multiple([])

    def test_load_multiple_renumbers_pages_sequentially(self) -> None:
        if not _READY_PNG.exists() or not _SAMPLE_PNG.exists():
            pytest.skip("test images not found")
        doc = self._router.load_multiple([_READY_PNG, _SAMPLE_PNG])
        indices = [p.index for p in doc.pages]
        assert indices == [0, 1]
