"""SplitLines - 切割线定义."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SplitLines:
    """不可变的切割线定义.

    Attributes:
        verticals: 垂直切割线的 X 坐标列表 (PDF 点).
        horizontals: 水平切割线的 Y 坐标列表 (PDF 点).
    """

    verticals: tuple[float, ...] = field(default_factory=tuple)
    horizontals: tuple[float, ...] = field(default_factory=tuple)

    @property
    def col_count(self) -> int:
        """列数 = 垂直线数 + 1."""
        return len(self.verticals) + 1

    @property
    def row_count(self) -> int:
        """行数 = 水平线数 + 1."""
        return len(self.horizontals) + 1

    @property
    def tile_count(self) -> int:
        """图块总数."""
        return self.col_count * self.row_count

    @property
    def is_empty(self) -> bool:
        """是否无切割线."""
        return len(self.verticals) == 0 and len(self.horizontals) == 0

    def with_vertical(self, x: float) -> SplitLines:
        """添加一条垂直线.

        Args:
            x: X 坐标 (PDF 点).

        Returns:
            新的 SplitLines.
        """
        new_verts = tuple(sorted([*self.verticals, x]))
        return SplitLines(verticals=new_verts, horizontals=self.horizontals)

    def with_horizontal(self, y: float) -> SplitLines:
        """添加一条水平线.

        Args:
            y: Y 坐标 (PDF 点).

        Returns:
            新的 SplitLines.
        """
        new_horiz = tuple(sorted([*self.horizontals, y]))
        return SplitLines(verticals=self.verticals, horizontals=new_horiz)

    def remove_vertical(self, index: int) -> SplitLines:
        """按索引移除垂直线.

        Args:
            index: 垂直线索引.

        Returns:
            新的 SplitLines.

        Raises:
            IndexError: 索引无效.
        """
        verts = list(self.verticals)
        if 0 <= index < len(verts):
            del verts[index]
            return SplitLines(verticals=tuple(verts), horizontals=self.horizontals)
        raise IndexError(f"垂直线索引 {index} 无效 (共 {len(verts)} 条)")

    def remove_horizontal(self, index: int) -> SplitLines:
        """按索引移除水平线.

        Args:
            index: 水平线索引.

        Returns:
            新的 SplitLines.

        Raises:
            IndexError: 索引无效.
        """
        horiz = list(self.horizontals)
        if 0 <= index < len(horiz):
            del horiz[index]
            return SplitLines(verticals=self.verticals, horizontals=tuple(horiz))
        raise IndexError(f"水平线索引 {index} 无效 (共 {len(horiz)} 条)")

    def move_vertical(self, index: int, x: float, min_x: float = 0.0, max_x: float = float("inf")) -> SplitLines:
        """移动一条垂直线到新位置.

        Args:
            index: 垂直线索引.
            x: 新 X 坐标.
            min_x: 最小允许值.
            max_x: 最大允许值.

        Returns:
            新的 SplitLines.
        """
        x = max(min_x, min(x, max_x))
        verts = list(self.verticals)
        if 0 <= index < len(verts):
            verts[index] = x
            verts.sort()
            return SplitLines(verticals=tuple(verts), horizontals=self.horizontals)
        raise IndexError(f"垂直线索引 {index} 无效")

    def move_horizontal(self, index: int, y: float, min_y: float = 0.0, max_y: float = float("inf")) -> SplitLines:
        """移动一条水平线到新位置.

        Args:
            index: 水平线索引.
            y: 新 Y 坐标.
            min_y: 最小允许值.
            max_y: 最大允许值.

        Returns:
            新的 SplitLines.
        """
        y = max(min_y, min(y, max_y))
        horiz = list(self.horizontals)
        if 0 <= index < len(horiz):
            horiz[index] = y
            horiz.sort()
            return SplitLines(verticals=self.verticals, horizontals=tuple(horiz))
        raise IndexError(f"水平线索引 {index} 无效")

    @classmethod
    def empty(cls) -> SplitLines:
        """无切割线."""
        return cls()

    @classmethod
    def halved_vertical(cls, page_width: float) -> SplitLines:
        """垂直二分 (一条中线).

        Args:
            page_width: 页面宽度.

        Returns:
            SplitLines.
        """
        return cls(verticals=(page_width / 2.0,))

    @classmethod
    def halved_horizontal(cls, page_height: float) -> SplitLines:
        """水平二分 (一条中线).

        Args:
            page_height: 页面高度.

        Returns:
            SplitLines.
        """
        return cls(horizontals=(page_height / 2.0,))

    @classmethod
    def quartered(cls, page_width: float, page_height: float) -> SplitLines:
        """四等分 (垂直+水平中线).

        Args:
            page_width: 页面宽度.
            page_height: 页面高度.

        Returns:
            SplitLines.
        """
        return cls(
            verticals=(page_width / 2.0,),
            horizontals=(page_height / 2.0,),
        )
