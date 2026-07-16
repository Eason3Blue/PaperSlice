"""Main ViewModel - 主窗口的业务逻辑桥接."""

from __future__ import annotations

import json
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
from pdfsplitter.infrastructure.config import ConfigService

logger = logging.getLogger(__name__)

PROJECT_VERSION = 1


class MainViewModel(QObject):
    """主窗口 ViewModel."""

    document_loaded_signal = Signal(DocumentDTO)
    preview_pixmap_ready_signal = Signal(object)
    split_lines_changed_signal = Signal(list, list, float, float, list)
    order_reset_signal = Signal()
    project_saved_signal = Signal(str)
    dirty_changed_signal = Signal(bool)
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
        self._is_dirty: bool = False
        self._project_path: Path | None = None
        self._page_states: dict[int, dict[str, Any]] = {}

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

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    @property
    def project_path(self) -> Path | None:
        return self._project_path

    def load_document(self, path: str) -> None:
        file_path = Path(path)
        try:
            self.progress_signal.emit(f"加载中: {file_path.name} ...")
            doc = self._usecase.load_document(file_path)
            self._document = doc
            self._current_page_index = 0
            self._split_lines = SplitLines.empty()
            self._tile_order = TileOrder.auto(1)
            self._has_manual_order = False
            self._is_dirty = False
            self._page_states.clear()
            self._project_path = None
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
        if not self._document or not (0 <= page_index < self._document.page_count):
            return
        if page_index != self._current_page_index:
            self._save_current_page_state()
        self._current_page_index = page_index
        restored = page_index in self._page_states
        if restored:
            self._restore_page_state(page_index)
        else:
            self._split_lines = SplitLines.empty()
            self._has_manual_order = False
            self._tile_order = TileOrder.auto(1)
        self._update_split_lines_preview()
        print(f"[DEBUG] select_page({page_index}): restored={restored} has_manual={self._has_manual_order} order_indices={self._tile_order.indices}")
        if not restored:
            self.order_reset_signal.emit()

    def apply_split_preset(self, preset: str) -> None:
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
        self._mark_dirty()
        self._update_split_lines_preview()

    def add_vertical_line(self) -> None:
        page = self.current_page_info
        if page is None:
            return
        center = page.width_pt / 2.0
        self._split_lines = self._split_lines.with_vertical(center)
        self._mark_dirty()
        self._update_split_lines_preview()

    def add_horizontal_line(self) -> None:
        page = self.current_page_info
        if page is None:
            return
        center = page.height_pt / 2.0
        self._split_lines = self._split_lines.with_horizontal(center)
        self._mark_dirty()
        self._update_split_lines_preview()

    def move_line(self, orientation: str, index: int, position: float) -> None:
        page = self.current_page_info
        if page is None:
            return
        if orientation == "v":
            self._split_lines = self._split_lines.move_vertical(index, position, 0.0, page.width_pt)
        else:
            self._split_lines = self._split_lines.move_horizontal(index, position, 0.0, page.height_pt)
        self._mark_dirty()
        self._update_split_lines_preview()

    def clear_split_lines(self) -> None:
        self._clear_order()
        self._split_lines = SplitLines.empty()
        self._mark_dirty()
        self._update_split_lines_preview()

    def set_tile_order(self, ordered_indices: list[int]) -> None:
        self._has_manual_order = True
        self._tile_order = TileOrder.auto(len(ordered_indices)).with_manual_order(ordered_indices)
        self._mark_dirty()

    def reset_order(self) -> None:
        tile_count = self._split_lines.tile_count
        self._has_manual_order = False
        self._tile_order = TileOrder.auto(max(1, tile_count))
        self._mark_dirty()

    @property
    def has_manual_order(self) -> bool:
        return self._has_manual_order

    def has_incomplete_order(self) -> bool:
        if not self._has_manual_order:
            return False
        expected = self._split_lines.tile_count
        return len(self._tile_order.indices) != expected

    def save_project(self, path: str) -> None:
        """保存项目到 .ppslc 文件."""
        self._save_current_page_state()
        file_path = Path(path)
        if file_path.suffix.lower() != ".ppslc":
            file_path = file_path.with_suffix(".ppslc")

        data: dict[str, Any] = {
            "version": PROJECT_VERSION,
            "source_path": str(self._document.path) if self._document else "",
            "pages": {},
        }
        page_states = dict(self._page_states)
        page_states[self._current_page_index] = self._serialize_current_page()
        for idx, state in page_states.items():
            has_content = bool(state.get("verticals")) or bool(state.get("horizontals")) or state.get("order_mode") == "manual"
            if has_content:
                data["pages"][str(idx)] = state

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._project_path = file_path
            self._is_dirty = False
            self.dirty_changed_signal.emit(False)
            self.project_saved_signal.emit(str(file_path))
            logger.info("Project saved to %s", file_path)
        except OSError as e:
            self.error_signal.emit(f"保存失败: {e}")

    def load_project(self, path: str) -> None:
        """从 .ppslc 文件加载项目."""
        file_path = Path(path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            self.error_signal.emit(f"无法读取存档: {e}")
            return

        version = data.get("version", 0)
        if version > PROJECT_VERSION:
            self.error_signal.emit(f"存档版本 {version} 高于当前支持版本 {PROJECT_VERSION}")
            return

        source_path = data.get("source_path", "")
        if source_path and Path(source_path).exists():
            self.progress_signal.emit(f"加载源文件: {Path(source_path).name} ...")
            self.load_document(source_path)
        elif source_path:
            self.error_signal.emit(f"源文件不存在: {source_path}")
            return

        self._page_states.clear()
        for key, state in data.get("pages", {}).items():
            self._page_states[int(key)] = state

        if self._document:
            self.select_page(0)
            self.render_page_preview(0)
        self._project_path = file_path
        self._is_dirty = False
        self.dirty_changed_signal.emit(False)
        self.project_saved_signal.emit(str(file_path))
        logger.info("Project loaded from %s", file_path)

    def _save_current_page_state(self) -> None:
        if self._document is None:
            return
        state = self._serialize_current_page()
        has_content = bool(state["verticals"]) or bool(state["horizontals"]) or state["order_mode"] == "manual"
        print(f"[DEBUG] _save_current_page_state: page={self._current_page_index} state={state} has_content={has_content}")
        if has_content:
            self._page_states[self._current_page_index] = state
        else:
            self._page_states.pop(self._current_page_index, None)

    def _serialize_current_page(self) -> dict[str, Any]:
        order_mode = "manual" if self._has_manual_order else "auto"
        return {
            "verticals": list(self._split_lines.verticals),
            "horizontals": list(self._split_lines.horizontals),
            "order_mode": order_mode,
            "order_indices": list(self._tile_order.indices),
        }

    def _restore_page_state(self, page_index: int) -> None:
        state = self._page_states.get(page_index, {})
        verticals = state.get("verticals", [])
        horizontals = state.get("horizontals", [])
        order_mode = state.get("order_mode", "auto")
        order_indices = state.get("order_indices", [])

        self._split_lines = SplitLines(
            verticals=tuple(verticals),
            horizontals=tuple(horizontals),
        )
        self._has_manual_order = (order_mode == "manual")
        if order_indices:
            self._tile_order = TileOrder(
                indices=tuple(order_indices),
                mode=order_mode,
            )
        else:
            self._tile_order = TileOrder.auto(max(1, self._split_lines.tile_count))
        logger.debug(
            "_restore_page_state: page=%d verticals=%s has_manual=%s order_indices=%s tile_order_indices=%s",
            page_index, verticals, self._has_manual_order, order_indices, self._tile_order.indices,
        )

    def _clear_order(self) -> None:
        self._has_manual_order = False
        self._tile_order = TileOrder.auto(max(1, self._split_lines.tile_count))
        self.order_reset_signal.emit()

    def _mark_dirty(self) -> None:
        if not self._is_dirty:
            self._is_dirty = True
            self.dirty_changed_signal.emit(True)

    def _update_split_lines_preview(self) -> None:
        page = self.current_page_info
        if page is None:
            return
        order_indices = list(self._tile_order.indices) if self._has_manual_order else []
        logger.debug(
            "_update_split_lines_preview: page=%d has_manual=%s order=%s",
            self._current_page_index, self._has_manual_order, order_indices,
        )
        self.split_lines_changed_signal.emit(
            list(self._split_lines.verticals),
            list(self._split_lines.horizontals),
            page.width_pt,
            page.height_pt,
            order_indices,
        )

    def render_page_preview(self, page_index: int) -> None:
        if self._document is None:
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

    def refresh_preview_state(self) -> None:
        """刷新预览的切割线和排序状态 (用于 set_page_image 清空后恢复)."""
        self._update_split_lines_preview()
