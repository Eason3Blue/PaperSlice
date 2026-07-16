"""Export domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class ExportFormat(Enum):
    PDF_SINGLE = auto()
    PDF_MULTIPLE = auto()


@dataclass(frozen=True)
class ExportConfig:
    """导出配置值对象.

    Attributes:
        format: 导出格式 (单文件 / 多文件).
        output_path: 输出路径.
        cut_lines: 是否添加裁切线.
        page_numbers: 是否添加页码.
    """

    format: ExportFormat = ExportFormat.PDF_SINGLE
    output_path: Path = field(default_factory=lambda: Path("output.pdf"))
    cut_lines: bool = False
    page_numbers: bool = False


@dataclass(frozen=True)
class ExportResult:
    """导出结果值对象.

    Attributes:
        output_paths: 导出的文件路径列表.
        tile_count: 导出的图块总数.
    """

    output_paths: tuple[Path, ...]
    tile_count: int
