"""PreviewWidget - 页面预览，支持拖拽切割线和点击标记图块顺序."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QGraphicsLineItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QRubberBand,
)

logger = logging.getLogger(__name__)

_READY_PNG = Path(__file__).resolve().parent.parent.parent / "resources" / "images" / "ready.png"
_DROP_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff")

LINE_COLOR = QColor(0, 120, 212)
LINE_HOVER_COLOR = QColor(200, 50, 50)
TILE_FILL = QColor(0, 120, 212, 60)
TILE_ORDERED_FILL = QColor(50, 180, 50, 80)
TEXT_COLOR = QColor(255, 255, 255)
TEXT_BG = QColor(0, 0, 0, 180)


class _DraggableLine(QGraphicsLineItem):
    """可拖拽的切割线."""

    HIT_TOLERANCE = 8.0

    def __init__(self, x1: float, y1: float, x2: float, y2: float,
                 orientation: str, line_index: int,
                 parent=None) -> None:
        super().__init__(x1, y1, x2, y2, parent)
        self._orientation = orientation
        self._line_index = line_index
        self._dragging = False
        self._color = LINE_COLOR
        self._update_pen()
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.SplitHCursor if orientation == "v" else Qt.CursorShape.SplitVCursor)
        self.setZValue(10)

    @property
    def orientation(self) -> str:
        return self._orientation

    @property
    def line_index(self) -> int:
        return self._line_index

    def set_line_index(self, idx: int) -> None:
        self._line_index = idx

    def _update_pen(self) -> None:
        pen = QPen(self._color, 2.0)
        pen.setCosmetic(True)
        self.setPen(pen)

    def hoverEnterEvent(self, event) -> None:
        self._color = LINE_HOVER_COLOR
        self._update_pen()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._color = LINE_COLOR
        self._update_pen()
        super().hoverLeaveEvent(event)

    def shape(self):
        from PySide6.QtGui import QPainterPathStroker, QPainterPath
        path = super().shape()
        stroker = QPainterPathStroker()
        stroker.setWidth(self.HIT_TOLERANCE * 2)
        return stroker.createStroke(path)


class _TileOverlay(QGraphicsRectItem):
    """图块覆盖层，用于高亮和点击排序.

    序号通过 paint 直接绘制在 rect 内，不创建独立 scene item.
    """

    def __init__(self, rect: QRectF, tile_index: int, row: int, col: int,
                 parent=None) -> None:
        super().__init__(rect, parent)
        self.tile_index = tile_index
        self.row = row
        self.col = col
        self._order_number: int | None = None
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QBrush(TILE_FILL))
        self.setZValue(5)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def set_order(self, number: int | None) -> None:
        self._order_number = number
        if number is not None:
            self.setBrush(QBrush(TILE_ORDERED_FILL))
        else:
            self.setBrush(QBrush(TILE_FILL))
        self.update()

    @property
    def order_number(self) -> int | None:
        return self._order_number

    def paint(self, painter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        if self._order_number is not None:
            r = self.rect()
            if r.width() < 30 or r.height() < 30:
                return
            text = str(self._order_number + 1)
            font = QFont()
            font.setBold(True)
            font.setPointSize(14)
            painter.setFont(font)

            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(text)
            text_h = fm.height()
            cx = r.center().x()
            cy = r.center().y()

            bg_rect = QRectF(cx - text_w / 2 - 8, cy - text_h / 2 - 4,
                             text_w + 16, text_h + 8)
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.setBrush(QBrush(TEXT_BG))
            painter.drawRoundedRect(bg_rect, 4, 4)

            painter.setPen(QPen(TEXT_COLOR))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, text)

    @property
    def order_number(self) -> int | None:
        return self._order_number


class PreviewWidget(QGraphicsView):
    """页面预览组件.

    支持:
    - 渲染页面截图
    - 显示可拖拽的切割线
    - 点击图块指定输出顺序
    - 拖拽 PDF 文件直接打开
    - 未加载文档时显示占位图
    """

    line_moved_signal = Signal(str, int, float)
    tile_clicked_signal = Signal(int)
    file_dropped_signal = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(self.renderHints())
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("background-color: #181a1f; border: none;")

        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._vertical_lines: list[_DraggableLine] = []
        self._horizontal_lines: list[_DraggableLine] = []
        self._tile_overlays: list[_TileOverlay] = []
        self._order_sequence: list[int] = []

        self._ready_pixmap: QPixmap | None = None
        self._ready_item: QGraphicsPixmapItem | None = None

        self.setMouseTracking(True)
        self.setAcceptDrops(True)

        self._load_placeholder()

    def _load_placeholder(self) -> None:
        if _READY_PNG.exists():
            self._ready_pixmap = QPixmap(str(_READY_PNG))
            self._ready_item = QGraphicsPixmapItem(self._ready_pixmap)
            self._ready_item.setZValue(0)
            self._scene.addItem(self._ready_item)
            self._scene.setSceneRect(QRectF(self._ready_pixmap.rect()))
            self._center_placeholder()
        else:
            logger.warning("Placeholder image not found: %s", _READY_PNG)

    def _center_placeholder(self) -> None:
        if self._ready_item is None:
            return
        scene_rect = self._ready_pixmap.rect()
        self._scene.setSceneRect(QRectF(scene_rect))
        self.fitInView(QRectF(scene_rect), Qt.AspectRatioMode.KeepAspectRatio)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(_DROP_EXTENSIONS):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(_DROP_EXTENSIONS):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(_DROP_EXTENSIONS):
                    self.file_dropped_signal.emit(path)
                    return
        event.ignore()

    def set_page_image(self, pixmap: QPixmap) -> None:
        """设置页面预览图."""
        self._scene.clear()
        self._vertical_lines.clear()
        self._horizontal_lines.clear()
        self._tile_overlays.clear()
        self._order_sequence.clear()
        self._ready_item = None
        self._ready_pixmap = None
        self._pixmap_item = QGraphicsPixmapItem(pixmap)
        self._pixmap_item.setZValue(0)
        self._scene.addItem(self._pixmap_item)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self._image_size = (pixmap.width(), pixmap.height())
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_split_lines(self, verticals: list[float], horizontals: list[float],
                        page_w: float, page_h: float,
                        order_indices: list[int] | None = None) -> None:
        """设置切割线位置与排序 (PDF 点坐标，内部自动缩放至场景坐标).

        Args:
            verticals: 垂直线 X 坐标列表 (PDF 点).
            horizontals: 水平线 Y 坐标列表 (PDF 点).
            page_w: 页面宽度 (PDF 点).
            page_h: 页面高度 (PDF 点).
            order_indices: 排序索引列表, None 或空列表表示自动/无排序.
        """
        for vl in self._vertical_lines:
            self._scene.removeItem(vl)
        for hl in self._horizontal_lines:
            self._scene.removeItem(hl)
        for to in self._tile_overlays:
            self._scene.removeItem(to)
        self._vertical_lines.clear()
        self._horizontal_lines.clear()
        self._tile_overlays.clear()

        saved_order_from_param = order_indices if order_indices else None
        self._order_sequence.clear()

        scene_w = self._scene.sceneRect().width()
        scene_h = self._scene.sceneRect().height()
        if scene_w <= 0 or scene_h <= 0:
            return
        self._page_w = page_w
        self._page_h = page_h
        sx = scene_w / page_w if page_w > 0 else 1.0
        sy = scene_h / page_h if page_h > 0 else 1.0

        scaled_verts = [x * sx for x in sorted(verticals)]
        scaled_horiz = [y * sy for y in sorted(horizontals)]

        for i, x in enumerate(scaled_verts):
            line = _DraggableLine(x, 0, x, scene_h, "v", i)
            self._scene.addItem(line)
            self._vertical_lines.append(line)

        for i, y in enumerate(scaled_horiz):
            line = _DraggableLine(0, y, scene_w, y, "h", i)
            self._scene.addItem(line)
            self._horizontal_lines.append(line)

        self._rebuild_tile_overlays(scaled_verts, scaled_horiz, scene_w, scene_h)

        if saved_order_from_param:
            self._order_sequence = list(saved_order_from_param)
            for order_num, tile_idx in enumerate(saved_order_from_param):
                if tile_idx < len(self._tile_overlays):
                    self._tile_overlays[tile_idx].set_order(order_num)
            self._scene.update()
            self.viewport().update()

    def _rebuild_tile_overlays(self, verticals: list[float], horizontals: list[float],
                                page_w: float, page_h: float) -> None:
        x_bounds = [0.0, *sorted(verticals), page_w]
        y_bounds = [0.0, *sorted(horizontals), page_h]
        idx = 0
        for row in range(len(y_bounds) - 1):
            for col in range(len(x_bounds) - 1):
                rect = QRectF(x_bounds[col], y_bounds[row],
                              x_bounds[col + 1] - x_bounds[col],
                              y_bounds[row + 1] - y_bounds[row])
                overlay = _TileOverlay(rect, idx, row, col)
                self._scene.addItem(overlay)
                self._tile_overlays.append(overlay)
                idx += 1

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            item = self._scene.itemAt(scene_pos, self.transform())
            if isinstance(item, _TileOverlay):
                if item.tile_index not in self._order_sequence:
                    self._order_sequence.append(item.tile_index)
                    item.set_order(len(self._order_sequence) - 1)
                    self.tile_clicked_signal.emit(item.tile_index)
                return
            if isinstance(item, _DraggableLine):
                item._dragging = True
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        for line in self._vertical_lines + self._horizontal_lines:
            if line._dragging:
                scene_pos = self.mapToScene(event.pos())
                x = scene_pos.x()
                y = scene_pos.y()
                if line.orientation == "v":
                    line.setLine(x, 0, x, self._scene.sceneRect().height())
                else:
                    line.setLine(0, y, self._scene.sceneRect().width(), y)
                self._update_tile_overlays()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        for line in self._vertical_lines + self._horizontal_lines:
            if line._dragging:
                line._dragging = False
                scene_pos = self.mapToScene(event.pos())
                scene_w = self._scene.sceneRect().width()
                scene_h = self._scene.sceneRect().height()
                pw = getattr(self, "_page_w", scene_w)
                ph = getattr(self, "_page_h", scene_h)
                sx_inv = pw / scene_w if scene_w > 0 else 1.0
                sy_inv = ph / scene_h if scene_h > 0 else 1.0
                if line.orientation == "v":
                    pos = scene_pos.x()
                    pos = max(0.0, min(pos, scene_w))
                    pdf_pos = pos * sx_inv
                else:
                    pos = scene_pos.y()
                    pos = max(0.0, min(pos, scene_h))
                    pdf_pos = pos * sy_inv
                self.line_moved_signal.emit(line.orientation, line.line_index, pdf_pos)
                return
        super().mouseReleaseEvent(event)

    def _update_tile_overlays(self) -> None:
        verts = sorted([line.line().x1() for line in self._vertical_lines])
        horiz = sorted([line.line().y1() for line in self._horizontal_lines])
        scene_rect = self._scene.sceneRect()
        x_bounds = [0.0, *verts, scene_rect.width()]
        y_bounds = [0.0, *horiz, scene_rect.height()]
        for overlay in self._tile_overlays:
            x0 = x_bounds[overlay.col]
            x1 = x_bounds[overlay.col + 1]
            y0 = y_bounds[overlay.row]
            y1 = y_bounds[overlay.row + 1]
            overlay.setRect(QRectF(x0, y0, x1 - x0, y1 - y0))

    def clear_order(self) -> None:
        """清除点击排序."""
        self._order_sequence.clear()
        for overlay in self._tile_overlays:
            overlay.set_order(None)

    def get_order_sequence(self) -> list[int]:
        """获取当前排序序列."""
        if not self._order_sequence:
            return list(range(len(self._tile_overlays)))
        return list(self._order_sequence)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._pixmap_item:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        elif self._ready_item:
            self._center_placeholder()
