"""Geometry module - 独立于 PDF 的纯几何计算核心."""

from pdfsplitter.domain.geometry.point import Point
from pdfsplitter.domain.geometry.size import Size
from pdfsplitter.domain.geometry.margin import Margin
from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.geometry.transform import Transform

__all__ = ["Point", "Size", "Margin", "Rect", "Transform"]
