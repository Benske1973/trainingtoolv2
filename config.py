# ===============================================================
# Training Management System v10 - PyQt6 (FIXED VERSION)
# Dashboard + Medewerkerbeheer + Planner/To-do (automatisch + zwevend)
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

# in trainingtest.py (bovenaan bij imports)


from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox,
    QScrollArea, QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
    QDialog, QDialogButtonBox, QToolButton, QButtonGroup,
    QStackedWidget, QFrame, QDateEdit, QTextEdit, QInputDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSizePolicy, QProgressDialog,
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
# CONFIG TAB - VOLLEDIG MET XAURUM RAPPORT
# ===============================================================

class ConfigTab(QWidget):
    def __init__(self, data_store:  DataStore, parent_window=None):
        super().__init__()
        self.data = data_store
        self.parent_window = parent_window
        self.rapport_df = None  # Voor opslag van Xaurum rapport data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # ══════════════════════════════════════════════════════════════
        # TITEL
        # ══════════════════════════════════════════════════════════════
        title = QLabel("⚙️ Configuratie & Controle (Superuser)")
        title.setStyleSheet("font-size: 20px;font-weight:bold;color:#005EB8;")
        layout.addWidget(title)

        desc = QLabel(
            "Via deze tab kun je de configuratiebestanden beheren en data-integriteit controleren.\n"
            "⚠️ Let op: wijzigingen hebben directe impact op de applicatie."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size:12px;color:#495057;")
        layout.addWidget(desc)

        layout.addSpacing(12)

        # ══════════════════════════════════════════════════════════════
        # SECTIE 1: DATA CONTROLE TOOLS
        # ══════════════════════════════════════════════════════════════
        controle_group = QGroupBox("🔍 Data Controle Tools")
        controle_group. setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #0ea5e9;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background: #f0f9ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #0369a1;
            }
        """)
        controle_layout = QVBoxLayout(controle_group)
        controle_layout.setSpacing(8)

        # ──────────────────────────────────────────────────────────────
        # 1. CERTIFICATEN CHECK
        # ──────────────────────────────────────────────────────────────
        cert_check_widget = QWidget()
        cert_check_layout = QVBoxLayout(cert_check_widget)
        cert_check_layout.setContentsMargins(0, 0, 0, 0)
        cert_check_layout.setSpacing(4)

        lbl_cert_check = QLabel(
            "📜 <b>Certificaten Controle</b><br>"
            "Controleert of alle CertNames uit 'Certificates' en 'Training_Req' "
            "voorkomen in Master_Certificaten. xlsx"
        )
        lbl_cert_check.setWordWrap(True)
        lbl_cert_check.setTextFormat(Qt.TextFormat.RichText)
        lbl_cert_check.setStyleSheet("font-size:11px;color:#374151;background: transparent;")
        cert_check_layout.addWidget(lbl_cert_check)

        btn_check_certs = QPushButton("🔎 Controleer Certificaten tegen Master")
        btn_check_certs.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_check_certs.setStyleSheet("""
            QPushButton {
                background:  qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                font-weight: bold;
                padding: 10px 16px;
                border:  none;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop: 0 #60a5fa, stop:1 #3b82f6);
            }
            QPushButton:pressed {
                background: #1e40af;
            }
        """)
        btn_check_certs.clicked.connect(self.on_check_certnames)
        cert_check_layout.addWidget(btn_check_certs)

        controle_layout.addWidget(cert_check_widget)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("background:#cbd5e1;margin:8px 0;")
        controle_layout.addWidget(sep1)

        # ──────────────────────────────────────────────────────────────
        # 2. COMPETENTIES CHECK
        # ──────────────────────────────────────────────────────────────
        comp_check_widget = QWidget()
        comp_check_layout = QVBoxLayout(comp_check_widget)
        comp_check_layout.setContentsMargins(0, 0, 0, 0)
        comp_check_layout.setSpacing(4)

        lbl_comp_check = QLabel(
            "🎯 <b>Competenties Controle</b><br>"
            "Controleert of alle Competence-namen uit 'Competences' "
            "voorkomen in Master_Competenties.xlsx"
        )
        lbl_comp_check.setWordWrap(True)
        lbl_comp_check.setTextFormat(Qt.TextFormat.RichText)
        lbl_comp_check.setStyleSheet("font-size:11px;color:#374151;background:transparent;")
        comp_check_layout.addWidget(lbl_comp_check)

        btn_check_comps = QPushButton("🔎 Controleer Competenties tegen Master")
        btn_check_comps.setCursor(Qt.CursorShape. PointingHandCursor)
        btn_check_comps.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                color: white;
                font-weight: bold;
                padding: 10px 16px;
                border: none;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a78bfa, stop: 1 #8b5cf6);
            }
            QPushButton:pressed {
                background:  #6d28d9;
            }
        """)
        btn_check_comps.clicked.connect(self.on_check_competences)
        comp_check_layout.addWidget(btn_check_comps)

        controle_layout.addWidget(comp_check_widget)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape. HLine)
        sep2.setStyleSheet("background:#cbd5e1;margin:8px 0;")
        controle_layout.addWidget(sep2)

        # ──────────────────────────────────────────────────────────────
        # 3. TOEKOMSTIGE TRAININGEN CHECK
        # ──────────────────────────────────────────────────────────────
        training_check_widget = QWidget()
        training_check_layout = QVBoxLayout(training_check_widget)
        training_check_layout.setContentsMargins(0, 0, 0, 0)
        training_check_layout.setSpacing(4)

        lbl_training_check = QLabel(
            "📅 <b>Toekomstige Trainingen Controle</b><br>"
            "Controleert of alle toekomstige inschrijvingen (Training_Req) "
            "als 'Nodig' staan in Medewerker_Certificaat_Config.xlsx"
        )
        lbl_training_check.setWordWrap(True)
        lbl_training_check.setTextFormat(Qt.TextFormat. RichText)
        lbl_training_check.setStyleSheet("font-size:11px;color:#374151;background:transparent;")
        training_check_layout.addWidget(lbl_training_check)

        btn_check_trainings = QPushButton("🔎 Controleer Toekomstige Trainingen")
        btn_check_trainings. setCursor(Qt.CursorShape.PointingHandCursor)
        btn_check_trainings.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop: 0 #10b981, stop:1 #059669);
                color: white;
                font-weight: bold;
                padding: 10px 16px;
                border: none;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34d399, stop:1 #10b981);
            }
            QPushButton:pressed {
                background: #047857;
            }
        """)
        btn_check_trainings.clicked.connect(self. on_check_future_trainings)
        training_check_layout.addWidget(btn_check_trainings)

        controle_layout.addWidget(training_check_widget)

        layout.addWidget(controle_group)

        layout.addSpacing(8)

        # ══════════════════════════════════════════════════════════════
        # SECTIE 2: XAURUM DATA KWALITEIT RAPPORT
        # ══════════════════════════════════════════════════════════════
        xaurum_group = QGroupBox("📊 Xaurum Data Kwaliteit Rapport")
        xaurum_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #f59e0b;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background: #fffbeb;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #d97706;
            }
        """)
        xaurum_layout = QVBoxLayout(xaurum_group)
        xaurum_layout.setSpacing(8)

        # Beschrijving
        lbl_xaurum_desc = QLabel(
            "🔍 <b>Xaurum Configuratie Analyse</b><br>"
            "Analyseert de Xaurum data op configuratiefouten zoals: <br>"
            "• Medewerkers met zowel <b>Basis</b> als <b>Refresh</b> op Nodig=1<br>"
            "• Taalvariaties (NL/FR) voor dezelfde opleiding<br>"
            "• Controleert verloopdatum om juiste aanbeveling te geven (>2 jaar = Basis, <2 jaar = Refresh)"
        )
        lbl_xaurum_desc.setWordWrap(True)
        lbl_xaurum_desc. setTextFormat(Qt.TextFormat.RichText)
        lbl_xaurum_desc. setStyleSheet("font-size: 11px;color:#374151;background:transparent;")
        xaurum_layout.addWidget(lbl_xaurum_desc)

        # Knoppen rij
        xaurum_btn_layout = QHBoxLayout()

        btn_xaurum_rapport = QPushButton("📊 Genereer Xaurum Rapport")
        btn_xaurum_rapport.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_xaurum_rapport.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f59e0b, stop:1 #d97706);
                color: white;
                font-weight: bold;
                padding: 10px 16px;
                border: none;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fbbf24, stop:1 #f59e0b);
            }
            QPushButton: pressed {
                background: #b45309;
            }
        """)
        btn_xaurum_rapport.clicked.connect(self.on_generate_xaurum_rapport)
        xaurum_btn_layout.addWidget(btn_xaurum_rapport)

        btn_show_inconsistenties = QPushButton("⚠️ Toon Naamvarianten")
        btn_show_inconsistenties.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_show_inconsistenties. setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef4444, stop:1 #dc2626);
                color: white;
                font-weight: bold;
                padding: 10px 16px;
                border:  none;
                border-radius:  6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f87171, stop:1 #ef4444);
            }
            QPushButton:pressed {
                background: #b91c1c;
            }
        """)
        btn_show_inconsistenties.clicked.connect(self.on_show_naam_varianten)
        xaurum_btn_layout.addWidget(btn_show_inconsistenties)

        xaurum_btn_layout.addStretch()
        xaurum_layout.addLayout(xaurum_btn_layout)

        layout.addWidget(xaurum_group)

        layout.addSpacing(8)

        # ══════════════════════════════════════════════════════════════
        # SECTIE 3: CONFIGURATIEBESTANDEN
        # ══════════════════════════════════════════════════════════════
        files_group = QGroupBox("📁 Configuratiebestanden")
        files_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #10b981;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background: #f0fdf4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #059669;
            }
        """)
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(8)

        config_files = [
            ("📋 Medewerker Certificaat Config",
             CONFIG_FILE_CERT,
             "Per medewerker instellen welke certificaten verplicht zijn (Nodig/Strategisch)."),
            ("🎯 Medewerker Competentie Config",
             CONFIG_FILE_COMP,
             "Per medewerker competenties en niveaus beheren. "),
            ("📝 Planner / To-do Config",
             TODO_FILE,
             "Alle taken in de planner, inclusief status en details."),
            ("📚 Training Catalogus",
             TRAINING_CATALOG_FILE,
             "Opleidingscatalogus met links naar Xaurum ReadyForFlow."),
        ]

        for idx, (title_text, path, help_text) in enumerate(config_files):
            if idx > 0:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape. HLine)
                sep.setStyleSheet("background:#d1d5db;margin:4px 0;")
                files_layout.addWidget(sep)

            file_widget = QWidget()
            file_layout = QVBoxLayout(file_widget)
            file_layout.setContentsMargins(8, 4, 8, 4)
            file_layout. setSpacing(4)

            lbl_title = QLabel(f"<b>{title_text}</b>")
            lbl_title. setTextFormat(Qt.TextFormat.RichText)
            lbl_title.setStyleSheet("font-size:12px;color:#1f2937;background:transparent;")
            file_layout.addWidget(lbl_title)

            lbl_help = QLabel(help_text)
            lbl_help.setWordWrap(True)
            lbl_help.setStyleSheet("font-size:10px;color:#6b7280;background:transparent;")
            file_layout.addWidget(lbl_help)

            lbl_path = QLabel(f"📂 {str(path)}")
            lbl_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl_path. setStyleSheet("font-size: 10px;color:#9ca3af;background:transparent;")
            file_layout.addWidget(lbl_path)

            exists = path.exists()
            status_text = "✅ Bestand gevonden" if exists else "⚠️ Bestand bestaat nog niet"
            status_color = "#059669" if exists else "#d97706"
            
            lbl_status = QLabel(status_text)
            lbl_status.setStyleSheet(f"font-size:10px;color:{status_color};font-weight:bold;background:transparent;")
            file_layout.addWidget(lbl_status)

            btn_open = QPushButton("📂 Openen in Excel")
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_open.setStyleSheet("""
                QPushButton {
                    background: white;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    color: #374151;
                }
                QPushButton:hover {
                    background: #f3f4f6;
                    border-color: #10b981;
                }
            """)
            btn_open. clicked.connect(lambda _, p=path: self.open_file(p))
            file_layout.addWidget(btn_open, alignment=Qt.AlignmentFlag.AlignRight)

            files_layout.addWidget(file_widget)

        layout.addWidget(files_group)

        layout.addStretch(1)

    # ══════════════════════════════════════════════════════════════
    # CERTIFICATEN CONTROLE
    # ══════════════════════════════════════════════════════════════
    def on_check_certnames(self):
        """
        Controleert CertNames tegen Master_Certificaten.xlsx
        """
        try:
            res = self.data. check_certnames_against_master()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fout bij controle",
                f"Er trad een fout op bij de CertName-controle:\n{e}",
            )
            return

        missing_certs = res.get("certificates") or []
        missing_req = res.get("training_req") or []

        totaal_missing = len(set(missing_certs + missing_req))

        if totaal_missing == 0:
            QMessageBox. information(
                self,
                "✅ Controle Certificaten",
                "Alle CertNames uit 'Certificates' en 'Training_Req' komen voor in Master_Certificaten.xlsx.\n\n"
                "✅ Data integriteit OK!"
            )
            return

        # Toon overzicht
        parts = []

        if missing_certs: 
            txt = "📜 Certificatenlijst (Certificates):\n"
            txt += f"- {len(missing_certs)} CertName(s) niet gevonden in master:\n"
            txt += "  • " + "\n  • ".join(missing_certs)
            parts.append(txt)

        if missing_req:
            txt = "🎓 Training Aanvragen (Training_Req):\n"
            txt += f"- {len(missing_req)} CertName(s) niet gevonden in master:\n"
            txt += "  • " + "\n  • ".join(missing_req)
            parts.append(txt)

        overview_text = "\n\n" + "─" * 60 + "\n\n".join(parts)

        # Toon in dialoog met scroll
        dialog = QDialog(self)
        dialog.setWindowTitle("⚠️ Ontbrekende Certificaten in Master")
        layout = QVBoxLayout(dialog)

        lbl = QLabel(
            f"<b>⚠️ Er zijn {totaal_missing} unieke CertName(s) die niet in "
            f"Master_Certificaten.xlsx voorkomen.</b><br><br>"
            f"Je kunt hieronder de volledige lijst bekijken (scrollbaar).",
            dialog,
        )
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        text = QTextEdit(dialog)
        text.setReadOnly(True)
        text.setPlainText(overview_text)
        text.setStyleSheet("font-family:monospace;font-size: 11px;")
        layout.addWidget(text)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            parent=dialog,
        )
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        dialog.resize(800, 500)
        dialog.exec()

        # Vraag of toevoegen
        antwoord = QMessageBox.question(
            self,
            "➕ Toevoegen aan Master? ",
            f"<b>Er ontbreken {totaal_missing} unieke CertName(s) in Master_Certificaten.xlsx. </b><br><br>"
            f"Wil je deze automatisch toevoegen aan de masterlijst? <br><br>"
            f"⚠️ Let op: Dit wijzigt het Master_Certificaten.xlsx bestand! ",
            QMessageBox.StandardButton.Yes | QMessageBox. StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if antwoord != QMessageBox.StandardButton.Yes:
            return

        try:
            added = self.data.add_missing_certnames_to_master(res)
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Fout bij bijwerken master",
                f"Er trad een fout op bij het toevoegen aan Master_Certificaten.xlsx:\n{e}",
            )
            return

        QMessageBox.information(
            self,
            "✅ Master bijgewerkt",
            f"<b>{added} CertName(s) toegevoegd aan Master_Certificaten.xlsx. </b><br><br>"
            f"💡 Herlaad de data om de wijzigingen te zien."
        )

    # ══════════════════════════════════════════════════════════════
    # COMPETENTIES CONTROLE
    # ══════════════════════════════════════════════════════════════
    def on_check_competences(self):
        """
        Controleert Competence-namen tegen Master_Competenties. xlsx
        """
        try: 
            res = self.data. check_competences_against_master()
        except Exception as e: 
            QMessageBox.critical(
                self,
                "Fout bij controle",
                f"Er trad een fout op bij de Competenties-controle:\n{e}",
            )
            return

        missing_comps = res.get("competences") or []

        if not missing_comps:
            QMessageBox.information(
                self,
                "✅ Controle Competenties",
                "Alle Competence-namen uit 'Competences' komen voor in Master_Competenties.xlsx.\n\n"
                "✅ Data integriteit OK!"
            )
            return

        # Toon overzicht
        overview_text = f"🎯 Competenties (Competences):\n"
        overview_text += f"- {len(missing_comps)} Competence(s) niet gevonden in master:\n"
        overview_text += "  • " + "\n  • ".join(missing_comps)

        # Toon in dialoog
        dialog = QDialog(self)
        dialog.setWindowTitle("⚠️ Ontbrekende Competenties in Master")
        layout = QVBoxLayout(dialog)

        lbl = QLabel(
            f"<b>⚠️ Er zijn {len(missing_comps)} Competence(s) die niet in "
            f"Master_Competenties.xlsx voorkomen.</b><br><br>"
            f"Je kunt hieronder de volledige lijst bekijken (scrollbaar).",
            dialog,
        )
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        text = QTextEdit(dialog)
        text.setReadOnly(True)
        text.setPlainText(overview_text)
        text.setStyleSheet("font-family:monospace;font-size:11px;")
        layout.addWidget(text)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            parent=dialog,
        )
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        dialog.resize(800, 500)
        dialog.exec()

        # Vraag of toevoegen
        antwoord = QMessageBox. question(
            self,
            "➕ Toevoegen aan Master?",
            f"<b>Er ontbreken {len(missing_comps)} Competence(s) in Master_Competenties.xlsx.</b><br><br>"
            f"Wil je deze automatisch toevoegen aan de masterlijst?<br><br>"
            f"⚠️ Let op: Dit wijzigt het Master_Competenties.xlsx bestand!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton. Yes,
        )

        if antwoord != QMessageBox. StandardButton.Yes:
            return

        try:
            added = self.data.add_missing_competences_to_master(res)
        except Exception as e: 
            QMessageBox.critical(
                self,
                "❌ Fout bij bijwerken master",
                f"Er trad een fout op bij het toevoegen aan Master_Competenties.xlsx:\n{e}",
            )
            return

        QMessageBox.information(
            self,
            "✅ Master bijgewerkt",
            f"<b>{added} Competence(s) toegevoegd aan Master_Competenties.xlsx.</b><br><br>"
            f"💡 Herlaad de data om de wijzigingen te zien."
        )

    # ══════════════════════════════════════════════════════════════
    # TOEKOMSTIGE TRAININGEN CONTROLE
    # ══════════════════════════════════════════════════════════════
    def on_check_future_trainings(self):
        """
        Controleert of alle toekomstige trainingen in Training_Req 
        als 'Nodig' staan in config. 
        """
        try:
            result = self.data.check_training_req_against_config()
        except Exception as e:
            QMessageBox. critical(
                self,
                "Fout bij controle",
                f"Er trad een fout op bij de Training_Req controle:\n{e}",
            )
            import traceback
            traceback.print_exc()
            return

        missing_count = result["missing_count"]
        missing_items = result["missing_items"]

        if missing_count == 0:
            QMessageBox.information(
                self,
                "✅ Controle Toekomstige Trainingen",
                "Alle toekomstige inschrijvingen (Training_Req) staan in "
                "Medewerker_Certificaat_Config.xlsx en hebben 'Nodig' ingesteld.\n\n"
                "✅ Data integriteit OK!"
            )
            return

        # ══════════════════════════════════════════════════════════════
        # Bouw overzicht voor dialoog
        # ══════════════════════════════════════════════════════════════
        overview_parts = []
        
        # Groepeer per costcenter
        by_costcenter = {}
        for item in missing_items: 
            cc = item['costcenter'] or "Onbekend"
            if cc not in by_costcenter:
                by_costcenter[cc] = []
            by_costcenter[cc].append(item)
        
        # Bouw tekst per costcenter
        for cc in sorted(by_costcenter.keys()):
            items = by_costcenter[cc]
            overview_parts.append(f"🏢 Costcenter:  {cc} ({len(items)} inschrijving(en))")
            overview_parts.append("─" * 80)
            
            for item in items:
                date_str = item['scheduled_date'] or "Datum onbekend"
                overview_parts.append(
                    f"  • {item['medewerker']} ({item['staff_id']})\n"
                    f"    → {item['cert_name']}\n"
                    f"    📅 {date_str} | 📍 {item['location'] or '-'} | Status: {item['status'] or '-'}"
                )
            overview_parts.append("")

        overview_text = "\n".join(overview_parts)

        # ══════════════════════════════════════════════════════════════
        # Toon in dialoog met scroll
        # ══════════════════════════════════════════════════════════════
        dialog = QDialog(self)
        dialog.setWindowTitle("⚠️ Toekomstige Trainingen Zonder 'Nodig' in Config")
        dialog.resize(900, 600)
        
        layout = QVBoxLayout(dialog)

        # Header met statistieken
        header = QLabel(
            f"<h2 style='color:#dc3545;'>⚠️ Toekomstige Trainingen Check</h2>"
            f"<p style='font-size:13px;'>"
            f"Er zijn <b>{missing_count}</b> toekomstige inschrijving(en) gevonden die <b>NIET</b> "
            f"als 'Nodig' in Medewerker_Certificaat_Config.xlsx staan. <br><br>"
            f"<span style='color:#d97706;'><b>⚠️ Let op: </b> Deze trainingen kunnen uit de planner verdwijnen!</span>"
            f"</p>",
            dialog,
        )
        header.setTextFormat(Qt.TextFormat.RichText)
        header.setWordWrap(True)
        layout.addWidget(header)

        # Scrollable text area
        text = QTextEdit(dialog)
        text.setReadOnly(True)
        text.setPlainText(overview_text)
        text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                background:  #f9fafb;
                border: 1px solid #d1d5db;
                border-radius: 4px;
            }
        """)
        layout.addWidget(text)

        # Info label
        info = QLabel(
            "💡 <b>Tip:</b> Export deze lijst naar Excel met onderstaande knop, "
            "of klik 'Auto-fix' om automatisch 'Nodig=True' te zetten in de config.",
            dialog
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        info.setStyleSheet("font-size:11px;color:#6b7280;padding:8px;background:#eff6ff;border-radius: 4px;")
        layout.addWidget(info)

        # Buttons
        btn_box = QHBoxLayout()
        
        btn_export = QPushButton("📊 Export naar Excel")
        btn_export. clicked.connect(lambda: self. export_training_check_to_excel(missing_items))
        btn_export.setStyleSheet("""
            QPushButton {
                background:  #3b82f6;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        btn_box.addWidget(btn_export)
        
        btn_autofix = QPushButton("🔧 Auto-fix:  Zet 'Nodig' aan")
        btn_autofix.clicked.connect(lambda: self.autofix_training_config(missing_items, dialog))
        btn_autofix. setStyleSheet("""
            QPushButton {
                background: #10b981;
                color:  white;
                font-weight:  bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton: hover { background: #059669; }
        """)
        btn_box.addWidget(btn_autofix)
        
        btn_box.addStretch()
        
        btn_close = QPushButton("Sluiten")
        btn_close.clicked.connect(dialog. reject)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color:  white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background: #4b5563; }
        """)
        btn_box.addWidget(btn_close)
        
        layout.addLayout(btn_box)

        dialog.exec()

    # ══════════════════════════════════════════════════════════════
    # EXPORT TRAINING CHECK NAAR EXCEL
    # ══════════════════════════════════════════════════════════════
    def export_training_check_to_excel(self, missing_items:  list):
        """
        Exporteert de lijst met ontbrekende trainingen naar Excel. 
        """
        if not missing_items:
            QMessageBox.information(self, "Geen data", "Geen items om te exporteren.")
            return
        
        try:
            # Maak DataFrame
            df = pd.DataFrame(missing_items)
            
            # Hernoem kolommen voor leesbaarheid
            df = df.rename(columns={
                "staff_id": "Medewerker ID",
                "medewerker": "Naam",
                "cert_name":  "Certificaat",
                "scheduled_date": "Geplande Datum",
                "location": "Locatie",
                "status": "Status",
                "costcenter": "Costcenter"
            })
            
            # Bepaal bestandsnaam met timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = CONFIG_DIR / f"Training_Check_{timestamp}.xlsx"
            
            # Export
            with pd.ExcelWriter(filename, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Ontbrekende Trainingen", index=False)
            
            # Feedback
            reply = QMessageBox.question(
                self,
                "✅ Export Geslaagd",
                f"Export voltooid!\n\n"
                f"Bestand: {filename. name}\n"
                f"Locatie: {filename.parent}\n\n"
                f"Wil je het bestand openen? ",
                QMessageBox.StandardButton.Yes | QMessageBox. StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton. Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(filename)))
                
        except Exception as e: 
            QMessageBox.critical(
                self,
                "❌ Export Fout",
                f"Kon niet exporteren naar Excel:\n{e}"
            )
            import traceback
            traceback.print_exc()

    # ══════════════════════════════════════════════════════════════
    # AUTO-FIX TRAINING CONFIG
    # ══════════════════════════════════════════════════════════════
    def autofix_training_config(self, missing_items: list, parent_dialog:  QDialog):
        """
        Automatische fix:  Voegt ontbrekende items toe aan config met Nodig=True.
        """
        if not missing_items: 
            QMessageBox.information(self, "Geen data", "Geen items om te fixen.")
            return
        
        # Bevestiging
        reply = QMessageBox.question(
            self,
            "🔧 Auto-fix Bevestiging",
            f"Je staat op het punt om <b>{len(missing_items)}</b> certificaat/certificaten "
            f"automatisch toe te voegen aan Medewerker_Certificaat_Config.xlsx. <br><br>"
            f"Voor alle items wordt: <br>"
            f"• <b>Nodig = True</b><br>"
            f"• <b>Strategisch = False</b><br>"
            f"• <b>Commentaar = 'Auto-toegevoegd door Training Check'</b><br><br>"
            f"<span style='color:#d97706;'>⚠️ Let op:  Dit wijzigt het config bestand!</span><br><br>"
            f"Doorgaan? ",
            QMessageBox.StandardButton.Yes | QMessageBox. StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Laad huidige config
            if CONFIG_FILE_CERT. exists():
                config_df = pd.read_excel(CONFIG_FILE_CERT)
            else:
                id_col = self.data.get_id_column() or "staffGID"
                config_df = pd.DataFrame(columns=[
                    id_col, "MedewerkerNaam", "CertName", "Nodig",
                    "Strategisch", "Commentaar", "DatumToegevoegd"
                ])
            
            # ID kolom
            id_col = self.data.get_id_column() or "staffGID"
            
            # Normaliseer bestaande data
            if id_col in config_df. columns:
                config_df[id_col] = config_df[id_col].astype(str).str.strip()
            if "CertName" in config_df. columns:
                config_df["CertName"] = config_df["CertName"].astype(str).str.strip()
            
            # Voeg nieuwe items toe
            now = datetime.now()
            added = 0
            
            for item in missing_items:
                staff_id = item['staff_id']
                cert_name = item['cert_name']
                medewerker = item['medewerker']
                
                # Check of al bestaat
                exists = False
                if not config_df.empty and id_col in config_df.columns and "CertName" in config_df.columns:
                    exists = (
                        (config_df[id_col] == staff_id) & 
                        (config_df["CertName"] == cert_name)
                    ).any()
                
                if not exists:
                    new_row = {
                        id_col: staff_id,
                        "MedewerkerNaam": medewerker,
                        "CertName":  cert_name,
                        "Nodig": True,
                        "Strategisch": False,
                        "Commentaar":  f"Auto-toegevoegd door Training Check ({now.strftime('%d-%m-%Y')})",
                        "DatumToegevoegd": now
                    }
                    config_df = pd.concat([config_df, pd.DataFrame([new_row])], ignore_index=True)
                    added += 1
            
            # Opslaan
            with pd.ExcelWriter(CONFIG_FILE_CERT, engine="openpyxl") as writer:
                config_df.to_excel(writer, sheet_name="Vereisten", index=False)
            
            # Update DataStore
            self.data.df["config_cert"] = config_df
            self.data.df["config"] = config_df
            
            # Sluit dialoog
            parent_dialog.accept()
            
            # Feedback
            QMessageBox.information(
                self,
                "✅ Auto-fix Voltooid",
                f"<b>{added}</b> certificaat/certificaten toegevoegd aan config. <br><br>"
                f"💡 <b>Aanbevolen:</b> Gebruik '🔄 Data verversen' om de planner bij te werken."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Auto-fix Fout",
                f"Kon config niet bijwerken:\n{e}"
            )
            import traceback
            traceback.print_exc()

    # ══════════════════════════════════════════════════════════════
    # XAURUM RAPPORT GENEREREN
    # ══════════════════════════════════════════════════════════════
    def on_generate_xaurum_rapport(self):
        """
        Genereert een rapport voor Xaurum met configuratiefouten.
        Checkt of Basis of Refresh nodig is op basis van certificaat verloopdatum.
        
        Regel:  Als certificaat > 2 jaar verlopen → BASIS nodig
               Als certificaat < 2 jaar verlopen → REFRESH nodig
               Als certificaat nog geldig → GEEN ACTIE nodig
        """
        from datetime import timedelta
        
        config = self.data.df. get("config", pd.DataFrame())
        certs = self.data.df.get("certificates", pd.DataFrame())
        
        if config.empty:
            QMessageBox.warning(self, "Geen data", "Geen config data beschikbaar!")
            return
        
        if certs.empty:
            QMessageBox.warning(self, "Geen data", "Geen certificates data beschikbaar!")
            return
        
        # Toon progress
        progress = QProgressDialog("Xaurum rapport genereren...", "Annuleren", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        QApplication.processEvents()
        
        try:
            # Normaliseer ID kolommen
            id_col = "staffGID"
            config = config.copy()
            certs = certs.copy()
            config[id_col] = config[id_col].astype(str).str.strip()
            certs[id_col] = certs[id_col].astype(str).str.strip()
            
            progress.setValue(20)
            QApplication.processEvents()
            
            # Functie om opleidingscode te extraheren
            def get_opl_code(certname):
                if pd.isna(certname):
                    return ""
                parts = str(certname).split(" - ")
                return parts[0]. strip() if parts else ""
            
            config["OplCode"] = config["CertName"]. apply(get_opl_code)
            certs["OplCode"] = certs["CertName"].apply(get_opl_code)
            
            # Detecteer expiry kolom
            expiry_col = None
            for col in ["Expiry_Date", "ExpiryDate", "Valid_Until", "Geldig_Tot", "VerloopDatum"]:
                if col in certs.columns:
                    expiry_col = col
                    break
            
            if expiry_col is None:
                QMessageBox.warning(self, "Geen data", "Geen verloopdatum kolom gevonden in certificates!")
                progress.close()
                return
            
            # Converteer expiry naar datetime
            certs[expiry_col] = pd. to_datetime(certs[expiry_col], errors='coerce')
            
            progress.setValue(40)
            QApplication.processEvents()
            
            # Filter config op Nodig=1
            if "Nodig" in config. columns:
                config["Nodig"] = config["Nodig"].apply(
                    lambda x: str(x).lower() in ['true', '1', 'yes', 'ja', 'aan']
                )
                config_nodig = config[config["Nodig"] == True]. copy()
            else:
                config_nodig = config.copy()
            
            # Identificeer Refresh opleidingen
            def is_refresh(certname):
                if pd. isna(certname):
                    return False
                name = str(certname).lower()
                return any(suffix in name for suffix in [' - refresh', ' - training', ' - recyclage'])
            
            config_nodig["IsRefresh"] = config_nodig["CertName"].apply(is_refresh)
            
            progress.setValue(60)
            QApplication.processEvents()
            
            # Vind fouten
            fouten = []
            taalvariatie_fouten = []
            
            # FOUT TYPE 1: Basis + Refresh beide op Nodig=1
            for (staff_id, opl_code), group in config_nodig.groupby([id_col, "OplCode"]):
                if progress.wasCanceled():
                    return
                
                basis_rows = group[~group["IsRefresh"]]
                refresh_rows = group[group["IsRefresh"]]
                
                if len(basis_rows) > 0 and len(refresh_rows) > 0:
                    basis_name = basis_rows.iloc[0]["CertName"]
                    refresh_name = refresh_rows. iloc[0]["CertName"]
                    medewerker_naam = basis_rows.iloc[0]. get("MedewerkerNaam", "Onbekend")
                    
                    # Zoek certificaat
                    cert_matches = certs[
                        (certs[id_col] == staff_id) &
                        (certs["OplCode"] == opl_code)
                    ].copy()
                    
                    if not cert_matches.empty:
                        cert_matches = cert_matches. sort_values(expiry_col, ascending=False)
                        latest_cert = cert_matches.iloc[0]
                        expiry_date = latest_cert[expiry_col]
                        cert_name = latest_cert["CertName"]
                    else:
                        expiry_date = None
                        cert_name = None
                    
                    # Bepaal aanbeveling
                    now = datetime.now()
                    two_years_ago = now - timedelta(days=730)
                    
                    if expiry_date is None or pd.isna(expiry_date):
                        aanbeveling = "Geen certificaat gevonden"
                        actie = "BASIS nodig - Zet Refresh op Nodig=0"
                        dagen_verlopen = None
                    elif expiry_date > now:
                        aanbeveling = "Certificaat nog geldig"
                        actie = "GEEN ACTIE nodig - Zet BEIDE op Nodig=0"
                        dagen_verlopen = -(expiry_date - now).days
                    elif expiry_date > two_years_ago:
                        aanbeveling = f"Verlopen < 2 jaar ({(now - expiry_date).days} dagen)"
                        actie = "REFRESH nodig - Zet Basis op Nodig=0"
                        dagen_verlopen = (now - expiry_date).days
                    else:
                        aanbeveling = f"Verlopen > 2 jaar ({(now - expiry_date).days} dagen)"
                        actie = "BASIS nodig - Zet Refresh op Nodig=0"
                        dagen_verlopen = (now - expiry_date).days
                    
                    fouten.append({
                        "FoutType": "Basis+Refresh",
                        "OpleidingsCode": opl_code,
                        "staffGID": staff_id,
                        "MedewerkerNaam": medewerker_naam,
                        "BasisOpleiding": basis_name,
                        "RefreshOpleiding":  refresh_name,
                        "HuidigCertificaat": cert_name if cert_name else "Geen",
                        "VerloopDatum": expiry_date. strftime("%d-%m-%Y") if expiry_date and pd.notna(expiry_date) else "Geen",
                        "DagenVerlopen": dagen_verlopen,
                        "Aanbeveling": aanbeveling,
                        "Actie": actie
                    })
            
            progress.setValue(80)
            QApplication.processEvents()
            
            # FOUT TYPE 2: Taalvariaties (NL + FR)
            taal_patterns = [
                ("Hulpverlener", "Secouriste"),
                ("hoogwerker", "nacelle"),
                ("Vorkheftruck", "Chariot"),
            ]
            
            for (staff_id, opl_code), group in config_nodig.groupby([id_col, "OplCode"]):
                if len(group) > 1:
                    certnames = group["CertName"].tolist()
                    medewerker_naam = group. iloc[0]. get("MedewerkerNaam", "Onbekend")
                    
                    for nl_pattern, fr_pattern in taal_patterns:
                        nl_match = [c for c in certnames if nl_pattern. lower() in str(c).lower()]
                        fr_match = [c for c in certnames if fr_pattern. lower() in str(c).lower()]
                        
                        if nl_match and fr_match: 
                            taalvariatie_fouten.append({
                                "FoutType": "Taalvariatie",
                                "OpleidingsCode": opl_code,
                                "staffGID":  staff_id,
                                "MedewerkerNaam":  medewerker_naam,
                                "BasisOpleiding": nl_match[0],
                                "RefreshOpleiding": fr_match[0],
                                "HuidigCertificaat": "-",
                                "VerloopDatum": "-",
                                "DagenVerlopen": None,
                                "Aanbeveling": "Dubbele taalvariant",
                                "Actie": "Verwijder één taalvariant"
                            })
            
            # Combineer fouten
            alle_fouten = fouten + taalvariatie_fouten
            self.rapport_df = pd.DataFrame(alle_fouten)
            
            progress. setValue(100)
            progress.close()
            
            if self.rapport_df.empty:
                QMessageBox.information(
                    self,
                    "✅ Xaurum Rapport",
                    "Geen configuratiefouten gevonden!\n\n"
                    "Alle medewerkers hebben een correcte configuratie."
                )
                return
            
            # Toon resultaten in dialoog
            self.show_xaurum_rapport_dialog(alle_fouten)
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "❌ Fout",
                f"Er trad een fout op bij het genereren van het rapport:\n{e}"
            )
            import traceback
            traceback.print_exc()

    def show_xaurum_rapport_dialog(self, fouten:  list):
        """
        Toont het Xaurum rapport in een dialoog.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("📊 Xaurum Data Kwaliteit Rapport")
        dialog.resize(1200, 700)
        
        layout = QVBoxLayout(dialog)
        
        # Samenvatting
        basis_refresh_count = len([f for f in fouten if f["FoutType"] == "Basis+Refresh"])
        taalvariatie_count = len([f for f in fouten if f["FoutType"] == "Taalvariatie"])
        
        # Samenvatting per actie
        actie_counts = {}
        for f in fouten:
            actie = f["Actie"]
            actie_counts[actie] = actie_counts. get(actie, 0) + 1
        
        header_html = f"""
        <h2 style='color:#d97706;'>📊 Xaurum Data Kwaliteit Rapport</h2>
        <p><b>Datum:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}</p>
        <hr>
        <h3>Samenvatting</h3>
        <table style='font-size: 12px;'>
            <tr><td>• Basis+Refresh fouten: </td><td><b>{basis_refresh_count}</b></td></tr>
            <tr><td>• Taalvariatie fouten:</td><td><b>{taalvariatie_count}</b></td></tr>
            <tr><td>• <b>Totaal fouten:</b></td><td><b>{len(fouten)}</b></td></tr>
        </table>
        <h3>Per Actie</h3>
        <table style='font-size:12px;'>
        """
        for actie, count in actie_counts.items():
            color = "#dc2626" if "BASIS" in actie else "#f59e0b" if "REFRESH" in actie else "#10b981"
            header_html += f"<tr><td style='color:{color};'>• {actie}:</td><td><b>{count}</b></td></tr>"
        header_html += "</table>"
        
        header = QLabel(header_html)
        header.setTextFormat(Qt.TextFormat.RichText)
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # Tabel
        table = QTableWidget()
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels([
            "FoutType", "OplCode", "staffGID", "MedewerkerNaam",
            "BasisOpleiding", "RefreshOpleiding", "HuidigCertificaat",
            "VerloopDatum", "DagenVerlopen", "Aanbeveling", "Actie"
        ])
        table.setRowCount(len(fouten))
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        for row_idx, fout in enumerate(fouten):
            table.setItem(row_idx, 0, QTableWidgetItem(str(fout["FoutType"])))
            table.setItem(row_idx, 1, QTableWidgetItem(str(fout["OpleidingsCode"])))
            table.setItem(row_idx, 2, QTableWidgetItem(str(fout["staffGID"])))
            table.setItem(row_idx, 3, QTableWidgetItem(str(fout["MedewerkerNaam"])))
            table.setItem(row_idx, 4, QTableWidgetItem(str(fout["BasisOpleiding"])))
            table.setItem(row_idx, 5, QTableWidgetItem(str(fout["RefreshOpleiding"])))
            table.setItem(row_idx, 6, QTableWidgetItem(str(fout["HuidigCertificaat"])))
            table.setItem(row_idx, 7, QTableWidgetItem(str(fout["VerloopDatum"])))
            table.setItem(row_idx, 8, QTableWidgetItem(str(fout["DagenVerlopen"]) if fout["DagenVerlopen"] else "-"))
            table.setItem(row_idx, 9, QTableWidgetItem(str(fout["Aanbeveling"])))
            table.setItem(row_idx, 10, QTableWidgetItem(str(fout["Actie"])))
            
            # Kleur codering
            if "BASIS nodig" in fout["Actie"]: 
                color = QColor(255, 200, 200)  # Licht rood
            elif "REFRESH nodig" in fout["Actie"]:
                color = QColor(255, 255, 200)  # Licht geel
            elif "GEEN ACTIE" in fout["Actie"]:
                color = QColor(200, 255, 200)  # Licht groen
            else:
                color = QColor(255, 220, 180)  # Licht oranje
            
            for col_idx in range(11):
                item = table.item(row_idx, col_idx)
                if item:
                    item.setBackground(color)
        
        layout.addWidget(table)
        
        # Knoppen
        btn_layout = QHBoxLayout()
        
        btn_export = QPushButton("📥 Exporteer naar Excel")
        btn_export. setStyleSheet("""
            QPushButton {
                background:  #10b981;
                color: white;
                font-weight: bold;
                padding:  10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover { background: #059669; }
        """)
        btn_export.clicked.connect(lambda: self.export_xaurum_rapport())
        btn_layout.addWidget(btn_export)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("Sluiten")
        btn_close.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color:  white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover { background: #4b5563; }
        """)
        btn_close.clicked. connect(dialog.close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()

    def export_xaurum_rapport(self):
        """
        Exporteert het Xaurum rapport naar Excel.
        """
        if self.rapport_df is None or self.rapport_df.empty:
            QMessageBox.warning(self, "Geen data", "Geen rapport om te exporteren!")
            return
        
        # Vraag bestandsnaam
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"Xaurum_Rapport_{timestamp}.xlsx"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Opslaan als", default_name, "Excel Files (*.xlsx)"
        )
        
        if not filepath:
            return
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Sheet 1: Alle fouten
                self.rapport_df.to_excel(writer, sheet_name='Alle Fouten', index=False)
                
                # Sheet 2: BASIS nodig
                basis_nodig = self.rapport_df[self.rapport_df["Actie"]. str.contains("BASIS nodig", na=False)]
                if not basis_nodig.empty:
                    basis_nodig. to_excel(writer, sheet_name='BASIS nodig', index=False)
                
                # Sheet 3: REFRESH nodig
                refresh_nodig = self. rapport_df[self.rapport_df["Actie"].str. contains("REFRESH nodig", na=False)]
                if not refresh_nodig.empty:
                    refresh_nodig. to_excel(writer, sheet_name='REFRESH nodig', index=False)
                
                # Sheet 4: Geen actie nodig
                geen_actie = self.rapport_df[self.rapport_df["Actie"]. str. contains("GEEN ACTIE", na=False)]
                if not geen_actie.empty:
                    geen_actie.to_excel(writer, sheet_name='Geen Actie Nodig', index=False)
                
                # Sheet 5: Taalvariaties
                taalvariatie = self.rapport_df[self.rapport_df["FoutType"] == "Taalvariatie"]
                if not taalvariatie. empty:
                    taalvariatie.to_excel(writer, sheet_name='Taalvariaties', index=False)
            
            # Open bestand? 
            reply = QMessageBox. question(
                self,
                "✅ Export Geslaagd",
                f"Rapport geëxporteerd naar:\n{filepath}\n\nWil je het bestand openen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                QDesktopServices.openUrl(QUrl. fromLocalFile(filepath))
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Export Fout", f"Kon niet exporteren:\n{e}")
            import traceback
            traceback.print_exc()

    # ══════════════════════════════════════════════════════════════
    # TOON NAAMVARIANTEN
    # ══════════════════════════════════════════════════════════════
    def on_show_naam_varianten(self):
        """
        Toont alle naamvarianten per opleidingscode.
        """
        config = self.data. df. get("config", pd.DataFrame())
        
        if config.empty:
            QMessageBox.warning(self, "Geen data", "Geen config data beschikbaar!")
            return
        
        # Functie om opleidingscode te extraheren
        def get_opl_code(certname):
            if pd.isna(certname):
                return ""
            parts = str(certname).split(" - ")
            return parts[0]. strip() if parts else ""
        
        config = config.copy()
        config["OplCode"] = config["CertName"].apply(get_opl_code)
        
        # Groepeer en vind varianten
        varianten = config.groupby("OplCode")["CertName"]. nunique()
        meerdere_varianten = varianten[varianten > 1]
        
        if meerdere_varianten.empty:
            QMessageBox.information(
                self,
                "✅ Geen Varianten",
                "Geen naamgeving inconsistenties gevonden!\n\n"
                "Alle opleidingen hebben één unieke naam."
            )
            return
        
        # Bouw overzicht
        overview_parts = []
        overview_parts.append(f"{'='*80}")
        overview_parts.append(f"OPLEIDINGEN MET MEERDERE NAAMVARIANTEN:  {len(meerdere_varianten)}")
        overview_parts.append(f"{'='*80}\n")
        
        for opl_code in sorted(meerdere_varianten.index):
            namen = config[config["OplCode"] == opl_code]["CertName"].unique()
            count = config[config["OplCode"] == opl_code]["CertName"].count()
            
            overview_parts.append(f"📌 {opl_code} ({len(namen)} varianten, {count} config entries):")
            for naam in sorted(namen):
                sub_count = len(config[config["CertName"] == naam])
                overview_parts.append(f"   • {naam} ({sub_count}x)")
            overview_parts.append("")
        
        overview_text = "\n".join(overview_parts)
        
        # Toon in dialoog
        dialog = QDialog(self)
        dialog.setWindowTitle("⚠️ Naamgeving Varianten per Opleiding")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        header = QLabel(
            f"<h2 style='color:#dc2626;'>⚠️ Naamgeving Inconsistenties</h2>"
            f"<p>Er zijn <b>{len(meerdere_varianten)}</b> opleidingen met meerdere naamvarianten.</p>"
            f"<p style='color:#d97706;'>Dit kan problemen veroorzaken bij matching van certificaten! </p>"
        )
        header.setTextFormat(Qt.TextFormat.RichText)
        header.setWordWrap(True)
        layout.addWidget(header)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(overview_text)
        text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                background:  #f9fafb;
            }
        """)
        layout.addWidget(text)
        
        # Knoppen
        btn_layout = QHBoxLayout()
        
        btn_export = QPushButton("📥 Exporteer naar Excel")
        btn_export. setStyleSheet("""
            QPushButton {
                background:  #10b981;
                color: white;
                font-weight: bold;
                padding:  8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background: #059669; }
        """)
        btn_export.clicked. connect(lambda: self.export_naam_varianten(config, meerdere_varianten))
        btn_layout.addWidget(btn_export)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("Sluiten")
        btn_close.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color:  white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background: #4b5563; }
        """)
        btn_close. clicked.connect(dialog.close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        dialog. exec()

    def export_naam_varianten(self, config:  pd.DataFrame, meerdere_varianten: pd.Series):
        """
        Exporteert de naamvarianten naar Excel.
        """
        try:
            # Bouw export data
            export_data = []
            
            for opl_code in sorted(meerdere_varianten.index):
                namen = config[config["OplCode"] == opl_code]["CertName"].unique()
                
                for naam in sorted(namen):
                    sub_count = len(config[config["CertName"] == naam])
                    export_data. append({
                        "OpleidingsCode": opl_code,
                        "CertName": naam,
                        "Aantal": sub_count,
                        "AantalVarianten": len(namen)
                    })
            
            export_df = pd. DataFrame(export_data)
            
            # Vraag bestandsnaam
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            default_name = f"Xaurum_NaamVarianten_{timestamp}.xlsx"
            
            filepath, _ = QFileDialog. getSaveFileName(
                self, "Opslaan als", default_name, "Excel Files (*.xlsx)"
            )
            
            if not filepath:
                return
            
            export_df.to_excel(filepath, index=False, sheet_name="NaamVarianten")
            
            # Open bestand? 
            reply = QMessageBox.question(
                self,
                "✅ Export Geslaagd",
                f"Rapport geëxporteerd naar:\n{filepath}\n\nWil je het bestand openen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton. No
            )
            
            if reply == QMessageBox. StandardButton.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
                
        except Exception as e: 
            QMessageBox. critical(self, "❌ Export Fout", f"Kon niet exporteren:\n{e}")
            import traceback
            traceback. print_exc()

    # ══════════════════════════════════════════════════════════════
    # BESTAND OPENEN
    # ══════════════════════════════════════════════════════════════
    def open_file(self, path:  Path):
        """
        Opent een bestand in de standaard applicatie (Excel).
        """
        if not path: 
            return
        url = QUrl.fromLocalFile(str(path))
        ok = QDesktopServices.openUrl(url)
        if not ok: 
            QMessageBox.warning(
                self,
                "Openen mislukt",
                f"Kon het bestand niet openen:\n{path}"
            )

