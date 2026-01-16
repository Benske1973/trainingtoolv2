import sys
from PyQt6.QtWidgets import QApplication

# Import from xaurum package
from xaurum.theme import APP_STYLE
from xaurum.ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setStyleSheet(APP_STYLE)

    win = MainWindow()
    win.showMaximized()
    
    sys.exit(app.exec())