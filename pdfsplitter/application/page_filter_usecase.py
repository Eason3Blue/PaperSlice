"""PageFilterUseCase - 页面筛选用例."""

from __future__ import annotations

import logging
import re

from pdfsplitter.application.dto import PageFilterDTO, PageInfoDTO
from pdfsplitter.domain.filter.page_filter import PageFilter
from pdfsplitter.domain.paper.paper_database import PaperDatabase

logger = logging.getLogger(__name__)

_MM_TO_PT = 72.0 / 25.4


class PageFilterUseCase:
    """页面筛选用例.

    将 PageFilter 领域对象应用于文档页面列表, 解析出匹配的页面索引.
    """

    @staticmethod
    def resolve(filter_obj: PageFilter, pages: tuple[PageInfoDTO, ...]) -> PageFilterDTO:
        """根据筛选条件解析匹配的页面索引.

        Args:
            filter_obj: 筛选条件值对象.
            pages: 文档页面信息列表.

        Returns:
            PageFilterDTO 包含匹配的页面索引集合.
        """
        if not pages:
            return PageFilterDTO(
                page_range_mode=filter_obj.page_range_mode,
                page_start=filter_obj.page_start,
                page_end=filter_obj.page_end,
                page_list_spec=filter_obj.page_list_spec,
                paper_names=filter_obj.paper_names,
                orientation_mode=filter_obj.orientation_mode,
                matched_indices=(),
                total_pages=0,
            )

        from_page_numbers = PageFilterUseCase._resolve_page_numbers(filter_obj, len(pages))
        from_paper = PageFilterUseCase._resolve_paper_names(filter_obj, pages)
        from_orientation = PageFilterUseCase._resolve_orientation(filter_obj, pages)

        matched = set(from_page_numbers)
        if from_paper:
            matched &= from_paper
        if from_orientation:
            matched &= from_orientation

        return PageFilterDTO(
            page_range_mode=filter_obj.page_range_mode,
            page_start=filter_obj.page_start,
            page_end=filter_obj.page_end,
            page_list_spec=filter_obj.page_list_spec,
            paper_names=filter_obj.paper_names,
            orientation_mode=filter_obj.orientation_mode,
            matched_indices=tuple(sorted(matched)),
            total_pages=len(pages),
        )

    @staticmethod
    def _resolve_page_numbers(filter_obj: PageFilter, total_pages: int) -> set[int]:
        """解析页码条件, 返回 0-indexed 集合."""
        if filter_obj.page_range_mode == "all":
            return set(range(total_pages))

        if filter_obj.page_range_mode == "range":
            start = max(1, filter_obj.page_start) - 1
            end = min(total_pages, filter_obj.page_end)
            return set(range(start, end))

        if filter_obj.page_range_mode == "list":
            return PageFilterUseCase._parse_page_list(filter_obj.page_list_spec, total_pages)

        return set()

    @staticmethod
    def _parse_page_list(spec: str, total_pages: int) -> set[int]:
        """解析页码列表字符串, 如 "1,3,5,7-10", 返回 0-indexed 集合.

        Args:
            spec: 页码列表字符串.
            total_pages: 总页数.

        Returns:
            0-indexed 页码集合.
        """
        result: set[int] = set()
        parts = re.split(r"[;,]", spec)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                try:
                    a_str, b_str = part.split("-", 1)
                    a, b = int(a_str.strip()), int(b_str.strip())
                    a = max(1, a)
                    b = min(total_pages, b)
                    for i in range(a - 1, b):
                        result.add(i)
                except (ValueError, IndexError):
                    continue
            else:
                try:
                    i = int(part)
                    if 1 <= i <= total_pages:
                        result.add(i - 1)
                except ValueError:
                    continue
        return result

    @staticmethod
    def _resolve_paper_names(filter_obj: PageFilter, pages: tuple[PageInfoDTO, ...]) -> set[int] | None:
        """解析纸张尺寸筛选, 返回匹配的 0-indexed 集合.

        Returns:
            None 表示不按尺寸筛选 (空条件).
        """
        if not filter_obj.paper_names:
            return None

        db = PaperDatabase.instance()
        allowed_sizes: set[tuple[float, float]] = set()
        for name in filter_obj.paper_names:
            spec = db.get(name)
            if spec is None:
                for cat in ["ISO216", "ANSI", "NorthAmerican"]:
                    spec = db.get(name, cat)
                    if spec is not None:
                        break
            if spec is not None:
                w_pt = spec.size.w * _MM_TO_PT
                h_pt = spec.size.h * _MM_TO_PT
                allowed_sizes.add((w_pt, h_pt))
                allowed_sizes.add((h_pt, w_pt))

        if not allowed_sizes:
            return set()

        result: set[int] = set()
        for i, page in enumerate(pages):
            page_dims = (page.width_pt, page.height_pt)
            if page_dims in allowed_sizes:
                result.add(i)
        return result

    @staticmethod
    def _resolve_orientation(filter_obj: PageFilter, pages: tuple[PageInfoDTO, ...]) -> set[int] | None:
        """解析方向筛选, 返回匹配的 0-indexed 集合.

        Returns:
            None 表示不按方向筛选.
        """
        if filter_obj.orientation_mode == "all":
            return None

        result: set[int] = set()
        for i, page in enumerate(pages):
            if filter_obj.orientation_mode == "portrait" and page.is_portrait:
                result.add(i)
            elif filter_obj.orientation_mode == "landscape" and page.is_landscape:
                result.add(i)
        return result
