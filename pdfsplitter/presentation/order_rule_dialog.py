"""OrderRuleDialog - 排序规则设置对话框."""

from __future__ import annotations

import logging

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from pdfsplitter.domain.layout.order_rule import OrderRule

logger = logging.getLogger(__name__)

_PREVIEW_ROWS = 3
_PREVIEW_COLS = 3


class _PreviewGrid(QWidget):
    """排序规则预览网格."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._indices: tuple[int, ...] = tuple(range(_PREVIEW_ROWS * _PREVIEW_COLS))
        self.setFixedSize(120, 120)

    def set_indices(self, indices: tuple[int, ...]) -> None:
        self._indices = indices
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cw = self.width() // _PREVIEW_COLS
        ch = self.height() // _PREVIEW_ROWS

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        for i, tile_idx in enumerate(self._indices):
            r = i // _PREVIEW_COLS
            c = i % _PREVIEW_COLS
            rect = QRect(c * cw + 1, r * ch + 1, cw - 2, ch - 2)

            if tile_idx == 0:
                painter.setBrush(QColor("#e3f2fd"))
            else:
                painter.setBrush(QColor("#ffffff"))
            painter.setPen(QPen(QColor("#bbb")))
            painter.drawRect(rect)

            painter.setPen(QColor("#333"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(tile_idx + 1))


class OrderRuleDialog(QDialog):
    """排序规则设置对话框.

    提供行/列方向、优先轴的选择, 上方预览微型网格.
    """

    def __init__(
        self,
        current_rule: OrderRule,
        parent: QWidget | None = None,
    ) -> None:
        """初始化.

        Args:
            current_rule: 当前排序规则.
            parent: 父窗口.
        """
        super().__init__(parent)
        self._rule = current_rule
        self.setWindowTitle("排序规则设置")
        self.setMinimumWidth(320)
        self._setup_ui()
        self._load_rule(current_rule)
        self._update_preview()

    def result_rule(self) -> OrderRule:
        """获取设置的规则."""
        return self._rule

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        preview_label = QLabel("预览")
        preview_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preview_label)
        preview_row = QHBoxLayout()
        self._preview = _PreviewGrid()
        preview_row.addWidget(self._preview)
        preview_row.addStretch()
        layout.addLayout(preview_row)

        primary_group = QGroupBox("优先顺序")
        pg_layout = QHBoxLayout(primary_group)
        self._pri_group = QButtonGroup(self)
        self._radio_row_first = QRadioButton("先行后列")
        self._pri_group.addButton(self._radio_row_first, 0)
        pg_layout.addWidget(self._radio_row_first)
        self._radio_col_first = QRadioButton("先列后行")
        self._pri_group.addButton(self._radio_col_first, 1)
        pg_layout.addWidget(self._radio_col_first)
        pg_layout.addStretch()
        layout.addWidget(primary_group)

        direction_group = QGroupBox("方向")
        dg_layout = QHBoxLayout(direction_group)

        dg_layout.addWidget(QLabel("行方向:"))
        self._combo_row = QComboBox()
        self._combo_row.addItems(["从上到下", "从下到上"])
        self._combo_row.setFixedWidth(90)
        dg_layout.addWidget(self._combo_row)

        dg_layout.addSpacing(12)

        dg_layout.addWidget(QLabel("列方向:"))
        self._combo_col = QComboBox()
        self._combo_col.addItems(["从左到右", "从右到左"])
        self._combo_col.setFixedWidth(90)
        dg_layout.addWidget(self._combo_col)

        dg_layout.addStretch()
        layout.addWidget(direction_group)

        self._pri_group.buttonClicked.connect(self._on_rule_changed)
        self._combo_row.currentIndexChanged.connect(self._on_rule_changed)
        self._combo_col.currentIndexChanged.connect(self._on_rule_changed)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_rule(self, rule: OrderRule) -> None:
        self._radio_row_first.setChecked(rule.primary_axis == "row")
        self._radio_col_first.setChecked(rule.primary_axis == "col")
        self._combo_row.setCurrentIndex(
            0 if rule.row_direction == "top_to_bottom" else 1
        )
        self._combo_col.setCurrentIndex(
            0 if rule.col_direction == "left_to_right" else 1
        )

    def _build_rule(self) -> OrderRule:
        return OrderRule(
            row_direction="top_to_bottom" if self._combo_row.currentIndex() == 0 else "bottom_to_top",
            col_direction="left_to_right" if self._combo_col.currentIndex() == 0 else "right_to_left",
            primary_axis="row" if self._radio_row_first.isChecked() else "col",
        )

    def _on_rule_changed(self) -> None:
        rule = self._build_rule()
        indices = rule.compute_indices(_PREVIEW_ROWS, _PREVIEW_COLS)
        self._preview.set_indices(indices)

    def _update_preview(self) -> None:
        self._on_rule_changed()

    def _on_accept(self) -> None:
        self._rule = self._build_rule()
        self.accept()
