"""PdfSplitter - 基于 PyMuPDF 的 PDF 切分服务."""

from __future__ import annotations

import logging
from pathlib import Path

from pdfsplitter.domain.document.document import Document
from pdfsplitter.domain.document.page import Page
from pdfsplitter.domain.export.export_config import ExportConfig, ExportFormat, ExportResult
from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.geometry.size import Size
from pdfsplitter.domain.layout.grid import Grid
from pdfsplitter.domain.layout.layout_engine import LayoutEngine
from pdfsplitter.domain.layout.split_lines import SplitLines
from pdfsplitter.domain.layout.tile_order import TileOrder
from pdfsplitter.domain.units.length import Length, MM_PER_INCH, POINTS_PER_INCH

logger = logging.getLogger(__name__)

MM_TO_PT = POINTS_PER_INCH / MM_PER_INCH


class PdfSplitter:
    """基于 PyMuPDF 的 PDF 切分器.

    负责: 打开源 PDF → 按 Grid 逐块提取 → 放置到目标纸张 → 输出.
    """

    def split(
        self,
        source_document: Document,
        page_index: int,
        grid: Grid,
        order: TileOrder,
        target_size_mm: tuple[float, float],
        config: ExportConfig,
    ) -> ExportResult:
        """执行 PDF 切分并导出.

        Args:
            source_document: 源文档.
            page_index: 源页码.
            grid: 切分网格.
            order: 输出顺序.
            target_size_mm: 目标纸张尺寸 (宽, 高) mm.
            config: 导出配置.

        Returns:
            ExportResult.

        Raises:
            ValueError: 参数无效.
            OSError: 文件写入失败.
        """
        import fitz

        src_path = source_document.path
        source_page = source_document.get_page(page_index)

        tw_mm, th_mm = target_size_mm
        target_w = tw_mm * MM_TO_PT
        target_h = th_mm * MM_TO_PT

        src_pdf = fitz.open(str(src_path))

        if config.format == ExportFormat.PDF_SINGLE:
            output_paths = self._split_to_single_pdf(
                src_pdf, source_page.index, target_w, target_h, grid, order, config,
            )
        else:
            output_paths = self._split_to_multiple_pdfs(
                src_pdf, source_page.index, target_w, target_h, grid, order, config,
            )

        src_pdf.close()
        logger.info("PdfSplitter: exported %d tiles to %d file(s)", order.count, len(output_paths))
        return ExportResult(output_paths=tuple(output_paths), tile_count=order.count)

    def split_all(
        self,
        source_document: Document,
        page_configs: list[tuple[int, SplitLines, TileOrder]],
        target_size_mm: tuple[float, float],
        config: ExportConfig,
    ) -> ExportResult:
        """合并多个页面的切分结果到单个 PDF.

        Args:
            source_document: 源文档.
            page_configs: [(page_index, SplitLines, TileOrder), ...].
            target_size_mm: 目标纸张尺寸 (宽, 高) mm.
            config: 导出配置.

        Returns:
            ExportResult.
        """
        import fitz

        tw_mm, th_mm = target_size_mm
        target_w = tw_mm * MM_TO_PT
        target_h = th_mm * MM_TO_PT

        src_pdf = fitz.open(str(source_document.path))
        out_pdf = fitz.open()

        total_output = 0
        for page_index, split_lines, order in page_configs:
            engine = LayoutEngine()
            src_page = src_pdf.load_page(page_index)
            grid = engine.calculate_from_lines(
                Size(src_page.rect.width, src_page.rect.height), split_lines,
            )
            for output_idx, tile_index in enumerate(order.indices):
                tile = grid.get_tile_by_index(tile_index)
                if tile is None:
                    continue
                out_page = out_pdf.new_page(width=target_w, height=target_h)
                self._copy_tile_to_page(out_page, src_pdf, src_page, tile.source_rect, target_w, target_h)
                if config.cut_lines:
                    self._draw_cut_lines(out_page, target_w, target_h)
                if config.page_numbers:
                    total_output += 1
                    self._draw_page_number(out_page, total_output, 0, target_w, target_h)
                else:
                    total_output += 1

        out_pdf.save(str(config.output_path))
        out_pdf.close()
        src_pdf.close()
        logger.info("PdfSplitter: exported %d tiles from %d pages → %s", total_output, len(page_configs), config.output_path)
        return ExportResult(output_paths=(config.output_path,), tile_count=total_output)

    def _split_to_single_pdf(
        self,
        src_pdf,
        page_index: int,
        target_w: float,
        target_h: float,
        grid: Grid,
        order: TileOrder,
        config: ExportConfig,
    ) -> list[Path]:
        import fitz

        out_pdf = fitz.open()
        src_page = src_pdf.load_page(page_index)

        for output_index, tile_index in enumerate(order.indices):
            tile = grid.get_tile_by_index(tile_index)
            if tile is None:
                continue
            out_page = out_pdf.new_page(width=target_w, height=target_h)
            self._copy_tile_to_page(out_page, src_pdf, src_page, tile.source_rect, target_w, target_h)
            if config.cut_lines:
                self._draw_cut_lines(out_page, target_w, target_h)
            if config.page_numbers:
                self._draw_page_number(out_page, output_index + 1, order.count, target_w, target_h)

        out_pdf.save(str(config.output_path))
        out_pdf.close()
        return [config.output_path]

    def _split_to_multiple_pdfs(
        self,
        src_pdf,
        page_index: int,
        target_w: float,
        target_h: float,
        grid: Grid,
        order: TileOrder,
        config: ExportConfig,
    ) -> list[Path]:
        import fitz

        paths: list[Path] = []
        src_page = src_pdf.load_page(page_index)
        base = config.output_path.stem
        suffix = config.output_path.suffix
        parent = config.output_path.parent

        for output_index, tile_index in enumerate(order.indices):
            tile = grid.get_tile_by_index(tile_index)
            if tile is None:
                continue
            out_pdf = fitz.open()
            out_page = out_pdf.new_page(width=target_w, height=target_h)
            self._copy_tile_to_page(out_page, src_pdf, src_page, tile.source_rect, target_w, target_h)
            if config.cut_lines:
                self._draw_cut_lines(out_page, target_w, target_h)
            if config.page_numbers:
                self._draw_page_number(out_page, output_index + 1, order.count, target_w, target_h)

            out_path = parent / f"{base}_{output_index + 1:02d}{suffix}"
            out_pdf.save(str(out_path))
            out_pdf.close()
            paths.append(out_path)

        return paths

    @staticmethod
    def _copy_tile_to_page(
        out_page,
        src_pdf,
        src_page,
        source_rect: Rect,
        target_w: float,
        target_h: float,
    ) -> None:
        """将源页面的一个图块复制到目标页面.

        将 source_rect 区域缩放并居中放置在目标页面上.
        """
        import fitz

        tw = source_rect.width
        th = source_rect.height
        if tw <= 0 or th <= 0:
            return

        scale_x = target_w / tw
        scale_y = target_h / th
        scale = min(scale_x, scale_y)

        placed_w = tw * scale
        placed_h = th * scale
        offset_x = (target_w - placed_w) / 2.0
        offset_y = (target_h - placed_h) / 2.0

        clip_rect = fitz.Rect(source_rect.x0, source_rect.y0, source_rect.x1, source_rect.y1)
        target_rect = fitz.Rect(offset_x, offset_y, offset_x + placed_w, offset_y + placed_h)

        out_page.show_pdf_page(target_rect, src_pdf, src_page.number, clip=clip_rect)

    @staticmethod
    def _draw_cut_lines(page, width: float, height: float) -> None:
        """在目标页面绘制裁切线."""
        import fitz

        corner_len = 15.0
        color = (0, 0, 0)
        line_width = 0.5

        corners = [
            ((0, 0), (corner_len, 0), (0, corner_len)),
            ((width, 0), (width - corner_len, 0), (width, corner_len)),
            ((0, height), (corner_len, height), (0, height - corner_len)),
            ((width, height), (width - corner_len, height), (width, height - corner_len)),
        ]
        for origin, h_end, v_end in corners:
            page.draw_line(origin, h_end, color=color, width=line_width)
            page.draw_line(origin, v_end, color=color, width=line_width)

    @staticmethod
    def _draw_page_number(page, current: int, total: int, width: float, height: float) -> None:
        """绘制页码."""
        import fitz

        text = f"{current} / {total}"
        fontsize = 10
        text_width = fitz.get_text_length(text, fontname="helv", fontsize=fontsize)
        x = (width - text_width) / 2.0
        y = height - 15.0
        page.insert_text(
            fitz.Point(x, y), text, fontname="helv", fontsize=fontsize, color=(0, 0, 0)
        )
