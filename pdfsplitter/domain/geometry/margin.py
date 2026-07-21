from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Margin:
    """不可变的页边距值对象.

    Attributes:
        left: 左边距.
        right: 右边距.
        top: 上边距.
        bottom: 下边距.
    """

    left: float
    right: float
    top: float
    bottom: float

    @property
    def horizontal(self) -> float:
        """水平总边距 (left + right)."""
        return self.left + self.right

    @property
    def vertical(self) -> float:
        """垂直总边距 (top + bottom)."""
        return self.top + self.bottom

    @property
    def is_uniform(self) -> bool:
        """四边边距是否一致."""
        return (
            math.isclose(self.left, self.right)
            and math.isclose(self.left, self.top)
            and math.isclose(self.left, self.bottom)
        )

    def to_tuple(self) -> tuple[float, float, float, float]:
        """返回 (left, right, top, bottom) 元组."""
        return (self.left, self.right, self.top, self.bottom)

    @classmethod
    def symmetric(cls, horizontal: float = 0.0, vertical: float = 0.0) -> Margin:
        """创建对称边距.

        Args:
            horizontal: 左右边距.
            vertical: 上下边距.

        Returns:
            对称的 Margin.
        """
        return cls(left=horizontal, right=horizontal, top=vertical, bottom=vertical)

    @classmethod
    def uniform(cls, value: float = 0.0) -> Margin:
        """创建四边一致的边距.

        Args:
            value: 四边相同的边距值.

        Returns:
            统一的 Margin.
        """
        return cls(left=value, right=value, top=value, bottom=value)

    @classmethod
    def zero(cls) -> Margin:
        """创建零边距."""
        return cls(left=0.0, right=0.0, top=0.0, bottom=0.0)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Margin):
            return NotImplemented
        return (
            math.isclose(self.left, other.left)
            and math.isclose(self.right, other.right)
            and math.isclose(self.top, other.top)
            and math.isclose(self.bottom, other.bottom)
        )

    def __hash__(self) -> int:
        return hash((
            round(self.left, 10),
            round(self.right, 10),
            round(self.top, 10),
            round(self.bottom, 10),
        ))
