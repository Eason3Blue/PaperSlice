from __future__ import annotations

from pathlib import Path

import pytest

from pdfsplitter.domain.document.document import Document
from pdfsplitter.domain.document.page import Page
from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.geometry.size import Size


class TestPage:
    """Page 领域对象测试套件."""

    def test_creation(self) -> None:
        media = Rect(0, 0, 612, 792)
        page = Page(index=0, media_box=media)
        assert page.index == 0
        assert page.media_box == media

    def test_effective_rect_defaults_to_media_box(self) -> None:
        media = Rect(0, 0, 612, 792)
        page = Page(index=0, media_box=media)
        assert page.effective_rect == media

    def test_effective_rect_uses_crop_box(self) -> None:
        media = Rect(0, 0, 612, 792)
        crop = Rect(36, 36, 576, 756)
        page = Page(index=0, media_box=media, crop_box=crop)
        assert page.effective_rect == crop

    def test_width(self) -> None:
        page = Page(index=0, media_box=Rect(0, 0, 612, 792))
        assert page.width == 612

    def test_height(self) -> None:
        page = Page(index=0, media_box=Rect(0, 0, 612, 792))
        assert page.height == 792

    def test_size(self) -> None:
        page = Page(index=0, media_box=Rect(0, 0, 612, 792))
        assert page.size == Size(612, 792)

    def test_is_portrait(self) -> None:
        page = Page(index=0, media_box=Rect(0, 0, 612, 792))
        assert page.is_portrait is True

    def test_is_landscape(self) -> None:
        page = Page(index=0, media_box=Rect(0, 0, 792, 612))
        assert page.is_landscape is True

    def test_immutable(self) -> None:
        page = Page(index=0, media_box=Rect(0, 0, 612, 792))
        with pytest.raises(Exception):
            page.index = 1  # type: ignore[misc]

    def test_default_dpi(self) -> None:
        page = Page(index=0, media_box=Rect(0, 0, 612, 792))
        assert page.dpi == 72

    def test_repr(self) -> None:
        page = Page(index=3, media_box=Rect(0, 0, 612, 792))
        assert "index=3" in repr(page)
        assert "612" in repr(page)


class TestDocument:
    """Document 领域对象测试套件."""

    def test_creation(self) -> None:
        doc = Document(path=Path("test.pdf"))
        assert doc.path == Path("test.pdf")
        assert doc.page_count == 0

    def test_with_pages(self) -> None:
        p1 = Page(index=0, media_box=Rect(0, 0, 612, 792))
        p2 = Page(index=1, media_box=Rect(0, 0, 612, 792))
        doc = Document(path=Path("test.pdf"), pages=(p1, p2))
        assert doc.page_count == 2

    def test_iteration(self) -> None:
        p1 = Page(index=0, media_box=Rect(0, 0, 612, 792))
        p2 = Page(index=1, media_box=Rect(0, 0, 612, 792))
        doc = Document(path=Path("test.pdf"), pages=(p1, p2))
        pages = list(doc)
        assert len(pages) == 2
        assert pages[0] is p1
        assert pages[1] is p2

    def test_get_page(self) -> None:
        p1 = Page(index=0, media_box=Rect(0, 0, 612, 792))
        p2 = Page(index=1, media_box=Rect(0, 0, 612, 792))
        doc = Document(path=Path("test.pdf"), pages=(p1, p2))
        assert doc.get_page(0) is p1
        assert doc.get_page(1) is p2

    def test_get_page_negative_index(self) -> None:
        p1 = Page(index=0, media_box=Rect(0, 0, 612, 792))
        p2 = Page(index=1, media_box=Rect(0, 0, 612, 792))
        doc = Document(path=Path("test.pdf"), pages=(p1, p2))
        assert doc.get_page(-1) is p2

    def test_get_page_out_of_range(self) -> None:
        doc = Document(path=Path("test.pdf"), pages=(Page(index=0, media_box=Rect(0, 0, 612, 792)),))
        with pytest.raises(IndexError):
            doc.get_page(1)
        with pytest.raises(IndexError):
            doc.get_page(-2)

    def test_filename(self) -> None:
        doc = Document(path=Path("path/to/myfile.pdf"))
        assert doc.filename == "myfile.pdf"

    def test_metadata(self) -> None:
        doc = Document(path=Path("test.pdf"), title="My Title", author="Author Name")
        assert doc.title == "My Title"
        assert doc.author == "Author Name"

    def test_immutable(self) -> None:
        doc = Document(path=Path("test.pdf"))
        with pytest.raises(Exception):
            doc.title = "new"  # type: ignore[misc]

    def test_repr(self) -> None:
        doc = Document(path=Path("test.pdf"), pages=(Page(index=0, media_box=Rect(0, 0, 612, 792)),))
        assert "test.pdf" in repr(doc)
        assert "1" in repr(doc)
