from __future__ import annotations

import math

import pytest

from pdfsplitter.domain.geometry.point import Point


class TestPoint:
    """Point 值对象测试套件."""

    def test_creation(self) -> None:
        p = Point(3.0, 4.0)
        assert p.x == 3.0
        assert p.y == 4.0

    def test_immutable(self) -> None:
        p = Point(1.0, 2.0)
        with pytest.raises(Exception):
            p.x = 5.0  # type: ignore[misc]

    def test_equality(self) -> None:
        assert Point(1.0, 2.0) == Point(1.0, 2.0)
        assert Point(1.0, 2.0) != Point(1.0, 3.0)

    def test_equality_floating_point_tolerance(self) -> None:
        a = Point(1.0 / 3.0, 2.0)
        b = Point(1.0 / 3.0, 2.0)
        assert a == b

    def test_hash(self) -> None:
        a = Point(1.0, 2.0)
        b = Point(1.0, 2.0)
        assert hash(a) == hash(b)

    def test_hash_stability(self) -> None:
        points = {Point(1.0, 2.0), Point(1.0, 2.0)}
        assert len(points) == 1

    def test_addition(self) -> None:
        result = Point(1.0, 2.0) + Point(3.0, 4.0)
        assert result == Point(4.0, 6.0)

    def test_subtraction(self) -> None:
        result = Point(5.0, 7.0) - Point(2.0, 3.0)
        assert result == Point(3.0, 4.0)

    def test_scalar_multiplication(self) -> None:
        result = Point(2.0, 3.0) * 2.0
        assert result == Point(4.0, 6.0)

    def test_right_scalar_multiplication(self) -> None:
        result = 2.0 * Point(2.0, 3.0)
        assert result == Point(4.0, 6.0)

    def test_division(self) -> None:
        result = Point(4.0, 6.0) / 2.0
        assert result == Point(2.0, 3.0)

    def test_negation(self) -> None:
        result = -Point(1.0, -2.0)
        assert result == Point(-1.0, 2.0)

    def test_distance_to(self) -> None:
        a = Point(0.0, 0.0)
        b = Point(3.0, 4.0)
        assert math.isclose(a.distance_to(b), 5.0)

    def test_distance_to_same_point(self) -> None:
        a = Point(1.0, 1.0)
        assert a.distance_to(a) == 0.0

    def test_to_tuple(self) -> None:
        p = Point(3.0, 4.0)
        assert p.to_tuple() == (3.0, 4.0)

    def test_origin(self) -> None:
        origin = Point.origin()
        assert origin == Point(0.0, 0.0)

    def test_equality_with_non_point(self) -> None:
        assert Point(1.0, 2.0) != "not_a_point"
        assert (Point(1.0, 2.0) == "not_a_point") is False
