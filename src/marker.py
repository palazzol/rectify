
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem

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
