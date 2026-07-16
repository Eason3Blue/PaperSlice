from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.geometry.size import Size
from pdfsplitter.domain.layout.grid import Grid
from pdfsplitter.domain.layout.tile import Tile
from pdfsplitter.domain.units.length import Length

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LayoutParams:
    """布局计算参数.

    Attributes:
        page_size: 源页面尺寸 (PDF 点).
        target_size: 目标纸张尺寸 (PDF 点).
        margin_h: 目标纸张水平总边距 (PDF 点).
        margin_v: 目标纸张垂直总边距 (PDF 点).
        overlap: 相邻图块重叠量 (PDF 点), 默认 0.
        dpi: 分辨率, 默认 72.
    """

    page_size: Size
    target_size: Size
    margin_h: float = 0.0
    margin_v: float = 0.0
    overlap: float = 0.0
    dpi: int = 72

    @property
    def printable_width(self) -> float:
        """目标纸张可打印宽度."""
        return max(self.target_size.w - self.margin_h, 1.0)

    @property
    def printable_height(self) -> float:
        """目标纸张可打印高度."""
        return max(self.target_size.h - self.margin_v, 1.0)

    def validate(self) -> None:
        """校验参数合法性.

        Raises:
            ValueError: 参数无效.
        """
        if self.page_size.w <= 0 or self.page_size.h <= 0:
            raise ValueError("源页面尺寸必须为正数")
        if self.target_size.w <= 0 or self.target_size.h <= 0:
            raise ValueError("目标纸张尺寸必须为正数")
        if self.margin_h < 0 or self.margin_v < 0:
            raise ValueError("边距不能为负数")
        if self.overlap < 0:
            raise ValueError("重叠量不能为负数")
        if self.margin_h >= self.target_size.w or self.margin_v >= self.target_size.h:
            raise ValueError("边距不能大于目标纸张尺寸")


class LayoutEngine:
    """布局计算引擎，仅负责纯几何计算，不涉及 PDF 操作.

    输入页面尺寸、纸张规格、边距和重叠量，输出网格切分方案.
    """

    def calculate(self, params: LayoutParams) -> Grid:
        """根据布局参数计算网格.

        Args:
            params: 布局参数.

        Returns:
            Grid 实例, 包含所有切分图块.

        Raises:
            ValueError: 参数校验失败.
        """
        params.validate()
        logger.debug(
            "LayoutEngine: page=%.1fx%.1f target=%.1fx%.1f margin=(%.1f,%.1f) overlap=%.1f",
            params.page_size.w,
            params.page_size.h,
            params.target_size.w,
            params.target_size.h,
            params.margin_h,
            params.margin_v,
            params.overlap,
        )

        pw = params.printable_width
        ph = params.printable_height
        overlap = params.overlap
        page_w = params.page_size.w
        page_h = params.page_size.h

        cols = math.ceil(page_w / pw) if pw > 0 else 1
        rows = math.ceil(page_h / ph) if ph > 0 else 1

        tiles: list[Tile] = []
        tile_index = 0

        for row in range(rows):
            for col in range(cols):
                x0 = col * pw
                y0 = row * ph
                x1 = min(x0 + pw + overlap, page_w)
                y1 = min(y0 + ph + overlap, page_h)
                source_rect = Rect(x0, y0, x1, y1)

                tile = Tile(
                    index=tile_index,
                    row=row,
                    col=col,
                    source_rect=source_rect,
                )
                tiles.append(tile)
                tile_index += 1

        logger.info("LayoutEngine: calculated %dx%d grid with %d tiles", rows, cols, len(tiles))
        return Grid(rows=rows, cols=cols, tiles=tuple(tiles))
