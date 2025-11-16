
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from imageview import ImageView

# Use a scaled pixmap for marker graphics
class Marker(QGraphicsPixmapItem):
    pixmaps_initialized: bool = False
    unselected_pixmap:     QtGui.QPixmap
    selected_pixmap:       QtGui.QPixmap
    prehighlighted_pixmap: QtGui.QPixmap
    next_marker_id = 0
    
    def _drawPixmap(self, r: int, color: QtGui.QColor, outline_color: QtGui.QColor) -> QtGui.QPixmap:
        pxmap = QtGui.QPixmap(64,64)
        pxmap.fill(QtGui.QColorConstants.Transparent)
        painter = QtGui.QPainter(pxmap)

        pen = QtGui.QPen(outline_color)
        pen.setWidth(5)
        painter.setPen(pen)
        painter.drawEllipse(32-r,32-r,2*r,2*r)
        painter.drawLine(32-r,32,64-(32-r),32)
        painter.drawLine(32,32-r,32,64-(32-r))

        pen = QtGui.QPen(color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawEllipse(32-r,32-r,2*r,2*r)
        painter.drawLine(32-r,32,64-(32-r),32)
        painter.drawLine(32,32-r,32,64-(32-r))

        return pxmap

    def _initPixmaps(self,r: int) -> None:
        Marker.unselected_pixmap     = self._drawPixmap(r,QtGui.QColorConstants.White, QtGui.QColorConstants.Black) # White on Black
        Marker.selected_pixmap       = self._drawPixmap(r,QtGui.QColorConstants.Yellow,QtGui.QColorConstants.Black) # Yellow on Black
        Marker.prehighlighted_pixmap = self._drawPixmap(r,QtGui.QColorConstants.White, QtGui.QColorConstants.Black)    # unused
        Marker.pixmaps_initialized = True

    def __init__(self, view: "ImageView", pos: QtCore.QPointF, mid:int | None = None) -> None:
        super().__init__()
        # Set the id if not given
        if mid is None:
            self.mid = Marker.next_marker_id
            Marker.next_marker_id += 1
        else:
            self.mid = mid
        self.r = 20   # radius in pixels on a 64x64 pixmap
        if not Marker.pixmaps_initialized:
            self._initPixmaps(self.r)
        self.setPos(pos)
        self.setOffset(-32,-32)
        self.rect = QtCore.QRect(-32,-32,32,32)
        #self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setPixmap(Marker.unselected_pixmap)
        self.setView(view)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        # if selection state changed, swap the pixmap
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if value:
                self.setPixmap(Marker.selected_pixmap)
            else:
                self.setPixmap(Marker.unselected_pixmap)
        return super().itemChange(change, value)
    
    def shape(self):
        # Outline for precise picking
        path = QtGui.QPainterPath()
        path.addEllipse(-self.r,-self.r,2*self.r,2*self.r)
        return path

    def setView(self, view: "ImageView"):
        # Pixmap scales with the View
        self.view = view    # TBD - maybe we should subscribe to changes instead
        # one pixel in the view is how much in the scene?
        scale = (self.view.mapToScene(0,1) - self.view.mapToScene(0,0)).y()
        #print(f'scale = {scale}')
        #super().setScale(scale*10.0/self.r)
        super().setScale(scale)
        self.update()

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
        if self in self.view._scene.selectedItems():
            action1 = QtGui.QAction("Delete Selection")
            action1.triggered.connect(self.view.deleteSelection)
            context_menu.addAction(action1)
            if len(self.view._scene.selectedItems()) > 1:
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
        self.view.deleteMarker(self.mid)
        self.view.undo_redo_manager.pushEndMark("Delete Marker")
        self.view.statusbar.showMessage("Delete Marker")
