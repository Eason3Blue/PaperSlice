from __future__ import annotations

import math
from dataclasses import dataclass
from typing import ClassVar

from pdfsplitter.domain.geometry.margin import Margin
from pdfsplitter.domain.geometry.point import Point
from pdfsplitter.domain.geometry.size import Size


@dataclass(frozen=True)
class Rect:
    """不可变矩形，由左下/右下两点或左上/右下两点定义.

    采用 (x0, y0) 左下角、(x1, y1) 右上角的 PDF 坐标系.
    保证 x0 <= x1 且 y0 <= y1.

    Attributes:
        x0: 左下角 X 坐标.
        y0: 左下角 Y 坐标.
        x1: 右上角 X 坐标.
        y1: 右上角 Y 坐标.
    """

    x0: float
    y0: float
    x1: float
    y1: float

    EMPTY: ClassVar[Rect]

    def __post_init__(self) -> None:
        """校验坐标并归一化."""
        if self.x0 > self.x1 or self.y0 > self.y1:
            x0 = min(self.x0, self.x1)
            x1 = max(self.x0, self.x1)
            y0 = min(self.y0, self.y1)
            y1 = max(self.y0, self.y1)
            object.__setattr__(self, "x0", x0)
            object.__setattr__(self, "x1", x1)
            object.__setattr__(self, "y0", y0)
            object.__setattr__(self, "y1", y1)

    @property
    def width(self) -> float:
        """矩形宽度."""
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        """矩形高度."""
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        """矩形面积."""
        return self.width * self.height

    @property
    def size(self) -> Size:
        """矩形尺寸."""
        return Size(self.width, self.height)

    @property
    def center(self) -> Point:
        """矩形中心点."""
        return Point((self.x0 + self.x1) / 2.0, (self.y0 + self.y1) / 2.0)

    @property
    def top_left(self) -> Point:
        """左上角."""
        return Point(self.x0, self.y1)

    @property
    def top_right(self) -> Point:
        """右上角."""
        return Point(self.x1, self.y1)

    @property
    def bottom_left(self) -> Point:
        """左下角."""
        return Point(self.x0, self.y0)

    @property
    def bottom_right(self) -> Point:
        """右下角."""
        return Point(self.x1, self.y0)

    @property
    def is_empty(self) -> bool:
        """是否为空矩形 (面积为零)."""
        return math.isclose(self.width, 0.0) or math.isclose(self.height, 0.0)

    def intersection(self, other: Rect) -> Rect | None:
        """计算与另一矩形的交集.

        Args:
            other: 另一矩形.

        Returns:
            交集矩形，若无交集则返回 None.
        """
        x0 = max(self.x0, other.x0)
        y0 = max(self.y0, other.y0)
        x1 = min(self.x1, other.x1)
        y1 = min(self.y1, other.y1)
        if x0 >= x1 or y0 >= y1:
            return None
        return Rect(x0, y0, x1, y1)

    def union(self, other: Rect) -> Rect:
        """计算与另一矩形的并集包围盒.

        Args:
            other: 另一矩形.

        Returns:
            包含两个矩形的最小矩形.
        """
        return Rect(
            min(self.x0, other.x0),
            min(self.y0, other.y0),
            max(self.x1, other.x1),
            max(self.y1, other.y1),
        )

    def contains(self, point: Point) -> bool:
        """判断点是否在矩形内部 (包含边界).

        Args:
            point: 待检测的点.

        Returns:
            是否包含.
        """
        return (self.x0 <= point.x <= self.x1) and (self.y0 <= point.y <= self.y1)

    def contains_rect(self, other: Rect) -> bool:
        """判断另一矩形是否完全在本矩形内部.

        Args:
            other: 另一矩形.

        Returns:
            是否完全包含.
        """
        return (
            self.x0 <= other.x0
            and self.y0 <= other.y0
            and self.x1 >= other.x1
            and self.y1 >= other.y1
        )

    def overlaps(self, other: Rect) -> bool:
        """判断是否与另一矩形有重叠区域.

        Args:
            other: 另一矩形.

        Returns:
            是否有重叠.
        """
        return not (
            self.x1 <= other.x0
            or self.x0 >= other.x1
            or self.y1 <= other.y0
            or self.y0 >= other.y1
        )

    def translate(self, dx: float, dy: float) -> Rect:
        """平移矩形.

        Args:
            dx: X 方向偏移.
            dy: Y 方向偏移.

        Returns:
            平移后的新矩形.
        """
        return Rect(self.x0 + dx, self.y0 + dy, self.x1 + dx, self.y1 + dy)

    def translate_point(self, point: Point) -> Rect:
        """以点向量平移.

        Args:
            point: 平移向量.

        Returns:
            平移后的新矩形.
        """
        return self.translate(point.x, point.y)

    def inflate(self, margin: Margin) -> Rect:
        """以 Margin 扩展/收缩矩形.

        正 margin 扩大，负 margin 缩小.

        Args:
            margin: 四边扩展量.

        Returns:
            新矩形.
        """
        return Rect(
            self.x0 - margin.left,
            self.y0 - margin.bottom,
            self.x1 + margin.right,
            self.y1 + margin.top,
        )

    def inflate_uniform(self, amount: float) -> Rect:
        """四边均匀扩展.

        Args:
            amount: 扩展量.

        Returns:
            新矩形.
        """
        margin = Margin.uniform(amount)
        return self.inflate(margin)

    def scale(self, sx: float, sy: float | None = None, origin: Point | None = None) -> Rect:
        """以某点为中心缩放矩形.

        Args:
            sx: X 方向缩放因子.
            sy: Y 方向缩放因子, 若为 None 则与 sx 相同.
            origin: 缩放中心，若为 None 则以矩形左下角为中心.

        Returns:
            缩放后的新矩形.
        """
        if sy is None:
            sy = sx
        if origin is None:
            origin = Point(self.x0, self.y0)
        new_width = self.width * sx
        new_height = self.height * sy
        x0 = origin.x + (self.x0 - origin.x) * sx
        y0 = origin.y + (self.y0 - origin.y) * sy
        return Rect(x0, y0, x0 + new_width, y0 + new_height)

    def clip(self, other: Rect) -> Rect | None:
        """以另一矩形裁剪本矩形 (同 intersection).

        Args:
            other: 裁剪矩形.

        Returns:
            裁剪后的矩形，若无交集则返回 None.
        """
        return self.intersection(other)

    def to_quad(self) -> tuple[float, float, float, float]:
        """返回四元组 (x0, y0, x1, y1)."""
        return (self.x0, self.y0, self.x1, self.y1)

    def to_tuple(self) -> tuple[float, float, float, float]:
        """返回四元组 (x0, y0, x1, y1)."""
        return self.to_quad()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rect):
            return NotImplemented
        return (
            math.isclose(self.x0, other.x0)
            and math.isclose(self.y0, other.y0)
            and math.isclose(self.x1, other.x1)
            and math.isclose(self.y1, other.y1)
        )

    def __hash__(self) -> int:
        return hash((round(self.x0, 10), round(self.y0, 10), round(self.x1, 10), round(self.y1, 10)))

    @classmethod
    def from_points(cls, p0: Point, p1: Point) -> Rect:
        """由任意两个对角点构造矩形.

        Args:
            p0: 第一个角点.
            p1: 第二个角点.

        Returns:
            Rect 实例.
        """
        return cls(p0.x, p0.y, p1.x, p1.y)

    @classmethod
    def from_origin_size(cls, origin: Point, size: Size) -> Rect:
        """由左下角原点和尺寸构造矩形.

        Args:
            origin: 左下角原点.
            size: 尺寸.

        Returns:
            Rect 实例.
        """
        return cls(origin.x, origin.y, origin.x + size.w, origin.y + size.h)

    @classmethod
    def from_center(cls, center: Point, size: Size) -> Rect:
        """由中心点和尺寸构造矩形.

        Args:
            center: 中心点.
            size: 尺寸.

        Returns:
            Rect 实例.
        """
        half_w = size.w / 2.0
        half_h = size.h / 2.0
        return cls(center.x - half_w, center.y - half_h, center.x + half_w, center.y + half_h)


Rect.EMPTY = Rect(0.0, 0.0, 0.0, 0.0)
