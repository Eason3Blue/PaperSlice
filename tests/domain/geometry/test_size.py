from __future__ import annotations

import pytest

from pdfsplitter.domain.geometry.size import Size


class TestSize:
    """Size 值对象测试套件."""

    def test_creation(self) -> None:
        s = Size(100.0, 200.0)
        assert s.w == 100.0
        assert s.h == 200.0

    def test_immutable(self) -> None:
        s = Size(1.0, 2.0)
        with pytest.raises(Exception):
            s.w = 5.0  # type: ignore[misc]

    def test_equality(self) -> None:
        assert Size(100.0, 200.0) == Size(100.0, 200.0)
        assert Size(100.0, 200.0) != Size(100.0, 201.0)

    def test_hash(self) -> None:
        a = Size(100.0, 200.0)
        b = Size(100.0, 200.0)
        assert hash(a) == hash(b)

    def test_area(self) -> None:
        s = Size(10.0, 20.0)
        assert s.area == 200.0

    def test_aspect_ratio(self) -> None:
        s = Size(200.0, 100.0)
        assert s.aspect_ratio == 2.0

    def test_aspect_ratio_zero_height(self) -> None:
        s = Size(100.0, 0.0)
        assert s.aspect_ratio == float("inf")

    def test_is_landscape(self) -> None:
        assert Size(200.0, 100.0).is_landscape is True
        assert Size(100.0, 200.0).is_landscape is False

    def test_is_portrait(self) -> None:
        assert Size(100.0, 200.0).is_portrait is True
        assert Size(200.0, 100.0).is_portrait is False

    def test_is_square(self) -> None:
        assert Size(100.0, 100.0).is_square is True
        assert Size(100.0, 200.0).is_square is False

    def test_scale_uniform(self) -> None:
        s = Size(100.0, 200.0)
        result = s.scale(2.0)
        assert result == Size(200.0, 400.0)

    def test_scale_non_uniform(self) -> None:
        s = Size(100.0, 200.0)
        result = s.scale(2.0, 0.5)
        assert result == Size(200.0, 100.0)

    def test_to_tuple(self) -> None:
        s = Size(100.0, 200.0)
        assert s.to_tuple() == (100.0, 200.0)

    def test_flipped(self) -> None:
        s = Size(100.0, 200.0)
        assert s.flipped() == Size(200.0, 100.0)

    def test_equality_with_non_size(self) -> None:
        assert (Size(1.0, 2.0) == "not_a_size") is False
