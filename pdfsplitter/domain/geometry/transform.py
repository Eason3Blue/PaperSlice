from __future__ import annotations

from dataclasses import dataclass

from pdfsplitter.domain.geometry.point import Point
from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.geometry.size import Size


@dataclass(frozen=True)
class Transform:
    """二维仿射变换的不可变表示 (预留矩阵实现).

    当前仅存储分离的 translate/scale/rotate 参数.
    未来将扩展为完整 3x3 齐次变换矩阵.

    Attributes:
        translate_x: X 方向平移量 (默认 0).
        translate_y: Y 方向平移量 (默认 0).
        scale_x: X 方向缩放因子 (默认 1).
        scale_y: Y 方向缩放因子 (默认 1).
        rotation: 旋转角度 (度数，暂未实现).
    """

    translate_x: float = 0.0
    translate_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0

    @classmethod
    def identity(cls) -> Transform:
        """返回单位变换."""
        return cls()

    @classmethod
    def translation(cls, dx: float, dy: float) -> Transform:
        """创建平移变换."""
        return cls(translate_x=dx, translate_y=dy)

    @classmethod
    def scaling(cls, sx: float, sy: float | None = None) -> Transform:
        """创建缩放变换."""
        sy = sy if sy is not None else sx
        return cls(scale_x=sx, scale_y=sy)

    def transform_point(self, point: Point) -> Point:
        """对点应用变换 (当前仅支持平移和缩放).

        Args:
            point: 待变换的点.

        Returns:
            变换后的点.
        """
        return Point(
            point.x * self.scale_x + self.translate_x,
            point.y * self.scale_y + self.translate_y,
        )

    def transform_rect(self, rect: Rect) -> Rect:
        """对矩形应用变换.

        Args:
            rect: 待变换的矩形.

        Returns:
            变换后的矩形.
        """
        p0 = self.transform_point(Point(rect.x0, rect.y0))
        p1 = self.transform_point(Point(rect.x1, rect.y1))
        return Rect.from_points(p0, p1)

    def transform_size(self, size: Size) -> Size:
        """对尺寸应用缩放.

        Args:
            size: 原始尺寸.

        Returns:
            缩放后的尺寸.
        """
        return Size(size.w * self.scale_x, size.h * self.scale_y)

    def compose(self, other: Transform) -> Transform:
        """组合两个变换 (当前为简化实现).

        Args:
            other: 另一个变换.

        Returns:
            组合后的变换.
        """
        return Transform(
            translate_x=self.translate_x + other.translate_x * self.scale_x,
            translate_y=self.translate_y + other.translate_y * self.scale_y,
            scale_x=self.scale_x * other.scale_x,
            scale_y=self.scale_y * other.scale_y,
            rotation=self.rotation + other.rotation,
        )
