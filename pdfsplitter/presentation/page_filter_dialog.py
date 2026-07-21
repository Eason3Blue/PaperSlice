"""PageFilterDialog - 页面筛选对话框."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pdfsplitter.application.dto import PageInfoDTO
from pdfsplitter.domain.filter.page_filter import PageFilter
from pdfsplitter.domain.paper.paper_database import PaperDatabase

logger = logging.getLogger(__name__)

_SIZES_BY_CATEGORY = {
    "ISO216": ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
                "B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10"],
    "ANSI": ["ANSI A", "ANSI B", "ANSI C", "ANSI D", "ANSI E"],
    "NorthAmerican": ["Letter", "Legal", "Tabloid", "Ledger"],
}


class PageFilterDialog(QDialog):
    """页面筛选对话框.

    提供页码、纸张尺寸、方向三维度筛选, 返回 PageFilterDTO.
    """

    def __init__(
        self,
        current_filter: PageFilter,
        pages: tuple[PageInfoDTO, ...],
        parent: QWidget | None = None,
    ) -> None:
        """初始化.

        Args:
            current_filter: 当前筛选条件.
            pages: 文档页面信息列表.
            parent: 父窗口.
        """
        super().__init__(parent)
        self._pages = pages
        self._current_filter = current_filter
        self._result_filter = current_filter

        self.setWindowTitle("页面筛选")
        self.setMinimumWidth(420)
        self._setup_ui()
        self._load_current_filter(current_filter)

    def result(self) -> PageFilter:
        """获取最终的筛选条件.

        Returns:
            用户确认的 PageFilter.
        """
        return self._result_filter

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(self._create_page_number_group())
        layout.addWidget(self._create_paper_size_group())
        layout.addWidget(self._create_orientation_group())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_page_number_group(self) -> QGroupBox:
        group = QGroupBox("页码筛选")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        self._pg_group = QButtonGroup(self)

        self._radio_all = QRadioButton("全部页")
        self._radio_all.setChecked(True)
        self._pg_group.addButton(self._radio_all, 0)
        layout.addWidget(self._radio_all)

        range_widget = QWidget()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)
        self._radio_range = QRadioButton("范围:")
        self._pg_group.addButton(self._radio_range, 1)
        range_layout.addWidget(self._radio_range)
        self._spin_start = QSpinBox()
        self._spin_start.setMinimum(1)
        self._spin_start.setMaximum(max(len(self._pages), 1))
        range_layout.addWidget(self._spin_start)
        range_layout.addWidget(QLabel("到"))
        self._spin_end = QSpinBox()
        self._spin_end.setMinimum(1)
        self._spin_end.setMaximum(max(len(self._pages), 1))
        self._spin_end.setValue(max(len(self._pages), 1))
        range_layout.addWidget(self._spin_end)
        range_layout.addStretch()
        layout.addWidget(range_widget)

        list_widget = QWidget()
        list_layout = QHBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        self._radio_list = QRadioButton("指定:")
        self._pg_group.addButton(self._radio_list, 2)
        list_layout.addWidget(self._radio_list)
        self._input_page_list = QLineEdit()
        self._input_page_list.setPlaceholderText("如 1,3,5,7-10")
        self._input_page_list.setMinimumWidth(180)
        list_layout.addWidget(self._input_page_list)
        list_layout.addStretch()
        layout.addWidget(list_widget)

        self._pg_group.buttonClicked.connect(self._on_range_mode_changed)
        return group

    def _create_paper_size_group(self) -> QGroupBox:
        group = QGroupBox("页面尺寸")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        self._size_checkboxes: dict[str, QCheckBox] = {}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(2)

        for cat_name, names in _SIZES_BY_CATEGORY.items():
            cat_label = QLabel(cat_name)
            cat_label.setStyleSheet("font-weight: bold; color: #666;")
            scroll_layout.addWidget(cat_label)

            cat_widget = QWidget()
            cat_layout = QHBoxLayout(cat_widget)
            cat_layout.setContentsMargins(0, 0, 0, 0)
            cat_layout.setSpacing(4)

            for name in names:
                cb = QCheckBox(name)
                cb.setFixedWidth(90)
                self._size_checkboxes[name] = cb
                cat_layout.addWidget(cb)
            cat_layout.addStretch()
            scroll_layout.addWidget(cat_widget)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return group

    def _create_orientation_group(self) -> QGroupBox:
        group = QGroupBox("页面方向")
        layout = QHBoxLayout(group)

        self._ori_group = QButtonGroup(self)

        self._radio_ori_all = QRadioButton("全部")
        self._radio_ori_all.setChecked(True)
        self._ori_group.addButton(self._radio_ori_all, 0)
        layout.addWidget(self._radio_ori_all)

        self._radio_ori_portrait = QRadioButton("纵向")
        self._ori_group.addButton(self._radio_ori_portrait, 1)
        layout.addWidget(self._radio_ori_portrait)

        self._radio_ori_landscape = QRadioButton("横向")
        self._ori_group.addButton(self._radio_ori_landscape, 2)
        layout.addWidget(self._radio_ori_landscape)

        layout.addStretch()
        return group

    def _on_range_mode_changed(self) -> None:
        mode = self._pg_group.checkedId()
        self._spin_start.setEnabled(mode == 1)
        self._spin_end.setEnabled(mode == 1)
        self._input_page_list.setEnabled(mode == 2)

    def _load_current_filter(self, f: PageFilter) -> None:
        if f.page_range_mode == "range":
            self._radio_range.setChecked(True)
            if f.page_start >= 1:
                self._spin_start.setValue(f.page_start)
            if f.page_end >= 1:
                self._spin_end.setValue(f.page_end)
        elif f.page_range_mode == "list":
            self._radio_list.setChecked(True)
            self._input_page_list.setText(f.page_list_spec)
        else:
            self._radio_all.setChecked(True)

        for name in self._size_checkboxes:
            self._size_checkboxes[name].setChecked(name in f.paper_names)

        if f.orientation_mode == "portrait":
            self._radio_ori_portrait.setChecked(True)
        elif f.orientation_mode == "landscape":
            self._radio_ori_landscape.setChecked(True)
        else:
            self._radio_ori_all.setChecked(True)

        self._on_range_mode_changed()

    def _on_accept(self) -> None:
        range_id = self._pg_group.checkedId()
        if range_id == 0:
            range_mode = "all"
            start, end = 1, 1
            list_spec = ""
        elif range_id == 1:
            range_mode = "range"
            start = self._spin_start.value()
            end = self._spin_end.value()
            list_spec = ""
        else:
            range_mode = "list"
            start, end = 1, 1
            list_spec = self._input_page_list.text().strip()

        paper_names = tuple(
            name for name, cb in self._size_checkboxes.items() if cb.isChecked()
        )

        ori_id = self._ori_group.checkedId()
        if ori_id == 1:
            orientation_mode = "portrait"
        elif ori_id == 2:
            orientation_mode = "landscape"
        else:
            orientation_mode = "all"

        self._result_filter = PageFilter(
            page_range_mode=range_mode,
            page_start=start,
            page_end=end,
            page_list_spec=list_spec,
            paper_names=paper_names,
            orientation_mode=orientation_mode,
        )
        self.accept()
