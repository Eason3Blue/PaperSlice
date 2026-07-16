from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """二维平面上的不可变点.

    Attributes:
        x: X 坐标.
        y: Y 坐标.
    """

    x: float
    y: float

    def __add__(self, other: Point) -> Point:
        """向量加法."""
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        """向量减法."""
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Point:
        """标量乘法."""
        return Point(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Point:
        """右标量乘法."""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> Point:
        """标量除法."""
        return Point(self.x / scalar, self.y / scalar)

    def __neg__(self) -> Point:
        """取反."""
        return Point(-self.x, -self.y)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return math.isclose(self.x, other.x) and math.isclose(self.y, other.y)

    def __hash__(self) -> int:
        return hash((round(self.x, 10), round(self.y, 10)))

    def distance_to(self, other: Point) -> float:
        """计算到另一点的欧几里得距离."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def to_tuple(self) -> tuple[float, float]:
        """返回 (x, y) 元组."""
        return (self.x, self.y)

    @classmethod
    def origin(cls) -> Point:
        """返回原点 (0, 0)."""
        return cls(0.0, 0.0)
