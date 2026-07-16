from __future__ import annotations

import math
from dataclasses import dataclass

MM_PER_INCH: float = 25.4
POINTS_PER_INCH: float = 72.0
MM_PER_POINT: float = MM_PER_INCH / POINTS_PER_INCH
POINTS_PER_MM: float = POINTS_PER_INCH / MM_PER_INCH


@dataclass(frozen=True)
class Length:
    """不可变的物理长度值对象，内部以毫米为规范单位.

    支持从毫米、PDF 点、英寸、像素构造，并可在各单元间互转.
    像素转换需要 DPI 参数.

    Attributes:
        mm: 以毫米为单位的规范值.
    """

    mm: float

    @classmethod
    def from_millimeter(cls, value: float) -> Length:
        """从毫米构造.

        Args:
            value: 毫米数.

        Returns:
            Length 实例.
        """
        return cls(mm=value)

    @classmethod
    def from_point(cls, value: float) -> Length:
        """从 PDF 点 (1/72 英寸) 构造.

        Args:
            value: PDF 点数.

        Returns:
            Length 实例.
        """
        return cls(mm=value * MM_PER_POINT)

    @classmethod
    def from_inch(cls, value: float) -> Length:
        """从英寸构造.

        Args:
            value: 英寸数.

        Returns:
            Length 实例.
        """
        return cls(mm=value * MM_PER_INCH)

    @classmethod
    def from_pixel(cls, value: float, dpi: int = 72) -> Length:
        """从像素构造.

        Args:
            value: 像素数.
            dpi: 每英寸像素数, 默认 72.

        Returns:
            Length 实例.
        """
        return cls(mm=value * MM_PER_INCH / dpi)

    @classmethod
    def zero(cls) -> Length:
        """零长度."""
        return cls(mm=0.0)

    @property
    def pt(self) -> float:
        """转换为 PDF 点."""
        return self.mm * POINTS_PER_MM

    @property
    def inch(self) -> float:
        """转换为英寸."""
        return self.mm / MM_PER_INCH

    def pixel(self, dpi: int = 72) -> float:
        """转换为像素.

        Args:
            dpi: 每英寸像素数, 默认 72.

        Returns:
            像素数 (float).
        """
        return self.inch * dpi

    def to_millimeter(self) -> float:
        """返回毫米值."""
        return self.mm

    def to_point(self) -> float:
        """返回 PDF 点值."""
        return self.pt

    def to_inch(self) -> float:
        """返回英寸值."""
        return self.inch

    def to_pixel(self, dpi: int = 72) -> float:
        """返回像素值.

        Args:
            dpi: 每英寸像素数, 默认 72.

        Returns:
            像素数 (float).
        """
        return self.pixel(dpi=dpi)

    def __add__(self, other: Length) -> Length:
        return Length(self.mm + other.mm)

    def __sub__(self, other: Length) -> Length:
        return Length(self.mm - other.mm)

    def __mul__(self, scalar: float) -> Length:
        return Length(self.mm * scalar)

    def __rmul__(self, scalar: float) -> Length:
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> Length:
        return Length(self.mm / scalar)

    def __neg__(self) -> Length:
        return Length(-self.mm)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Length):
            return NotImplemented
        return math.isclose(self.mm, other.mm)

    def __hash__(self) -> int:
        return hash(round(self.mm, 10))

    def __lt__(self, other: Length) -> bool:
        return self.mm < other.mm

    def __le__(self, other: Length) -> bool:
        return self.mm <= other.mm

    def __gt__(self, other: Length) -> bool:
        return self.mm > other.mm

    def __ge__(self, other: Length) -> bool:
        return self.mm >= other.mm

    def __repr__(self) -> str:
        return f"Length({self.mm:.4f}mm)"
