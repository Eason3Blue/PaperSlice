from __future__ import annotations

import math

import pytest

from pdfsplitter.domain.geometry.margin import Margin


class TestMargin:
    """Margin 值对象测试套件."""

    def test_creation(self) -> None:
        m = Margin(1.0, 2.0, 3.0, 4.0)
        assert m.left == 1.0
        assert m.right == 2.0
        assert m.top == 3.0
        assert m.bottom == 4.0

    def test_immutable(self) -> None:
        m = Margin(1.0, 2.0, 3.0, 4.0)
        with pytest.raises(Exception):
            m.left = 5.0  # type: ignore[misc]

    def test_horizontal(self) -> None:
        m = Margin(10.0, 20.0, 5.0, 15.0)
        assert math.isclose(m.horizontal, 30.0)

    def test_vertical(self) -> None:
        m = Margin(10.0, 20.0, 5.0, 15.0)
        assert math.isclose(m.vertical, 20.0)

    def test_is_uniform_true(self) -> None:
        m = Margin(10.0, 10.0, 10.0, 10.0)
        assert m.is_uniform is True

    def test_is_uniform_false(self) -> None:
        m = Margin(10.0, 20.0, 10.0, 10.0)
        assert m.is_uniform is False

    def test_to_tuple(self) -> None:
        m = Margin(1.0, 2.0, 3.0, 4.0)
        assert m.to_tuple() == (1.0, 2.0, 3.0, 4.0)

    def test_symmetric(self) -> None:
        m = Margin.symmetric(horizontal=5.0, vertical=10.0)
        assert m == Margin(5.0, 5.0, 10.0, 10.0)

    def test_symmetric_defaults(self) -> None:
        m = Margin.symmetric()
        assert m == Margin(0.0, 0.0, 0.0, 0.0)

    def test_uniform(self) -> None:
        m = Margin.uniform(5.0)
        assert m == Margin(5.0, 5.0, 5.0, 5.0)

    def test_uniform_default(self) -> None:
        m = Margin.uniform()
        assert m == Margin(0.0, 0.0, 0.0, 0.0)

    def test_zero(self) -> None:
        m = Margin.zero()
        assert m == Margin(0.0, 0.0, 0.0, 0.0)

    def test_equality(self) -> None:
        a = Margin(1.0, 2.0, 3.0, 4.0)
        b = Margin(1.0, 2.0, 3.0, 4.0)
        assert a == b

    def test_inequality(self) -> None:
        a = Margin(1.0, 2.0, 3.0, 4.0)
        b = Margin(1.0, 2.0, 3.0, 5.0)
        assert a != b

    def test_hash(self) -> None:
        a = Margin(1.0, 2.0, 3.0, 4.0)
        b = Margin(1.0, 2.0, 3.0, 4.0)
        assert hash(a) == hash(b)
