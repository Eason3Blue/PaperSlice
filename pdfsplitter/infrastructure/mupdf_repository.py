"""MuPDF Repository - 基于 PyMuPDF 的 DocumentRepository 实现."""

from __future__ import annotations

import logging
from pathlib import Path

from pdfsplitter.application.repository import DocumentRepository
from pdfsplitter.domain.document.document import Document
from pdfsplitter.domain.document.page import Page
from pdfsplitter.domain.geometry.rect import Rect

logger = logging.getLogger(__name__)


class MuPDFRepository(DocumentRepository):
    """基于 PyMuPDF (fitz) 的文档仓库实现."""

    SUPPORTED_EXTENSIONS: tuple[str, ...] = (".pdf",)

    def load(self, path: Path, password: str | None = None) -> Document:
        """加载 PDF 文档.

        Args:
            path: 文档路径.
            password: 可选的打开密码.

        Returns:
            Document 领域对象.

        Raises:
            FileNotFoundError: 文件不存在.
            ValueError: 文件格式无效或密码错误.
        """
        import fitz

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {path.suffix}")

        try:
            pdf = fitz.open(str(path))
        except Exception as e:
            raise ValueError(f"无法打开 PDF 文件: {e}") from e

        if password and pdf.needs_pass:
            auth_ok = pdf.authenticate(password)
            if not auth_ok:
                pdf.close()
                raise ValueError("PDF 密码错误")

        pages: list[Page] = []
        for i in range(pdf.page_count):
            fitz_page = pdf.load_page(i)
            media = fitz_page.mediabox
            crop = fitz_page.cropbox
            media_rect = Rect(media.x0, media.y0, media.x1, media.y1)
            crop_rect = Rect(crop.x0, crop.y0, crop.x1, crop.y1)
            pages.append(Page(index=i, media_box=media_rect, crop_box=crop_rect))

        metadata = pdf.metadata or {}
        title = metadata.get("title") or None
        author = metadata.get("author") or None

        pdf.close()
        logger.info("MuPDFRepository: loaded %s with %d pages", path.name, len(pages))
        return Document(path=path, pages=tuple(pages), title=title, author=author)

    def supports(self, path: Path) -> bool:
        """检查是否支持该文件格式.

        Args:
            path: 文件路径.

        Returns:
            是否支持.
        """
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS
