from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from pdfsplitter.domain.document.page import Page


@dataclass(frozen=True)
class Document:
    """不可变的文档领域对象.

    Attributes:
        path: 文档主文件路径 (单文件时即为源文件, 多文件时为第一个).
        pages: 页面列表.
        source_paths: 所有源文件路径 (单文件时为空或等于 (path,)).
        title: 文档标题 (可选).
        author: 作者 (可选).
    """

    path: Path
    pages: tuple[Page, ...] = field(default_factory=tuple)
    source_paths: tuple[Path, ...] = field(default_factory=tuple)
    title: str | None = None
    author: str | None = None

    @property
    def page_count(self) -> int:
        """页数."""
        return len(self.pages)

    @property
    def filename(self) -> str:
        """文件名 (不含路径)."""
        return self.path.name

    def __iter__(self) -> Iterator[Page]:
        return iter(self.pages)

    def get_page(self, index: int) -> Page:
        """按索引获取页面.

        Args:
            index: 页索引 (0-based).

        Returns:
            对应的 Page.

        Raises:
            IndexError: 索引超出范围.
        """
        if index < 0:
            index = index + self.page_count
        if 0 <= index < self.page_count:
            return self.pages[index]
        raise IndexError(f"页索引 {index} 超出范围 [0, {self.page_count - 1}]")

    def __repr__(self) -> str:
        return f"Document(path={self.path}, pages={self.page_count})"
