"""Repository interfaces - 文档仓库抽象接口."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

from pdfsplitter.domain.document.document import Document


class DocumentRepository(ABC):
    """文档仓库抽象接口.

    Application 层依赖此接口，Infrastructure 层提供 MuPDF 实现.
    """

    @abstractmethod
    def load(self, path: Path, password: str | None = None) -> Document:
        """加载 PDF 文档.

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
