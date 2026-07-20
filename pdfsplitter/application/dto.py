from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class ExportFormat(Enum):
    """导出格式枚举."""

    PDF_SINGLE = auto()
    PDF_MULTIPLE = auto()
    PNG = auto()
    JPEG = auto()


class PaperCategory(Enum):
    """纸张类别枚举."""

    ISO216 = "ISO216"
    ANSI = "ANSI"
    NORTH_AMERICAN = "NorthAmerican"
    CUSTOM = "Custom"


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
class PageDTO:
    """页面 DTO (含缩略图数据)."""

    index: int
    width_pt: float
    height_pt: float
    is_landscape: bool
    is_portrait: bool
    thumbnail_bytes: bytes | None = None


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
class ExportOptionDTO:
    """导出选项 DTO."""

    format: ExportFormat = ExportFormat.PDF_SINGLE
    output_path: Path | None = None
    dpi: int = 150
    jpeg_quality: int = 85
