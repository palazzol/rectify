# Source - https://stackoverflow.com/a
# Posted by ekhumoro, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-09, License - CC BY-SA 4.0

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QGraphicsView

from imageview import ImageView
from undoredo import UndoRedoManager
from configparser import ConfigParser

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Rectify')
        self.viewer = ImageView(self)
        self.viewer.coordinatesChanged.connect(self.handleCoords)
        '''
        self.labelCoords = QtWidgets.QLabel(self)
        self.labelCoords.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight |
            QtCore.Qt.AlignmentFlag.AlignCenter)
        self.buttonOpen = QtWidgets.QPushButton(self)
        self.buttonOpen.setText('Open Image')
        self.buttonOpen.clicked.connect(self.handleOpen)
        self.buttonPin = QtWidgets.QPushButton(self)
        self.buttonPin.setText('Pin Zoom')
        self.buttonPin.setCheckable(True)
        self.buttonPin.toggled.connect(self.viewer.setZoomPinned)
        '''

        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setSizeGripEnabled(False)

        widget = QtWidgets.QWidget(self)

        layout = QtWidgets.QGridLayout(widget)
        layout.addWidget(self.viewer, 0, 0, 1, 3)
        #layout.addWidget(self.buttonOpen, 1, 0, 1, 1)
        #layout.addWidget(self.buttonPin, 1, 1, 1, 1)
        #layout.addWidget(self.labelCoords, 1, 2, 1, 1)
        layout.addWidget(self.statusbar, 1, 2, 1, 1)
        layout.setColumnStretch(2, 2)

        self.setCentralWidget(widget)

        self._createMenuBar()

        self.undo_redo_manager = UndoRedoManager()

        self.config = ConfigParser()
        self.config.read('config.ini')

        self._path = None

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Z and event.modifiers() | QtCore.Qt.CTRL:
            did_something = self.undo_redo_manager.undo()
            if not did_something:
                self.statusbar.showMessage('Nothing to Undo!')
        elif event.key() == QtCore.Qt.Key_Y and event.modifiers() | QtCore.Qt.CTRL:
            did_something = self.undo_redo_manager.redo()
            if not did_something:
                self.statusbar.showMessage('Nothing to Redo!')
        elif event.key() == QtCore.Qt.Key_M and event.modifiers() == QtCore.Qt.NoModifier:
            self.viewer.createMarker(event)
        elif event.key() == QtCore.Qt.Key_D and event.modifiers() == QtCore.Qt.NoModifier:
            print('TBD - Delete Marker')
        elif ((event.key() == QtCore.Qt.Key_Backspace) or (event.key() == QtCore.Qt.Key_Delete )) and event.modifiers() == QtCore.Qt.NoModifier:
            print('TBD - Delete Selection')
        else:
            pass
            #print(event.key(), event.isAutoRepeat(), event.keyCombination(), event.modifiers())

    def _createMenuBar(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        #new_action = QAction("&New", self)
        #new_action.setShortcut("Ctrl+N")
        #new_action.setStatusTip("Create a new document")
        #new_action.triggered.connect(self._new_file)
        #file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an existing document")
        open_action.triggered.connect(self.handleOpen)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.setStatusTip("Copy selected text")
        #copy_action.triggered.connect(lambda: self._edit_action("Copy"))
        edit_menu.addAction(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.setStatusTip("Paste text from clipboard")
        #paste_action.triggered.connect(lambda: self._edit_action("Paste"))
        edit_menu.addAction(paste_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        #about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def handleCoords(self, point):
        if not point.isNull():
            #self.labelCoords.setText(f'{point.x()}, {point.y()}')
            self.statusbar.showMessage(f'Fractional Pixel Position: ({point.x():.6f}, {point.y():.6f})')
        else:
            #self.labelCoords.clear()
            self.statusbar.clearMessage()

    def handleOpen(self):
        if (start := self._path) is None:
            start = QtCore.QStandardPaths.standardLocations(
                QtCore.QStandardPaths.StandardLocation.PicturesLocation)[0]
        if path := QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open Image', start)[0]:
            #self.labelCoords.clear()
            self.statusbar.clearMessage()
            if not (pixmap := QtGui.QPixmap(path)).isNull():
                self.viewer.setPhoto(pixmap)
                self._path = path
            else:
                QtWidgets.QMessageBox.warning(self, 'Error',
                    f'<br>Could not load image file:<br>'
                    f'<br><b>{path}</b><br>'
                    )