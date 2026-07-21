"""TileOrder - 图块排序定义."""

from __future__ import annotations

from dataclasses import dataclass, field

from pdfsplitter.domain.layout.order_rule import OrderRule


@dataclass(frozen=True)
class TileOrder:
    """图块输出顺序.

    Attributes:
        indices: 按输出顺序排列的图块索引列表.
        mode: 排序模式: "auto" 或 "manual".
        rule: 自动排序规则, 仅 auto 模式生效.
        rows: 网格行数, 仅 auto 模式需要.
        cols: 网格列数, 仅 auto 模式需要.
    """

    indices: tuple[int, ...] = field(default_factory=tuple)
    mode: str = "auto"
    rule: OrderRule = field(default_factory=OrderRule.default)
    rows: int = 0
    cols: int = 0

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
    def auto(cls, tile_count: int, rule: OrderRule | None = None, rows: int = 0, cols: int = 0) -> TileOrder:
        """自动顺序.

        Args:
            tile_count: 图块总数.
            rule: 排序规则, 默认使用 OrderRule.default().
            rows: 网格行数.
            cols: 网格列数.

        Returns:
            TileOrder.
        """
        r = rule or OrderRule.default()
        if rows > 0 and cols > 0:
            indices = r.compute_indices(rows, cols)
        else:
            indices = tuple(range(tile_count))
        return cls(indices=indices, mode="auto", rule=r, rows=rows, cols=cols)
