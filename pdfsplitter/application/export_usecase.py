"""Export use case."""

from __future__ import annotations

import logging
from pathlib import Path

from pdfsplitter.application.repository import DocumentRepository
from pdfsplitter.domain.document.document import Document
from pdfsplitter.domain.export.export_config import ExportConfig, ExportFormat, ExportResult
from pdfsplitter.domain.geometry.size import Size
from pdfsplitter.domain.layout.layout_engine import LayoutEngine
from pdfsplitter.domain.layout.split_lines import SplitLines
from pdfsplitter.domain.layout.tile_order import TileOrder
from pdfsplitter.infrastructure.pdf_splitter import PdfSplitter

logger = logging.getLogger(__name__)


class ExportUseCase:
    """导出用例.

    编排: 文档加载 → 布局计算 → PDF 切分 → 输出.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        pdf_splitter: PdfSplitter | None = None,
        layout_engine: LayoutEngine | None = None,
    ) -> None:
        self._repository = repository
        self._pdf_splitter = pdf_splitter or PdfSplitter()
        self._layout_engine = layout_engine or LayoutEngine()

    def execute(
        self,
        source_path: Path,
        page_index: int,
        split_lines: SplitLines,
        order: TileOrder,
        target_size_mm: tuple[float, float],
        config: ExportConfig,
        source_path_override: Path | None = None,
        local_page_index: int | None = None,
    ) -> ExportResult:
        """执行导出.

        Args:
            source_path: 源文件路径.
            page_index: 源页码.
            split_lines: 切割线.
            order: 输出顺序.
            target_size_mm: 目标纸张 (宽, 高) mm.
            config: 导出配置.

        Returns:
            ExportResult.

        Raises:
            FileNotFoundError, ValueError: 源文件问题.
            OSError: 输出文件写入失败.
        """
        source_doc = self._repository.load(source_path)
        page = source_doc.get_page(page_index)
        grid = self._layout_engine.calculate_from_lines(page.size, split_lines)

        logger.info(
            "ExportUseCase: splitting page %d into %d tiles → %s",
            page_index, len(grid.tiles), config.output_path,
        )
        return self._pdf_splitter.split(
            source_document=source_doc,
            page_index=page_index,
            grid=grid,
            order=order,
            target_size_mm=target_size_mm,
            config=config,
            source_path_override=source_path_override,
            local_page_index=local_page_index,
        )

    def execute_all(
        self,
        source_path: Path,
        page_configs: dict[int, tuple[SplitLines, TileOrder]],
        target_size_mm: tuple[float, float],
        output_path: Path,
        source_document: Document | None = None,
    ) -> ExportResult:
        """导出多个页面到单个 PDF.

        Args:
            source_path: 源文件路径 (单文件场景).
            page_configs: {page_index: (SplitLines, TileOrder)}.
            target_size_mm: 目标纸张 (宽, 高) mm.
            output_path: 输出文件路径.
            source_document: 可选的预加载源文档 (多文件场景, 含 source_paths).

        Returns:
            ExportResult.
        """
        source_doc = source_document if source_document is not None else self._repository.load(source_path)
        grouped: list[tuple[int, SplitLines, TileOrder]] = []
        for page_idx in sorted(page_configs.keys()):
            sl, order = page_configs[page_idx]
            grouped.append((page_idx, sl, order))

        config = ExportConfig(format=ExportFormat.PDF_SINGLE, output_path=output_path)
        result = self._pdf_splitter.split_all(
            source_document=source_doc,
            page_configs=grouped,
            target_size_mm=target_size_mm,
            config=config,
        )
        logger.info(
            "ExportUseCase: exported %d tiles from %d pages → %s",
            result.tile_count, len(grouped), output_path,
        )
        return result
