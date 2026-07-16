"""PreviewWidget - 页面预览，支持拖拽切割线和点击标记图块顺序."""

from __future__ import annotations

import logging
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
    """图块覆盖层，用于高亮和点击排序."""

    def __init__(self, rect: QRectF, tile_index: int, row: int, col: int,
                 parent=None) -> None:
        super().__init__(rect, parent)
        self.tile_index = tile_index
        self.row = row
        self.col = col
        self._order_number: int | None = None
        self._label: QGraphicsTextItem | None = None
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QBrush(TILE_FILL))
        self.setZValue(5)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def set_order(self, number: int | None) -> None:
        self._order_number = number
        if self._label:
            self.scene().removeItem(self._label)
            self._label = None
        if number is not None:
            self.setBrush(QBrush(TILE_ORDERED_FILL))
            cx = self.rect().center().x()
            cy = self.rect().center().y()
            self._label = QGraphicsTextItem(str(number + 1))
            self._label.setDefaultTextColor(TEXT_COLOR)
            font = QFont()
            font.setBold(True)
            font.setPointSize(16)
            self._label.setFont(font)
            self._label.setPos(cx - 10, cy - 14)
            self._label.setZValue(15)
            self.scene().addItem(self._label)
            bg = QGraphicsRectItem(cx - 14, cy - 16, 28, 28, self._label)
            bg.setBrush(QBrush(TEXT_BG))
            bg.setPen(QPen(Qt.PenStyle.NoPen))
            bg.setZValue(14)
        else:
            self.setBrush(QBrush(TILE_FILL))

    @property
    def order_number(self) -> int | None:
        return self._order_number


class PreviewWidget(QGraphicsView):
    """页面预览组件.

    支持:
    - 渲染页面截图
    - 显示可拖拽的切割线
    - 点击图块指定输出顺序
    """

    line_moved_signal = Signal(str, int, float)
    tile_clicked_signal = Signal(int)

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
        self.setStyleSheet("background-color: #2d2d2d; border: none;")

        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._vertical_lines: list[_DraggableLine] = []
        self._horizontal_lines: list[_DraggableLine] = []
        self._tile_overlays: list[_TileOverlay] = []
        self._order_sequence: list[int] = []

        self.setMouseTracking(True)

    def set_page_image(self, pixmap: QPixmap) -> None:
        """设置页面预览图."""
        self._scene.clear()
        self._vertical_lines.clear()
        self._horizontal_lines.clear()
        self._tile_overlays.clear()
        self._order_sequence.clear()
        self._pixmap_item = QGraphicsPixmapItem(pixmap)
        self._pixmap_item.setZValue(0)
        self._scene.addItem(self._pixmap_item)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_split_lines(self, verticals: list[float], horizontals: list[float],
                        page_w: float, page_h: float) -> None:
        """设置切割线位置.

        Args:
            verticals: 垂直线 X 坐标列表.
            horizontals: 水平线 Y 坐标列表.
            page_w: 页面宽度.
            page_h: 页面高度.
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
        self._order_sequence.clear()

        for i, x in enumerate(verticals):
            line = _DraggableLine(x, 0, x, page_h, "v", i)
            self._scene.addItem(line)
            self._vertical_lines.append(line)

        for i, y in enumerate(horizontals):
            line = _DraggableLine(0, y, page_w, y, "h", i)
            self._scene.addItem(line)
            self._horizontal_lines.append(line)

        self._rebuild_tile_overlays(verticals, horizontals, page_w, page_h)

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
                if line.orientation == "v":
                    pos = scene_pos.x()
                else:
                    pos = scene_pos.y()
                pos = max(0.0, min(pos,
                    self._scene.sceneRect().height() if line.orientation == "h"
                    else self._scene.sceneRect().width()))
                self.line_moved_signal.emit(line.orientation, line.line_index, pos)
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
