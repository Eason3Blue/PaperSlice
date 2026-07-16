"""Bootstrap - 依赖注入装配器.

负责统一创建和装配所有组件:
    Repository → UseCase → ViewModel → View
"""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from pdfsplitter.application.repository import DocumentRepository
from pdfsplitter.infrastructure.config import ConfigService
from pdfsplitter.infrastructure.logging_config import setup_logging
from pdfsplitter.infrastructure.mupdf_repository import MuPDFRepository
from pdfsplitter.presentation.main_viewmodel import MainViewModel
from pdfsplitter.presentation.main_window import MainWindow

logger = logging.getLogger(__name__)


class App:
    """应用程序根对象，管理所有依赖.

    构造时创建 QApplication 并完成所有组件的 DI 装配.
    """

    def __init__(self, argv: list[str] | None = None) -> None:
        setup_logging(level=logging.DEBUG if _is_dev_mode() else logging.INFO)

        self._qapp = QApplication(argv or sys.argv)
        self._qapp.setApplicationName("PDF Poster Splitter")
        self._qapp.setOrganizationName("PaperSlice")

        self.config = ConfigService()
        self.repository: DocumentRepository = MuPDFRepository()
        self.viewmodel = MainViewModel(self.repository, self.config)
        self.main_window = MainWindow(self.viewmodel)

    def run(self) -> int:
        """启动事件循环.

        Returns:
            QApplication 退出码.
        """
        self.main_window.show()
        logger.info("Application started")
        return self._qapp.exec()


def _is_dev_mode() -> bool:
    import os
    return os.environ.get("pdfsplitter_DEV", "").lower() in ("1", "true", "yes")
