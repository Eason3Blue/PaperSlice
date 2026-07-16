"""DTO module - 用于 GUI 层与领域层之间的数据传输."""

from pdfsplitter.application.dto import (
    DocumentDTO,
    ExportOptionDTO,
    LayoutResultDTO,
    PageDTO,
    PageInfoDTO,
    PaperDTO,
    PosterSplitConfigDTO,
    PreviewTileDTO,
)

__all__ = [
    "PosterSplitConfigDTO",
    "LayoutResultDTO",
    "PreviewTileDTO",
    "DocumentDTO",
    "PageDTO",
    "PageInfoDTO",
    "PaperDTO",
    "ExportOptionDTO",
]
