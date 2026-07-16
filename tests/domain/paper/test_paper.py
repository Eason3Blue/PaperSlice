from __future__ import annotations

import math

import pytest

from pdfsplitter.domain.geometry.size import Size
from pdfsplitter.domain.paper.paper_database import PaperDatabase
from pdfsplitter.domain.paper.paper_spec import PaperSpec


class TestPaperSpec:
    """PaperSpec 值对象测试套件."""

    def test_creation(self) -> None:
        spec = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        assert spec.name == "A4"
        assert spec.category == "ISO216"
        assert spec.size == Size(210.0, 297.0)

    def test_width(self) -> None:
        spec = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        assert math.isclose(spec.width.mm, 210.0)

    def test_height(self) -> None:
        spec = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        assert math.isclose(spec.height.mm, 297.0)

    def test_area(self) -> None:
        spec = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        assert math.isclose(spec.area, 62370.0)

    def test_is_portrait(self) -> None:
        spec = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        assert spec.is_portrait is True

    def test_is_landscape(self) -> None:
        spec = PaperSpec(name="Ledger", category="NorthAmerican", size=Size(431.8, 279.4))
        assert spec.is_landscape is True

    def test_rotated(self) -> None:
        spec = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        rotated = spec.rotated()
        assert rotated.size == Size(297.0, 210.0)
        assert rotated.is_landscape is True
        assert rotated.name == "A4 (L)"

    def test_custom(self) -> None:
        spec = PaperSpec.custom("MyPaper", 100.0, 200.0, "Test paper")
        assert spec.name == "MyPaper"
        assert spec.category == "Custom"
        assert spec.size == Size(100.0, 200.0)
        assert spec.description == "Test paper"

    def test_immutable(self) -> None:
        spec = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        with pytest.raises(Exception):
            spec.name = "A3"  # type: ignore[misc]

    def test_equality(self) -> None:
        a = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        b = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        assert a == b

    def test_hash(self) -> None:
        a = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        b = PaperSpec(name="A4", category="ISO216", size=Size(210.0, 297.0))
        assert hash(a) == hash(b)


class TestPaperDatabase:
    """PaperDatabase 纸张注册表测试套件."""

    def setup_method(self) -> None:
        PaperDatabase.reset()

    def test_singleton(self) -> None:
        db1 = PaperDatabase.instance()
        db2 = PaperDatabase.instance()
        assert db1 is db2

    def test_get_iso_a4(self) -> None:
        db = PaperDatabase.instance()
        spec = db.get("A4")
        assert spec is not None
        assert spec.size == Size(210.0, 297.0)

    def test_get_iso_a0(self) -> None:
        db = PaperDatabase.instance()
        spec = db.get("A0")
        assert spec is not None
        assert spec.size == Size(841.0, 1189.0)

    def test_get_iso_b5(self) -> None:
        db = PaperDatabase.instance()
        spec = db.get("B5")
        assert spec is not None
        assert spec.size == Size(176.0, 250.0)

    def test_get_nonexistent(self) -> None:
        db = PaperDatabase.instance()
        spec = db.get("Z999")
        assert spec is None

    def test_get_or_raise(self) -> None:
        db = PaperDatabase.instance()
        spec = db.get_or_raise("A4")
        assert spec.name == "A4"

    def test_get_or_raise_missing(self) -> None:
        db = PaperDatabase.instance()
        with pytest.raises(KeyError):
            db.get_or_raise("Z999")

    def test_get_ansi(self) -> None:
        db = PaperDatabase.instance()
        spec = db.get("ANSI A", category="ANSI")
        assert spec is not None
        assert spec.size == Size(216.0, 279.0)

    def test_get_letter(self) -> None:
        db = PaperDatabase.instance()
        spec = db.get("Letter", category="NorthAmerican")
        assert spec is not None
        assert math.isclose(spec.size.w, 215.9)
        assert math.isclose(spec.size.h, 279.4)

    def test_get_legal(self) -> None:
        db = PaperDatabase.instance()
        spec = db.get("Legal", category="NorthAmerican")
        assert spec is not None
        assert math.isclose(spec.size.h, 355.6)

    def test_list_all(self) -> None:
        db = PaperDatabase.instance()
        all_specs = db.list_all()
        assert len(all_specs) >= 27

    def test_list_by_category_iso(self) -> None:
        db = PaperDatabase.instance()
        iso = db.list_by_category("ISO216")
        assert len(iso) == 22  # A0-A10 + B0-B10

    def test_list_by_category_north_american(self) -> None:
        db = PaperDatabase.instance()
        na = db.list_by_category("NorthAmerican")
        assert len(na) == 4

    def test_list_names(self) -> None:
        db = PaperDatabase.instance()
        names = db.list_names("ISO216")
        assert "A4" in names
        assert "B5" in names

    def test_register_custom(self) -> None:
        db = PaperDatabase.instance()
        custom = PaperSpec.custom("Custom1", 100.0, 200.0)
        db.register(custom)
        retrieved = db.get("Custom1", category="Custom")
        assert retrieved is not None
        assert retrieved.size == Size(100.0, 200.0)

    def test_iso_a_series_scaling(self) -> None:
        db = PaperDatabase.instance()
        a4 = db.get_or_raise("A4")
        a3 = db.get_or_raise("A3")
        assert math.isclose(a3.size.w, a4.size.h, rel_tol=0.01)
        assert math.isclose(a3.size.h, a4.size.w * 2, rel_tol=0.01)
