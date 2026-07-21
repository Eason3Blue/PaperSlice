"""Use cases - 面向 GUI 层的业务用例."""

from __future__ import annotations

import logging
from pathlib import Path

from pdfsplitter.application.dto import (
    DocumentDTO,
    LayoutResultDTO,
    PageInfoDTO,
    PosterSplitConfigDTO,
    PreviewTileDTO,
)
from pdfsplitter.application.repository import DocumentRepository
from pdfsplitter.domain.document.page import Page
from pdfsplitter.domain.layout.layout_engine import LayoutEngine, LayoutParams
from pdfsplitter.domain.geometry.size import Size
from pdfsplitter.domain.units.length import POINTS_PER_MM

logger = logging.getLogger(__name__)


class LoadDocumentUseCase:
    """加载文档用例.

    通过 DocumentRepository 加载 PDF，将其转换为 DTO 返回给 GUI 层.
    """

    def __init__(self, repository: DocumentRepository) -> None:
        """初始化.

        Args:
            repository: 文档仓库实现 (由 DI 注入).
        """
        self._repository = repository

    def execute(self, path: Path, password: str | None = None) -> DocumentDTO:
        """执行加载.

        Args:
            path: 文档路径.
            password: 可选的打开密码.

        Returns:
            DocumentDTO 供 GUI 使用.

        Raises:
            FileNotFoundError, ValueError: 加载失败.
        """
        doc = self._repository.load(path, password)
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


class PosterSplitUseCase:
    """海报切分用例.

    编排完整的切分流程：加载文档 → 计算布局 → 返回结果.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        layout_engine: LayoutEngine | None = None,
    ) -> None:
        self._repository = repository
        self._layout_engine = layout_engine or LayoutEngine()

    def load_document(self, path: Path, password: str | None = None) -> DocumentDTO:
        """加载文档.

        Args:
            path: 文档路径.
            password: 可选的打开密码.

        Returns:
            DocumentDTO.
        """
        loader = LoadDocumentUseCase(self._repository)
        return loader.execute(path, password)

    def calculate_layout(
        self,
        page: Page,
        target_size_mm: tuple[float, float],
        config: PosterSplitConfigDTO,
    ) -> LayoutResultDTO:
        """计算切分布局.

        Args:
            page: 源页面领域对象.
            target_size_mm: 目标纸张宽高 (mm).
            config: 切分配置.

        Returns:
            LayoutResultDTO.
        """
        tw, th = target_size_mm
        target_size = Size(tw * POINTS_PER_MM, th * POINTS_PER_MM)
        margin_pt = config.margin_mm * POINTS_PER_MM
        overlap_pt = config.overlap_mm * POINTS_PER_MM

        params = LayoutParams(
            page_size=page.size,
            target_size=target_size,
            margin_h=margin_pt * 2,
            margin_v=margin_pt * 2,
            overlap=overlap_pt,
        )
        grid = self._layout_engine.calculate(params)

        tiles = tuple(
            PreviewTileDTO(
                tile_index=t.index,
                row=t.row,
                col=t.col,
                source_x0=t.source_rect.x0,
                source_y0=t.source_rect.y0,
                source_x1=t.source_rect.x1,
                source_y1=t.source_rect.y1,
            )
            for t in grid.tiles
        )
        return LayoutResultDTO(
            total_tiles=grid.total_tiles,
            rows=grid.rows,
            cols=grid.cols,
            tiles=tiles,
        )
