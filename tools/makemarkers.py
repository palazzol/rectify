
from PySide6 import QtCore, QtGui, QtWidgets

'''
Notes on how QPainter does things:

If you use integer coordinates, with no antialiasing, the pixels are indexed conventionally,
with (0,0) as the upper-left pixel.

If you use float coordinates, with antialiasing, the coordinates are centered on (m+0.5,n+0.5)
So, the point at (0.5,0.5) is the middle of the top-left pixel.

If you use integer coordinates with antialiasing, the pen is centered on the edge of the pixels,
and you will get half-pixels drawn.

'''
def genPixmap(params: list[Any]) -> None:
    size = params[0]
    r = params[1]
    border_ellipse_aa = params[2]
    border_ellipse_width = params[3]
    inside_ellipse_aa = params[4]
    inside_ellipse_width = params[5]
    border_line_aa = params[6]
    border_line_width = params[7]
    inside_line_aa = params[8]
    inside_line_width = params[9]
    center = size // 2

    pxmap = QtGui.QPixmap(size,size)
    pxmap.fill(QtGui.QColorConstants.Transparent)
    painter = QtGui.QPainter(pxmap)

    pen = QtGui.QPen(QtGui.QColor("#000000"))
    painter.setRenderHint(QtGui.QPainter.Antialiasing, border_ellipse_aa)
    pen.setWidth(border_ellipse_width)
    painter.setPen(pen)
    painter.drawEllipse(QtCore.QRectF(center-r+0.5,center-r+0.5,2*r,2*r))
    painter.setRenderHint(QtGui.QPainter.Antialiasing, border_line_aa)
    pen.setWidth(border_line_width)
    painter.setPen(pen)
    painter.drawLine(QtCore.QPointF(center-r+0.5,center+0.5),QtCore.QPointF(size-(center-r)+0.5,center+0.5))
    painter.drawLine(QtCore.QPointF(center+0.5,center-r+0.5),QtCore.QPointF(center+0.5,size-(center-r)+0.5))

    pen = QtGui.QPen(QtGui.QColor("#FFFFFF"))
    painter.setRenderHint(QtGui.QPainter.Antialiasing, inside_ellipse_aa)
    pen.setWidth(inside_ellipse_width)
    painter.setPen(pen)
    painter.drawEllipse(QtCore.QRectF(center-r+0.5,center-r+0.5,2*r,2*r))
    painter.setRenderHint(QtGui.QPainter.Antialiasing, inside_line_aa)
    pen.setWidth(inside_line_width)
    painter.setPen(pen)
    painter.drawLine(QtCore.QPointF(center-r+0.5,center+0.5),QtCore.QPointF(size-(center-r)+0.5,center+0.5))
    painter.drawLine(QtCore.QPointF(center+0.5,center-r+0.5),QtCore.QPointF(center+0.5,size-(center-r)+0.5))
    return pxmap
    

def main():
    QtWidgets.QApplication([])

    variations = [  #      e       e       l       l
                    [64,25,False,3,False,1,False,3,False,1], # most pixellated
                    [64,25, True,3,False,1, True,3,False,1],
                    [64,25, True,3, True,1, True,3, True,1], # Smoothest
                    [64,25,False,5,False,1,False,5,False,1],
                    [64,25, True,5,False,1, True,5,False,1],
                    [64,25, True,5, True,1, True,5, True,1],
                    [64,25, True,5, True,1,False,3,False,1],
                    [64,25, True,4, True,2,False,3,False,1], # These two look the same
                    [64,25, True,4, True,2, True,3, True,1], # These two look the same
                 ]
    # Personally, I think the last two are the best.
    # 1) The crosshairs are 1-pixel wide inside, with 1-pixel borders, so they are precise
    # 2) The circles are antialiased so they look smooth
    # 3) The circles are more than one pixel wide, so the anti-aliasing doesn't wash them out too much.
    
    for params in variations:
        pxmap = genPixmap(params)
        pxmap.save(f"testmarker_{params[0]}_{params[1]}_{params[2]}_{params[3]}_{params[4]}_{params[5]}_{params[6]}_{params[7]}_{params[8]}_{params[9]}.png", "PNG")

if __name__ == '__main__':
    main()
