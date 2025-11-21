
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem
from configparser import ConfigParser
from undoredo import undoContext

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from imageview import ImageView

# Use a scaled pixmap for marker graphics
class Marker(QGraphicsPixmapItem):
    pixmaps_initialized: bool = False
    unselected_pixmap:     QtGui.QPixmap
    selected_pixmap:       QtGui.QPixmap
    prehighlighted_pixmap: QtGui.QPixmap
    r = 0
    offset = 0
    next_marker_id = 0
    
    def _drawPixmap(self, size: int, r: int, color: QtGui.QColor, outline_color: QtGui.QColor) -> QtGui.QPixmap:
        center = size // 2
        pxmap = QtGui.QPixmap(size,size)
        pxmap.fill(QtGui.QColorConstants.Transparent)
        painter = QtGui.QPainter(pxmap)

        pen = QtGui.QPen(outline_color)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawEllipse(QtCore.QRectF(center-r+0.5,center-r+0.5,2*r,2*r))
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(QtCore.QPointF(center-r+0.5,center+0.5),QtCore.QPointF(size-(center-r)+0.5,center+0.5))
        painter.drawLine(QtCore.QPointF(center+0.5,center-r+0.5),QtCore.QPointF(center+0.5,size-(center-r)+0.5))

        pen = QtGui.QPen(color)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(QtCore.QRectF(center-r+0.5,center-r+0.5,2*r,2*r))
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(QtCore.QPointF(center-r+0.5,center+0.5),QtCore.QPointF(size-(center-r)+0.5,center+0.5))
        painter.drawLine(QtCore.QPointF(center+0.5,center-r+0.5),QtCore.QPointF(center+0.5,size-(center-r)+0.5))

        return pxmap

    def _initPixmaps(self) -> None:
        config = ConfigParser()
        config.read('config.ini')
        size = config.getint('Marker', 'pixmap_size', fallback=64)
        r    = config.getint('Marker', 'radius', fallback=20)    
        unselected_color       = QtGui.QColor(config.get('Marker', 'color_default', fallback='#FFFFFF'))
        selected_color         = QtGui.QColor(config.get('Marker', 'color_selected', fallback='#FFFF00'))
        prehighlighted_color   = QtGui.QColor(config.get('Marker', 'color_prehighlighted', fallback='#0000FF'))
        Marker.unselected_pixmap     = self._drawPixmap(size,r,unselected_color,     QtGui.QColor("#000000"))
        Marker.selected_pixmap       = self._drawPixmap(size,r,selected_color,       QtGui.QColor("#000000"))
        Marker.prehighlighted_pixmap = self._drawPixmap(size,r,prehighlighted_color, QtGui.QColor("#000000"))    # unused
        Marker.unselected_pixmap.save("unselected_pixmap.png", "PNG")
        Marker.selected_pixmap.save("selected_pixmap.png", "PNG")
        Marker.prehighlighted_pixmap.save("prehighlighted_pixmap.png", "PNG")
        Marker.offset = size // 2
        Marker.r = r
        Marker.pixmaps_initialized = True

    def __init__(self, view: ImageView, pos: QtCore.QPointF, mid:int | None = None) -> None:
        super().__init__()
        # Set the id if not given
        if mid is None:
            self.mid = Marker.next_marker_id
            Marker.next_marker_id += 1
        else:
            self.mid = mid
        if not Marker.pixmaps_initialized:
           self._initPixmaps()
        self.setPos(pos)
        self.setOffset(-Marker.offset,-Marker.offset)
        #self.rect = QtCore.QRect(-(Marker.offset),-(Marker.offset),Marker.offset,Marker.offset)
        #self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setPixmap(Marker.unselected_pixmap)
        self.view = view

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        # if selection state changed, swap the pixmap
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if value:
                self.setPixmap(Marker.selected_pixmap)
            else:
                self.setPixmap(Marker.unselected_pixmap)
        return super().itemChange(change, value)
    
    def shape(self) -> QtGui.QPainterPath:
        # Outline for precise picking
        path = QtGui.QPainterPath()
        path.addEllipse(-Marker.r,-Marker.r,2*Marker.r,2*Marker.r)
        return path

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        # Save pos to detect an interactive move
        self.mouse_pressed_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        # If we are being moved, the whole selection is being moved - notify the view
        if self.pos() != self.mouse_pressed_pos:
            self.view.setSelectionDeltaPos(self.pos() - self.mouse_pressed_pos)
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        context_menu = QtWidgets.QMenu()
        if self in self.scene().selectedItems():
            action1 = QtGui.QAction("Delete Selection")
            action1.triggered.connect(self.view.deleteSelection)
            context_menu.addAction(action1)
            if len(self.scene().selectedItems()) > 1:
                action2 = QtGui.QAction("Create Constraint")
                action2.triggered.connect(self.view.createConstraint)
                context_menu.addAction(action2)
        else:
            action = QtGui.QAction("Delete Marker")
            action.triggered.connect(self.deleteYourself)
            context_menu.addAction(action)
        context_menu.exec(event.screenPos())

    # Atomic Action
    def deleteYourself(self) -> None:
        with undoContext("Delete Marker") as uctx:
            self.view.deleteMarker(uctx, self.mid)
        self.view.statusbar.showMessage("Delete Marker")
