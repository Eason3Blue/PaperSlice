"""OrderRule - 图块排序规则值对象."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderRule:
    """图块自动排序规则.

    描述二维网格图块按何种顺序输出:
    - row_direction: 行遍历方向 (top_to_bottom / bottom_to_top).
    - col_direction: 列遍历方向 (left_to_right / right_to_left).
    - primary_axis: 主遍历轴 (row 先行 / col 先列).

    Attributes:
        row_direction: 行方向.
        col_direction: 列方向.
        primary_axis: 优先轴.
    """

    row_direction: str = "top_to_bottom"
    col_direction: str = "left_to_right"
    primary_axis: str = "row"

    def compute_indices(self, rows: int, cols: int) -> tuple[int, ...]:
        """根据规则计算图块索引序列.

        Args:
            rows: 网格行数.
            cols: 网格列数.

        Returns:
            按规则排序的图块索引元组.
        """
        if rows <= 0 or cols <= 0:
            return ()

        row_range = list(range(rows))
        col_range = list(range(cols))

        if self.row_direction == "bottom_to_top":
            row_range.reverse()
        if self.col_direction == "right_to_left":
            col_range.reverse()

        result: list[int] = []
        if self.primary_axis == "col":
            for c in col_range:
                for r in row_range:
                    result.append(r * cols + c)
        else:
            for r in row_range:
                for c in col_range:
                    result.append(r * cols + c)

        return tuple(result)

    @property
    def is_default(self) -> bool:
        """是否为默认规则 (先行, 从上到下, 从左到右)."""
        return (
            self.row_direction == "top_to_bottom"
            and self.col_direction == "left_to_right"
            and self.primary_axis == "row"
        )

    @classmethod
    def default(cls) -> OrderRule:
        """返回默认规则."""
        return cls()
