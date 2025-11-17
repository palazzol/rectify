
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QDialog

class ConstraintDialog(QDialog):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle('Constraint')
        hbutton = QtWidgets.QPushButton('Make Horizontal')
        vbutton = QtWidgets.QPushButton('Make Vertical')
        hlabel = QtWidgets.QLabel('Horizontal Distance')
        vlabel = QtWidgets.QLabel('Vertical Distance')
        hdistance = QtWidgets.QLineEdit()
        vdistance = QtWidgets.QLineEdit()
        okbutton = QtWidgets.QPushButton('OK')
        cancelvbutton = QtWidgets.QPushButton('Cancel')
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(hbutton, 0, 0, 1, 1)
        layout.addWidget(vbutton, 1, 0, 1, 1)
        layout.addWidget(hlabel, 2, 0, 1, 1)
        layout.addWidget(hdistance, 2, 1, 1, 1)
        layout.addWidget(vlabel, 3, 0, 1, 1)
        layout.addWidget(vdistance, 3, 1, 1, 1)
        layout.addWidget(okbutton, 4, 2, 1, 1)
        layout.addWidget(cancelvbutton, 4, 3, 1, 1)
