# Source - https://stackoverflow.com/a
# Posted by ekhumoro, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-09, License - CC BY-SA 4.0

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from typing import cast

from undoredo import undoContext, UndoContext
from marker import Marker
from constraint import ConstraintDialog

SCALE_FACTOR = 1.25

class ImageView(QGraphicsView):
    coordinatesChanged = QtCore.Signal(QtCore.QPointF)

    def __init__(self, parent: QtWidgets.QWidget | None, statusbar: QtWidgets.QStatusBar) -> None:
        super().__init__(parent)
        self.statusbar = statusbar
        self._zoom = 0
        self._pinned = False
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._photo.setShapeMode(QGraphicsPixmapItem.ShapeMode.BoundingRectShape)
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        #self._scene.selectionChanged.connect(self.handleSelectionChange)
        self.markerlist: list[Marker] = []

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        if self._photo.isUnderMouse():
            if len(self.items(QtCore.QRect(event.x(), event.y(), 1, 1))) > 1: # TBD need to ignore the image item!
                super().contextMenuEvent(event) # Handle Items first
            else:
                context_menu = QtWidgets.QMenu(self)
                create_marker_action = QtGui.QAction("Create &Marker", self)
                create_marker_action.setShortcut("M")
                create_marker_action.triggered.connect(self.createMarkerAtMenuPos)
                context_menu.addAction(create_marker_action)
                self.menupos = event.globalPos() # save this as the menu action needs it
                if len(self._scene.selectedItems()) > 1:
                    create_constraint_action = QtGui.QAction("Create &Constraint", self)
                    create_constraint_action.setShortcut("C")
                    create_constraint_action.triggered.connect(self.createConstraint)
                    context_menu.addAction(create_constraint_action)
                context_menu.exec(event.globalPos())

    # Atomic Action
    def createMarkerAtMenuPos(self) -> None:
        with undoContext("Create Marker") as uctx:
            pos = self.mapFromGlobal(self.menupos)
            point = self.mapToScene(pos)
            self.createMarker(uctx, point)
            self.statusbar.showMessage("Create Marker")

    # Atomic Action
    def createMarkerAtCursor(self) -> None:
        with undoContext("Create Marker") as uctx:
            viewpos = self.mapFromGlobal(QtGui.QCursor.pos())
            point = self.mapToScene(viewpos)
            self.createMarker(uctx, point)
            self.statusbar.showMessage("Create Marker")

    def createMarker(self, uctx: UndoContext, point: QtCore.QPointF, mid: int | None = None) -> None:
        marker = Marker(self,point,mid)
        self._scene.addItem(marker)
        self.markerlist.append(marker)
        marker.update()
        #print(f'Created marker id={marker.mid}')
        uctx.recordAction(self.deleteMarker, uctx, marker.mid)

    def deleteMarker(self, uctx: UndoContext, mid: int ) -> None:
        marker = self.getItemById(mid)
        pos,mid = marker.pos(),marker.mid
        self.markerlist.remove(marker)
        self._scene.removeItem(marker)
        #print(f'Deleted marker id={id}')
        uctx.recordAction(self.createMarker, uctx, pos, mid)

    # Atomic Action
    def deleteSelection(self) -> None:
        with undoContext("Delete Selection") as uctx:
            selectedItems = self._scene.selectedItems().copy()
            if len(selectedItems) == 0:
                return
            for item in selectedItems:
                mid = cast(Marker, item).mid
                self.deleteMarker(uctx, mid)
        self.statusbar.showMessage("Delete Selection")

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if not self.hasPhoto():
            return
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            #print('Begin Window Select')
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            super().mousePressEvent(event)
        elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
            #print('Begin Drag')
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            fakeevent = QtGui.QMouseEvent(event.type(), event.pos(), QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.MouseButton.LeftButton, event.modifiers())
            super().mousePressEvent(fakeevent)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if not self.hasPhoto():
            return
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            #print('End Window Select')
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
            super().mouseReleaseEvent(event)
        elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
            if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag:
                #print('End Drag')
                self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
                fakeevent = QtGui.QMouseEvent(event.type(), event.pos(), QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.MouseButton.LeftButton, event.modifiers())
                super().mouseReleaseEvent(fakeevent)

    def hasPhoto(self) -> bool:
        return not self._empty

    def resetView(self, scale: float = 1.0) -> None:
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if (scale := max(1, scale)) == 1:
                self._zoom = 0
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height()) * scale
                self.scale(factor, factor)
                if not self.zoomPinned():
                    self.centerOn(self._photo)
                self.updateCoordinates()

    def setPhoto(self, pixmap: QtGui.QPixmap | None = None) -> None:
        if pixmap and not pixmap.isNull():
            self._empty = False
            #self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            #self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        if not (self.zoomPinned() and self.hasPhoto()):
            self._zoom = 0
        self.resetView(SCALE_FACTOR ** self._zoom)

    def zoomLevel(self) -> float:
        return self._zoom

    def zoomPinned(self) -> bool:
        return self._pinned

    def setZoomPinned(self, enable: bool) -> None:
        self._pinned = bool(enable)

    def zoom(self, step: float) -> None:
        zoom = max(0, self._zoom + (step := int(step)))
        if zoom != self._zoom:
            self._zoom = zoom
            if self._zoom > 0:
                if step > 0:
                    factor = SCALE_FACTOR ** step
                else:
                    factor = 1 / SCALE_FACTOR ** abs(step)
                self.scale(factor, factor)
            else:
                self.resetView()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        delta = event.angleDelta().y()
        self.zoom(delta and delta // abs(delta))

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.resetView()

    def toggleDragMode(self) -> None:
        if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def updateCoordinates(self, pos: QtCore.QPoint | None = None) -> None:
        if self._photo.isUnderMouse():
            if pos is None:
                pos = self.mapFromGlobal(QtGui.QCursor.pos())
            # Fractional Pixels! Yay!
            point = self.mapToScene(pos)
        else:
            point = QtCore.QPointF()
        self.coordinatesChanged.emit(point)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        self.updateCoordinates(event.position().toPoint())
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.coordinatesChanged.emit(QtCore.QPointF())
        super().leaveEvent(event)

    #def handleSelectionChange(self):
    #    print('Selection Changed!')

    # Atomic Action
    def setSelectionDeltaPos(self, delta_pos: QtCore.QPointF) -> None:
        with undoContext("Move Selection") as uctx:
            for item in self._scene.selectedItems():
                new_pos = item.pos()
                old_pos = new_pos - delta_pos
                marker = cast(Marker, item)
                uctx.recordAction(self.moveMarker, uctx, marker.mid, old_pos)
        self.statusbar.showMessage("Move Selection")
    
    def moveMarker(self, uctx: UndoContext, mid, pos: QtCore.QPointF) -> None:
        item = self.getItemById(mid)
        old_pos = item.pos()
        uctx.recordAction(self.moveMarker, uctx, mid, old_pos)
        item.setPos(pos)
    
    def createConstraint(self) -> None:
        dialog = ConstraintDialog(self)
        dialog.exec()

    # TBD - we can make this more efficient later 
    # by using a dict of ids to items
    def getItemById(self, mid: int) -> Marker:
        for item in self.markerlist:
            if item.mid == mid:
                return item
        raise KeyError
