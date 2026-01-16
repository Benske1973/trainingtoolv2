import sys
import os
from PyQt6.QtWidgets import QApplication

# --- HIER IS DE FIX ---
# We voegen de map bóven de huidige map toe aan het pad. 
# Hierdoor snapt Python imports als 'from xaurum.theme...' weer.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# ----------------------

# Nu kunnen we importeren zoals de rest van de bestanden dat ook doen
from xaurum.theme import APP_STYLE
from xaurum.ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setStyleSheet(APP_STYLE)

    win = MainWindow()
    win.showMaximized()
    
    sys.exit(app.exec())