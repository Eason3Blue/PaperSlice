"""Bootstrap - 依赖注入装配器.

负责统一创建和装配所有组件:
    Repository → UseCase → ViewModel → View
"""

from __future__ import annotations

import logging
from pathlib import Path

from pdfsplitter.application.repository import DocumentRepository
from pdfsplitter.application.usecases import PosterSplitUseCase
from pdfsplitter.infrastructure.config import ConfigService
from pdfsplitter.infrastructure.logging_config import setup_logging
from pdfsplitter.infrastructure.mupdf_repository import MuPDFRepository
from pdfsplitter.presentation.main_viewmodel import MainViewModel
from pdfsplitter.presentation.main_window import MainWindow

logger = logging.getLogger(__name__)


class App:
    """应用程序根对象，管理所有依赖."""

    def __init__(self) -> None:
        setup_logging(level=logging.DEBUG if _is_dev_mode() else logging.INFO)

        self.config = ConfigService()
        self.repository: DocumentRepository = MuPDFRepository()
        self.viewmodel = MainViewModel(self.repository, self.config)
        self.main_window = MainWindow(self.viewmodel)

    def run(self) -> None:
        """启动应用程序."""
        from PySide6.QtWidgets import QApplication
        import sys

        app = QApplication(sys.argv)
        app.setApplicationName("PDF Poster Splitter")
        app.setOrganizationName("pdfsplitter")

        self.main_window.show()
        logger.info("Application started")
        sys.exit(app.exec())


def _is_dev_mode() -> bool:
    import os
    return os.environ.get("pdfsplitter_DEV", "").lower() in ("1", "true", "yes")
