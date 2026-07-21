"""Main Window - 主窗口视图 (交互式预览 + 切割线)."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pdfsplitter.application.dto import DocumentDTO, PageFilterDTO, PageListStateDTO
from pdfsplitter.presentation.main_viewmodel import MainViewModel
from pdfsplitter.presentation.page_filter_dialog import PageFilterDialog
from pdfsplitter.presentation.preview_widget import PreviewWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """PDF Poster Splitter 主窗口.

    布局: 左侧面板(文件+页面列表) | 预览 | 右侧面板(纸张+切割线+导出)
    """

    def __init__(self, viewmodel: MainViewModel) -> None:
        super().__init__()
        self._vm = viewmodel
        self._list_rebuilding: bool = False
        self._setup_ui()
        self._connect_signals()
        self.setWindowTitle("PDF Poster Splitter")
        self.resize(1400, 800)

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_left_panel())
        splitter.addWidget(self._create_preview_panel())
        splitter.addWidget(self._create_right_panel())
        splitter.setSizes([200, 920, 280])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 请打开 PDF 文件")

        github_label = QLabel('<a href="https://github.com/Eason3Blue/PaperSlice" style="color: #888;">项目主页</a>')
        github_label.setOpenExternalLinks(True)
        self.status_bar.addPermanentWidget(github_label)

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

        header_row = QHBoxLayout()
        header_row.setSpacing(4)
        self.check_select_all = QCheckBox("全选")
        self.check_select_all.setTristate(True)
        self.check_select_all.setChecked(True)
        header_row.addWidget(self.check_select_all)
        self.combo_view_mode = QComboBox()
        self.combo_view_mode.addItems(["全部页面", "筛选结果"])
        self.combo_view_mode.setFixedWidth(80)
        header_row.addWidget(self.combo_view_mode)
        header_row.addStretch()
        fl.addLayout(header_row)

        self.page_list = QListWidget()
        fl.addWidget(self.page_list)

        filter_row = QHBoxLayout()
        self.btn_filter = QPushButton("筛选")
        self.btn_filter.setToolTip("按页码/尺寸/方向筛选页面")
        filter_row.addWidget(self.btn_filter)
        self.btn_clear_filter = QPushButton("清除")
        self.btn_clear_filter.setVisible(False)
        self.btn_clear_filter.setToolTip("清除筛选条件")
        filter_row.addWidget(self.btn_clear_filter)
        filter_row.addStretch()
        fl.addLayout(filter_row)

        self.label_page_info = QLabel("未选择页面")
        fl.addWidget(self.label_page_info)
        self.label_filter_status = QLabel("")
        self.label_filter_status.setStyleSheet("color: #0078D4; font-size: 11px;")
        fl.addWidget(self.label_filter_status)

        file_group.setLayout(fl)
        layout.addWidget(file_group)

        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

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

        preset_label_row = QHBoxLayout()
        preset_label_row.addWidget(QLabel("自动预设:"))
        self.check_preset_all = QCheckBox("应用到已选择页")
        self.check_preset_all.setChecked(True)
        preset_label_row.addWidget(self.check_preset_all)
        preset_label_row.addStretch()
        sl.addLayout(preset_label_row)

        preset_row = QHBoxLayout()
        self.btn_half_v = QPushButton("垂直二分")
        self.btn_half_h = QPushButton("水平二分")
        self.btn_quarter = QPushButton("四等分")
        preset_row.addWidget(self.btn_half_v)
        preset_row.addWidget(self.btn_half_h)
        preset_row.addWidget(self.btn_quarter)
        sl.addLayout(preset_row)

        manual_label_row = QHBoxLayout()
        manual_label_row.addWidget(QLabel("手动添加:"))
        self.check_manual_all = QCheckBox("应用到已选择页")
        self.check_manual_all.setChecked(False)
        manual_label_row.addWidget(self.check_manual_all)
        manual_label_row.addStretch()
        sl.addLayout(manual_label_row)

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
        self.btn_export.setStyleSheet(
            "QPushButton { font-weight: bold; background-color: #0078D4; color: white; }"
        )
        layout.addWidget(self.btn_export)

        return panel

    def _create_preview_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        self.preview = PreviewWidget()
        layout.addWidget(self.preview)

        zoom_bar = QHBoxLayout()
        zoom_bar.setContentsMargins(4, 2, 4, 4)

        self.label_zoom = QLabel("100%")
        self.label_zoom.setFixedWidth(46)
        self.label_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_zoom.setStyleSheet("color: #aaa; font-size: 11px;")

        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setFixedSize(28, 24)
        self.btn_zoom_out.setToolTip("缩小 (Ctrl+滚轮)")
        self.btn_zoom_out.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; }")

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedSize(28, 24)
        self.btn_zoom_in.setToolTip("放大 (Ctrl+滚轮)")
        self.btn_zoom_in.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; }")

        self.btn_zoom_fit = QPushButton("适应")
        self.btn_zoom_fit.setFixedHeight(24)
        self.btn_zoom_fit.setToolTip("适应窗口")

        self.combo_dpi = QComboBox()
        self.combo_dpi.setFixedWidth(110)
        self.combo_dpi.setToolTip("预览渲染质量")
        self.combo_dpi.addItems(["快速(100dpi)", "标准(150dpi)", "高清(300dpi)", "自定义"])

        self.input_custom_dpi = QLineEdit()
        self.input_custom_dpi.setFixedWidth(70)
        self.input_custom_dpi.setPlaceholderText("50-600")
        self.input_custom_dpi.setValidator(QIntValidator(50, 600))
        self.input_custom_dpi.setVisible(False)

        zoom_bar.addStretch()
        zoom_bar.addWidget(self.label_zoom)
        zoom_bar.addWidget(self.btn_zoom_out)
        zoom_bar.addWidget(self.btn_zoom_in)
        zoom_bar.addWidget(self.btn_zoom_fit)
        zoom_bar.addWidget(self.combo_dpi)
        zoom_bar.addWidget(self.input_custom_dpi)
        zoom_bar.addStretch()
        layout.addLayout(zoom_bar)

        return panel

    def _connect_signals(self) -> None:
        self.btn_open.clicked.connect(self._on_open)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_load.clicked.connect(self._on_load)
        self.combo_category.currentTextChanged.connect(self._on_paper_category_changed)
        self.page_list.currentRowChanged.connect(self._on_page_selected)
        self.page_list.itemChanged.connect(self._on_item_check_changed)

        self.check_select_all.clicked.connect(self._on_select_all_clicked)
        self.combo_view_mode.currentTextChanged.connect(self._on_view_mode_changed)

        self.btn_half_v.clicked.connect(lambda: self._vm.apply_split_preset("half_v", self.check_preset_all.isChecked()))
        self.btn_half_h.clicked.connect(lambda: self._vm.apply_split_preset("half_h", self.check_preset_all.isChecked()))
        self.btn_quarter.clicked.connect(lambda: self._vm.apply_split_preset("quarter", self.check_preset_all.isChecked()))

        self.btn_add_v.clicked.connect(lambda: self._vm.add_vertical_line(self.check_manual_all.isChecked()))
        self.btn_add_h.clicked.connect(lambda: self._vm.add_horizontal_line(self.check_manual_all.isChecked()))
        self.btn_clear_lines.clicked.connect(lambda: self._vm.clear_split_lines(self.check_manual_all.isChecked()))

        self.btn_filter.clicked.connect(self._on_open_filter)
        self.btn_clear_filter.clicked.connect(self._on_clear_filter)

        self.check_auto_order.toggled.connect(self._on_order_mode_changed)
        self.btn_reset_order.clicked.connect(self._on_reset_order)

        self.btn_export_page.clicked.connect(self._on_export_page)
        self.btn_export.clicked.connect(self._on_export_all)

        self.preview.line_moved_signal.connect(self._vm.move_line)
        self.preview.tile_clicked_signal.connect(self._on_tile_clicked)
        self.preview.file_dropped_signal.connect(self._on_file_dropped)
        self.preview.zoom_changed_signal.connect(self._on_zoom_changed)

        self.btn_zoom_in.clicked.connect(self.preview.zoom_in)
        self.btn_zoom_out.clicked.connect(self.preview.zoom_out)
        self.btn_zoom_fit.clicked.connect(self.preview.zoom_fit)

        self.combo_dpi.currentIndexChanged.connect(self._on_dpi_changed)
        self.input_custom_dpi.returnPressed.connect(self._on_custom_dpi_entered)
        self.input_custom_dpi.editingFinished.connect(self._on_custom_dpi_entered)

        self._vm.document_loaded_signal.connect(self._on_document_loaded)
        self._vm.preview_pixmap_ready_signal.connect(self._on_preview_ready)
        self._vm.split_lines_changed_signal.connect(self.preview.set_split_lines)
        self._vm.order_reset_signal.connect(self.preview.clear_order)
        self._vm.project_saved_signal.connect(lambda p: self.status_bar.showMessage(f"已保存: {p}"))
        self._vm.dirty_changed_signal.connect(self._on_dirty_changed)
        self._vm.error_signal.connect(lambda m: QMessageBox.critical(self, "错误", m))
        self._vm.progress_signal.connect(self.status_bar.showMessage)
        self._vm.page_filter_changed_signal.connect(self._on_filter_changed)
        self._vm.page_list_state_changed_signal.connect(self._on_page_list_state_changed)

    def _on_open(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "打开文件", "",
            "PDF/Images (*.pdf *.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )
        if paths:
            if len(paths) == 1:
                self._vm.load_document(paths[0])
            else:
                self._vm.load_documents(paths)

    def _on_file_dropped(self, path: str) -> None:
        self._vm.load_document(path)

    def _on_page_selected(self, index: int) -> None:
        if self._list_rebuilding:
            return
        if index >= 0:
            self._vm.select_page(index)
            self._vm.render_page_preview(index)

    def _on_item_check_changed(self, item: QListWidgetItem) -> None:
        if self._list_rebuilding:
            return
        page_index = item.data(Qt.ItemDataRole.UserRole)
        if page_index is not None:
            self._vm.toggle_page_selection(int(page_index))

    def _on_select_all_clicked(self, checked: bool) -> None:
        if self._list_rebuilding:
            return
        if checked:
            self._vm.select_all_visible()
        else:
            self._vm.deselect_all()

    def _on_view_mode_changed(self, text: str) -> None:
        if self._list_rebuilding:
            return
        mode = "filtered" if text == "筛选结果" else "all"
        self._vm.set_view_mode(mode)

    def _on_document_loaded(self, doc: DocumentDTO) -> None:
        self._list_rebuilding = True
        self.page_list.blockSignals(True)
        self.page_list.clear()
        for page in doc.pages:
            orientation = "L" if page.is_landscape else "P"
            item = QListWidgetItem(
                f"第 {page.index + 1} 页 ({page.width_pt:.0f}x{page.height_pt:.0f}pt {orientation})"
            )
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, page.index)
            self.page_list.addItem(item)
        self.page_list.setCurrentRow(0)
        self.page_list.blockSignals(False)
        self._list_rebuilding = False
        self.check_select_all.setCheckState(Qt.CheckState.Checked)
        self.combo_view_mode.setCurrentIndex(0)
        self._init_dpi_combo()
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
        pixmap.loadFromData(img_data)
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

    def _on_zoom_changed(self, level: float) -> None:
        self.label_zoom.setText(f"{int(level * 100)}%")

    def _init_dpi_combo(self) -> None:
        """根据当前配置设置 DPI 下拉框."""
        dpi = self._vm.get_render_dpi()
        self.combo_dpi.blockSignals(True)
        if dpi == 100:
            self.combo_dpi.setCurrentIndex(0)
        elif dpi == 150:
            self.combo_dpi.setCurrentIndex(1)
        elif dpi == 300:
            self.combo_dpi.setCurrentIndex(2)
        else:
            self.combo_dpi.setCurrentIndex(3)
            self.input_custom_dpi.setText(str(dpi))
            self.input_custom_dpi.setVisible(True)
        self.combo_dpi.blockSignals(False)

    def _on_dpi_changed(self, index: int) -> None:
        self.input_custom_dpi.clear()
        if index == 0:
            self.input_custom_dpi.setVisible(False)
            self._vm.set_render_dpi(100)
        elif index == 1:
            self.input_custom_dpi.setVisible(False)
            self._vm.set_render_dpi(150)
        elif index == 2:
            self.input_custom_dpi.setVisible(False)
            self._vm.set_render_dpi(300)
        else:
            self.input_custom_dpi.setVisible(True)
            self.input_custom_dpi.setFocus()

    def _on_custom_dpi_entered(self) -> None:
        text = self.input_custom_dpi.text().strip()
        if not text:
            return
        try:
            dpi = int(text)
        except ValueError:
            return
        dpi = max(50, min(dpi, 600))
        self.input_custom_dpi.setText(str(dpi))
        self._vm.set_render_dpi(dpi)

    def _on_open_filter(self) -> None:
        if self._vm.document is None:
            QMessageBox.warning(self, "提示", "请先加载文档")
            return

        pages = self._vm.document.pages
        dialog = PageFilterDialog(self._vm.page_filter, pages, self)
        if dialog.exec() == PageFilterDialog.DialogCode.Accepted:
            new_filter = dialog.result()
            self._vm.set_page_filter(new_filter)

    def _on_clear_filter(self) -> None:
        self._vm.clear_page_filter()

    def _on_filter_changed(self, dto: PageFilterDTO) -> None:
        self.btn_clear_filter.setVisible(dto.is_active)

    def _on_page_list_state_changed(self, state: PageListStateDTO) -> None:
        self._list_rebuilding = True

        self.page_list.blockSignals(True)

        if state.filter_active and state.view_mode == "filtered":
            filtered_set = set(state.filtered_indices)
        else:
            filtered_set = set(range(state.total_pages))

        selected_set = set(state.selected_indices)

        for row in range(self.page_list.count()):
            item = self.page_list.item(row)
            page_index = item.data(Qt.ItemDataRole.UserRole)
            if page_index is None:
                continue
            idx = int(page_index)

            visible = idx in filtered_set
            self.page_list.setRowHidden(row, not visible)

            if idx in selected_set:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

        self.page_list.blockSignals(False)

        if state.is_all_selected:
            self.check_select_all.setCheckState(Qt.CheckState.Checked)
        elif state.is_partially_selected:
            self.check_select_all.setCheckState(Qt.CheckState.PartiallyChecked)
        else:
            self.check_select_all.setCheckState(Qt.CheckState.Unchecked)

        self.combo_view_mode.blockSignals(True)
        self.combo_view_mode.setCurrentIndex(0 if state.view_mode == "all" else 1)
        self.combo_view_mode.blockSignals(False)

        if state.filter_active:
            filtered_count = state.visible_count
            self.label_filter_status.setText(
                f"显示 {filtered_count}/{state.total_pages} 页 (已筛选 {state.total_pages - filtered_count} 页)"
            )
            self.btn_clear_filter.setVisible(True)
        else:
            self.label_filter_status.setText("")
            self.btn_clear_filter.setVisible(False)

        self._list_rebuilding = False

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
        """导出全部已配置页面."""
        if self._vm.document is None:
            QMessageBox.warning(self, "提示", "请先加载文档")
            return

        default_name = Path(self._vm.document.filename).stem + "_all_split.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出全部页面", default_name,
            "PDF Files (*.pdf);;All Files (*)"
        )
        if not path:
            return

        paper_name = self.combo_paper.currentText()
        paper_category = self.combo_category.currentText()
        self._vm.export_all(path, paper_name, paper_category)

    def _on_save(self) -> None:
        if self._vm.document is None:
            QMessageBox.warning(self, "提示", "请先打开文件")
            return
        default_name = self._vm.default_project_name() + ".ppslc"
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

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._maybe_save():
            event.accept()
        else:
            event.ignore()
