from __future__ import annotations

import math

import pytest

from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.geometry.size import Size
from pdfsplitter.domain.layout.grid import Grid
from pdfsplitter.domain.layout.layout_engine import LayoutEngine, LayoutParams
from pdfsplitter.domain.layout.tile import Tile


class TestTile:
    """Tile 值对象测试套件."""

    def test_creation(self) -> None:
        rect = Rect(0, 0, 100, 200)
        tile = Tile(index=0, row=0, col=0, source_rect=rect)
        assert tile.index == 0
        assert tile.row == 0
        assert tile.col == 0
        assert tile.source_rect == rect
        assert tile.target_rect is None

    def test_grid_position(self) -> None:
        tile = Tile(index=0, row=2, col=3, source_rect=Rect(0, 0, 100, 100))
        assert tile.grid_position == (2, 3)

    def test_immutable(self) -> None:
        tile = Tile(index=0, row=0, col=0, source_rect=Rect(0, 0, 100, 100))
        with pytest.raises(Exception):
            tile.row = 1  # type: ignore[misc]

    def test_repr(self) -> None:
        tile = Tile(index=5, row=1, col=2, source_rect=Rect(10, 20, 110, 220))
        s = repr(tile)
        assert "index=5" in s
        assert "row=1" in s
        assert "col=2" in s


class TestGrid:
    """Grid 值对象测试套件."""

    def _make_tile(self, index: int, row: int, col: int) -> Tile:
        return Tile(index=index, row=row, col=col, source_rect=Rect(col * 100, row * 100, (col + 1) * 100, (row + 1) * 100))

    def test_creation(self) -> None:
        grid = Grid(rows=1, cols=1)
        assert grid.rows == 1
        assert grid.cols == 1
        assert grid.total_tiles == 0

    def test_with_tiles(self) -> None:
        t1 = self._make_tile(0, 0, 0)
        t2 = self._make_tile(1, 0, 1)
        grid = Grid(rows=1, cols=2, tiles=(t1, t2))
        assert grid.total_tiles == 2

    def test_is_empty(self) -> None:
        grid = Grid(rows=0, cols=0)
        assert grid.is_empty is True

    def test_is_empty_false(self) -> None:
        t = self._make_tile(0, 0, 0)
        grid = Grid(rows=1, cols=1, tiles=(t,))
        assert grid.is_empty is False

    def test_get_tile_found(self) -> None:
        t = self._make_tile(0, 0, 0)
        grid = Grid(rows=1, cols=1, tiles=(t,))
        assert grid.get_tile(0, 0) is t

    def test_get_tile_not_found(self) -> None:
        t = self._make_tile(0, 0, 0)
        grid = Grid(rows=1, cols=1, tiles=(t,))
        assert grid.get_tile(1, 0) is None

    def test_get_tiles_in_row(self) -> None:
        t00 = self._make_tile(0, 0, 0)
        t01 = self._make_tile(1, 0, 1)
        t10 = self._make_tile(2, 1, 0)
        grid = Grid(rows=2, cols=2, tiles=(t00, t01, t10))
        row0 = grid.get_tiles_in_row(0)
        assert len(row0) == 2
        assert row0[0] is t00
        assert row0[1] is t01

    def test_get_tiles_in_col(self) -> None:
        t00 = self._make_tile(0, 0, 0)
        t01 = self._make_tile(1, 0, 1)
        t10 = self._make_tile(2, 1, 0)
        grid = Grid(rows=2, cols=2, tiles=(t00, t01, t10))
        col0 = grid.get_tiles_in_col(0)
        assert len(col0) == 2
        assert t00 in col0
        assert t10 in col0

    def test_iteration(self) -> None:
        tiles = tuple(self._make_tile(i, 0, i) for i in range(3))
        grid = Grid(rows=1, cols=3, tiles=tiles)
        count = 0
        for t in grid:
            count += 1
        assert count == 3

    def test_immutable(self) -> None:
        grid = Grid(rows=1, cols=1)
        with pytest.raises(Exception):
            grid.rows = 2  # type: ignore[misc]

    def test_repr(self) -> None:
        grid = Grid(rows=2, cols=3, tiles=tuple(self._make_tile(i, 0, i) for i in range(6)))
        s = repr(grid)
        assert "rows=2" in s
        assert "cols=3" in s
        assert "6" in s


class TestLayoutParams:
    """LayoutParams 测试套件."""

    def test_defaults(self) -> None:
        lp = LayoutParams(
            page_size=Size(1000, 2000),
            target_size=Size(300, 400),
        )
        assert lp.margin_h == 0.0
        assert lp.margin_v == 0.0
        assert lp.overlap == 0.0

    def test_printable_width_no_margin(self) -> None:
        lp = LayoutParams(page_size=Size(1000, 2000), target_size=Size(300, 400))
        assert lp.printable_width == 300

    def test_printable_width_with_margin(self) -> None:
        lp = LayoutParams(page_size=Size(1000, 2000), target_size=Size(300, 400), margin_h=20)
        assert lp.printable_width == 280

    def test_printable_height_with_margin(self) -> None:
        lp = LayoutParams(page_size=Size(1000, 2000), target_size=Size(300, 400), margin_v=30)
        assert lp.printable_height == 370

    def test_validate_negative_page_size_raises(self) -> None:
        lp = LayoutParams(page_size=Size(-1, 100), target_size=Size(300, 400))
        with pytest.raises(ValueError):
            lp.validate()

    def test_validate_negative_margin_raises(self) -> None:
        lp = LayoutParams(page_size=Size(1000, 2000), target_size=Size(300, 400), margin_h=-1)
        with pytest.raises(ValueError):
            lp.validate()

    def test_validate_margin_exceeds_target_raises(self) -> None:
        lp = LayoutParams(page_size=Size(1000, 2000), target_size=Size(300, 400), margin_h=300)
        with pytest.raises(ValueError):
            lp.validate()


class TestLayoutEngine:
    """LayoutEngine 测试套件."""

    def test_single_tile_fits_exactly(self) -> None:
        engine = LayoutEngine()
        params = LayoutParams(
            page_size=Size(100, 200),
            target_size=Size(100, 200),
        )
        grid = engine.calculate(params)
        assert grid.rows == 1
        assert grid.cols == 1
        assert grid.total_tiles == 1
        tile = grid.tiles[0]
        assert tile.source_rect == Rect(0, 0, 100, 200)

    def test_2x2_no_overlap(self) -> None:
        engine = LayoutEngine()
        params = LayoutParams(
            page_size=Size(200, 200),
            target_size=Size(100, 100),
        )
        grid = engine.calculate(params)
        assert grid.rows == 2
        assert grid.cols == 2
        assert grid.total_tiles == 4

    def test_tiles_cover_entire_page(self) -> None:
        engine = LayoutEngine()
        params = LayoutParams(
            page_size=Size(300, 300),
            target_size=Size(100, 100),
        )
        grid = engine.calculate(params)
        union = grid.tiles[0].source_rect
        for tile in grid.tiles[1:]:
            union = union.union(tile.source_rect)
        assert math.isclose(union.width, 300)
        assert math.isclose(union.height, 300)
        assert union.x0 == 0
        assert union.y0 == 0

    def test_overlap_increases_tile_rect(self) -> None:
        engine = LayoutEngine()
        params = LayoutParams(
            page_size=Size(200, 200),
            target_size=Size(100, 100),
            overlap=10,
        )
        grid = engine.calculate(params)
        tile = grid.get_tile(0, 0)
        assert tile is not None
        assert tile.source_rect.width == 110
        assert tile.source_rect.height == 110

    def test_overlap_clipped_at_page_edge(self) -> None:
        engine = LayoutEngine()
        params = LayoutParams(
            page_size=Size(150, 150),
            target_size=Size(100, 100),
            overlap=10,
        )
        grid = engine.calculate(params)
        assert grid.rows == 2
        assert grid.cols == 2
        right_tile = grid.get_tile(0, 1)
        assert right_tile is not None
        assert math.isclose(right_tile.source_rect.x1, 150.0)

    def test_partial_last_tile(self) -> None:
        engine = LayoutEngine()
        params = LayoutParams(
            page_size=Size(250, 100),
            target_size=Size(100, 100),
        )
        grid = engine.calculate(params)
        assert grid.rows == 1
        assert grid.cols == 3
        last_tile = grid.tiles[-1]
        assert math.isclose(last_tile.source_rect.width, 50)
        assert math.isclose(last_tile.source_rect.x0, 200)

    def test_margin_reduces_printable_area(self) -> None:
        engine = LayoutEngine()
        params = LayoutParams(
            page_size=Size(400, 400),
            target_size=Size(200, 200),
            margin_h=50,
            margin_v=50,
        )
        grid = engine.calculate(params)
        tile = grid.get_tile(0, 0)
        assert tile is not None
        assert math.isclose(tile.source_rect.width, 150)
        assert math.isclose(tile.source_rect.height, 150)

    def test_grid_indices_are_sequential(self) -> None:
        engine = LayoutEngine()
        params = LayoutParams(
            page_size=Size(300, 300),
            target_size=Size(100, 100),
        )
        grid = engine.calculate(params)
        for i, tile in enumerate(grid.tiles):
            assert tile.index == i

    def test_grid_row_col_positions(self) -> None:
        engine = LayoutEngine()
        params = LayoutParams(
            page_size=Size(300, 300),
            target_size=Size(100, 100),
        )
        grid = engine.calculate(params)
        assert grid.get_tile(0, 0).col == 0
        assert grid.get_tile(0, 0).row == 0
        assert grid.get_tile(0, 1).col == 1
        assert grid.get_tile(0, 1).row == 0
        assert grid.get_tile(1, 0).col == 0
        assert grid.get_tile(1, 0).row == 1

    @pytest.mark.parametrize(
        "page_w,page_h,target_w,target_h,expected_rows,expected_cols",
        [
            (100, 100, 100, 100, 1, 1),
            (200, 200, 100, 100, 2, 2),
            (300, 200, 100, 100, 2, 3),
            (200, 300, 100, 100, 3, 2),
            (500, 500, 100, 100, 5, 5),
            (150, 100, 100, 100, 1, 2),
            (100, 150, 100, 100, 2, 1),
        ],
    )
    def test_grid_dimensions(
        self, page_w: float, page_h: float, target_w: float, target_h: float,
        expected_rows: int, expected_cols: int,
    ) -> None:
        engine = LayoutEngine()
        params = LayoutParams(
            page_size=Size(page_w, page_h),
            target_size=Size(target_w, target_h),
        )
        grid = engine.calculate(params)
        assert grid.rows == expected_rows
        assert grid.cols == expected_cols
