"""PdfSplitter image source tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pdfsplitter.application.repository import RepositoryRouter
from pdfsplitter.domain.document.document import Document
from pdfsplitter.domain.document.page import Page
from pdfsplitter.domain.export.export_config import ExportConfig, ExportFormat
from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.layout.layout_engine import LayoutEngine
from pdfsplitter.domain.layout.split_lines import SplitLines
from pdfsplitter.domain.layout.tile_order import TileOrder
from pdfsplitter.infrastructure.image_repository import ImageRepository
from pdfsplitter.infrastructure.mupdf_repository import MuPDFRepository
from pdfsplitter.infrastructure.pdf_splitter import PdfSplitter

_RESOURCES = Path(__file__).resolve().parent.parent.parent / "resources"
_READY_PNG = _RESOURCES / "images" / "ready.png"
_SAMPLE_PNG = _RESOURCES / "images" / "sample.png"


def _has_test_images() -> bool:
    return _READY_PNG.exists() and _SAMPLE_PNG.exists()


def _make_doc_single(path: Path) -> Document:
    repo = ImageRepository()
    return repo.load(path)


def _make_doc_multi(paths: list[Path]) -> Document:
    router = RepositoryRouter([MuPDFRepository(), ImageRepository()])
    return router.load_multiple(paths)


class TestResolveSourcePath:
    """_resolve_source_path 测试."""

    def test_returns_document_path_when_source_paths_empty(self) -> None:
        doc = Document(path=Path("a.pdf"), pages=())
        result = PdfSplitter._resolve_source_path(doc, 0)
        assert result == Path("a.pdf")

    def test_returns_per_page_path_when_source_paths_match(self) -> None:
        doc = Document(
            path=Path("img1.png"),
            pages=(Page(0, Rect(0, 0, 100, 100)), Page(1, Rect(0, 0, 100, 100))),
            source_paths=(Path("img1.png"), Path("img2.png")),
        )
        assert PdfSplitter._resolve_source_path(doc, 0) == Path("img1.png")
        assert PdfSplitter._resolve_source_path(doc, 1) == Path("img2.png")

    def test_falls_back_when_source_paths_count_mismatches(self) -> None:
        doc = Document(
            path=Path("a.pdf"),
            pages=(Page(0, Rect(0, 0, 100, 100)), Page(1, Rect(0, 0, 100, 100))),
            source_paths=(Path("img1.png"),),
        )
        assert PdfSplitter._resolve_source_path(doc, 1) == Path("a.pdf")


class TestResolveLocalPageIndex:
    """_resolve_local_page_index 测试."""

    def test_returns_page_index_when_source_paths_empty(self) -> None:
        doc = Document(path=Path("a.pdf"), pages=(Page(0, Rect(0, 0, 100, 100)),))
        assert PdfSplitter._resolve_local_page_index(doc, 0) == 0

    def test_returns_local_index_with_1to1_mapping(self) -> None:
        if not _has_test_images():
            pytest.skip("test images not found")
        doc = _make_doc_multi([_READY_PNG, _SAMPLE_PNG])
        assert PdfSplitter._resolve_local_page_index(doc, 0) == 0
        assert PdfSplitter._resolve_local_page_index(doc, 1) == 0
        assert doc.source_paths == (_READY_PNG, _SAMPLE_PNG)


class TestSplitWithImage:
    """split / split_all 对图片源的处理."""

    def test_split_single_image(self) -> None:
        if not _has_test_images():
            pytest.skip("test images not found")
        doc = _make_doc_single(_READY_PNG)
        sl = SplitLines.halved_horizontal(doc.pages[0].height)
        order = TileOrder.auto(sl.tile_count)
        engine = LayoutEngine()
        grid = engine.calculate_from_lines(doc.pages[0].size, sl)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            out_path = Path(f.name)
        try:
            config = ExportConfig(format=ExportFormat.PDF_SINGLE, output_path=out_path)
            splitter = PdfSplitter()
            result = splitter.split(doc, 0, grid, order, (210.0, 297.0), config)
            assert result.tile_count == 2
            assert len(result.output_paths) == 1
            assert out_path.exists()
            assert out_path.stat().st_size > 0
        finally:
            out_path.unlink(missing_ok=True)

    def test_split_all_single_image(self) -> None:
        if not _has_test_images():
            pytest.skip("test images not found")
        doc = _make_doc_single(_READY_PNG)
        sl = SplitLines.halved_horizontal(doc.pages[0].height)
        order = TileOrder.auto(sl.tile_count)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            out_path = Path(f.name)
        try:
            config = ExportConfig(format=ExportFormat.PDF_SINGLE, output_path=out_path)
            splitter = PdfSplitter()
            result = splitter.split_all(doc, [(0, sl, order)], (210.0, 297.0), config)
            assert result.tile_count == 2
            assert out_path.stat().st_size > 0
        finally:
            out_path.unlink(missing_ok=True)

    def test_split_all_two_images(self) -> None:
        """多图片导出: 验证 source_paths 映射和每页独立处理."""
        if not _has_test_images():
            pytest.skip("test images not found")
        doc = _make_doc_multi([_READY_PNG, _SAMPLE_PNG])
        sl0 = SplitLines.halved_vertical(doc.pages[0].width)
        sl1 = SplitLines.halved_horizontal(doc.pages[1].height)
        order0 = TileOrder.auto(sl0.tile_count)
        order1 = TileOrder.auto(sl1.tile_count)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            out_path = Path(f.name)
        try:
            config = ExportConfig(format=ExportFormat.PDF_SINGLE, output_path=out_path)
            splitter = PdfSplitter()
            result = splitter.split_all(
                doc, [(0, sl0, order0), (1, sl1, order1)],
                (210.0, 297.0), config,
            )
            assert result.tile_count == 4  # 2 from each
            assert out_path.stat().st_size > 0
        finally:
            out_path.unlink(missing_ok=True)

    def test_split_single_image_with_cut_lines(self) -> None:
        if not _has_test_images():
            pytest.skip("test images not found")
        doc = _make_doc_single(_READY_PNG)
        sl = SplitLines.halved_horizontal(doc.pages[0].height)
        order = TileOrder.auto(sl.tile_count)
        engine = LayoutEngine()
        grid = engine.calculate_from_lines(doc.pages[0].size, sl)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            out_path = Path(f.name)
        try:
            config = ExportConfig(
                format=ExportFormat.PDF_SINGLE,
                output_path=out_path,
                cut_lines=True,
            )
            splitter = PdfSplitter()
            result = splitter.split(doc, 0, grid, order, (210.0, 297.0), config)
            assert result.tile_count == 2
            assert out_path.stat().st_size > 0
        finally:
            out_path.unlink(missing_ok=True)
