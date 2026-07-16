from __future__ import annotations

import math

import pytest

from pdfsplitter.domain.units.length import Length


class TestLength:
    """Length 值对象测试套件."""

    def test_from_millimeter(self) -> None:
        l = Length.from_millimeter(10.0)
        assert l.mm == 10.0

    def test_from_point(self) -> None:
        l = Length.from_point(72.0)
        assert math.isclose(l.mm, 25.4)

    def test_from_inch(self) -> None:
        l = Length.from_inch(1.0)
        assert math.isclose(l.mm, 25.4)

    def test_from_pixel_default_dpi(self) -> None:
        l = Length.from_pixel(72.0)
        assert math.isclose(l.mm, 25.4)

    def test_from_pixel_custom_dpi(self) -> None:
        l = Length.from_pixel(300.0, dpi=300)
        assert math.isclose(l.mm, 25.4)

    def test_zero(self) -> None:
        l = Length.zero()
        assert l.mm == 0.0

    def test_to_point(self) -> None:
        l = Length.from_inch(1.0)
        assert math.isclose(l.pt, 72.0)

    def test_to_inch(self) -> None:
        l = Length.from_millimeter(25.4)
        assert math.isclose(l.inch, 1.0)

    def test_to_pixel_default_dpi(self) -> None:
        l = Length.from_inch(1.0)
        assert math.isclose(l.pixel(), 72.0)

    def test_to_pixel_custom_dpi(self) -> None:
        l = Length.from_inch(1.0)
        assert math.isclose(l.pixel(dpi=300), 300.0)

    def test_to_millimeter(self) -> None:
        l = Length.from_inch(1.0)
        assert math.isclose(l.to_millimeter(), 25.4)

    def test_to_point_method(self) -> None:
        l = Length.from_inch(1.0)
        assert math.isclose(l.to_point(), 72.0)

    def test_to_inch_method(self) -> None:
        l = Length.from_millimeter(25.4)
        assert math.isclose(l.to_inch(), 1.0)

    def test_to_pixel_method(self) -> None:
        l = Length.from_inch(1.0)
        assert math.isclose(l.to_pixel(dpi=150), 150.0)

    def test_addition(self) -> None:
        a = Length.from_millimeter(10.0)
        b = Length.from_millimeter(20.0)
        assert (a + b).mm == 30.0

    def test_subtraction(self) -> None:
        a = Length.from_millimeter(30.0)
        b = Length.from_millimeter(10.0)
        assert (a - b).mm == 20.0

    def test_multiplication(self) -> None:
        a = Length.from_millimeter(10.0)
        assert (a * 3.0).mm == 30.0

    def test_right_multiplication(self) -> None:
        a = Length.from_millimeter(10.0)
        assert (3.0 * a).mm == 30.0

    def test_division(self) -> None:
        a = Length.from_millimeter(30.0)
        assert (a / 3.0).mm == 10.0

    def test_negation(self) -> None:
        a = Length.from_millimeter(10.0)
        assert (-a).mm == -10.0

    def test_equality(self) -> None:
        a = Length.from_millimeter(25.4)
        b = Length.from_inch(1.0)
        assert a == b

    def test_inequality(self) -> None:
        a = Length.from_millimeter(25.4)
        b = Length.from_millimeter(25.5)
        assert a != b

    def test_hash(self) -> None:
        a = Length.from_millimeter(25.4)
        b = Length.from_millimeter(25.4)
        assert hash(a) == hash(b)

    def test_comparisons(self) -> None:
        a = Length.from_millimeter(10.0)
        b = Length.from_millimeter(20.0)
        assert a < b
        assert a <= b
        assert b > a
        assert b >= a
        assert a <= a
        assert a >= a

    def test_immutable(self) -> None:
        l = Length.from_millimeter(10.0)
        with pytest.raises(Exception):
            l.mm = 5.0  # type: ignore[misc]

    def test_equality_with_non_length(self) -> None:
        assert (Length.zero() == "not_a_length") is False

    def test_repr(self) -> None:
        l = Length.from_millimeter(10.0)
        repr_str = repr(l)
        assert "10" in repr_str
        assert "mm" in repr_str

    @pytest.mark.parametrize(
        "mm_value,pt_value",
        [
            (0.0, 0.0),
            (25.4, 72.0),
            (12.7, 36.0),
            (254.0, 720.0),
        ],
    )
    def test_roundtrip_mm_to_pt(self, mm_value: float, pt_value: float) -> None:
        l = Length.from_millimeter(mm_value)
        assert math.isclose(l.pt, pt_value)

    @pytest.mark.parametrize(
        "inch_value,mm_value",
        [
            (0.0, 0.0),
            (1.0, 25.4),
            (2.0, 50.8),
            (0.5, 12.7),
        ],
    )
    def test_roundtrip_inch_to_mm(self, inch_value: float, mm_value: float) -> None:
        l = Length.from_inch(inch_value)
        assert math.isclose(l.mm, mm_value)
