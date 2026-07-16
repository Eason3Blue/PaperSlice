from __future__ import annotations

import logging
from typing import ClassVar

from pdfsplitter.domain.geometry.size import Size
from pdfsplitter.domain.paper.paper_spec import PaperSpec

logger = logging.getLogger(__name__)


class PaperDatabase:
    """纸张规格注册表, 支持标准纸张和自定义纸张的查找.

    支持的标准:
        - ISO216: A0-A10, B0-B10
        - ANSI: A-E
        - NorthAmerican: Letter, Legal, Tabloid, Ledger

    支持 registration 扩展.
    """

    _instance: ClassVar[PaperDatabase | None] = None
    _specs: dict[str, PaperSpec]

    def __init__(self) -> None:
        self._specs = {}
        self._register_iso216()
        self._register_ansi()
        self._register_north_american()

    @classmethod
    def instance(cls) -> PaperDatabase:
        """获取全局单例."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置单例 (主要用于测试)."""
        cls._instance = None

    def register(self, spec: PaperSpec) -> None:
        """注册一张纸张规格.

        Args:
            spec: 纸张规格.
        """
        key = self._make_key(spec.name, spec.category)
        self._specs[key] = spec

    def get(self, name: str, category: str = "ISO216") -> PaperSpec | None:
        """按名称和类别查找纸张.

        Args:
            name: 纸张名称.
            category: 类别, 默认 ISO216.

        Returns:
            找到的 PaperSpec, 不存在则返回 None.
        """
        key = self._make_key(name, category)
        return self._specs.get(key)

    def get_or_raise(self, name: str, category: str = "ISO216") -> PaperSpec:
        """按名称查找, 不存在则抛出 KeyError."""
        spec = self.get(name, category)
        if spec is None:
            raise KeyError(f"Paper '{name}' not found in category '{category}'")
        return spec

    def list_all(self) -> list[PaperSpec]:
        """列出所有已注册的纸张规格."""
        return list(self._specs.values())

    def list_by_category(self, category: str) -> list[PaperSpec]:
        """按类别列出纸张规格.

        Args:
            category: 类别名称.

        Returns:
            该类别下的所有 PaperSpec.
        """
        return [s for s in self._specs.values() if s.category == category]

    def list_names(self, category: str | None = None) -> list[str]:
        """列出纸张名称.

        Args:
            category: 可选, 限定类别.

        Returns:
            纸张名称列表.
        """
        if category:
            return [s.name for s in self.list_by_category(category)]
        return [s.name for s in self._specs.values()]

    @staticmethod
    def _make_key(name: str, category: str) -> str:
        return f"{category}::{name}"

    def _register_iso216(self) -> None:
        """注册 ISO216 A 系列和 B 系列."""
        iso_specs: list[tuple[str, float, float]] = [
            ("A0", 841.0, 1189.0),
            ("A1", 594.0, 841.0),
            ("A2", 420.0, 594.0),
            ("A3", 297.0, 420.0),
            ("A4", 210.0, 297.0),
            ("A5", 148.0, 210.0),
            ("A6", 105.0, 148.0),
            ("A7", 74.0, 105.0),
            ("A8", 52.0, 74.0),
            ("A9", 37.0, 52.0),
            ("A10", 26.0, 37.0),
            ("B0", 1000.0, 1414.0),
            ("B1", 707.0, 1000.0),
            ("B2", 500.0, 707.0),
            ("B3", 353.0, 500.0),
            ("B4", 250.0, 353.0),
            ("B5", 176.0, 250.0),
            ("B6", 125.0, 176.0),
            ("B7", 88.0, 125.0),
            ("B8", 62.0, 88.0),
            ("B9", 44.0, 62.0),
            ("B10", 31.0, 44.0),
        ]
        for name, w, h in iso_specs:
            self.register(PaperSpec(name=name, category="ISO216", size=Size(w, h)))

    def _register_ansi(self) -> None:
        """注册 ANSI 纸张."""
        ansi_specs: list[tuple[str, float, float]] = [
            ("A", 216.0, 279.0),
            ("B", 279.0, 432.0),
            ("C", 432.0, 559.0),
            ("D", 559.0, 864.0),
            ("E", 864.0, 1118.0),
        ]
        for name, w, h in ansi_specs:
            self.register(PaperSpec(name=f"ANSI {name}", category="ANSI", size=Size(w, h)))

    def _register_north_american(self) -> None:
        """注册北美常用纸张."""
        na_specs: list[tuple[str, float, float]] = [
            ("Letter", 215.9, 279.4),
            ("Legal", 215.9, 355.6),
            ("Tabloid", 279.4, 431.8),
            ("Ledger", 431.8, 279.4),
        ]
        for name, w, h in na_specs:
            self.register(PaperSpec(name=name, category="NorthAmerican", size=Size(w, h)))
