"""PageFilter - 页面筛选条件值对象."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PageFilter:
    """不可变的页面筛选条件.

    用于描述对文档页面子集的筛选规则:
    - 页码筛选 (范围 / 指定列表)
    - 页面尺寸筛选 (按纸张名称)
    - 页面方向筛选 (纵向 / 横向)

    Attributes:
        page_range_mode: 页码范围模式 ("all", "range", "list").
        page_start: 范围起始页 (1-indexed), 仅 range 模式有效.
        page_end: 范围结束页 (1-indexed), 仅 range 模式有效.
        page_list_spec: 指定页码字符串, 支持 "1,3,5,7-10" 格式.
        paper_names: 筛选的纸张名称列表 (空表示不按尺寸筛选).
        orientation_mode: 方向模式 ("all", "portrait", "landscape").
    """

    page_range_mode: str = "all"
    page_start: int = 1
    page_end: int = 1
    page_list_spec: str = ""
    paper_names: tuple[str, ...] = field(default_factory=tuple)
    orientation_mode: str = "all"

    @property
    def is_active(self) -> bool:
        """是否有任何筛选条件生效."""
        if self.page_range_mode != "all":
            return True
        if self.paper_names:
            return True
        if self.orientation_mode != "all":
            return True
        return False

    @classmethod
    def empty(cls) -> PageFilter:
        """返回无筛选条件的实例."""
        return cls()
