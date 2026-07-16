from __future__ import annotations

from pdfsplitter.domain.geometry.point import Point
from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.geometry.size import Size
from pdfsplitter.domain.geometry.transform import Transform


class TestTransform:
    """Transform 变换对象测试套件."""

    def test_identity(self) -> None:
        t = Transform.identity()
        assert t.translate_x == 0.0
        assert t.translate_y == 0.0
        assert t.scale_x == 1.0
        assert t.scale_y == 1.0
        assert t.rotation == 0.0

    def test_identity_transforms_point_unchanged(self) -> None:
        t = Transform.identity()
        p = Point(10.0, 20.0)
        assert t.transform_point(p) == p

    def test_translation(self) -> None:
        t = Transform.translation(10.0, 20.0)
        p = Point(5.0, 5.0)
        result = t.transform_point(p)
        assert result == Point(15.0, 25.0)

    def test_scaling_uniform(self) -> None:
        t = Transform.scaling(2.0)
        p = Point(10.0, 20.0)
        result = t.transform_point(p)
        assert result == Point(20.0, 40.0)

    def test_scaling_non_uniform(self) -> None:
        t = Transform.scaling(2.0, 3.0)
        p = Point(10.0, 20.0)
        result = t.transform_point(p)
        assert result == Point(20.0, 60.0)

    def test_transform_rect(self) -> None:
        t = Transform(translate_x=10.0, translate_y=20.0, scale_x=2.0, scale_y=2.0)
        r = Rect(0.0, 0.0, 100.0, 200.0)
        result = t.transform_rect(r)
        assert result == Rect(10.0, 20.0, 210.0, 420.0)

    def test_transform_size(self) -> None:
        t = Transform(scale_x=2.0, scale_y=3.0)
        s = Size(100.0, 200.0)
        result = t.transform_size(s)
        assert result == Size(200.0, 600.0)

    def test_compose_translations(self) -> None:
        a = Transform.translation(10.0, 0.0)
        b = Transform.translation(0.0, 20.0)
        combined = a.compose(b)
        p = Point(5.0, 5.0)
        assert combined.transform_point(p) == Point(15.0, 25.0)

    def test_compose_scaling(self) -> None:
        a = Transform.scaling(2.0)
        b = Transform.scaling(3.0)
        combined = a.compose(b)
        p = Point(10.0, 20.0)
        assert combined.transform_point(p) == Point(60.0, 120.0)

    def test_immutable(self) -> None:
        t = Transform()
        with pytest.raises(Exception):
            t.translate_x = 5.0  # type: ignore[misc]


import pytest
