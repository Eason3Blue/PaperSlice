"""Main Window - 主窗口视图 (交互式预览 + 切割线)."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pdfsplitter.application.dto import DocumentDTO
from pdfsplitter.presentation.main_viewmodel import MainViewModel
from pdfsplitter.presentation.preview_widget import PreviewWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """PDF Poster Splitter 主窗口.

    布局: 左侧面板(文件+控制) | 右侧预览
    """

    def __init__(self, viewmodel: MainViewModel) -> None:
        super().__init__()
        self._vm = viewmodel
        self._setup_ui()
        self._connect_signals()
        self.setWindowTitle("PDF Poster Splitter")
        self.resize(1300, 800)

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_left_panel())
        splitter.addWidget(self._create_preview_panel())
        splitter.setSizes([320, 960])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 请打开 PDF 文件")

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        file_group = QGroupBox("文件")
        fl = QVBoxLayout()
        self.btn_open = QPushButton("打开 PDF / 图片")
        fl.addWidget(self.btn_open)
        project_row = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        self.btn_load = QPushButton("加载存档")
        project_row.addWidget(self.btn_save)
        project_row.addWidget(self.btn_load)
        fl.addLayout(project_row)
        self.page_list = QListWidget()
        self.page_list.setMaximumHeight(180)
        fl.addWidget(self.page_list)
        self.label_page_info = QLabel("未选择页面")
        fl.addWidget(self.label_page_info)
        file_group.setLayout(fl)
        layout.addWidget(file_group)

        paper_group = QGroupBox("目标纸张")
        pl = QVBoxLayout()
        pr1 = QHBoxLayout()
        pr1.addWidget(QLabel("类别:"))
        self.combo_category = QComboBox()
        self.combo_category.addItems(["ISO216", "ANSI", "NorthAmerican"])
        pr1.addWidget(self.combo_category)
        pl.addLayout(pr1)
        pr2 = QHBoxLayout()
        pr2.addWidget(QLabel("大小:"))
        self.combo_paper = QComboBox()
        pr2.addWidget(self.combo_paper)
        pl.addLayout(pr2)
        paper_group.setLayout(pl)
        layout.addWidget(paper_group)

        split_group = QGroupBox("切割线")
        sl = QVBoxLayout()
        sl.setSpacing(4)

        sl.addWidget(QLabel("自动预设:"))
        preset_row = QHBoxLayout()
        self.btn_half_v = QPushButton("垂直二分")
        self.btn_half_h = QPushButton("水平二分")
        self.btn_quarter = QPushButton("四等分")
        preset_row.addWidget(self.btn_half_v)
        preset_row.addWidget(self.btn_half_h)
        preset_row.addWidget(self.btn_quarter)
        sl.addLayout(preset_row)

        sl.addWidget(QLabel("手动添加:"))
        manual_row = QHBoxLayout()
        self.btn_add_v = QPushButton("+ 竖线")
        self.btn_add_h = QPushButton("+ 横线")
        manual_row.addWidget(self.btn_add_v)
        manual_row.addWidget(self.btn_add_h)
        sl.addLayout(manual_row)

        sl.addWidget(QLabel("提示: 拖拽切割线可微调位置"))
        self.btn_clear_lines = QPushButton("清除切割线")
        sl.addWidget(self.btn_clear_lines)
        split_group.setLayout(sl)
        layout.addWidget(split_group)

        order_group = QGroupBox("排序方式")
        ol = QVBoxLayout()
        ol.setSpacing(4)
        self.check_auto_order = QCheckBox("自动顺序 (从左到右, 从上到下)")
        self.check_auto_order.setChecked(False)
        ol.addWidget(self.check_auto_order)
        self.label_order_hint = QLabel("手动模式: 点击预览图块标记输出顺序")
        self.label_order_hint.setStyleSheet("color: #888;")
        ol.addWidget(self.label_order_hint)
        self.btn_reset_order = QPushButton("重置顺序")
        ol.addWidget(self.btn_reset_order)
        order_group.setLayout(ol)
        layout.addWidget(order_group)

        layout.addStretch()

        self.btn_export_page = QPushButton("导出当前页")
        self.btn_export_page.setMinimumHeight(32)
        layout.addWidget(self.btn_export_page)

        self.btn_export = QPushButton("切分并导出 (全部页)")
        self.btn_export.setMinimumHeight(36)
        self.btn_export.setStyleSheet("QPushButton { font-weight: bold; background-color: #0078D4; color: white; }")
        layout.addWidget(self.btn_export)

        return panel

    def _create_preview_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        self.preview = PreviewWidget()
        layout.addWidget(self.preview)
        return panel

    def _connect_signals(self) -> None:
        self.btn_open.clicked.connect(self._on_open)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_load.clicked.connect(self._on_load)
        self.combo_category.currentTextChanged.connect(self._on_paper_category_changed)
        self.page_list.currentRowChanged.connect(self._on_page_selected)

        self.btn_half_v.clicked.connect(lambda: self._vm.apply_split_preset("half_v"))
        self.btn_half_h.clicked.connect(lambda: self._vm.apply_split_preset("half_h"))
        self.btn_quarter.clicked.connect(lambda: self._vm.apply_split_preset("quarter"))

        self.btn_add_v.clicked.connect(self._vm.add_vertical_line)
        self.btn_add_h.clicked.connect(self._vm.add_horizontal_line)
        self.btn_clear_lines.clicked.connect(self._vm.clear_split_lines)

        self.check_auto_order.toggled.connect(self._on_order_mode_changed)
        self.btn_reset_order.clicked.connect(self._on_reset_order)

        self.btn_export_page.clicked.connect(self._on_export_page)
        self.btn_export.clicked.connect(self._on_export_all)

        self.preview.line_moved_signal.connect(self._vm.move_line)
        self.preview.tile_clicked_signal.connect(self._on_tile_clicked)

        self._vm.document_loaded_signal.connect(self._on_document_loaded)
        self._vm.preview_pixmap_ready_signal.connect(self._on_preview_ready)
        self._vm.split_lines_changed_signal.connect(self.preview.set_split_lines)
        self._vm.order_reset_signal.connect(self.preview.clear_order)
        self._vm.project_saved_signal.connect(lambda p: self.status_bar.showMessage(f"已保存: {p}"))
        self._vm.dirty_changed_signal.connect(self._on_dirty_changed)
        self._vm.error_signal.connect(lambda m: QMessageBox.critical(self, "错误", m))
        self._vm.progress_signal.connect(self.status_bar.showMessage)

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "",
            "PDF/Images (*.pdf *.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )
        if path:
            self._vm.load_document(path)

    def _on_page_selected(self, index: int) -> None:
        if index >= 0:
            self._vm.select_page(index)
            self._vm.render_page_preview(index)

    def _on_document_loaded(self, doc: DocumentDTO) -> None:
        self.page_list.blockSignals(True)
        self.page_list.clear()
        for page in doc.pages:
            orientation = "L" if page.is_landscape else "P"
            self.page_list.addItem(
                f"第 {page.index + 1} 页 ({page.width_pt:.0f}x{page.height_pt:.0f}pt {orientation})"
            )
        self.page_list.setCurrentRow(0)
        self.page_list.blockSignals(False)
        self._populate_paper_list("ISO216")
        self._vm.render_page_preview(0)

    def _on_paper_category_changed(self, category: str) -> None:
        self._populate_paper_list(category)

    def _populate_paper_list(self, category: str) -> None:
        self.combo_paper.clear()
        papers = self._vm.list_papers(category)
        for p in papers:
            self.combo_paper.addItem(p["name"])
        if papers:
            self.combo_paper.setCurrentIndex(0)

    def _on_preview_ready(self, img_data: bytes) -> None:
        pixmap = QPixmap()
        pixmap.loadFromData(img_data, "PNG")
        self.preview.set_page_image(pixmap)
        self._vm.refresh_preview_state()
        page = self._vm.current_page_info
        if page:
            self.label_page_info.setText(
                f"页面 {page.index + 1}: {page.width_pt:.0f} x {page.height_pt:.0f} pt"
            )

    def _on_order_mode_changed(self, checked: bool) -> None:
        if checked:
            self._vm.reset_order()
            self.preview.clear_order()
            self.label_order_hint.setText("已启用自动顺序, 取消勾选后可手动点击图块排序")
            self.label_order_hint.setStyleSheet("color: #d9534f; font-weight: bold;")
        else:
            self.label_order_hint.setText("手动模式: 点击预览图块标记输出顺序")
            self.label_order_hint.setStyleSheet("color: #888;")

    def _on_tile_clicked(self, tile_index: int) -> None:
        if self.check_auto_order.isChecked():
            self.status_bar.showMessage('请先取消勾选"自动顺序"以启用手动排序')
            return
        order = self.preview.get_order_sequence()
        self._vm.set_tile_order(order)
        self.status_bar.showMessage(f"图块顺序: {[i + 1 for i in order]}")

    def _on_reset_order(self) -> None:
        self._vm.reset_order()
        self.preview.clear_order()
        self.status_bar.showMessage("排序已重置为自动")

    def _on_export_page(self) -> None:
        """导出当前页."""
        if self._vm.split_lines.is_empty:
            QMessageBox.warning(self, "提示", "请先放置切割线")
            return
        if self._vm.has_incomplete_order():
            reply = QMessageBox.question(
                self, "确认",
                "仍有未选择顺序的图块，\n未选择的图块将被舍弃，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        default_name = Path(self._vm.document.filename).stem + "_split.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出当前页", default_name,
            "PDF Files (*.pdf);;All Files (*)"
        )
        if not path:
            return

        paper_name = self.combo_paper.currentText()
        paper_category = self.combo_category.currentText()
        self._vm.export(path, paper_name, paper_category)

    def _on_export_all(self) -> None:
        """导出全部页 (使用各页缓存的分割线配置)."""
        QMessageBox.information(self, "提示", "全部页批量导出功能将在后续版本中实现")

    def _on_save(self) -> None:
        if self._vm.document is None:
            QMessageBox.warning(self, "提示", "请先打开文件")
            return
        default_name = Path(self._vm.document.filename).stem + ".ppslc"
        path, _ = QFileDialog.getSaveFileName(
            self, "保存项目", default_name,
            "PaperSlice Project (*.ppslc);;All Files (*)"
        )
        if path:
            self._vm.save_project(path)

    def _on_load(self) -> None:
        if self._vm.is_dirty:
            reply = QMessageBox.question(
                self, "未保存的更改",
                "当前项目有未保存的修改，是否继续加载？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        path, _ = QFileDialog.getOpenFileName(
            self, "加载存档", "",
            "PaperSlice Project (*.ppslc);;All Files (*)"
        )
        if path:
            self._vm.load_project(path)

    def _on_dirty_changed(self, dirty: bool) -> None:
        title = "PDF Poster Splitter"
        if self._vm.project_path:
            title += f" - {self._vm.project_path.name}"
        if dirty:
            title += " *"
        self.setWindowTitle(title)

    def _maybe_save(self) -> bool:
        if not self._vm.is_dirty:
            return True
        reply = QMessageBox.question(
            self, "保存更改",
            "是否保存当前项目的修改？",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Save:
            self._on_save()
            return not self._vm.is_dirty
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False

    def closeEvent(self, event) -> None:
        if self._maybe_save():
            event.accept()
        else:
            event.ignore()
