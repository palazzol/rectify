
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