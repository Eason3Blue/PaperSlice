from __future__ import annotations

from dataclasses import dataclass, field

from pdfsplitter.domain.geometry.rect import Rect


@dataclass(frozen=True)
class Tile:
    """不可变的图块值对象，代表分割后的一个切片.

    Attributes:
        index: 图块编号 (0-based).
        row: 网格行索引.
        col: 网格列索引.
        source_rect: 在源页面上的裁剪区域.
        target_rect: 在目标纸张上的放置位置 (用于渲染).
    """

    index: int
    row: int
    col: int
    source_rect: Rect
    target_rect: Rect | None = None

    @property
    def grid_position(self) -> tuple[int, int]:
        """网格位置 (row, col)."""
        return (self.row, self.col)

    def __repr__(self) -> str:
        return f"Tile(index={self.index}, row={self.row}, col={self.col}, source={self.source_rect.to_quad()})"
