from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PaperDTO:
    """纸张规格 DTO."""

    name: str
    category: str
    width_mm: float
    height_mm: float


@dataclass(frozen=True)
class PageInfoDTO:
    """页面信息 DTO."""

    index: int
    width_pt: float
    height_pt: float
    is_landscape: bool
    is_portrait: bool


@dataclass(frozen=True)
class DocumentDTO:
    """文档 DTO."""

    path: Path
    filename: str
    page_count: int
    pages: tuple[PageInfoDTO, ...]
    source_paths: tuple[Path, ...] = field(default_factory=tuple)
    title: str | None = None
    author: str | None = None


@dataclass(frozen=True)
class PosterSplitConfigDTO:
    """海报切分配置 DTO."""

    page_index: int = 0
    paper_name: str = "A4"
    paper_category: str = "ISO216"
    margin_mm: float = 0.0
    overlap_mm: float = 0.0
    cut_lines: bool = False
    page_numbers: bool = False


@dataclass(frozen=True)
class PreviewTileDTO:
    """预览图块 DTO."""

    tile_index: int
    row: int
    col: int
    source_x0: float
    source_y0: float
    source_x1: float
    source_y1: float
    thumbnail_bytes: bytes | None = None


@dataclass(frozen=True)
class LayoutResultDTO:
    """布局计算结果 DTO."""

    total_tiles: int
    rows: int
    cols: int
    tiles: tuple[PreviewTileDTO, ...]


@dataclass(frozen=True)
class PageFilterDTO:
    """页面筛选条件 DTO."""

    page_range_mode: str = "all"
    page_start: int = 1
    page_end: int = 1
    page_list_spec: str = ""
    paper_names: tuple[str, ...] = field(default_factory=tuple)
    orientation_mode: str = "all"
    matched_indices: tuple[int, ...] = field(default_factory=tuple)
    total_pages: int = 0

    @property
    def matched_count(self) -> int:
        """匹配的页数."""
        return len(self.matched_indices)

    @property
    def is_active(self) -> bool:
        """是否有筛选条件生效."""
        return self.page_range_mode != "all" or bool(self.paper_names) or self.orientation_mode != "all"


@dataclass(frozen=True)
class PageListStateDTO:
    """页面列表完整状态 DTO.

    打包筛选结果、选中状态和视图模式, 供 UI 层一次性同步.
    """

    total_pages: int = 0
    view_mode: str = "all"
    selected_indices: tuple[int, ...] = field(default_factory=tuple)
    filtered_indices: tuple[int, ...] = field(default_factory=tuple)
    filter_active: bool = False

    @property
    def visible_indices(self) -> tuple[int, ...]:
        """当前可见的页面索引."""
        if self.view_mode == "filtered" and self.filter_active:
            return self.filtered_indices
        return tuple(range(self.total_pages))

    @property
    def visible_count(self) -> int:
        """可见页数."""
        return len(self.visible_indices)

    @property
    def is_all_selected(self) -> bool:
        """是否所有可见页面都被选中."""
        if not self.visible_indices:
            return False
        selected = set(self.selected_indices)
        return all(i in selected for i in self.visible_indices)

    @property
    def is_partially_selected(self) -> bool:
        """是否部分（非全部、非零）可见页面被选中."""
        if not self.visible_indices:
            return False
        selected = set(self.selected_indices)
        visible_set = set(self.visible_indices)
        some = any(i in selected for i in visible_set)
        all_sel = all(i in selected for i in visible_set)
        return some and not all_sel

    @property
    def selected_count(self) -> int:
        """被选中的页数."""
        return len(self.selected_indices)
