
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem

# Use a scaled pixmap for marker graphics
class Marker(QGraphicsPixmapItem):
    pixmap = None
    selected_pixmap = None
    prehighlighted_pixmap = None
    next_marker_id = 0
    
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
        Marker.prehighlighted_pixmap = self._drawPixmap(r,QtGui.QColor(255,255,  0))    # unused

    def __init__(self, view, pos, id=id):
        super().__init__()
        # Set the id if not given
        if id == None:
            self.id = Marker.next_marker_id
            Marker.next_marker_id += 1
        else:
            self.id = id
        self.r = 25.0   # radius in pixels on a 64x64 pixmap
        if Marker.pixmap is None:
            self._initPixmaps(self.r)
        self.setPos(pos)
        self.setOffset(-32,-32)
        self.rect = QtCore.QRect(-32,-32,32,32)
        self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setPixmap(Marker.pixmap)
        self.setView(view)

    def itemChange(self, change, value):
        # if selection state changed, swap the pixmap
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if value:
                self.setPixmap(Marker.selected_pixmap)
            else:
                self.setPixmap(Marker.pixmap)
        return super().itemChange(change, value)
    
    def shape(self):
        # Outline for precise picking
        path = QtGui.QPainterPath()
        path.addEllipse(-self.r,-self.r,2*self.r,2*self.r)
        return path

    def setView(self, view):
        # Pixmap scales with the View
        self.view = view    # TBD - maybe we should subscribe to changes instead
        # one pixel in the view is how much in the scene?
        scale = (self.view.mapToScene(0,1) - self.view.mapToScene(0,0)).y()
        #print(f'scale = {scale}')
        super().setScale(scale*10.0/self.r)
        self.update()

    def mousePressEvent(self, event):
        # Save pos to detect an interactive move
        self.mouse_pressed_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # If we are being moved, the whole selection is being moved - notify the view
        if self.pos() != self.mouse_pressed_pos:
            self.view.setSelectionDeltaPos(self.pos() - self.mouse_pressed_pos)
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        context_menu = QtWidgets.QMenu()
        action = QtGui.QAction("Delete Marker")
        action.triggered.connect(self.deleteYourself)
        context_menu.addAction(action)
        context_menu.exec(event.screenPos())

    # Atomic Action
    def deleteYourself(self):
        self.view.deleteMarker(self.id)
        self.view.parent.undo_redo_manager.pushEndMark()