import math

from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog, QDialogButtonBox

# Dialog to set or unset a marker's target X and Y coordinates.
# Each axis has a checkbox: checked means the value is set, unchecked means unset.
class TargetDialog(QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None, mid: int,
                 target_x: float | None, target_y: float | None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f'Marker {mid} Target')

        layout = QtWidgets.QGridLayout(self)
        self._xcheck, self._xedit = self._addRow(layout, 0, 'Target X', target_x)
        self._ycheck, self._yedit = self._addRow(layout, 1, 'Target Y', target_y)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                         QDialogButtonBox.StandardButton.Cancel)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons, 2, 0, 1, 2)

        # Start with the cursor in the first field that is set
        if self._xcheck.isChecked():
            self._xedit.setFocus()
            self._xedit.selectAll()
        elif self._ycheck.isChecked():
            self._yedit.setFocus()
            self._yedit.selectAll()

        self._validate()

    def _addRow(self, layout: QtWidgets.QGridLayout, row: int, label: str,
                value: float | None) -> tuple[QtWidgets.QCheckBox, QtWidgets.QLineEdit]:
        check = QtWidgets.QCheckBox(label)
        edit = QtWidgets.QLineEdit()
        check.setChecked(value is not None)
        # repr gives the shortest text that converts back to the same float
        edit.setText('' if value is None else repr(value))
        edit.setEnabled(value is not None)
        check.toggled.connect(edit.setEnabled)
        check.toggled.connect(self._validate)
        check.toggled.connect(lambda checked: checked and edit.setFocus())
        edit.textChanged.connect(self._validate)
        layout.addWidget(check, row, 0)
        layout.addWidget(edit, row, 1)
        return check, edit

    @staticmethod
    def _parse(text: str) -> float | None:
        try:
            value = float(text)
        except ValueError:
            return None
        return value if math.isfinite(value) else None

    def _fieldValid(self, check: QtWidgets.QCheckBox, edit: QtWidgets.QLineEdit) -> bool:
        valid = not check.isChecked() or self._parse(edit.text()) is not None
        edit.setStyleSheet('' if valid else 'color: red')
        return valid

    def _validate(self) -> None:
        # OK is only enabled when every set value is a valid number
        valid = self._fieldValid(self._xcheck, self._xedit)
        valid = self._fieldValid(self._ycheck, self._yedit) and valid
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(valid)

    # The values entered, with None for unset. Only meaningful after accept.
    def targets(self) -> tuple[float | None, float | None]:
        x = self._parse(self._xedit.text()) if self._xcheck.isChecked() else None
        y = self._parse(self._yedit.text()) if self._ycheck.isChecked() else None
        return x, y
