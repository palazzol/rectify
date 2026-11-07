# Source - https://stackoverflow.com/a
# Posted by ekhumoro, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-09, License - CC BY-SA 4.0

import os

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QAction

from imageview import ImageView
from project import ProjectFile, PROJECT_EXTENSION
from undoredo import undo, redo, clearHistory
from warp import warpImage, OUTPUT_DPI

# Persistent user settings, e.g. the last project folder
def _settings() -> QtCore.QSettings:
    return QtCore.QSettings(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope,
                            'rectify', 'rectify')

_LAST_PROJECT_DIR = 'paths/last_project_dir'

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('Rectify')
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setSizeGripEnabled(False)
        self.viewer = ImageView(self, self.statusbar)
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

        self._path: str | None = None
        self._imageName = ''
        self._imageData = b''
        self._projectPath: str | None = None

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_M and event.modifiers() == QtCore.Qt.KeyboardModifier.NoModifier:
            self.viewer.createMarkerAtCursor()
        #elif event.key() == QtCore.Qt.Key.Key_D and event.modifiers() == QtCore.Qt.KeyboardModifier.NoModifier:
        #    print('TBD - Delete Marker')
        elif event.key() == QtCore.Qt.Key.Key_C and event.modifiers() == QtCore.Qt.KeyboardModifier.NoModifier:
            if len(self.viewer._scene.selectedItems()) > 1:
                self.viewer.createConstraint()
        elif (event.key() == QtCore.Qt.Key.Key_T and not event.isAutoRepeat() and
              event.modifiers() in (QtCore.Qt.KeyboardModifier.NoModifier, QtCore.Qt.KeyboardModifier.ShiftModifier)):
            # t or T over a marker edits its target coordinates
            self.viewer.editTargetsAtCursor()
        elif (event.key() == QtCore.Qt.Key.Key_S and not event.isAutoRepeat() and
              event.modifiers() in (QtCore.Qt.KeyboardModifier.NoModifier, QtCore.Qt.KeyboardModifier.ShiftModifier)):
            # s or S solves for the transformation matrix and saves the warped image
            self.solveAndWarp()
        elif ((event.key() == QtCore.Qt.Key.Key_Backspace) or (event.key() == QtCore.Qt.Key.Key_Delete )) and event.modifiers() == QtCore.Qt.KeyboardModifier.NoModifier:
            self.viewer.deleteSelection()
        else:
            pass
            #print(event.key(), event.isAutoRepeat(), event.keyCombination(), event.modifiers())

    def _createMenuBar(self) -> None:
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        #new_action = QAction("&New", self)
        #new_action.setShortcut("Ctrl+N")
        #new_action.setStatusTip("Create a new document")
        #new_action.triggered.connect(self._new_file)
        #file_menu.addAction(new_action)

        open_action = QAction("&Open Image...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Start a new project from an image")
        open_action.triggered.connect(self.handleOpen)
        file_menu.addAction(open_action)

        open_project_action = QAction("Open &Project...", self)
        open_project_action.setShortcut("Ctrl+P")
        open_project_action.setStatusTip("Open an existing project")
        open_project_action.triggered.connect(self.handleOpenProject)
        file_menu.addAction(open_project_action)

        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save the current project")
        save_action.triggered.connect(self.handleSaveProject)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setStatusTip("Save the current project under a new name")
        save_as_action.triggered.connect(self.handleSaveProjectAs)
        file_menu.addAction(save_as_action)

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

        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setStatusTip("Undo last action")
        undo_action.triggered.connect(self.handleUndo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setStatusTip("Redo last action")
        redo_action.triggered.connect(self.handleRedo)
        edit_menu.addAction(redo_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        #about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def handleUndo(self) -> None:
        msg = undo()
        if msg == '':
            self.statusbar.showMessage('Nothing to Undo!')
        else:
            self.statusbar.showMessage(f'{msg} Undone')

    def handleRedo(self) -> None:
        msg = redo()
        if msg == '':
            self.statusbar.showMessage('Nothing to Redo!')
        else:
            self.statusbar.showMessage(f'{msg} Redone')

    def handleCoords(self, point: QtCore.QPointF) -> None:
        if not point.isNull():
            #self.labelCoords.setText(f'{point.x()}, {point.y()}')
            #self.statusbar.showMessage(f'Fractional Pixel Position: ({point.x():.6f}, {point.y():.6f})')
            pass
        else:
            #self.labelCoords.clear()
            self.statusbar.clearMessage()

    def handleOpen(self) -> None:
        if (start := self._path) is None:
            start = QtCore.QStandardPaths.standardLocations(
                QtCore.QStandardPaths.StandardLocation.PicturesLocation)[0]
        if path := QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open Image', start)[0]:
            #self.labelCoords.clear()
            self.statusbar.clearMessage()
            # Keep the original file contents, as they get saved in the project
            try:
                with open(path, 'rb') as f:
                    data = f.read()
            except OSError:
                data = b''
            if (pixmap := QtGui.QPixmap()).loadFromData(data):
                # A new image starts a new, unsaved project
                self.viewer.clearMarkers()
                clearHistory()
                self.viewer.setPhoto(pixmap)
                self._path = path
                self._imageName = os.path.basename(path)
                self._imageData = data
                self._projectPath = None
                self.updateTitle()
            else:
                QtWidgets.QMessageBox.warning(self, 'Error',
                    f'<br>Could not load image file:<br>'
                    f'<br><b>{path}</b><br>'
                    )

    def lastProjectDir(self) -> str | None:
        last = _settings().value(_LAST_PROJECT_DIR)
        return last if isinstance(last, str) and os.path.isdir(last) else None

    def rememberProjectDir(self, path: str) -> None:
        _settings().setValue(_LAST_PROJECT_DIR, os.path.dirname(os.path.abspath(path)))

    def projectDialogStart(self) -> str:
        if self._projectPath is not None:
            return self._projectPath
        if (last := self.lastProjectDir()) is not None:
            # The folder a project was last opened from or saved to
            if self._imageName:
                return os.path.join(last, os.path.splitext(self._imageName)[0] + PROJECT_EXTENSION)
            return last
        if self._path is not None:
            return os.path.splitext(self._path)[0] + PROJECT_EXTENSION
        return QtCore.QStandardPaths.standardLocations(
            QtCore.QStandardPaths.StandardLocation.DocumentsLocation)[0]

    def handleOpenProject(self) -> None:
        path = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open Project', self.projectDialogStart(),
            f'Rectify Project (*{PROJECT_EXTENSION});;All Files (*)')[0]
        if not path:
            return
        try:
            project = ProjectFile.load(path)
            pixmap = project.pixmap()
        except (OSError, ValueError) as e:
            QtWidgets.QMessageBox.warning(self, 'Error',
                f'<br>Could not load project file:<br>'
                f'<br><b>{path}</b><br>'
                f'<br>{e}<br>'
                )
            return
        self.viewer.clearMarkers()
        clearHistory()
        self.viewer.setPhoto(pixmap)
        self.viewer.setMarkers(project.markers)
        self._imageName = project.image_name
        self._imageData = project.image_data
        self._projectPath = path
        self.rememberProjectDir(path)
        self.updateTitle()
        self.statusbar.showMessage(f'Opened {os.path.basename(path)}')

    def handleSaveProject(self) -> None:
        if self._projectPath is None:
            self.handleSaveProjectAs()
        else:
            self.saveProject(self._projectPath)

    def handleSaveProjectAs(self) -> None:
        if not self.viewer.hasPhoto():
            self.statusbar.showMessage('Nothing to Save!')
            return
        path = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save Project', self.projectDialogStart(),
            f'Rectify Project (*{PROJECT_EXTENSION})')[0]
        if not path:
            return
        if not path.lower().endswith(PROJECT_EXTENSION):
            path += PROJECT_EXTENSION
        self.saveProject(path)

    def saveProject(self, path: str) -> None:
        if not self.viewer.hasPhoto():
            self.statusbar.showMessage('Nothing to Save!')
            return
        project = ProjectFile(self._imageName, self._imageData, self.viewer.markerData())
        try:
            project.save(path)
        except OSError as e:
            QtWidgets.QMessageBox.warning(self, 'Error',
                f'<br>Could not save project file:<br>'
                f'<br><b>{path}</b><br>'
                f'<br>{e}<br>'
                )
            return
        self._projectPath = path
        self.rememberProjectDir(path)
        self.updateTitle()
        self.statusbar.showMessage(f'Saved {os.path.basename(path)}')

    def solveAndWarp(self) -> None:
        if not self.viewer.hasPhoto():
            return
        T = self.viewer.solveTransform()
        if T is None:
            return
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            image = warpImage(self.viewer.photoImage(), T)
        except ValueError as e:
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.warning(self, 'Error',
                f'<br>Could not warp the image:<br><br>{e}<br>')
            return
        QtWidgets.QApplication.restoreOverrideCursor()
        path = QtWidgets.QFileDialog.getSaveFileName(
            self, f'Save Rectified Image ({image.width()} x {image.height()}, {OUTPUT_DPI:g} dpi)',
            self.rectifiedDialogStart(), 'PNG Image (*.png);;TIFF Image (*.tif *.tiff);;All Files (*)')[0]
        if not path:
            return
        if not os.path.splitext(path)[1]:
            path += '.png'
        if not image.save(path):
            QtWidgets.QMessageBox.warning(self, 'Error',
                f'<br>Could not save image file:<br><br><b>{path}</b><br>')
            return
        self.statusbar.showMessage(f'Saved {os.path.basename(path)} ({image.width()} x {image.height()})')

    def rectifiedDialogStart(self) -> str:
        if self._projectPath is not None:
            base = os.path.splitext(self._projectPath)[0]
        elif self._path is not None:
            base = os.path.splitext(self._path)[0]
        else:
            base = os.path.join(QtCore.QStandardPaths.standardLocations(
                QtCore.QStandardPaths.StandardLocation.PicturesLocation)[0],
                os.path.splitext(self._imageName)[0] or 'image')
        return base + '_rectified.png'

    def updateTitle(self) -> None:
        if self._projectPath is not None:
            self.setWindowTitle(f'Rectify - {os.path.basename(self._projectPath)}')
        elif self._imageName:
            self.setWindowTitle(f'Rectify - {self._imageName} (unsaved)')
        else:
            self.setWindowTitle('Rectify')