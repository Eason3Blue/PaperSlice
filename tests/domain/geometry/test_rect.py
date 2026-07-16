from __future__ import annotations

import math

import pytest

from pdfsplitter.domain.geometry.margin import Margin
from pdfsplitter.domain.geometry.point import Point
from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.geometry.size import Size


class TestRect:
    """Rect 值对象测试套件."""

    def test_creation(self) -> None:
        r = Rect(0.0, 0.0, 100.0, 200.0)
        assert r.x0 == 0.0
        assert r.y0 == 0.0
        assert r.x1 == 100.0
        assert r.y1 == 200.0

    def test_normalization(self) -> None:
        r = Rect(100.0, 200.0, 0.0, 0.0)
        assert r.x0 == 0.0
        assert r.y0 == 0.0
        assert r.x1 == 100.0
        assert r.y1 == 200.0

    def test_width(self) -> None:
        r = Rect(10.0, 20.0, 110.0, 220.0)
        assert r.width == 100.0

    def test_height(self) -> None:
        r = Rect(10.0, 20.0, 110.0, 220.0)
        assert r.height == 200.0

    def test_area(self) -> None:
        r = Rect(0.0, 0.0, 10.0, 20.0)
        assert r.area == 200.0

    def test_size(self) -> None:
        r = Rect(0.0, 0.0, 100.0, 200.0)
        assert r.size == Size(100.0, 200.0)

    def test_center(self) -> None:
        r = Rect(0.0, 0.0, 100.0, 200.0)
        assert r.center == Point(50.0, 100.0)

    def test_corners(self) -> None:
        r = Rect(0.0, 0.0, 100.0, 200.0)
        assert r.top_left == Point(0.0, 200.0)
        assert r.top_right == Point(100.0, 200.0)
        assert r.bottom_left == Point(0.0, 0.0)
        assert r.bottom_right == Point(100.0, 0.0)

    def test_is_empty(self) -> None:
        assert Rect(0.0, 0.0, 0.0, 0.0).is_empty is True
        assert Rect(0.0, 0.0, 100.0, 0.0).is_empty is True
        assert Rect(0.0, 0.0, 100.0, 200.0).is_empty is False

    def test_intersection_overlapping(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 100.0)
        b = Rect(50.0, 50.0, 150.0, 150.0)
        result = a.intersection(b)
        assert result is not None
        assert result == Rect(50.0, 50.0, 100.0, 100.0)

    def test_intersection_contained(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 100.0)
        b = Rect(20.0, 20.0, 80.0, 80.0)
        result = a.intersection(b)
        assert result is not None
        assert result == b

    def test_intersection_disjoint(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 100.0)
        b = Rect(200.0, 200.0, 300.0, 300.0)
        result = a.intersection(b)
        assert result is None

    def test_intersection_touching_edge(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 100.0)
        b = Rect(100.0, 0.0, 200.0, 100.0)
        result = a.intersection(b)
        assert result is None

    def test_union(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 100.0)
        b = Rect(50.0, 50.0, 150.0, 150.0)
        result = a.union(b)
        assert result == Rect(0.0, 0.0, 150.0, 150.0)

    def test_union_disjoint(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 100.0)
        b = Rect(200.0, 200.0, 300.0, 300.0)
        result = a.union(b)
        assert result == Rect(0.0, 0.0, 300.0, 300.0)

    def test_contains_point(self) -> None:
        r = Rect(0.0, 0.0, 100.0, 100.0)
        assert r.contains(Point(50.0, 50.0)) is True
        assert r.contains(Point(0.0, 0.0)) is True
        assert r.contains(Point(100.0, 100.0)) is True
        assert r.contains(Point(150.0, 50.0)) is False

    def test_contains_rect(self) -> None:
        outer = Rect(0.0, 0.0, 100.0, 100.0)
        inner = Rect(20.0, 20.0, 80.0, 80.0)
        assert outer.contains_rect(inner) is True
        assert inner.contains_rect(outer) is False

    def test_overlaps(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 100.0)
        b = Rect(50.0, 50.0, 150.0, 150.0)
        assert a.overlaps(b) is True

    def test_overlaps_disjoint(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 100.0)
        b = Rect(200.0, 200.0, 300.0, 300.0)
        assert a.overlaps(b) is False

    def test_translate(self) -> None:
        r = Rect(10.0, 20.0, 110.0, 220.0)
        result = r.translate(5.0, -10.0)
        assert result == Rect(15.0, 10.0, 115.0, 210.0)

    def test_translate_point(self) -> None:
        r = Rect(10.0, 20.0, 110.0, 220.0)
        result = r.translate_point(Point(5.0, -10.0))
        assert result == Rect(15.0, 10.0, 115.0, 210.0)

    def test_inflate_positive(self) -> None:
        r = Rect(10.0, 10.0, 100.0, 100.0)
        m = Margin.uniform(5.0)
        result = r.inflate(m)
        assert result == Rect(5.0, 5.0, 105.0, 105.0)

    def test_inflate_negative(self) -> None:
        r = Rect(10.0, 10.0, 100.0, 100.0)
        m = Margin.uniform(-5.0)
        result = r.inflate(m)
        assert result == Rect(15.0, 15.0, 95.0, 95.0)

    def test_inflate_asymmetric(self) -> None:
        r = Rect(10.0, 10.0, 100.0, 100.0)
        m = Margin(1.0, 2.0, 3.0, 4.0)
        result = r.inflate(m)
        assert result == Rect(9.0, 6.0, 102.0, 103.0)

    def test_inflate_uniform(self) -> None:
        r = Rect(10.0, 10.0, 100.0, 100.0)
        result = r.inflate_uniform(5.0)
        assert result == Rect(5.0, 5.0, 105.0, 105.0)

    def test_scale_uniform_from_origin(self) -> None:
        r = Rect(0.0, 0.0, 100.0, 200.0)
        result = r.scale(2.0)
        assert result == Rect(0.0, 0.0, 200.0, 400.0)

    def test_scale_from_center(self) -> None:
        r = Rect(0.0, 0.0, 100.0, 200.0)
        center = Point(50.0, 100.0)
        result = r.scale(2.0, 2.0, center)
        assert result == Rect(-50.0, -100.0, 150.0, 300.0)

    def test_scale_non_uniform(self) -> None:
        r = Rect(0.0, 0.0, 100.0, 200.0)
        result = r.scale(0.5, 2.0)
        assert result == Rect(0.0, 0.0, 50.0, 400.0)

    def test_clip(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 100.0)
        b = Rect(50.0, 50.0, 150.0, 150.0)
        result = a.clip(b)
        assert result is not None
        assert result == Rect(50.0, 50.0, 100.0, 100.0)

    def test_to_quad(self) -> None:
        r = Rect(1.0, 2.0, 3.0, 4.0)
        assert r.to_quad() == (1.0, 2.0, 3.0, 4.0)

    def test_to_tuple(self) -> None:
        r = Rect(1.0, 2.0, 3.0, 4.0)
        assert r.to_tuple() == (1.0, 2.0, 3.0, 4.0)

    def test_from_points(self) -> None:
        r = Rect.from_points(Point(10.0, 20.0), Point(110.0, 220.0))
        assert r == Rect(10.0, 20.0, 110.0, 220.0)

    def test_from_points_reversed(self) -> None:
        r = Rect.from_points(Point(110.0, 220.0), Point(10.0, 20.0))
        assert r == Rect(10.0, 20.0, 110.0, 220.0)

    def test_from_origin_size(self) -> None:
        r = Rect.from_origin_size(Point(10.0, 20.0), Size(100.0, 200.0))
        assert r == Rect(10.0, 20.0, 110.0, 220.0)

    def test_from_center(self) -> None:
        r = Rect.from_center(Point(50.0, 100.0), Size(100.0, 200.0))
        assert r == Rect(0.0, 0.0, 100.0, 200.0)

    def test_equality(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 200.0)
        b = Rect(0.0, 0.0, 100.0, 200.0)
        assert a == b

    def test_inequality(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 200.0)
        b = Rect(0.0, 0.0, 100.0, 201.0)
        assert a != b

    def test_hash(self) -> None:
        a = Rect(0.0, 0.0, 100.0, 200.0)
        b = Rect(0.0, 0.0, 100.0, 200.0)
        assert hash(a) == hash(b)

    def test_hash_set(self) -> None:
        rects = {Rect(0.0, 0.0, 100.0, 200.0), Rect(0.0, 0.0, 100.0, 200.0)}
        assert len(rects) == 1

    def test_immutable(self) -> None:
        r = Rect(0.0, 0.0, 100.0, 200.0)
        with pytest.raises(Exception):
            r.x0 = 5.0  # type: ignore[misc]

    def test_empty_class_var(self) -> None:
        assert Rect.EMPTY == Rect(0.0, 0.0, 0.0, 0.0)
        assert Rect.EMPTY.is_empty is True

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (Rect(0, 0, 100, 100), Rect(25, 25, 50, 50), True),
            (Rect(25, 25, 50, 50), Rect(0, 0, 100, 100), False),
            (Rect(0, 0, 100, 100), Rect(90, 90, 110, 110), False),
        ],
    )
    def test_contains_rect_parametrized(self, a: Rect, b: Rect, expected: bool) -> None:
        assert a.contains_rect(b) is expected

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (Rect(0, 0, 100, 100), Rect(50, 50, 150, 150), True),
            (Rect(0, 0, 100, 100), Rect(200, 200, 300, 300), False),
            (Rect(0, 0, 100, 100), Rect(100, 100, 200, 200), False),
        ],
    )
    def test_overlaps_parametrized(self, a: Rect, b: Rect, expected: bool) -> None:
        assert a.overlaps(b) is expected
