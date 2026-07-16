"""Main ViewModel - 主窗口的业务逻辑桥接."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from pdfsplitter.application.dto import DocumentDTO, PageInfoDTO, PosterSplitConfigDTO
from pdfsplitter.application.repository import DocumentRepository
from pdfsplitter.application.usecases import PosterSplitUseCase
from pdfsplitter.domain.layout.layout_engine import LayoutEngine
from pdfsplitter.domain.layout.split_lines import SplitLines
from pdfsplitter.domain.layout.tile_order import TileOrder
from pdfsplitter.domain.paper.paper_database import PaperDatabase
from pdfsplitter.infrastructure.config import ConfigService

logger = logging.getLogger(__name__)


class MainViewModel(QObject):
    """主窗口 ViewModel."""

    document_loaded_signal = Signal(DocumentDTO)
    preview_pixmap_ready_signal = Signal(object)
    split_lines_changed_signal = Signal(list, list, float, float)
    order_reset_signal = Signal()
    error_signal = Signal(str)
    progress_signal = Signal(str)

    def __init__(self, repository: DocumentRepository, config: ConfigService) -> None:
        super().__init__()
        self._repository = repository
        self._config = config
        self._usecase = PosterSplitUseCase(repository)
        self._document: DocumentDTO | None = None
        self._current_page_index: int = 0
        self._split_lines = SplitLines.empty()
        self._tile_order = TileOrder.auto(1)
        self._layout_engine = LayoutEngine()
        self._has_manual_order: bool = False

    @property
    def document(self) -> DocumentDTO | None:
        return self._document

    @property
    def split_lines(self) -> SplitLines:
        return self._split_lines

    @property
    def current_page_info(self) -> PageInfoDTO | None:
        if self._document and 0 <= self._current_page_index < len(self._document.pages):
            return self._document.pages[self._current_page_index]
        return None

    @property
    def tile_order(self) -> TileOrder:
        return self._tile_order

    def load_document(self, path: str) -> None:
        file_path = Path(path)
        try:
            self.progress_signal.emit(f"加载中: {file_path.name} ...")
            doc = self._usecase.load_document(file_path)
            self._document = doc
            self._current_page_index = 0
            self._split_lines = SplitLines.empty()
            self.document_loaded_signal.emit(doc)
            self.progress_signal.emit(f"已加载: {file_path.name} ({doc.page_count} 页)")
        except FileNotFoundError:
            self.error_signal.emit(f"文件不存在: {path}")
        except ValueError as e:
            self.error_signal.emit(f"加载失败: {e}")
        except Exception:
            logger.exception("load_document failed")
            self.error_signal.emit(f"加载文档时发生未知错误: {path}")

    def select_page(self, page_index: int) -> None:
        if self._document and 0 <= page_index < self._document.page_count:
            self._current_page_index = page_index
            self._split_lines = SplitLines.empty()
            self._has_manual_order = False
            self._tile_order = TileOrder.auto(1)
            self._update_split_lines_preview()
            self.order_reset_signal.emit()

    def apply_split_preset(self, preset: str) -> None:
        """应用预设切割, 始终重置为预设状态并清除排序.

        Args:
            preset: "half_v", "half_h", "quarter"
        """
        page = self.current_page_info
        if page is None:
            return
        self._clear_order()
        if preset == "half_v":
            self._split_lines = SplitLines.halved_vertical(page.width_pt)
        elif preset == "half_h":
            self._split_lines = SplitLines.halved_horizontal(page.height_pt)
        elif preset == "quarter":
            self._split_lines = SplitLines.quartered(page.width_pt, page.height_pt)
        self._update_split_lines_preview()

    def add_vertical_line(self) -> None:
        """添加垂直线."""
        page = self.current_page_info
        if page is None:
            return
        center = page.width_pt / 2.0
        self._split_lines = self._split_lines.with_vertical(center)
        self._update_split_lines_preview()

    def add_horizontal_line(self) -> None:
        """添加水平线."""
        page = self.current_page_info
        if page is None:
            return
        center = page.height_pt / 2.0
        self._split_lines = self._split_lines.with_horizontal(center)
        self._update_split_lines_preview()

    def move_line(self, orientation: str, index: int, position: float) -> None:
        page = self.current_page_info
        if page is None:
            return
        if orientation == "v":
            self._split_lines = self._split_lines.move_vertical(index, position, 0.0, page.width_pt)
        else:
            self._split_lines = self._split_lines.move_horizontal(index, position, 0.0, page.height_pt)
        self._update_split_lines_preview()

    def clear_split_lines(self) -> None:
        """清除所有切割线并重置排序."""
        self._clear_order()
        self._split_lines = SplitLines.empty()
        self._update_split_lines_preview()

    def set_tile_order(self, ordered_indices: list[int]) -> None:
        self._has_manual_order = True
        self._tile_order = TileOrder.auto(len(ordered_indices)).with_manual_order(ordered_indices)

    def reset_order(self) -> None:
        tile_count = self._split_lines.tile_count
        self._has_manual_order = False
        self._tile_order = TileOrder.auto(max(1, tile_count))

    @property
    def has_manual_order(self) -> bool:
        return self._has_manual_order

    def has_incomplete_order(self) -> bool:
        """手动排序模式下是否还有未选中的图块."""
        if not self._has_manual_order:
            return False
        expected = self._split_lines.tile_count
        return len(self._tile_order.indices) != expected

    def _clear_order(self) -> None:
        self._has_manual_order = False
        self._tile_order = TileOrder.auto(max(1, self._split_lines.tile_count))
        self.order_reset_signal.emit()

    def _reset_all(self) -> None:
        """清除所有分割线和排序状态."""
        self._split_lines = SplitLines.empty()
        self._has_manual_order = False
        self._tile_order = TileOrder.auto(1)
        self.order_reset_signal.emit()

    def _update_split_lines_preview(self) -> None:
        page = self.current_page_info
        if page is None:
            return
        self.split_lines_changed_signal.emit(
            list(self._split_lines.verticals),
            list(self._split_lines.horizontals),
            page.width_pt,
            page.height_pt,
        )

    def render_page_preview(self, page_index: int) -> None:
        page = self.current_page_info
        if page is None or self._document is None:
            return
        doc_path = self._document.path
        import fitz
        try:
            pdf = fitz.open(str(doc_path))
            fitz_page = pdf.load_page(page_index)
            zoom = 1.5
            mat = fitz.Matrix(zoom, zoom)
            pix = fitz_page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            pdf.close()
            self.preview_pixmap_ready_signal.emit(img_data)
        except Exception:
            logger.exception("render_page_preview failed")
