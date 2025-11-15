
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QApplication, QDialog

class ConstraintDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

