"""Main Window - 主窗口视图."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pdfsplitter.application.dto import DocumentDTO, LayoutResultDTO
from pdfsplitter.presentation.main_viewmodel import MainViewModel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """PDF Poster Splitter 主窗口."""

    def __init__(self, viewmodel: MainViewModel) -> None:
        super().__init__()
        self._vm = viewmodel
        self._setup_ui()
        self._connect_signals()
        self.setWindowTitle("PDF Poster Splitter")
        self.resize(1100, 700)

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 750])
        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        file_group = QGroupBox("文件")
        file_layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton("打开 PDF")
        btn_layout.addWidget(self.btn_open)
        file_layout.addLayout(btn_layout)
        self.page_list = QListWidget()
        file_layout.addWidget(self.page_list)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        paper_group = QGroupBox("纸张设置")
        paper_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("纸张类别:"))
        self.combo_category = QComboBox()
        self.combo_category.addItems(["ISO216", "ANSI", "NorthAmerican"])
        row1.addWidget(self.combo_category)
        paper_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("纸张大小:"))
        self.combo_paper = QComboBox()
        row2.addWidget(self.combo_paper)
        paper_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("边距 (mm):"))
        self.spin_margin = QDoubleSpinBox()
        self.spin_margin.setRange(0.0, 100.0)
        self.spin_margin.setValue(10.0)
        self.spin_margin.setSingleStep(1.0)
        row3.addWidget(self.spin_margin)
        paper_layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("重叠 (mm):"))
        self.spin_overlap = QDoubleSpinBox()
        self.spin_overlap.setRange(0.0, 100.0)
        self.spin_overlap.setValue(5.0)
        self.spin_overlap.setSingleStep(1.0)
        row4.addWidget(self.spin_overlap)
        paper_layout.addLayout(row4)

        paper_group.setLayout(paper_layout)
        layout.addWidget(paper_group)

        bottom_layout = QVBoxLayout()
        self.btn_preview = QPushButton("生成预览")
        bottom_layout.addWidget(self.btn_preview)

        self.btn_split = QPushButton("开始切分")
        bottom_layout.addWidget(self.btn_split)

        layout.addLayout(bottom_layout)
        layout.addStretch()
        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        info_group = QGroupBox("文档信息")
        info_layout = QVBoxLayout()
        self.label_info = QLabel("尚未加载文档")
        info_layout.addWidget(self.label_info)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        result_group = QGroupBox("切分结果")
        result_layout = QVBoxLayout()
        self.label_result = QLabel("尚未计算布局")
        result_layout.addWidget(self.label_result)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        layout.addStretch()
        return panel

    def _connect_signals(self) -> None:
        self.btn_open.clicked.connect(self._on_open)
        self.btn_preview.clicked.connect(self._on_preview)
        self.btn_split.clicked.connect(self._on_split)

        self.combo_category.currentTextChanged.connect(self._on_category_changed)

        self._vm.document_loaded_signal.connect(self._on_document_loaded)
        self._vm.layout_calculated_signal.connect(self._on_layout_calculated)
        self._vm.error_signal.connect(self._on_error)
        self._vm.progress_signal.connect(self.status_bar.showMessage)

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "打开 PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if path:
            self._vm.load_document(path)

    def _on_category_changed(self, category: str) -> None:
        papers = self._vm.list_papers(category)
        self.combo_paper.clear()
        for p in papers:
            self.combo_paper.addItem(p.name)

    def _on_preview(self) -> None:
        idx = self.page_list.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "提示", "请先选择一个页面")
            return
        config_updates = {
            "paper_name": self.combo_paper.currentText(),
            "paper_category": self.combo_category.currentText(),
            "margin_mm": self.spin_margin.value(),
            "overlap_mm": self.spin_overlap.value(),
        }
        self._vm.update_config(**config_updates)
        self._vm.calculate_layout(idx)

    def _on_split(self) -> None:
        QMessageBox.information(self, "提示", "切分功能将在后续版本中实现")

    def _on_document_loaded(self, doc: DocumentDTO) -> None:
        self.page_list.clear()
        for page in doc.pages:
            orientation = "L" if page.is_landscape else "P"
            self.page_list.addItem(f"第 {page.index + 1} 页 ({page.width_pt:.0f}x{page.height_pt:.0f}pt {orientation})")
        self.label_info.setText(
            f"文件: {doc.filename}\n页数: {doc.page_count}\n标题: {doc.title or '无'}"
        )
        self.combo_paper.clear()
        papers = self._vm.list_papers("ISO216")
        for p in papers:
            self.combo_paper.addItem(p.name)

    def _on_layout_calculated(self, result: LayoutResultDTO) -> None:
        tiles_info = "\n".join(
            f"  图块 {t.tile_index}: 行={t.row} 列={t.col} "
            f"区域=({t.source_x0:.0f},{t.source_y0:.0f})-({t.source_x1:.0f},{t.source_y1:.0f})"
            for t in result.tiles[:10]
        )
        if result.total_tiles > 10:
            tiles_info += f"\n  ... (共 {result.total_tiles} 个图块)"
        self.label_result.setText(
            f"布局: {result.rows} 行 x {result.cols} 列, 共 {result.total_tiles} 个图块\n{tiles_info}"
        )

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self, "错误", message)
