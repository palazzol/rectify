# Source - https://stackoverflow.com/a
# Posted by ekhumoro, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-09, License - CC BY-SA 4.0

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem

SCALE_FACTOR = 1.25

# Use a scaled pixmap for marker graphics
class Marker(QGraphicsPixmapItem):
    pixmap = None
    selected_pixmap = None
    prehighlighted_pixmap = None
    
    def _drawPixmap(self,r,color):
        pxmap = QtGui.QPixmap(64,64)
        pxmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pxmap)
        pen = QtGui.QPen(color)
        painter.setPen(pen)
        pen.setWidth(5)
        painter.setPen(pen)
        painter.drawEllipse(32-r,32-r,2*r,2*r)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(32-r,32,64-(32-r),32)
        painter.drawLine(32,32-r,32,64-(32-r))
        return pxmap

    def _initPixmaps(self,r):
        Marker.pixmap                = self._drawPixmap(r,QtGui.QColor(128,128,255))
        Marker.selected_pixmap       = self._drawPixmap(r,QtGui.QColor(  0,  0,255))
        Marker.prehighlighted_pixmap = self._drawPixmap(r,QtGui.QColor(255,255,  0))

    def __init__(self, pos, scale):
        super().__init__()
        self.scale = None
        self.r = 25.0
        if Marker.pixmap is None:
            self._initPixmaps(self.r)
        self.setPos(pos)
        self.setOffset(-32,-32)
        self.rect = QtCore.QRect(-32,-32,32,32)
        self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setPixmap(Marker.pixmap)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setScale(scale)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if value:
                self.setPixmap(Marker.selected_pixmap)
            else:
                self.setPixmap(Marker.pixmap)
            print('x')
        return super().itemChange(change, value)

    #def paint(self, painter, options, widget):
        #print("paint")
        #if self.isSelected():
        #    self.setPen(QtGui.QPen(QtGui.QColor(255,255,0)))
        #self.setPixmap(Marker.selected_pixmap)
        #else:
        #    self.setPixmap(Marker.pixmap)
        #return super().paint(painter, options, widget)
    
    # Used for picking
    def shape(self):
        path = QtGui.QPainterPath()
        path.addEllipse(-self.r,-self.r,2*self.r,2*self.r)
        return path

    # Scales with the View
    def setScale(self, scale):
        if scale == self.scale:
            return
        super().setScale(scale*10.0/self.r)
        self.scale = scale
        self.update()

'''
class Marker(QGraphicsItem):
    def __init__(self, pos, scale=1.0):
        super().__init__()
        self.pos = pos
        self.resize(scale)
        # You can set flags for movability, selectability, etc.
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setPos(pos)
        self.rect = QtCore.QRect(-self.r,-self.r,self.r*2,self.r*2)
        print("init")

    def boundingRect(self):
        return self.rect.adjusted(-(self.adjwidth+1),-(self.adjwidth+1),+(self.adjwidth+1),+(self.adjwidth+1)) # thick line + 0.5?

    def shape(self):
        path = QtGui.QPainterPath()
        path.addEllipse(self.rect.adjusted(-self.adjwidth,-self.adjwidth,+self.adjwidth,+self.adjwidth)) # for thick line
        return path
    
    def paint(self, painter, options, widget=None):
        if self.isSelected():
            pen = QtGui.QPen(QtGui.QColor(255,255,0))
        else:
            pen = QtGui.QPen(QtGui.QColor(0,0,255))
        painter.setPen(pen)
        #brush = QtGui.QBrush(QtGui.QColor(255,0,0))
        #painter.setBrush(brush)
        pen.setWidth(self.thickwidth)
        painter.setPen(pen)
        painter.drawEllipse(self.rect)
        pen.setWidth(self.thinwidth)
        painter.setPen(pen)
        painter.drawLine(-self.r,0,+self.r,0)
        painter.drawLine(0,-self.r,0,+self.r)
        print("paint")

    def resize(self,scale):
        self.scale = scale
        self.r = scale*10.0
        self.thickwidth = scale*3.0
        self.adjwidth = scale*1.0 # thickwidth/2 rounded down
        self.thinwidth = scale*1.0
        self.rect = QtCore.QRect(-self.r,-self.r,self.r*2,self.r*2)
'''

class ImageView(QGraphicsView):
    coordinatesChanged = QtCore.Signal(QtCore.QPointF)

    def __init__(self, parent):
        super().__init__(parent)
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

    def createMarker(self, event):
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        point = self.mapToScene(pos)
        # one pixel in the view is how much in the scene?
        scale = (self.mapToScene(0,1) - self.mapToScene(0,0)).y()
        print(f'scale = {scale}')
        marker = Marker(point,scale)
        self._scene.addItem(marker)
        self.markerlist.append(marker)
        marker.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.hasPhoto():
                print('Begin Window Select')
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
                super().mousePressEvent(event)
        elif event.button() == QtCore.Qt.MiddleButton:
            if self.hasPhoto():
                print('Begin Drag')
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                fakeevent = QtGui.QMouseEvent(event.type(), event.pos(), QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, event.modifiers());
                super().mousePressEvent(fakeevent)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.hasPhoto():
                print('End Window Select')
                self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
                super().mouseReleaseEvent(event)
        elif event.button() == QtCore.Qt.MiddleButton:
            if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag:
                print('End Drag')
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
        s = (self.mapToScene(0,1) - self.mapToScene(0,0)).y()
        for elem in self.markerlist:
            elem.setScale(s)

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

