from PySide6.QtWidgets import QApplication

from mainwindow import MainWindow

def main() -> None:
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setGeometry(500, 300, 800, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
