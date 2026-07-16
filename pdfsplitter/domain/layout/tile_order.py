"""TileOrder - 图块排序定义."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TileOrder:
    """图块输出顺序.

    Attributes:
        indices: 按输出顺序排列的图块索引列表.
        mode: 排序模式: "auto" 或 "manual".
    """

    indices: tuple[int, ...] = field(default_factory=tuple)
    mode: str = "auto"

    @property
    def count(self) -> int:
        """图块数量."""
        return len(self.indices)

    def with_manual_order(self, ordered_indices: list[int]) -> TileOrder:
        """设置手动排序.

        Args:
            ordered_indices: 手动指定的索引顺序.

        Returns:
            新的 TileOrder.
        """
        return TileOrder(indices=tuple(ordered_indices), mode="manual")

    @classmethod
    def auto(cls, tile_count: int) -> TileOrder:
        """自动顺序 (0, 1, 2, ...).

        Args:
            tile_count: 图块总数.

        Returns:
            TileOrder.
        """
        return cls(indices=tuple(range(tile_count)), mode="auto")
