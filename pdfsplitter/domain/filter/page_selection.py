"""PageSelection - 页面选中状态值对象."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PageSelection:
    """不可变的页面选中状态.

    表示哪些页面被用户勾选参与导出. 独立于 PageFilter (仅控制可见性).

    Attributes:
        selected_indices: 被选中的页面索引集合 (0-indexed).
    """

    selected_indices: frozenset[int] = field(default_factory=frozenset)

    def is_selected(self, index: int) -> bool:
        """检查指定页是否被选中."""
        return index in self.selected_indices

    def with_toggled(self, index: int) -> PageSelection:
        """切换指定页的选中状态.

        Args:
            index: 页面索引.

        Returns:
            新的 PageSelection.
        """
        if index in self.selected_indices:
            return PageSelection(
                selected_indices=self.selected_indices - {index}
            )
        return PageSelection(
            selected_indices=self.selected_indices | {index}
        )

    def with_selected(self, indices: set[int]) -> PageSelection:
        """设置选中的页面索引集合.

        Args:
            indices: 要选中的页面索引.

        Returns:
            新的 PageSelection.
        """
        return PageSelection(selected_indices=frozenset(indices))

    def with_added(self, indices: set[int]) -> PageSelection:
        """添加选中页面索引.

        Args:
            indices: 要添加的页面索引.

        Returns:
            新的 PageSelection.
        """
        return PageSelection(
            selected_indices=self.selected_indices | frozenset(indices)
        )

    def with_removed(self, indices: set[int]) -> PageSelection:
        """移除选中页面索引.

        Args:
            indices: 要移除的页面索引.

        Returns:
            新的 PageSelection.
        """
        return PageSelection(
            selected_indices=self.selected_indices - frozenset(indices)
        )

    @classmethod
    def all_selected(cls, count: int) -> PageSelection:
        """创建全部选中的状态.

        Args:
            count: 总页数.

        Returns:
            PageSelection.
        """
        return cls(selected_indices=frozenset(range(count)))

    @classmethod
    def empty(cls) -> PageSelection:
        """创建无选中的状态."""
        return cls()
