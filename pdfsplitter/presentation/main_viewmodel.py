"""Main ViewModel - 主窗口的业务逻辑桥接."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from pdfsplitter.application.dto import (
    DocumentDTO,
    ExportFormat,
    ExportOptionDTO,
    LayoutResultDTO,
    PaperDTO,
    PosterSplitConfigDTO,
    PreviewTileDTO,
)
from pdfsplitter.application.repository import DocumentRepository
from pdfsplitter.application.usecases import PosterSplitUseCase
from pdfsplitter.domain.paper.paper_database import PaperDatabase
from pdfsplitter.domain.paper.paper_spec import PaperSpec
from pdfsplitter.infrastructure.config import ConfigService

logger = logging.getLogger(__name__)


class MainViewModel(QObject):
    """主窗口 ViewModel.

    桥接 GUI 层与 Application 层，通过 Qt Signal 通知 UI 更新.
    """

    document_loaded_signal = Signal(DocumentDTO)
    layout_calculated_signal = Signal(LayoutResultDTO)
    error_signal = Signal(str)
    progress_signal = Signal(str)

    def __init__(
        self,
        repository: DocumentRepository,
        config: ConfigService,
    ) -> None:
        super().__init__()
        self._repository = repository
        self._config = config
        self._usecase = PosterSplitUseCase(repository)
        self._document: DocumentDTO | None = None
        self._config_dto = PosterSplitConfigDTO(
            paper_name=config.get("last_paper", "A4"),
            paper_category=config.get("last_paper_category", "ISO216"),
            margin_mm=config.get("last_margin_mm", 10.0),
            overlap_mm=config.get("last_overlap_mm", 5.0),
            cut_lines=config.get("cut_lines_enabled", False),
            page_numbers=config.get("page_numbers_enabled", False),
        )

    @property
    def config(self) -> PosterSplitConfigDTO:
        """当前切分配置."""
        return self._config_dto

    @property
    def document(self) -> DocumentDTO | None:
        """当前已加载文档."""
        return self._document

    def load_document(self, path: str) -> None:
        """加载 PDF 文档.

        Args:
            path: 文档路径字符串.
        """
        file_path = Path(path)
        try:
            self.progress_signal.emit(f"加载中: {file_path.name} ...")
            doc = self._usecase.load_document(file_path)
            self._document = doc
            self.document_loaded_signal.emit(doc)
            self.progress_signal.emit(f"已加载: {file_path.name} ({doc.page_count} 页)")
        except FileNotFoundError:
            self.error_signal.emit(f"文件不存在: {path}")
        except ValueError as e:
            self.error_signal.emit(f"加载失败: {e}")
        except Exception:
            logger.exception("load_document failed")
            self.error_signal.emit(f"加载文档时发生未知错误: {path}")

    def update_config(self, **kwargs: Any) -> None:
        """更新切分配置.

        Args:
            **kwargs: 要更新的配置字段.
        """
        dto = self._config_dto
        updates: dict[str, Any] = {}
        for key, value in kwargs.items():
            if hasattr(dto, key):
                updates[key] = value
        if updates:
            self._config_dto = PosterSplitConfigDTO(**{**dto.__dict__, **updates})

    def calculate_layout(self, page_index: int | None = None) -> None:
        """计算切分布局.

        Args:
            page_index: 页面索引，若为 None 则使用配置中的索引.
        """
        if self._document is None:
            self.error_signal.emit("请先加载 PDF 文档")
            return

        pi = page_index if page_index is not None else self._config_dto.page_index
        if pi < 0 or pi >= len(self._document.pages):
            self.error_signal.emit(f"无效的页面索引: {pi}")
            return

        page_info = self._document.pages[pi]

        paper_db = PaperDatabase.instance()
        paper = paper_db.get(self._config_dto.paper_name, self._config_dto.paper_category)
        if paper is None:
            paper = PaperSpec.custom(
                self._config_dto.paper_name,
                page_info.width_pt * 25.4 / 72,
                page_info.height_pt * 25.4 / 72,
            )

        from pdfsplitter.domain.document.page import Page
        from pdfsplitter.domain.geometry.rect import Rect

        domain_page = Page(
            index=pi,
            media_box=Rect(0, 0, page_info.width_pt, page_info.height_pt),
        )

        target_size_mm = (paper.size.w, paper.size.h)

        try:
            self.progress_signal.emit("计算布局中...")
            result = self._usecase.calculate_layout(
                page=domain_page,
                target_size_mm=target_size_mm,
                config=self._config_dto,
            )
            self.layout_calculated_signal.emit(result)
            self.progress_signal.emit(f"布局完成: {result.total_tiles} 个图块 ({result.rows}x{result.cols})")
        except Exception as e:
            logger.exception("calculate_layout failed")
            self.error_signal.emit(f"布局计算失败: {e}")

    def list_papers(self, category: str | None = None) -> list[PaperDTO]:
        """列出可选纸张.

        Args:
            category: 可选的类别筛选.

        Returns:
            纸张 DTO 列表.
        """
        db = PaperDatabase.instance()
        specs = db.list_by_category(category) if category else db.list_all()
        return [
            PaperDTO(name=s.name, category=s.category, width_mm=s.size.w, height_mm=s.size.h)
            for s in specs
        ]

    def get_paper(self, name: str, category: str) -> PaperDTO | None:
        """获取纸张信息.

        Args:
            name: 纸张名称.
            category: 类别.

        Returns:
            PaperDTO 或 None.
        """
        db = PaperDatabase.instance()
        spec = db.get(name, category)
        if spec is None:
            return None
        return PaperDTO(
            name=spec.name,
            category=spec.category,
            width_mm=spec.size.w,
            height_mm=spec.size.h,
        )

    def save_config_to_file(self) -> None:
        """将当前配置持久化."""
        self._config.set("last_paper", self._config_dto.paper_name)
        self._config.set("last_paper_category", self._config_dto.paper_category)
        self._config.set("last_margin_mm", self._config_dto.margin_mm)
        self._config.set("last_overlap_mm", self._config_dto.overlap_mm)
        self._config.set("cut_lines_enabled", self._config_dto.cut_lines)
        self._config.set("page_numbers_enabled", self._config_dto.page_numbers)
        self._config.save()
