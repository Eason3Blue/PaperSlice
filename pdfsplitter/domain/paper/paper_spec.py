from __future__ import annotations

from dataclasses import dataclass, field

from pdfsplitter.domain.geometry.size import Size
from pdfsplitter.domain.units.length import Length


@dataclass(frozen=True)
class PaperSpec:
    """不可变的纸张规格值对象.

    Attributes:
        name: 纸张名称, 如 "A4", "Letter".
        category: 所属标准, 如 "ISO216", "ANSI", "NorthAmerican", "Custom".
        size: 纸张尺寸 (宽, 高) 以毫米为单位.
        description: 可选的描述文本.
    """

    name: str
    category: str
    size: Size
    description: str = ""

    @property
    def width(self) -> Length:
        """宽度."""
        return Length.from_millimeter(self.size.w)

    @property
    def height(self) -> Length:
        """高度."""
        return Length.from_millimeter(self.size.h)

    @property
    def area(self) -> float:
        """面积 (mm²)."""
        return self.size.area

    @property
    def is_landscape(self) -> bool:
        """是否为横向."""
        return self.size.is_landscape

    @property
    def is_portrait(self) -> bool:
        """是否为纵向."""
        return self.size.is_portrait

    def rotated(self) -> PaperSpec:
        """返回宽高交换后的纸张规格 (旋转 90°)."""
        return PaperSpec(
            name=f"{self.name} (L)",
            category=self.category,
            size=self.size.flipped(),
            description=f"{self.description} (landscape)".strip(),
        )

    @classmethod
    def custom(cls, name: str, width_mm: float, height_mm: float, description: str = "") -> PaperSpec:
        """创建自定义纸张规格.

        Args:
            name: 自定义名称.
            width_mm: 宽度 (mm).
            height_mm: 高度 (mm).
            description: 描述.

        Returns:
            PaperSpec 实例.
        """
        return cls(name=name, category="Custom", size=Size(width_mm, height_mm), description=description)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PaperSpec):
            return NotImplemented
        return self.name == other.name and self.category == other.category and self.size == other.size

    def __hash__(self) -> int:
        return hash((self.name, self.category, self.size))
