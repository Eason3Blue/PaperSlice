"""Main ViewModel - 主窗口的业务逻辑桥接."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from pdfsplitter.application.dto import DocumentDTO, PageFilterDTO, PageInfoDTO, PageListStateDTO, PosterSplitConfigDTO
from pdfsplitter.application.export_usecase import ExportUseCase
from pdfsplitter.application.page_filter_usecase import PageFilterUseCase
from pdfsplitter.application.repository import DocumentRepository, RepositoryRouter
from pdfsplitter.application.usecases import PosterSplitUseCase
from pdfsplitter.domain.export.export_config import ExportConfig, ExportFormat, ExportResult
from pdfsplitter.domain.filter.page_filter import PageFilter
from pdfsplitter.domain.filter.page_selection import PageSelection
from pdfsplitter.domain.layout.layout_engine import LayoutEngine
from pdfsplitter.domain.layout.split_lines import SplitLines
from pdfsplitter.domain.layout.tile_order import TileOrder
from pdfsplitter.domain.paper.paper_database import PaperDatabase
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
    page_filter_changed_signal = Signal(object)
    page_list_state_changed_signal = Signal(object)

    def __init__(self, repository: RepositoryRouter, config: ConfigService) -> None:
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
        self._page_filter: PageFilter = PageFilter.empty()
        self._resolved_filter: PageFilterDTO = PageFilterDTO()
        self._selection: PageSelection = PageSelection.empty()
        self._view_mode: str = "all"

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

    @property
    def page_filter(self) -> PageFilter:
        return self._page_filter

    @property
    def resolved_filter(self) -> PageFilterDTO:
        return self._resolved_filter

    @property
    def selection(self) -> PageSelection:
        return self._selection

    @property
    def view_mode(self) -> str:
        return self._view_mode

    @property
    def selected_indices(self) -> frozenset[int]:
        return self._selection.selected_indices

    def _build_page_list_state(self) -> PageListStateDTO:
        if self._document is None:
            return PageListStateDTO()
        return PageListStateDTO(
            total_pages=self._document.page_count,
            view_mode=self._view_mode,
            selected_indices=tuple(sorted(self._selection.selected_indices)),
            filtered_indices=self._resolved_filter.matched_indices,
            filter_active=self._page_filter.is_active,
        )

    def _emit_page_list_state(self) -> None:
        self.page_list_state_changed_signal.emit(self._build_page_list_state())

    def toggle_page_selection(self, page_index: int) -> None:
        self._selection = self._selection.with_toggled(page_index)
        self._mark_dirty()
        self._emit_page_list_state()

    def select_all_visible(self) -> None:
        if self._document is None:
            return
        state = self._build_page_list_state()
        self._selection = self._selection.with_added(set(state.visible_indices))
        self._mark_dirty()
        self._emit_page_list_state()

    def deselect_all(self) -> None:
        self._selection = PageSelection.empty()
        self._mark_dirty()
        self._emit_page_list_state()

    def set_view_mode(self, mode: str) -> None:
        self._view_mode = mode
        self._emit_page_list_state()

    def get_filtered_indices(self) -> set[int]:
        if self._document is None:
            return set()
        return set(self._selection.selected_indices)

    def set_page_filter(self, filter_obj: PageFilter) -> None:
        self._page_filter = filter_obj
        self._resolve_filter()
        if filter_obj.is_active:
            self._view_mode = "filtered"
        else:
            self._view_mode = "all"
        self._mark_dirty()
        self.page_filter_changed_signal.emit(self._resolved_filter)
        self._emit_page_list_state()

    def clear_page_filter(self) -> None:
        self._page_filter = PageFilter.empty()
        self._resolve_filter()
        self._view_mode = "all"
        self._mark_dirty()
        self.page_filter_changed_signal.emit(self._resolved_filter)
        self._emit_page_list_state()

    def _resolve_filter(self) -> None:
        if self._document is None:
            self._resolved_filter = PageFilterDTO(
                page_range_mode=self._page_filter.page_range_mode,
                matched_indices=(),
                total_pages=0,
            )
            return
        self._resolved_filter = PageFilterUseCase.resolve(
            self._page_filter, self._document.pages,
        )

    def load_document(self, path: str) -> None:
        self.load_documents([path])

    def load_documents(self, paths: list[str]) -> None:
        file_paths = [Path(p) for p in paths]
        if not file_paths:
            return
        try:
            names = ", ".join(p.name for p in file_paths[:3])
            if len(file_paths) > 3:
                names += f" ... 等 {len(file_paths)} 个文件"
            self.progress_signal.emit(f"加载中: {names} ...")

            if len(file_paths) == 1:
                domain_doc = self._repository.load(file_paths[0])
            else:
                domain_doc = self._repository.load_multiple(file_paths)

            dto = self._domain_to_dto(domain_doc)
            self._document = dto
            self._current_page_index = 0
            self._split_lines = SplitLines.empty()
            self._tile_order = TileOrder.auto(1)
            self._has_manual_order = False
            self._is_dirty = False
            self._page_states.clear()
            self._project_path = None
            self._page_filter = PageFilter.empty()
            self._resolved_filter = PageFilterDTO()
            self._selection = PageSelection.all_selected(dto.page_count)
            self._view_mode = "all"
            self.document_loaded_signal.emit(dto)
            self.progress_signal.emit(f"已加载: {names} ({dto.page_count} 页)")
            self.page_filter_changed_signal.emit(self._resolved_filter)
            self._emit_page_list_state()
        except FileNotFoundError:
            self.error_signal.emit(f"文件不存在: {paths[0]}")
        except ValueError as e:
            self.error_signal.emit(f"加载失败: {e}")
        except Exception:
            logger.exception("load_document failed")
            self.error_signal.emit(f"加载文档时发生未知错误")

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
        if not restored:
            self.order_reset_signal.emit()

    def apply_split_preset(self, preset: str, apply_to_all: bool = False) -> None:
        page = self.current_page_info
        if page is None:
            return

        def _make_lines(p: PageInfoDTO) -> SplitLines:
            if preset == "half_v":
                return SplitLines.halved_vertical(p.width_pt)
            elif preset == "half_h":
                return SplitLines.halved_horizontal(p.height_pt)
            elif preset == "quarter":
                return SplitLines.quartered(p.width_pt, p.height_pt)
            return SplitLines.empty()

        if apply_to_all and self._document:
            target_indices = self.get_filtered_indices()
            if not target_indices:
                return
            for page_idx in range(self._document.page_count):
                if page_idx not in target_indices:
                    continue
                p = self._document.pages[page_idx]
                sl = _make_lines(p)
                self._page_states[page_idx] = self._make_page_state(sl)
            if self._current_page_index in target_indices:
                self._split_lines = _make_lines(page)
        else:
            self._split_lines = _make_lines(page)

        self._clear_order()
        self._mark_dirty()
        self._update_split_lines_preview()

    def add_vertical_line(self, apply_to_all: bool = False) -> None:
        page = self.current_page_info
        if page is None:
            return

        if apply_to_all and self._document:
            self._save_current_page_state()
            target_indices = self.get_filtered_indices()
            if not target_indices:
                return
            for page_idx in range(self._document.page_count):
                if page_idx not in target_indices:
                    continue
                p = self._document.pages[page_idx]
                center = p.width_pt / 2.0
                existing = self._page_states.get(page_idx, dict(self._empty_page_state()))
                verts = sorted([*existing["verticals"], center])
                existing["verticals"] = verts
                existing["order_mode"] = "auto"
                existing["order_indices"] = []
                self._page_states[page_idx] = existing
            if self._current_page_index in target_indices:
                self._split_lines = self._split_lines.with_vertical(page.width_pt / 2.0)
        else:
            self._split_lines = self._split_lines.with_vertical(page.width_pt / 2.0)

        self._clear_order()
        self._mark_dirty()
        self._update_split_lines_preview()

    def add_horizontal_line(self, apply_to_all: bool = False) -> None:
        page = self.current_page_info
        if page is None:
            return

        if apply_to_all and self._document:
            self._save_current_page_state()
            target_indices = self.get_filtered_indices()
            if not target_indices:
                return
            for page_idx in range(self._document.page_count):
                if page_idx not in target_indices:
                    continue
                p = self._document.pages[page_idx]
                center = p.height_pt / 2.0
                existing = self._page_states.get(page_idx, dict(self._empty_page_state()))
                horiz = sorted([*existing["horizontals"], center])
                existing["horizontals"] = horiz
                existing["order_mode"] = "auto"
                existing["order_indices"] = []
                self._page_states[page_idx] = existing
            if self._current_page_index in target_indices:
                self._split_lines = self._split_lines.with_horizontal(page.height_pt / 2.0)
        else:
            self._split_lines = self._split_lines.with_horizontal(page.height_pt / 2.0)

        self._clear_order()
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

    def clear_split_lines(self, apply_to_all: bool = False) -> None:
        if apply_to_all and self._document:
            self._save_current_page_state()
            target_indices = self.get_filtered_indices()
            if not target_indices:
                return
            if len(target_indices) < self._document.page_count:
                for idx in target_indices:
                    self._page_states.pop(idx, None)
            else:
                self._page_states.clear()
            if self._current_page_index in target_indices:
                self._clear_order()
                self._split_lines = SplitLines.empty()
        else:
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

    def default_project_name(self) -> str:
        if self._document is None:
            return "未命名"
        paths = self._document.source_paths
        if paths:
            _image_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
            suffixes = {p.suffix.lower() for p in paths}
            if suffixes and suffixes.issubset(_image_exts):
                return "未命名"
        stem = Path(self._document.filename).stem
        return stem if stem else "未命名"

    def list_papers(self, category: str | None = None) -> list[dict[str, str | float]]:
        """列出可选纸张.

        Args:
            category: 可选的类别筛选.

        Returns:
            [{name, category, width_mm, height_mm}, ...]
        """
        db = PaperDatabase.instance()
        specs = db.list_by_category(category) if category else db.list_all()
        return [
            {"name": s.name, "category": s.category, "width_mm": s.size.w, "height_mm": s.size.h}
            for s in specs
        ]

    def save_project(self, path: str) -> None:
        """保存项目到 .ppslc 文件."""
        self._save_current_page_state()
        file_path = Path(path)
        if file_path.suffix.lower() != ".ppslc":
            file_path = file_path.with_suffix(".ppslc")

        data: dict[str, Any] = {
            "version": PROJECT_VERSION,
            "source_path": str(self._document.path) if self._document else "",
            "source_paths": [str(p) for p in self._document.source_paths] if self._document and self._document.source_paths else [],
            "pages": {},
        }
        if self._page_filter.is_active:
            data["page_filter"] = {
                "page_range_mode": self._page_filter.page_range_mode,
                "page_start": self._page_filter.page_start,
                "page_end": self._page_filter.page_end,
                "page_list_spec": self._page_filter.page_list_spec,
                "paper_names": list(self._page_filter.paper_names),
                "orientation_mode": self._page_filter.orientation_mode,
            }
        data["selected_indices"] = list(sorted(self._selection.selected_indices))
        data["view_mode"] = self._view_mode
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

        saved_paths = data.get("source_paths", [])
        if saved_paths:
            existing = [p for p in saved_paths if Path(p).exists()]
            if existing:
                self.load_documents(existing)
            else:
                self.error_signal.emit("所有源文件均不存在")
                return
        else:
            source_path = data.get("source_path", "")
            if source_path and Path(source_path).exists():
                self.load_document(source_path)
            elif source_path:
                self.error_signal.emit(f"源文件不存在: {source_path}")
                return

        self._page_states.clear()
        for key, state in data.get("pages", {}).items():
            self._page_states[int(key)] = state

        pf = data.get("page_filter")
        if pf:
            self._page_filter = PageFilter(
                page_range_mode=pf.get("page_range_mode", "all"),
                page_start=pf.get("page_start", 1),
                page_end=pf.get("page_end", 1),
                page_list_spec=pf.get("page_list_spec", ""),
                paper_names=tuple(pf.get("paper_names", [])),
                orientation_mode=pf.get("orientation_mode", "all"),
            )
        else:
            self._page_filter = PageFilter.empty()
        self._resolve_filter()

        si = data.get("selected_indices", [])
        if si:
            self._selection = PageSelection(selected_indices=frozenset(int(i) for i in si))
        elif self._document:
            self._selection = PageSelection.all_selected(self._document.page_count)
        else:
            self._selection = PageSelection.empty()
        self._view_mode = data.get("view_mode", "all")

        if self._document:
            self.select_page(0)
            self.render_page_preview(0)
        self._project_path = file_path
        self._is_dirty = False
        self.dirty_changed_signal.emit(False)
        self.project_saved_signal.emit(str(file_path))
        self.page_filter_changed_signal.emit(self._resolved_filter)
        self._emit_page_list_state()
        logger.info("Project loaded from %s", file_path)

    def _save_current_page_state(self) -> None:
        if self._document is None:
            return
        state = self._serialize_current_page()
        has_content = bool(state["verticals"]) or bool(state["horizontals"]) or state["order_mode"] == "manual"
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

    def export(self, output_path: str, paper_name: str, paper_category: str) -> None:
        """执行切分导出.

        Args:
            output_path: 输出文件路径.
            paper_name: 纸张名称.
            paper_category: 纸张类别.
        """
        if self._document is None:
            self.error_signal.emit("请先加载文档")
            return
        if self._split_lines.is_empty:
            self.error_signal.emit("请先放置切割线")
            return

        paper_db = PaperDatabase.instance()
        paper = paper_db.get(paper_name, paper_category)
        if paper is None:
            self.error_signal.emit(f"未知纸张: {paper_name}")
            return

        config = ExportConfig(
            format=ExportFormat.PDF_SINGLE,
            output_path=Path(output_path),
        )

        export_uc = ExportUseCase(self._repository)
        try:
            self.progress_signal.emit("正在导出...")
            source_path = self._get_source_path_for_page(self._current_page_index)
            local_index = self._get_local_page_index(self._current_page_index)
            result = export_uc.execute(
                source_path=self._document.path,
                page_index=self._current_page_index,
                split_lines=self._split_lines,
                order=self._tile_order,
                target_size_mm=(paper.size.w, paper.size.h),
                config=config,
                source_path_override=source_path,
                local_page_index=local_index,
            )
            self.progress_signal.emit(
                f"导出完成: {result.tile_count} 个图块 → {result.output_paths[0]}"
            )
        except Exception as e:
            logger.exception("export failed")
            self.error_signal.emit(f"导出失败: {e}")

    def export_all(self, output_path: str, paper_name: str, paper_category: str) -> None:
        """导出全部已配置的页面到单个 PDF.

        Args:
            output_path: 输出文件路径.
            paper_name: 纸张名称.
            paper_category: 纸张类别.
        """
        if self._document is None:
            self.error_signal.emit("请先加载文档")
            return

        self._save_current_page_state()

        paper_db = PaperDatabase.instance()
        paper = paper_db.get(paper_name, paper_category)
        if paper is None:
            self.error_signal.emit(f"未知纸张: {paper_name}")
            return

        skipped: list[int] = []
        incomplete: list[int] = []
        unselected: list[int] = []
        page_configs: dict[int, tuple[SplitLines, TileOrder]] = {}

        for page_idx in range(self._document.page_count):
            if page_idx not in self._selection.selected_indices:
                unselected.append(page_idx)
                continue
            if page_idx in self._page_states:
                state = self._page_states[page_idx]
                sl = SplitLines(
                    verticals=tuple(state.get("verticals", [])),
                    horizontals=tuple(state.get("horizontals", [])),
                )
                mode = state.get("order_mode", "auto")
                indices = state.get("order_indices", [])
                if mode == "manual" and len(indices) != sl.tile_count:
                    incomplete.append(page_idx)
                order = TileOrder(indices=tuple(indices) if indices else tuple(range(sl.tile_count)), mode=mode)
                page_configs[page_idx] = (sl, order)
            else:
                skipped.append(page_idx)

        if not page_configs:
            self.error_signal.emit("没有任何页面配置了切割线，请先编辑页面")
            return

        warnings: list[str] = []
        if unselected:
            warnings.append(f"以下页面未勾选, 将被跳过: {[p + 1 for p in unselected]}")
        if skipped:
            warnings.append(f"以下页面未配置切割线，将被跳过: {[p + 1 for p in skipped]}")
        if incomplete:
            warnings.append(f"以下页面排序不完整，未选区块将被舍弃: {[p + 1 for p in incomplete]}")

        export_uc = ExportUseCase(self._repository)
        try:
            self.progress_signal.emit("正在导出全部页面...")
            source_doc = self._build_export_source_document()
            result = export_uc.execute_all(
                source_path=self._document.path,
                page_configs=page_configs,
                target_size_mm=(paper.size.w, paper.size.h),
                output_path=Path(output_path),
                source_document=source_doc,
            )
            msg = f"导出完成: {result.tile_count} 个图块 → {result.output_paths[0]}"
            if warnings:
                msg += "\n" + "\n".join(warnings)
            self.progress_signal.emit(msg)
        except Exception as e:
            logger.exception("export_all failed")
            self.error_signal.emit(f"导出失败: {e}")

    def _clear_order(self) -> None:
        self._has_manual_order = False
        self._tile_order = TileOrder.auto(max(1, self._split_lines.tile_count))
        self.order_reset_signal.emit()

    @staticmethod
    def _empty_page_state() -> dict[str, Any]:
        return {"verticals": [], "horizontals": [], "order_mode": "auto", "order_indices": []}

    @staticmethod
    def _make_page_state(sl: SplitLines) -> dict[str, Any]:
        return {
            "verticals": list(sl.verticals),
            "horizontals": list(sl.horizontals),
            "order_mode": "auto",
            "order_indices": [],
        }

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
        source_path = self._get_source_path_for_page(page_index)
        import fitz
        try:
            pdf = fitz.open(str(source_path))
            local_index = self._get_local_page_index(page_index)
            fitz_page = pdf.load_page(local_index)
            dpi = self._config.get("default_dpi", 150)
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = fitz_page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            pdf.close()
            self.preview_pixmap_ready_signal.emit(img_data)
        except Exception:
            logger.exception("render_page_preview failed")

    def set_render_dpi(self, dpi: int) -> None:
        """设置预览渲染 DPI 并重新渲染当前页.

        Args:
            dpi: 渲染 DPI (50-600).
        """
        dpi = max(50, min(dpi, 600))
        current = self._config.get("default_dpi", 150)
        if dpi == current:
            return
        self._config.set("default_dpi", dpi)
        if self._document and self._current_page_index < self._document.page_count:
            self.render_page_preview(self._current_page_index)

    def get_render_dpi(self) -> int:
        """获取当前渲染 DPI."""
        return self._config.get("default_dpi", 150)

    def _get_source_path_for_page(self, page_index: int) -> Path:
        if self._document is None:
            return Path(".")
        paths = self._document.source_paths
        if paths and len(paths) == self._document.page_count:
            return paths[page_index]
        return self._document.path

    def _get_local_page_index(self, global_index: int) -> int:
        """将全局页索引转换为源文件内的局部页索引."""
        if self._document is None:
            return 0
        paths = self._document.source_paths
        if not paths or len(paths) != self._document.page_count:
            return global_index
        import fitz
        offset = 0
        for sp in paths:
            try:
                doc = fitz.open(str(sp))
                count = doc.page_count
                doc.close()
                if global_index < offset + count:
                    return global_index - offset
                offset += count
            except Exception:
                pass
        return global_index

    @staticmethod
    def _domain_to_dto(doc: Document) -> DocumentDTO:
        """将 Document 领域对象转换为 DocumentDTO.

        Args:
            doc: 领域 Document.

        Returns:
            DocumentDTO.
        """
        page_infos = tuple(
            PageInfoDTO(
                index=p.index,
                width_pt=p.width,
                height_pt=p.height,
                is_landscape=p.is_landscape,
                is_portrait=p.is_portrait,
            )
            for p in doc.pages
        )
        return DocumentDTO(
            path=doc.path,
            filename=doc.filename,
            page_count=doc.page_count,
            pages=page_infos,
            source_paths=doc.source_paths,
            title=doc.title,
            author=doc.author,
        )

    def _build_export_source_document(self):
        """构建导出用的源文档, 多文件场景包含完整 source_paths 映射.

        Returns:
            领域 Document (含正确 source_paths).
        """
        paths = self._document.source_paths if self._document else ()
        if paths and len(paths) > 1:
            return self._repository.load_multiple(list(paths))
        return self._repository.load(self._document.path)

    def refresh_preview_state(self) -> None:
        """刷新预览的切割线和排序状态 (用于 set_page_image 清空后恢复)."""
        self._update_split_lines_preview()
