"""SplitLines and TileOrder tests."""

from __future__ import annotations

import math

import pytest

from pdfsplitter.domain.layout.split_lines import SplitLines
from pdfsplitter.domain.layout.tile_order import TileOrder


class TestSplitLines:
    """SplitLines 测试套件."""

    def test_empty(self) -> None:
        sl = SplitLines.empty()
        assert sl.is_empty is True
        assert sl.col_count == 1
        assert sl.row_count == 1
        assert sl.tile_count == 1

    def test_halved_vertical(self) -> None:
        sl = SplitLines.halved_vertical(100.0)
        assert sl.verticals == (50.0,)
        assert len(sl.horizontals) == 0
        assert sl.col_count == 2
        assert sl.row_count == 1
        assert sl.tile_count == 2

    def test_halved_horizontal(self) -> None:
        sl = SplitLines.halved_horizontal(200.0)
        assert sl.horizontals == (100.0,)
        assert len(sl.verticals) == 0
        assert sl.col_count == 1
        assert sl.row_count == 2
        assert sl.tile_count == 2

    def test_quartered(self) -> None:
        sl = SplitLines.quartered(100.0, 200.0)
        assert sl.verticals == (50.0,)
        assert sl.horizontals == (100.0,)
        assert sl.col_count == 2
        assert sl.row_count == 2
        assert sl.tile_count == 4

    def test_with_vertical_sorted(self) -> None:
        sl = SplitLines(verticals=(100.0,))
        sl2 = sl.with_vertical(50.0)
        assert sl2.verticals == (50.0, 100.0)

    def test_with_horizontal_sorted(self) -> None:
        sl = SplitLines(horizontals=(200.0,))
        sl2 = sl.with_horizontal(100.0)
        assert sl2.horizontals == (100.0, 200.0)

    def test_remove_vertical(self) -> None:
        sl = SplitLines(verticals=(50.0, 100.0, 150.0))
        sl2 = sl.remove_vertical(1)
        assert sl2.verticals == (50.0, 150.0)

    def test_remove_vertical_invalid_index(self) -> None:
        sl = SplitLines(verticals=(50.0,))
        with pytest.raises(IndexError):
            sl.remove_vertical(5)

    def test_remove_horizontal(self) -> None:
        sl = SplitLines(horizontals=(50.0, 100.0))
        sl2 = sl.remove_horizontal(0)
        assert sl2.horizontals == (100.0,)

    def test_move_vertical(self) -> None:
        sl = SplitLines(verticals=(50.0, 150.0))
        sl2 = sl.move_vertical(0, 80.0)
        assert sl2.verticals == (80.0, 150.0)

    def test_move_horizontal_clamped(self) -> None:
        sl = SplitLines(horizontals=(50.0,))
        sl2 = sl.move_horizontal(0, -10.0, min_y=0.0, max_y=100.0)
        assert sl2.horizontals == (0.0,)

    def test_move_horizontal_clamped_max(self) -> None:
        sl = SplitLines(horizontals=(50.0,))
        sl2 = sl.move_horizontal(0, 200.0, max_y=100.0)
        assert sl2.horizontals == (100.0,)

    def test_immutable(self) -> None:
        sl = SplitLines(verticals=(50.0,))
        with pytest.raises(Exception):
            sl.verticals = (60.0,)  # type: ignore[misc]

    def test_sorted_preservation(self) -> None:
        sl = SplitLines.empty()
        sl = sl.with_vertical(100.0).with_vertical(30.0).with_vertical(60.0)
        assert sl.verticals == (30.0, 60.0, 100.0)


class TestTileOrder:
    """TileOrder 测试套件."""

    def test_auto(self) -> None:
        order = TileOrder.auto(5)
        assert order.indices == (0, 1, 2, 3, 4)
        assert order.mode == "auto"
        assert order.count == 5

    def test_with_manual_order(self) -> None:
        order = TileOrder.auto(4)
        manual = order.with_manual_order([3, 1, 0, 2])
        assert manual.indices == (3, 1, 0, 2)
        assert manual.mode == "manual"

    def test_immutable(self) -> None:
        order = TileOrder.auto(3)
        with pytest.raises(Exception):
            order.indices = (1, 2, 3)  # type: ignore[misc]
