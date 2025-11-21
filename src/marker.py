
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem
from configparser import ConfigParser
from undoredo import undoContext
from pathlib import Path

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from imageview import ImageView

# Use a scaled pixmap for marker graphics
class Marker(QGraphicsPixmapItem):
    pixmaps_initialized: bool = False
    unselected_pixmap:     QtGui.QPixmap
    selected_pixmap:       QtGui.QPixmap
    prehighlighted_pixmap: QtGui.QPixmap
    prehighlighted_selected_pixmap: QtGui.QPixmap
    r = 0
    offset = 0
    next_marker_id = 0
    
    def _drawPixmap(self, size: int, r: int, color: QtGui.QColor, prehighlight_color: QtGui.QColor, border_color: QtGui.QColor) -> QtGui.QPixmap:
        center = size // 2
        pxmap = QtGui.QPixmap(size,size)
        pxmap.fill(QtGui.QColorConstants.Transparent)
        painter = QtGui.QPainter(pxmap)

        # Test routine
        brush = QtGui.QBrush(QtGui.QColor(prehighlight_color))
        pen = QtGui.QPen(color)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setBrush(brush)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(QtCore.QRectF(center-r+0.5,center-r+0.5,2*r,2*r))
        
        pen = QtGui.QPen(border_color)
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
        transparent_color      = QtGui.QColor("#00ffffff")
        unselected_color       = QtGui.QColor(config.get('Marker', 'color_default', fallback='#ffffffff'))
        selected_color         = QtGui.QColor(config.get('Marker', 'color_selected', fallback='#ffffff00'))
        prehighlighted_color   = QtGui.QColor(config.get('Marker', 'color_prehighlighted', fallback='#10ffff00'))
        border_color            = QtGui.QColor(config.get('Marker', 'color_border', fallback='#000000'))
        Marker.unselected_pixmap                = self._drawPixmap(size,r,unselected_color,   transparent_color,border_color)
        Marker.selected_pixmap                  = self._drawPixmap(size,r,  selected_color,   transparent_color,border_color)
        Marker.prehighlighted_pixmap            = self._drawPixmap(size,r,unselected_color,prehighlighted_color,border_color)    # unused
        Marker.prehighlighted_selected_pixmap   = self._drawPixmap(size,r,  selected_color,prehighlighted_color,border_color)    # unused
        Marker.unselected_pixmap.save(str(Path('images') / 'unselected_pixmap.png'), 'png')
        Marker.selected_pixmap.save(str(Path('images') / 'selected_pixmap.png'), 'png')
        Marker.prehighlighted_pixmap.save(str(Path('images') / 'prehighlighted_pixmap.png'), 'png')
        Marker.prehighlighted_selected_pixmap.save(str(Path('images') / 'prehighlighted_selected_pixmap.png'), 'png')
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
        self.setAcceptHoverEvents(True)
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

    def hoverEnterEvent(self, event):
        if self.isSelected():
            self.setPixmap(Marker.prehighlighted_selected_pixmap)
        else:
            self.setPixmap(Marker.prehighlighted_pixmap)
        return super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        if self.isSelected():
            self.setPixmap(Marker.selected_pixmap)
        else:
            self.setPixmap(Marker.unselected_pixmap)
        return super().hoverLeaveEvent(event)
    
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
