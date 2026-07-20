"""Repository interfaces - 文档仓库抽象接口与组合路由."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

from pdfsplitter.domain.document.document import Document
from pdfsplitter.domain.document.page import Page
from pdfsplitter.domain.geometry.rect import Rect

logger = logging.getLogger(__name__)


class DocumentRepository(ABC):
    """文档仓库抽象接口.

    Application 层依赖此接口，Infrastructure 层提供具体实现.
    """

    @abstractmethod
    def load(self, path: Path, password: str | None = None) -> Document:
        """加载单个文档.

        Args:
            path: 文档路径.
            password: 可选的打开密码.

        Returns:
            Document 领域对象.

        Raises:
            FileNotFoundError: 文件不存在.
            ValueError: 文件格式无效或密码错误.
        """
        ...

    @abstractmethod
    def supports(self, path: Path) -> bool:
        """检查是否支持该文件格式.

        Args:
            path: 文件路径.

        Returns:
            是否支持.
        """
        ...


class RepositoryRouter(DocumentRepository):
    """组合仓库路由器.

    持有多个 DocumentRepository 实现, 按文件扩展名路由到对应的仓库.
    提供 load_multiple 能力: 加载多个文件合并为一个多页文档.
    """

    def __init__(self, repositories: list[DocumentRepository]) -> None:
        """初始化.

        Args:
            repositories: 仓库实现列表 (按需匹配, 取首个 supports=True 的).
        """
        self._repos = repositories

    def load(self, path: Path, password: str | None = None) -> Document:
        """路由到正确的仓库加载单个文档.

        Args:
            path: 文档路径.
            password: 可选的打开密码.

        Returns:
            Document 领域对象.

        Raises:
            FileNotFoundError: 文件不存在.
            ValueError: 无仓库支持该格式.
        """
        for repo in self._repos:
            if repo.supports(path):
                return repo.load(path, password)
        raise ValueError(f"不支持的文件格式: {path.suffix}")

    def load_multiple(self, paths: list[Path], password: str | None = None) -> Document:
        """加载多个文件合并为一个多页文档.

        每个文件按其扩展名路由到对应仓库, 所有页面顺序拼接.

        Args:
            paths: 文件路径列表.
            password: 可选的打开密码.

        Returns:
            Document 领域对象, source_paths 包含所有输入路径.

        Raises:
            FileNotFoundError: 文件不存在.
            ValueError: 文件列表为空或无仓库支持.
        """
        if not paths:
            raise ValueError("文件列表为空")

        all_pages: list[Page] = []
        page_index: int = 0

        for p in paths:
            doc = self.load(p, password)
            for page in doc.pages:
                all_pages.append(Page(
                    index=page_index,
                    media_box=page.media_box,
                    crop_box=page.crop_box,
                ))
                page_index += 1

        logger.info(
            "RepositoryRouter: loaded %d files → %d pages total",
            len(paths), len(all_pages),
        )
        return Document(
            path=paths[0],
            pages=tuple(all_pages),
            source_paths=tuple(paths),
        )

    def supports(self, path: Path) -> bool:
        """检查是否有仓库支持该格式.

        Args:
            path: 文件路径.

        Returns:
            是否支持.
        """
        return any(repo.supports(path) for repo in self._repos)
