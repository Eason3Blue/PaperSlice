"""Image Repository - 基于 PyMuPDF 的图片文档仓库实现."""

from __future__ import annotations

import logging
from pathlib import Path

from pdfsplitter.application.repository import DocumentRepository
from pdfsplitter.domain.document.document import Document
from pdfsplitter.domain.document.page import Page
from pdfsplitter.domain.geometry.rect import Rect

logger = logging.getLogger(__name__)


class ImageRepository(DocumentRepository):
    """基于 PyMuPDF (fitz) 的图片文档仓库实现.

    将单张图片包装为一页文档.
    支持 PNG, JPG, JPEG, BMP, TIFF.
    """

    SUPPORTED_EXTENSIONS: tuple[str, ...] = (
        ".png", ".jpg", ".jpeg", ".bmp", ".tiff",
    )

    def load(self, path: Path, password: str | None = None) -> Document:
        """加载图片为单页文档.

        Args:
            path: 图片路径.
            password: 忽略 (图片无密码).

        Returns:
            Document 领域对象 (单页).

        Raises:
            FileNotFoundError: 文件不存在.
            ValueError: 文件格式无效.
        """
        import fitz

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的图片格式: {path.suffix}")

        try:
            img_doc = fitz.open(str(path))
        except Exception as e:
            raise ValueError(f"无法打开图片文件: {e}") from e

        page_count = img_doc.page_count
        pages: list[Page] = []
        for i in range(page_count):
            fitz_page = img_doc.load_page(i)
            media = fitz_page.mediabox
            media_rect = Rect(media.x0, media.y0, media.x1, media.y1)
            pages.append(Page(index=i, media_box=media_rect, crop_box=media_rect))

        img_doc.close()
        logger.info("ImageRepository: loaded %s (%dx%d pt)", path.name,
                     int(pages[0].width) if pages else 0,
                     int(pages[0].height) if pages else 0)
        return Document(path=path, pages=tuple(pages))

    def supports(self, path: Path) -> bool:
        """检查是否支持该图片格式.

        Args:
            path: 文件路径.

        Returns:
            是否支持.
        """
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS
