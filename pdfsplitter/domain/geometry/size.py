from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Size:
    """二维不可变尺寸.

    Attributes:
        w: 宽度.
        h: 高度.
    """

    w: float
    h: float

    @property
    def area(self) -> float:
        """面积."""
        return self.w * self.h

    @property
    def aspect_ratio(self) -> float:
        """宽高比 (w / h)."""
        return self.w / self.h if self.h != 0 else float("inf")

    @property
    def is_landscape(self) -> bool:
        """是否为横向."""
        return self.w > self.h

    @property
    def is_portrait(self) -> bool:
        """是否为纵向."""
        return self.h > self.w

    @property
    def is_square(self) -> bool:
        """是否为正方形."""
        return math.isclose(self.w, self.h)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Size):
            return NotImplemented
        return math.isclose(self.w, other.w) and math.isclose(self.h, other.h)

    def __hash__(self) -> int:
        return hash((round(self.w, 10), round(self.h, 10)))

    def scale(self, sx: float, sy: float | None = None) -> Size:
        """等比或不等比缩放.

        Args:
            sx: 宽度缩放因子.
            sy: 高度缩放因子, 若为 None 则与 sx 相同.

        Returns:
            新的 Size.
        """
        if sy is None:
            sy = sx
        return Size(self.w * sx, self.h * sy)

    def to_tuple(self) -> tuple[float, float]:
        """返回 (w, h) 元组."""
        return (self.w, self.h)

    def flipped(self) -> Size:
        """返回宽高互换的 Size."""
        return Size(self.h, self.w)
