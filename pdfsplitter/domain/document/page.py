from __future__ import annotations

from dataclasses import dataclass

from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.geometry.size import Size


@dataclass(frozen=True)
class Page:
    """不可变的 PDF 页面领域对象.

    Attributes:
        index: 页索引 (0-based).
        media_box: 页面介质框 (PDF 坐标系).
        crop_box: 裁剪框, 若未指定则与 media_box 相同.
        dpi: 页面默认 DPI, 用于像素转换.
    """

    index: int
    media_box: Rect
    crop_box: Rect | None = None
    dpi: int = 72

    @property
    def effective_rect(self) -> Rect:
        """返回有效页面区域 (crop_box 优先, 否则 media_box)."""
        return self.crop_box if self.crop_box is not None else self.media_box

    @property
    def width(self) -> float:
        """页面宽度 (PDF 点)."""
        return self.effective_rect.width

    @property
    def height(self) -> float:
        """页面高度 (PDF 点)."""
        return self.effective_rect.height

    @property
    def size(self) -> Size:
        """页面尺寸 (PDF 点)."""
        return self.effective_rect.size

    @property
    def is_landscape(self) -> bool:
        """是否为横向."""
        return self.size.is_landscape

    @property
    def is_portrait(self) -> bool:
        """是否为纵向."""
        return self.size.is_portrait

    def __repr__(self) -> str:
        return f"Page(index={self.index}, media_box={self.media_box.to_quad()})"
