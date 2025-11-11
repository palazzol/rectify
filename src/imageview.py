# Source - https://stackoverflow.com/a
# Posted by ekhumoro, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-09, License - CC BY-SA 4.0

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QApplication

from marker import Marker

SCALE_FACTOR = 1.25

class ImageView(QGraphicsView):
    coordinatesChanged = QtCore.Signal(QtCore.QPointF)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
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
        self.markerlist = []

    def createMarkerAtCursor(self):
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        point = self.mapToScene(pos)
        self.createMarker(point)

    def createMarker(self, point, id=None):
        marker = Marker(self,point,id)
        self._scene.addItem(marker)
        self.markerlist.append(marker)
        marker.update()
        #print(f'Created marker id={marker.id}')
        self.parent.undo_redo_manager.pushAction(self.deleteMarker, marker.id)

    def deleteMarker(self, id):
        marker = None
        for elem in self.markerlist:
            if elem.id == id:
                marker = elem
                break
        pos,id = marker.pos(),marker.id
        self.markerlist.remove(marker)
        self._scene.removeItem(marker)
        #print(f'Deleted marker id={id}')
        self.parent.undo_redo_manager.pushAction(self.createMarker, pos, id)
        #self.parent.undo_redo_manager.pushEndMark()

    def deleteSelection(self):
        selectedItems = self._scene.selectedItems().copy()
        count = 0
        for marker in selectedItems:
            id = marker.id
            self.deleteMarker(id)
            count += 1
        return count

    def mousePressEvent(self, event):
        if not self.hasPhoto():
            return
        if event.button() == QtCore.Qt.LeftButton:
            #print('Begin Window Select')
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            super().mousePressEvent(event)
        elif event.button() == QtCore.Qt.MiddleButton:
            #print('Begin Drag')
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            fakeevent = QtGui.QMouseEvent(event.type(), event.pos(), QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, event.modifiers());
            super().mousePressEvent(fakeevent)

    def mouseReleaseEvent(self, event):
        if not self.hasPhoto():
            return
        if event.button() == QtCore.Qt.LeftButton:
            #print('End Window Select')
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
            super().mouseReleaseEvent(event)
        elif event.button() == QtCore.Qt.MiddleButton:
            if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag:
                #print('End Drag')
                self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
                fakeevent = QtGui.QMouseEvent(event.type(), event.pos(), QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, event.modifiers());
                super().mouseReleaseEvent(fakeevent)

    def hasPhoto(self):
        return not self._empty

    def resetView(self, scale=1):
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

    def setPhoto(self, pixmap=None):
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

    def zoomLevel(self):
        return self._zoom

    def zoomPinned(self):
        return self._pinned

    def setZoomPinned(self, enable):
        self._pinned = bool(enable)

    def zoom(self, step):
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
            self.updateMarkers()

    def updateMarkers(self):
        # Update Markers
        for elem in self.markerlist:
            elem.setView(self)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.zoom(delta and delta // abs(delta))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resetView()
        self.updateMarkers()

    def toggleDragMode(self):
        if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def updateCoordinates(self, pos=None):
        if self._photo.isUnderMouse():
            if pos is None:
                pos = self.mapFromGlobal(QtGui.QCursor.pos())
            # Fractional Pixels! Yay!
            point = self.mapToScene(pos)
        else:
            point = QtCore.QPointF()
        self.coordinatesChanged.emit(point)

    def mouseMoveEvent(self, event):
        self.updateCoordinates(event.position().toPoint())
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.coordinatesChanged.emit(QtCore.QPointF())
        super().leaveEvent(event)

    #def handleSelectionChange(self):
    #    print('Selection Changed!')

    def setSelectionDeltaPos(self, delta_pos):
        for item in self._scene.selectedItems():
            new_pos = item.pos()
            old_pos = new_pos - delta_pos
            self.parent.undo_redo_manager.pushAction(self.moveMarker, item.id, old_pos)
        self.parent.undo_redo_manager.pushEndMark()
    
    def moveMarker(self, id, pos):
        for item in self.markerlist:
            if item.id == id:
               old_pos = item.pos()
               self.parent.undo_redo_manager.pushAction(self.moveMarker, id, old_pos)
               item.setPos(pos)
