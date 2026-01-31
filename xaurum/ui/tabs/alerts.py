# ===============================================================
# BESTAND: xaurum/ui/tabs/alerts.py
# ===============================================================

import os
import math
import webbrowser
import re

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from PyQt6.QtGui import QDesktopServices, QColor
from PyQt6.QtCore import QUrl
from sqlalchemy import create_engine, text

import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox,
    QScrollArea, QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
    QDialog, QDialogButtonBox, QToolButton, QButtonGroup,
    QStackedWidget, QFrame, QDateEdit, QTextEdit, QInputDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSizePolicy,
    )

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF, QDate, QUrl
from PyQt6.QtGui import (
    QIcon, QPainter, QPixmap, QColor,
    QPen, QPainterPath, QRadialGradient,
    QDesktopServices, QBrush, QLinearGradient, QFontMetrics, 
)
from dataclasses import dataclass

# ===============================================================
# PADEN / SETTINGS
# ===============================================================

from xaurum.theme import APP_STYLE, load_logo_icon
from xaurum.config import *
from xaurum.utils import *
from xaurum.ui.widgets import *
from xaurum.ui.dialogs import *
from xaurum.core.datastore import DataStore

# ===============================================================
# ALERTS TAB
# ===============================================================

class AlertsTab(QWidget):
    def __init__(self, data_store: DataStore):
        super().__init__()
        self.data = data_store
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("🔔 Alerts – Opleidingen binnen 3 weken")
        # AANGEPAST: Font Segoe UI en kleur #00263D
        title.setStyleSheet("font-family: 'Segoe UI'; font-size: 22px; font-weight: bold; color: #00263D;")
        layout.addWidget(title)

        self.subtitle = QLabel(
            "Overzicht van alle geplande opleidingen in de komende 21 dagen\n"
            "(gebaseerd op Training_Req_Xaurum_ready.xlsx)."
        )
        self.subtitle.setStyleSheet("font-family: 'Segoe UI'; color: #64748b; font-size: 12px;")
        layout.addWidget(self.subtitle)

        self.lbl_stats = QLabel("")
        # AANGEPAST: Font Segoe UI en kleur #00263D
        self.lbl_stats.setStyleSheet("font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; color: #00263D;")
        layout.addWidget(self.lbl_stats)

        self.list_alerts = QListWidget()
        self.list_alerts.setAlternatingRowColors(True)
        self.list_alerts.setStyleSheet("""
            QListWidget { 
                border: 1px solid #dee2e6; 
                border-radius: 6px; 
                font-family: 'Segoe UI'; 
                font-size: 13px; 
            }
            QListWidget::item { padding: 6px; }
            QListWidget::item:selected { background: #e3f2fd; color: black; }
        """)
        layout.addWidget(self.list_alerts, stretch=1)

        self.info_label = QLabel(
            "🔴 = binnen 7 dagen • 🟠 = binnen 14 dagen • 🟡 = binnen 21 dagen"
        )
        self.info_label.setStyleSheet("font-family: 'Segoe UI'; color: #6c757d; font-size: 11px;")
        layout.addWidget(self.info_label)

    def refresh(self):
        df = self.data.get_upcoming_trainings(days=21)
        self.list_alerts.clear()

        cc_text = self.data.active_costcenter if self.data.active_costcenter else "alle afdelingen"
        if self.data.full_access and self.data.active_costcenter is None:
            scope = "volledig beheer (alle costcenters)"
        else:
            scope = f"filter op costcenter: {cc_text}"
        self.subtitle.setText(
            f"Opleidingen binnen 21 dagen – {scope}"
        )

        if df is None or df.empty:
            self.lbl_stats.setText("Geen geplande opleidingen binnen 3 weken.")
            self.list_alerts.addItem("✅ Geen opleidingen ingepland binnen 21 dagen.")
            return

        today = pd.Timestamp.today().normalize()
        date_col = "ScheduledDateParsed"

        total = len(df)
        self.lbl_stats.setText(f"{total} geplande opleiding(en) binnen 21 dagen.")

        for _, r in df.iterrows():
            dt = r.get(date_col, pd.NaT)
            try:
                dt = pd.to_datetime(dt)
            except Exception:
                dt = pd.NaT

            if pd.isna(dt):
                date_str = "datum onbekend"
                days_left = None
            else:
                date_str = dt.strftime("%d-%m-%Y")
                days_left = (dt.normalize() - today).days

            naam = str(r.get("MedewerkerNaam", "") or "").strip()
            if not naam:
                naam = str(r.get("staffGID", "") or "").strip()
            cert = str(r.get("CertName", "") or "").strip()
            loc = str(r.get("LocatieAlert", "") or "").strip()
            bron = str(r.get("Bron", "Onbekend") or "Onbekend").strip()

            # Voeg bron toe aan display voor duidelijkheid
            base = f"{date_str} – {naam} – {cert}"
            if loc:
                base += f" ({loc})"
            base += f" [{bron}]"

            if days_left is None:
                icon = "⚪"
                bg = QColor(240, 240, 240)
            elif days_left <= 7:
                icon = "🔴"
                bg = QColor(255, 210, 210)
            elif days_left <= 14:
                icon = "🟠"
                bg = QColor(255, 235, 205)
            else:
                icon = "🟡"
                bg = QColor(255, 255, 210)

            item = QListWidgetItem(f"{icon} {base}")
            item.setBackground(bg)

            tip_parts = [f"Startdatum: {date_str}"]
            if loc:
                tip_parts.append(f"Locatie: {loc}")
            tip_parts.append(f"Bron: {bron}")
            status = str(r.get("RequestStatus", "") or "").strip()
            if status:
                tip_parts.append(f"Status: {status}")
            cc = str(r.get("staffCOSTCENTER315", "") or "").strip()
            if cc:
                tip_parts.append(f"Costcenter: {cc}")
            item.setToolTip(" | ".join(tip_parts))

            self.list_alerts.addItem(item)