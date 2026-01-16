"""
theme.py

Thema / styling helper voor Training Management System
- Achtergrond: Wit
- Sidebar: Donkerblauw (#002439) met witte tekst
- Knoppen: Donkerblauw (#002439) met grotere tekst voor opslaan
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtGui import QPixmap, QIcon, QColor, QPainter, QBrush
from PyQt6.QtCore import Qt

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

# Kleurenpalet
COLORS = {
    "primary": "#00121D",    # Zeer donkerblauw
    "sidebar_bg": "#002439", # Sidebar achtergrond
    "accent": "#002439",     # Knoppen kleur
    "accent_hover": "#003352", # Hover kleur
    "equans_green": "#25C096", # Accent groen
    "background": "#FFFFFF", 
    "panel": "#FFFFFF",      
    "border": "#E5E7EB",     
    "text": "#1F2937",       
    "text_light": "#FFFFFF", 
}

# APP_STYLE: De centrale CSS voor de applicatie
APP_STYLE = f"""
/* 1. ALGEMENE BASIS */
QWidget {{
    background: {COLORS['background']};
    color: {COLORS['text']};
    font-family: "Roboto", "Segoe UI", "Arial", sans-serif;
    font-size: 11pt;
}}

QMainWindow {{
    background: {COLORS['background']};
}}

/* 2. SIDEBAR */
QWidget#sidebar {{
    background: {COLORS['sidebar_bg']};
    color: {COLORS['text_light']};
    border-right: 1px solid {COLORS['primary']};
}}
QWidget#sidebar QLabel {{
    color: {COLORS['text_light']};
}}

/* Sidebar knoppen */
QWidget#sidebar QPushButton {{
    color: #cbd5e1;
    text-align: left;
    padding: 10px 15px;
    border: none;
    background: transparent;
    font-weight: 500;
}}
QWidget#sidebar QPushButton:hover {{
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border-radius: 6px;
}}
QWidget#sidebar QPushButton:checked {{
    background: rgba(255, 255, 255, 0.15);
    color: white;
    font-weight: bold;
    border-radius: 6px;
    border-left: 4px solid {COLORS['equans_green']};
}}

/* 3. ALGEMENE KNOPPEN */
QPushButton {{
    background: {COLORS['accent']};
    color: white;
    border-radius: 4px;
    padding: 6px 12px;
    border: none;
    font-weight: 600;
    min-height: 30px;
}}
QPushButton:hover {{
    background: {COLORS['accent_hover']};
}}
QPushButton:pressed {{
    background: #001a29;
}}
QPushButton:disabled {{
    background: #9ca3af;
    color: #f3f4f6;
}}

/* 4. COMPACTE KNOPPEN (Certificaat / Vaardigheid / Opslaan) */
/* AANGEPAST: Grotere tekst en meer hoogte */
QPushButton#small_btn {{
    background: {COLORS['accent']};
    color: white;
    border-radius: 4px;
    padding: 4px 16px;  /* Iets breder */
    min-height: 34px;   /* Hoger voor de grotere tekst */
    max-height: 42px;
    font-size: 12pt;    /* GROTERE TEKST */
    font-weight: bold;
}}
/* Zorgt dat geselecteerde radio buttons (Cert/Vaardigheid) duidelijk zijn */
QPushButton#small_btn:checked {{
    background: {COLORS['equans_green']}; 
    border: 1px solid {COLORS['primary']};
}}

/* 5. SECUNDAIRE KNOPPEN */
QPushButton#secondary_btn {{
    background: white;
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
}}
QPushButton#secondary_btn:hover {{
    background: #f9fafb;
    border-color: #d1d5db;
}}

/* 6. INPUT VELDEN & DROPDOWNS */
QLineEdit, QComboBox, QDateEdit, QTextEdit {{
    background: white;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 8px;
    color: {COLORS['text']};
    selection-background-color: {COLORS['accent']};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 2px solid {COLORS['accent']};
}}

/* 7. TABELLEN & LIJSTEN */
QListWidget, QTableWidget {{
    background: white;
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    gridline-color: #f3f4f6;
}}
QListWidget::item:selected, QTableWidget::item:selected {{
    background: #e0f2fe;
    color: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
}}
QHeaderView::section {{
    background-color: #f9fafb;
    color: {COLORS['text']};
    padding: 6px;
    border: none;
    border-bottom: 2px solid {COLORS['border']};
    font-weight: bold;
}}

/* 8. GROUPS & CARDS */
QGroupBox {{
    background: white;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 24px;
    padding: 16px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: {COLORS['primary']};
    font-weight: bold;
    background: white;
}}

/* 9. TOOLTIPS */
QToolTip {{
    background-color: {COLORS['primary']};
    color: white;
    border: 1px solid white;
    padding: 4px;
    border-radius: 4px;
}}

/* 10. SCROLLBARS */
QScrollBar:vertical {{
    border: none;
    background: #f9fafb;
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: #d1d5db;
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: #9ca3af;
}}
"""

def load_logo_icon(size: int = 24) -> QIcon:
    path_png = ASSETS_DIR / "equans_logo.png"
    if path_png.exists():
        return QIcon(str(path_png))

    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    brush = QBrush(QColor(COLORS["accent"]))
    painter.setBrush(brush)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size - 1, size - 1)

    painter.setPen(QColor("white"))
    font = painter.font()
    font.setBold(True)
    font.setFamily("Roboto")
    font.setPointSize(max(8, int(size / 2.4)))
    painter.setFont(font)
    rect = pix.rect()
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "EQ")

    painter.end()
    return QIcon(pix)