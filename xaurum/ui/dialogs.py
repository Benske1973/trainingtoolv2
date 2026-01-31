# ===============================================================
# BESTAND: xaurum/ui/dialogs.py
# ===============================================================

# import os
# import pandas as pd
# from PyQt6.QtWidgets import (
    # QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    # QComboBox, QLineEdit, QDateEdit, QCheckBox, QMessageBox,
    # QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox,
    # QInputDialog
# )
# from PyQt6.QtCore import Qt, QDate
# from PyQt6.QtGui import QColor

import os
import pandas as pd
from typing import List, Dict, Any, Optional  # <--- DEZE MOET ERBIJ
from sqlalchemy import text # Als je deze gebruikt voor de locaties

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QLineEdit, QDateEdit, QCheckBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox,
    QInputDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

# Stylesheet voor knoppen om consistentie te bewaren met de rest van de app
BTN_STYLE_GREEN = "QPushButton { background-color: #70bd95; border: 1px solid #5da683; color: white !important; padding: 8px 16px; font-weight: bold; min-width: 120px; }"
BTN_STYLE_BLUE = "QPushButton { background-color: #005EB8; border: 1px solid #004a91; color: white !important; padding: 8px 16px; font-weight: bold; min-width: 120px; }"
BTN_STYLE_WHITE = "QPushButton { background-color: #f8fafc; border: 1px solid #cbd5e1; color: #334155 !important; padding: 8px 16px; min-width: 100px; }"

# ===============================================================
# 1. INGESCHREVEN WIZARD
# ===============================================================
class IngeschrevenWizard(QDialog):
    def __init__(self, task_row: pd.Series, engine, parent=None):
        super().__init__(parent)
        self.task_row = task_row
        self.engine = engine
        self.parent_widget = parent
        self.setWindowTitle("Opleiding inschrijven")
        self.setFixedSize(450, 380)
        self.setStyleSheet("QDialog { background-color: white; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        medewerker = task_row.get("MedewerkerNaam", "")
        cert = task_row.get("CertName", "")

        # Info Sectie
        info = QLabel(f"<b>Medewerker:</b> {medewerker}<br><b>Opleiding:</b> {cert}")
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #f1f5f9; padding: 12px; border: 1px solid #e2e8f0; border-radius: 4px; color: #1e293b;")
        layout.addWidget(info)

        # STAP 1: Xaurum integratie
        self.btn_xaurum = QPushButton("🔗 Stap 1: Open Xaurum & Zoek")
        self.btn_xaurum.setStyleSheet(BTN_STYLE_BLUE)
        self.btn_xaurum.clicked.connect(self.handle_xaurum_action)
        layout.addWidget(self.btn_xaurum)

        # STAP 2: Datum
        hbox_date = QHBoxLayout()
        hbox_date.addWidget(QLabel("Stap 2: Inschrijfdatum:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet("border: 1px solid #cbd5e1; padding: 4px;")
        hbox_date.addWidget(self.date_edit)
        layout.addLayout(hbox_date)

        # STAP 3: Locatie
        hbox_loc = QHBoxLayout()
        hbox_loc.addWidget(QLabel("Stap 3: Locatie:"))
        self.cb_location = QComboBox()
        self.load_locations()
        self.cb_location.setStyleSheet("border: 1px solid #cbd5e1; padding: 4px;")
        
        self.btn_add_loc = QPushButton("➕")
        self.btn_add_loc.setFixedWidth(35)
        self.btn_add_loc.setStyleSheet(BTN_STYLE_WHITE)
        self.btn_add_loc.clicked.connect(self.add_new_location)
        
        hbox_loc.addWidget(self.cb_location, 1)
        hbox_loc.addWidget(self.btn_add_loc)
        layout.addLayout(hbox_loc)

        # Opmerking
        layout.addWidget(QLabel("Opmerking:"))
        self.txt_comment = QLineEdit()
        self.txt_comment.setPlaceholderText("Bijv. tijdstip of specifieke instructies")
        self.txt_comment.setStyleSheet("border: 1px solid #cbd5e1; padding: 6px;")
        layout.addWidget(self.txt_comment)

        layout.addStretch()

        # Knoppen onderaan
        hbox_btns = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuleren")
        self.btn_cancel.setStyleSheet(BTN_STYLE_WHITE)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton("Bevestig Inschrijving")
        self.btn_ok.setStyleSheet(BTN_STYLE_GREEN)
        self.btn_ok.clicked.connect(self.accept_with_validation)

        hbox_btns.addWidget(self.btn_cancel)
        hbox_btns.addStretch()
        hbox_btns.addWidget(self.btn_ok)
        layout.addLayout(hbox_btns)

    def handle_xaurum_action(self):
        if self.parent_widget and hasattr(self.parent_widget, "on_open_xaurum"):
            self.parent_widget.on_open_xaurum()

    def load_locations(self):
        try:
            query = "SELECT LocatieNaam FROM dbo.TM_Ref_TrainingLocation ORDER BY LocatieNaam"
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn)
                self.cb_location.clear()
                self.cb_location.addItems(df["LocatieNaam"].tolist())
        except:
            self.cb_location.addItems(['Technicity', 'ECS Wetteren', 'ECS Brussels', 'Zandvliet'])

    def add_new_location(self):
        new_loc, ok = QInputDialog.getText(self, "Nieuwe Locatie", "Naam van het opleidingscentrum:")
        if ok and new_loc.strip():
            try:
                with self.engine.begin() as conn:
                    conn.execute(text("INSERT INTO dbo.TM_Ref_TrainingLocation (LocatieNaam) VALUES (:loc)"), {"loc": new_loc.strip()})
                self.load_locations()
                self.cb_location.setCurrentText(new_loc.strip())
            except Exception as e:
                QMessageBox.warning(self, "Fout", f"Kon locatie niet toevoegen: {e}")

    def accept_with_validation(self):
        self.final_data = {
            "datum": self.date_edit.date().toPyDate(),
            "locatie": self.cb_location.currentText(),
            "commentaar": self.txt_comment.text().strip()
        }
        self.accept()

# ===============================================================
# 2. SELF-REGISTERED DIALOG
# ===============================================================
class SelfRegisteredDialog(QDialog):
    def __init__(self, medewerker: str, cert: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zelf ingeschreven")
        self.setFixedSize(500, 300)
        self.setStyleSheet("QDialog { background-color: white; }")

        layout = QVBoxLayout(self)

        info = QLabel(f"<b>Medewerker:</b> {medewerker}<br><b>Opleiding:</b> {cert}")
        info.setStyleSheet("padding: 10px; background-color: #f0fdf4; border: 1px solid #bbf7d0; color: #166534;")
        layout.addWidget(info)

        # Datum
        hbox_date = QHBoxLayout()
        self.date_checkbox = QCheckBox("Ik weet de datum:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setEnabled(False)
        self.date_checkbox.toggled.connect(self.date_edit.setEnabled)
        hbox_date.addWidget(self.date_checkbox)
        hbox_date.addWidget(self.date_edit)
        layout.addLayout(hbox_date)

        # Locatie
        layout.addWidget(QLabel("Locatie (optioneel):"))
        self.loc_edit = QLineEdit()
        self.loc_edit.setPlaceholderText("Bijv. 'Online' of 'Extern'")
        layout.addWidget(self.loc_edit)

        layout.addStretch()

        hbox_btns = QHBoxLayout()
        btn_cancel = QPushButton("Annuleren")
        btn_cancel.setStyleSheet(BTN_STYLE_WHITE)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Markeer als Zelf Ingeschreven")
        btn_ok.setStyleSheet(BTN_STYLE_BLUE)
        btn_ok.clicked.connect(self.accept)

        hbox_btns.addWidget(btn_cancel)
        hbox_btns.addStretch()
        hbox_btns.addWidget(btn_ok)
        layout.addLayout(hbox_btns)

    def get_date(self): return self.date_edit.date().toPyDate() if self.date_checkbox.isChecked() else None
    def get_location(self): return self.loc_edit.text().strip()

# ===============================================================
# 3. REPLACEMENT CANDIDATES DIALOG
# ===============================================================
class ReplacementCandidatesDialog(QDialog):
    def __init__(self, candidates: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mogelijke vervangers")
        self.resize(1000, 550)
        self.setStyleSheet("QDialog { background-color: white; }")

        layout = QVBoxLayout(self)

        intro = QLabel("Kies een vervanger die deze plek in Xaurum kan overnemen. Gebruik de Mail-knop om de Academy te informeren.")
        intro.setStyleSheet("color: #64748b; margin-bottom: 5px;")
        layout.addWidget(intro)

        if not candidates:
            lbl = QLabel("Geen geschikte vervangers gevonden.")
            lbl.setStyleSheet("font-weight:bold; color:#ef4444; padding: 20px;")
            layout.addWidget(lbl)
        else:
            self.table = QTableWidget(len(candidates), 7, self)
            self.table.setHorizontalHeaderLabels(["Medewerker", "SAP NR", "Afdeling", "Type", "Datum", "Locatie", "Match"])
            
            for row_idx, c in enumerate(candidates):
                # Data verrijken met SAPNR uit de candidate data
                sap = str(c.get("sapnr", "")).replace(".0", "")
                
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(c.get("name", ""))))
                self.table.setItem(row_idx, 1, QTableWidgetItem(sap))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(c.get("costcenter", ""))))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(c.get("type", ""))))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(c.get("date", ""))))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(c.get("location", ""))))
                
                match_val = "Perfect" if c.get("same_costcenter") else "Beschikbaar"
                self.table.setItem(row_idx, 6, QTableWidgetItem(match_val))

                # Kleurcodering
                if c.get("same_costcenter"): bg = QColor(240, 253, 244) # Groen
                elif "planner" in str(c.get("type")).lower(): bg = QColor(239, 246, 255) # Blauw
                else: bg = QColor(255, 255, 255)

                for col in range(7):
                    item = self.table.item(row_idx, col)
                    if item: item.setBackground(bg)

            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            layout.addWidget(self.table)

        # Button Box met correcte styling
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.setStyleSheet(f"""
            QPushButton {{ 
                background-color: #70bd95; color: white !important; border: 1px solid #5da683; 
                padding: 8px 20px; font-weight: bold; min-width: 100px;
            }}
            QPushButton[text="Cancel"], QPushButton[text="Annuleren"] {{ 
                background-color: #f8fafc; color: #334155 !important; border: 1px solid #cbd5e1; 
            }}
        """)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

# # ===============================================================
# # Training Management System v10 - PyQt6 (FIXED VERSION)
# # Dashboard + Medewerkerbeheer + Planner/To-do (automatisch + zwevend)
# # ===============================================================

# import os
# import math
# import webbrowser
# import re

# from pathlib import Path
# from datetime import datetime
# from typing import Dict, List, Optional, Tuple, Any
# from PyQt6.QtGui import QDesktopServices, QColor
# from PyQt6.QtCore import QUrl
# from sqlalchemy import create_engine, text

# import pandas as pd

# # in trainingtest.py (bovenaan bij imports)


# from PyQt6.QtWidgets import (
    # QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    # QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox,
    # QScrollArea, QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
    # QDialog, QDialogButtonBox, QToolButton, QButtonGroup,
    # QStackedWidget, QFrame, QDateEdit, QTextEdit, QInputDialog,
    # QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSizePolicy,
    # )

# from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF, QDate, QUrl
# from PyQt6.QtGui import (
    # QIcon, QPainter, QPixmap, QColor,
    # QPen, QPainterPath, QRadialGradient,
    # QDesktopServices, QBrush, QLinearGradient, QFontMetrics, 
# )
# from dataclasses import dataclass

# # ===============================================================
# # PADEN / SETTINGS
# # ===============================================================

# from xaurum.theme import APP_STYLE, load_logo_icon
# from xaurum.config import *
# from xaurum.utils import *
# from xaurum.ui.widgets import *
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
    # from xaurum.core.datastore import DataStore

# # ===============================================================
# # INGESCHREVEN WIZARD
# # ===============================================================
# class IngeschrevenWizard(QDialog):
    # def __init__(self, task_row: pd.Series, engine, parent=None):
        # super().__init__(parent)
        # self.task_row = task_row
        # self.engine = engine
        # self.parent_widget = parent
        # self.setWindowTitle("Opleiding inschrijven")
        # self.setFixedSize(450, 350) # Iets groter gemaakt voor de Xaurum knop
        # self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # layout = QVBoxLayout(self)

        # medewerker = task_row.get("MedewerkerNaam", "")
        # cert = task_row.get("CertName", "")

        # # Info Sectie
        # info = QLabel(f"<b>Medewerker:</b> {medewerker}<br><b>Opleiding:</b> {cert}")
        # info.setWordWrap(True)
        # info.setStyleSheet("background-color: #f8f9fa; padding: 10px; border: 1px solid #ddd; border-radius: 5px;")
        # layout.addWidget(info)

        # # STAP 1: Xaurum integratie knop
        # self.btn_xaurum = QPushButton("🔗 Stap 1: Open Xaurum & Kopieer Naam")
        # self.btn_xaurum.setStyleSheet("background-color: #005596; color: white; font-weight: bold; height: 35px;")
        # self.btn_xaurum.clicked.connect(self.handle_xaurum_action)
        # layout.addWidget(self.btn_xaurum)

        # layout.addSpacing(10)

        # # Datum selectie
        # hbox_date = QHBoxLayout()
        # hbox_date.addWidget(QLabel("Stap 2: Inschrijfdatum:"))
        # self.date_edit = QDateEdit()
        # self.date_edit.setDate(QDate.currentDate())
        # self.date_edit.setCalendarPopup(True)
        # hbox_date.addWidget(self.date_edit)
        # layout.addLayout(hbox_date)

        # # Locatie selectie met Dropdown en Toevoeg-knop
        # hbox_loc = QHBoxLayout()
        # hbox_loc.addWidget(QLabel("Stap 3: Locatie:"))
        # self.cb_location = QComboBox()
        # self.load_locations()
        
        # self.btn_add_loc = QPushButton("➕")
        # self.btn_add_loc.setFixedWidth(35)
        # self.btn_add_loc.setToolTip("Nieuwe locatie toevoegen aan SQL")
        # self.btn_add_loc.clicked.connect(self.add_new_location)
        
        # hbox_loc.addWidget(self.cb_location, 1)
        # hbox_loc.addWidget(self.btn_add_loc)
        # layout.addLayout(hbox_loc)

        # # Opmerking veld
        # hbox_comm = QHBoxLayout()
        # hbox_comm.addWidget(QLabel("Opmerking:"))
        # self.txt_comment = QLineEdit()
        # self.txt_comment.setPlaceholderText("Bijv. tijdstip of specifieke instructies")
        # hbox_comm.addWidget(self.txt_comment)
        # layout.addLayout(hbox_comm)

        # layout.addStretch()

        # # Knoppen onderaan
        # hbox_btns = QHBoxLayout()
        # btn_cancel = QPushButton("Annuleren")
        # btn_cancel.clicked.connect(self.reject)

        # btn_ok = QPushButton("Markeer als ingeschreven")
        # btn_ok.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; height: 35px;")
        # btn_ok.clicked.connect(self.accept_with_validation)

        # hbox_btns.addStretch()
        # hbox_btns.addWidget(btn_cancel)
        # hbox_btns.addWidget(btn_ok)
        # layout.addLayout(hbox_btns)

    # def handle_xaurum_action(self):
        # """Roept de Xaurum helper aan in de hoofdtab (todo.py)."""
        # if self.parent_widget and hasattr(self.parent_widget, "on_open_xaurum"):
            # self.parent_widget.on_open_xaurum()

    # def load_locations(self):
        # """Laadt de lijst met opleidingscentra uit de SQL database."""
        # try:
            # query = "SELECT LocatieNaam FROM dbo.TM_Ref_TrainingLocation ORDER BY LocatieNaam"
            # with self.engine.connect() as conn:
                # df = pd.read_sql(text(query), conn)
                # self.cb_location.clear()
                # self.cb_location.addItems(df["LocatieNaam"].tolist())
        # except Exception as e:
            # # Fallback als de tabel nog niet bestaat of SQL plat ligt
            # self.cb_location.addItems(['Technicity', 'ECS Wetteren', 'ECS Brussels'])

    # def add_new_location(self):
        # """Voegt on-the-fly een nieuw opleidingscentrum toe aan SQL."""
        # new_loc, ok = QInputDialog.getText(self, "Nieuwe Locatie", "Naam van het opleidingscentrum:")
        # if ok and new_loc.strip():
            # try:
                # with self.engine.begin() as conn:
                    # conn.execute(
                        # text("INSERT INTO dbo.TM_Ref_TrainingLocation (LocatieNaam) VALUES (:loc)"),
                        # {"loc": new_loc.strip()}
                    # )
                # self.load_locations()
                # self.cb_location.setCurrentText(new_loc.strip())
            # except Exception as e:
                # QMessageBox.warning(self, "Fout", f"Kon locatie niet toevoegen: {e}")

    # def accept_with_validation(self):
        # datum = self.date_edit.date().toPyDate()
        # locatie = self.cb_location.currentText()
        # commentaar = self.txt_comment.text().strip()

        # if not locatie:
            # QMessageBox.warning(self, "Fout", "Selecteer of voeg een locatie toe!")
            # return

        # # Gegevens teruggeven aan de parent
        # self.final_data = {
            # "datum": datum,
            # "locatie": locatie,
            # "commentaar": commentaar
        # }
        # self.accept()



# # ===============================================================
# # SELF-REGISTERED DIALOG
# # ===============================================================

# class SelfRegisteredDialog(QDialog):
    # """
    # Dialog voor het markeren van een taak als 'zelf ingeschreven' door de medewerker.
    # Vraagt optioneel om datum en locatie.
    # """
    # def __init__(self, medewerker: str, cert: str, parent=None):
        # super().__init__(parent)
        # self.setWindowTitle("Markeer als zelf ingeschreven")
        # self.setFixedSize(500, 280)
        # self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # layout = QVBoxLayout(self)

        # # Info label
        # info = QLabel(
            # f"Medewerker: {medewerker}\n"
            # f"Opleiding: {cert}\n\n"
            # f"Deze medewerker heeft zich zelf ingeschreven voor deze opleiding.\n"
            # f"Vul optioneel de inschrijfdetails in om dubbele registraties te voorkomen."
        # )
        # info.setWordWrap(True)
        # info.setStyleSheet("font-size: 12px; color: #333; margin-bottom: 10px;")
        # layout.addWidget(info)

        # # Datum veld (optioneel)
        # hbox_date = QHBoxLayout()
        # hbox_date.addWidget(QLabel("Inschrijfdatum (optioneel):"))
        # self.date_edit = QDateEdit()
        # self.date_edit.setDate(QDate.currentDate())
        # self.date_edit.setCalendarPopup(True)
        # self.date_checkbox = QCheckBox("Datum opgeven")
        # self.date_checkbox.setChecked(False)
        # self.date_edit.setEnabled(False)
        # self.date_checkbox.toggled.connect(lambda checked: self.date_edit.setEnabled(checked))
        # hbox_date.addWidget(self.date_checkbox)
        # hbox_date.addWidget(self.date_edit)
        # layout.addLayout(hbox_date)

        # # Locatie veld (optioneel)
        # hbox_loc = QHBoxLayout()
        # hbox_loc.addWidget(QLabel("Locatie (optioneel):"))
        # self.loc_edit = QLineEdit()
        # self.loc_edit.setPlaceholderText("Bijv. 'Online' of 'Externe training'")
        # hbox_loc.addWidget(self.loc_edit)
        # layout.addLayout(hbox_loc)

        # # Uitleg
        # explanation = QLabel(
            # "💡 Door deze taak te markeren als 'Zelf ingeschreven' voorkom je dat "
            # "andere beheerders deze medewerker opnieuw inschrijven voor dezelfde opleiding."
        # )
        # explanation.setWordWrap(True)
        # explanation.setStyleSheet("font-size: 11px; color: #666; margin-top: 10px;")
        # layout.addWidget(explanation)

        # # Buttons
        # hbox_btns = QHBoxLayout()
        # btn_cancel = QPushButton("Annuleren")
        # btn_cancel.clicked.connect(self.reject)

        # btn_ok = QPushButton("Markeer als zelf ingeschreven")
        # btn_ok.setStyleSheet(
            # "QPushButton { background-color: #007bff; color: white; font-weight: bold; }"
        # )
        # btn_ok.clicked.connect(self.accept)

        # hbox_btns.addStretch()
        # hbox_btns.addWidget(btn_cancel)
        # hbox_btns.addWidget(btn_ok)
        # layout.addLayout(hbox_btns)

    # def get_date(self):
        # """Return the selected date if checkbox is checked, otherwise None."""
        # if self.date_checkbox.isChecked():
            # return self.date_edit.date().toPyDate()
        # return None

    # def get_location(self):
        # """Return the location text, or empty string if not filled."""
        # return self.loc_edit.text().strip()


# # ===============================================================
# # REPLACEMENT CANDIDATES DIALOG
# # ===============================================================

# class ReplacementCandidatesDialog(QDialog):
    # def __init__(self, candidates: List[Dict[str, Any]], parent=None):
        # super().__init__(parent)
        # self.setWindowTitle("Mogelijke vervangers voor deze opleiding")
        # self.resize(900, 500)

        # layout = QVBoxLayout(self)

        # intro = QLabel(
            # "Overzicht van medewerkers die mogelijk in aanmerking komen om "
            # "deze opleiding over te nemen.\n"
            # "Bronnen:\n"
            # "• training_req: ingepland binnen 6 maanden\n"
            # "• planner/to-do: reeds ingeschreven voor dezelfde opleiding\n"
            # "• planner/to-do: open taken voor dezelfde opleiding (nog niet ingeschreven)."
        # )
        # intro.setWordWrap(True)
        # layout.addWidget(intro)

        # if not candidates:
            # lbl = QLabel("Geen vervangers gevonden op basis van de huidige gegevens.")
            # lbl.setStyleSheet("font-weight:bold; color:#aa0000;")
            # layout.addWidget(lbl)
        # else:
            # table = QTableWidget(len(candidates), 6, self)
            # table.setHorizontalHeaderLabels([
                # "Medewerker",
                # "Afdeling",
                # "Pool",
                # "Type",
                # "Datum",
                # "Locatie / extra",
            # ])

            # for row_idx, c in enumerate(candidates):
                # table.setItem(row_idx, 0, QTableWidgetItem(str(c.get("name", ""))))
                # table.setItem(row_idx, 1, QTableWidgetItem(str(c.get("costcenter", ""))))
                # table.setItem(row_idx, 2, QTableWidgetItem(str(c.get("pool", ""))))
                # table.setItem(row_idx, 3, QTableWidgetItem(str(c.get("type", ""))))
                # table.setItem(row_idx, 4, QTableWidgetItem(str(c.get("date", ""))))
                # extra = c.get("location", "")
                # if c.get("staff_id"):
                    # extra = f"{extra} (ID: {c['staff_id']})".strip()
                # table.setItem(row_idx, 5, QTableWidgetItem(str(extra)))

                # same_cc = bool(c.get("same_costcenter", False))
                # type_txt = str(c.get("type", ""))

                # bg = None
                # if same_cc:
                    # bg = QColor(220, 245, 220)
                # elif "Binnen 6 maanden" in type_txt:
                    # bg = QColor(255, 245, 225)
                # elif "Reeds ingeschreven" in type_txt:
                    # bg = QColor(225, 235, 255)
                # elif "Open in planner" in type_txt:
                    # bg = QColor(245, 245, 245)

                # if bg is not None:
                    # for col in range(6):
                        # item = table.item(row_idx, col)
                        # if item:
                            # item.setBackground(bg)

            # table.horizontalHeader().setStretchLastSection(True)
            # table.horizontalHeader().setSectionResizeMode(
                # QHeaderView.ResizeMode.Stretch
            # )
            # table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            # layout.addWidget(table)

        # btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        # btn_box.rejected.connect(self.reject)
        # btn_box.accepted.connect(self.accept)
        # layout.addWidget(btn_box)


