"""Application layer tests."""

from __future__ import annotations

import math
from pathlib import Path
from dataclasses import dataclass

import pytest

from pdfsplitter.application.dto import PosterSplitConfigDTO
from pdfsplitter.application.repository import DocumentRepository
from pdfsplitter.application.usecases import LoadDocumentUseCase, PosterSplitUseCase
from pdfsplitter.domain.document.document import Document
from pdfsplitter.domain.document.page import Page
from pdfsplitter.domain.geometry.rect import Rect
from pdfsplitter.domain.geometry.size import Size


class FakeDocumentRepository(DocumentRepository):
    """测试用假仓库."""

    def load(self, path: Path, password: str | None = None) -> Document:
        page = Page(index=0, media_box=Rect(0, 0, 612, 792))
        return Document(path=path, pages=(page,), title="Test", author="Tester")

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff")


class TestLoadDocumentUseCase:
    """LoadDocumentUseCase 测试套件."""

    def test_load_returns_dto(self) -> None:
        repo = FakeDocumentRepository()
        uc = LoadDocumentUseCase(repo)
        dto = uc.execute(Path("test.pdf"))
        assert dto.filename == "test.pdf"
        assert dto.page_count == 1
        assert dto.title == "Test"
        assert dto.author == "Tester"
        assert len(dto.pages) == 1
        assert dto.pages[0].index == 0
        assert dto.pages[0].width_pt == 612
        assert dto.pages[0].height_pt == 792


class TestPosterSplitUseCase:
    """PosterSplitUseCase 测试套件."""

    def test_calculate_layout_basic(self) -> None:
        repo = FakeDocumentRepository()
        uc = PosterSplitUseCase(repo)

        page = Page(index=0, media_box=Rect(0, 0, 612, 792))
        config = PosterSplitConfigDTO(
            paper_name="A4",
            paper_category="ISO216",
            margin_mm=0.0,
            overlap_mm=0.0,
        )
        target_mm = (210.0, 297.0)
        result = uc.calculate_layout(page, target_mm, config)
        assert result.total_tiles > 0
        assert result.rows >= 1
        assert result.cols >= 1
        assert len(result.tiles) == result.total_tiles

    def test_calculate_layout_with_margin(self) -> None:
        repo = FakeDocumentRepository()
        uc = PosterSplitUseCase(repo)

        page = Page(index=0, media_box=Rect(0, 0, 612, 792))
        config = PosterSplitConfigDTO(
            paper_name="A4",
            paper_category="ISO216",
            margin_mm=10.0,
            overlap_mm=0.0,
        )
        target_mm = (210.0, 297.0)
        result = uc.calculate_layout(page, target_mm, config)
        assert result.total_tiles > 0

    def test_load_document(self) -> None:
        repo = FakeDocumentRepository()
        uc = PosterSplitUseCase(repo)
        dto = uc.load_document(Path("sample.pdf"))
        assert dto.filename == "sample.pdf"
        assert dto.page_count == 1


class TestPipeline:
    """Pipeline 测试套件."""

    def test_pipeline_stages_executed_in_order(self) -> None:
        from pdfsplitter.application.pipeline import Pipeline, PipelineContext, PipelineStage

        call_order: list[str] = []

        class StageA(PipelineStage):
            name = "A"
            def process(self, ctx: PipelineContext) -> PipelineContext:
                call_order.append("A")
                return ctx

        class StageB(PipelineStage):
            name = "B"
            def process(self, ctx: PipelineContext) -> PipelineContext:
                call_order.append("B")
                return ctx

        pipeline = Pipeline()
        pipeline.add_stage(StageA()).add_stage(StageB())
        pipeline.execute()
        assert call_order == ["A", "B"]

    def test_pipeline_context_passes_data(self) -> None:
        from pdfsplitter.application.pipeline import Pipeline, PipelineContext, PipelineStage

        class DataStage(PipelineStage):
            name = "DataStage"
            def process(self, ctx: PipelineContext) -> PipelineContext:
                ctx.data["key"] = "value"
                return ctx

        pipeline = Pipeline()
        pipeline.add_stage(DataStage())
        result = pipeline.execute()
        assert result.data["key"] == "value"

    def test_pipeline_stage_failure_propagates(self) -> None:
        from pdfsplitter.application.pipeline import Pipeline, PipelineContext, PipelineStage

        class FailStage(PipelineStage):
            name = "Fail"
            def process(self, ctx: PipelineContext) -> PipelineContext:
                raise RuntimeError("stage failed")

        pipeline = Pipeline()
        pipeline.add_stage(FailStage())
        with pytest.raises(RuntimeError, match="stage failed"):
            pipeline.execute()
