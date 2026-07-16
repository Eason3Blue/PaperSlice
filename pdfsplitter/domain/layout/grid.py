from __future__ import annotations

from dataclasses import dataclass, field

from pdfsplitter.domain.layout.tile import Tile


@dataclass(frozen=True)
class Grid:
    """不可变的网格值对象，包含页面的行列切分信息.

    Attributes:
        rows: 总行数.
        cols: 总列数.
        tiles: 所有图块的有序列表 (按行优先排列).
    """

    rows: int
    cols: int
    tiles: tuple[Tile, ...] = field(default_factory=tuple)

    @property
    def total_tiles(self) -> int:
        """图块总数."""
        return len(self.tiles)

    @property
    def is_empty(self) -> bool:
        """是否为空网格."""
        return self.total_tiles == 0

    def get_tile(self, row: int, col: int) -> Tile | None:
        """按行列获取图块.

        Args:
            row: 行索引.
            col: 列索引.

        Returns:
            图块, 若行列无效则返回 None.
        """
        for tile in self.tiles:
            if tile.row == row and tile.col == col:
                return tile
        return None

    def get_tiles_in_row(self, row: int) -> list[Tile]:
        """获取指定行的所有图块.

        Args:
            row: 行索引.

        Returns:
            该行的图块列表.
        """
        return [t for t in self.tiles if t.row == row]

    def get_tiles_in_col(self, col: int) -> list[Tile]:
        """获取指定列的所有图块.

        Args:
            col: 列索引.

        Returns:
            该列的图块列表.
        """
        return [t for t in self.tiles if t.col == col]

    def get_tile_by_index(self, tile_index: int) -> Tile | None:
        """按 tile.index 获取图块.

        Args:
            tile_index: 图块编号.

        Returns:
            图块, 若不存在则返回 None.
        """
        for tile in self.tiles:
            if tile.index == tile_index:
                return tile
        return None

    def __iter__(self):
        return iter(self.tiles)

    def __repr__(self) -> str:
        return f"Grid(rows={self.rows}, cols={self.cols}, tiles={self.total_tiles})"
