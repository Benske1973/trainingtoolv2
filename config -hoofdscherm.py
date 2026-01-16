# ===============================================================
# Training Management System - Configuratie
# ===============================================================

import os
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# 1. SQL SERVER CONFIGURATIE
# ═══════════════════════════════════════════════════════════
SQL_CONNECTION_STRING = (
    "mssql+pyodbc:///?odbc_connect="
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=ShrdSqlDevVM01;"
    "DATABASE=Operations_support_portal;"
    "Trusted_Connection=yes;"
)

# ═══════════════════════════════════════════════════════════
# 2. PADEN EN MAPPEN (Jouw Specifieke SharePoint Logica)
# ═══════════════════════════════════════════════════════════

# Huidige gebruiker ophalen (nodig voor het pad)
USERNAME = os.getenv("USERNAME") or os.getenv("USER") or "CP1234"

# Lijst met mogelijke locaties van de SharePoint map
POSSIBLE_BASE_PATHS = [
    Path(f"C:/Users/{USERNAME}/EQUANS/Competentie Management - Documenten"),
    Path(f"C:/Users/{USERNAME}/OneDrive - EQUANS/Competentie Management - Documenten"),
    Path(f"C:/Users/{USERNAME}/OneDrive/EQUANS/Competentie Management - Documenten"),
    # Fallback naar de map van het script zelf als niets gevonden wordt
    Path(os.path.dirname(os.path.abspath(__file__))) 
]

# De eerste map die bestaat wordt gebruikt als BASIS
BASE_PATH = next((p for p in POSSIBLE_BASE_PATHS if p.exists()), Path("."))

# BELANGRIJK: Alias voor compatibiliteit (zodat datastore.py niet crasht op BASE_DIR)
BASE_DIR = BASE_PATH

# ═══════════════════════════════════════════════════════════
# 3. BESTANDSDEFINITIES
# ═══════════════════════════════════════════════════════════

# Config map
CONFIG_DIR = BASE_PATH / "config"
try:
    CONFIG_DIR.mkdir(exist_ok=True, parents=True)
except:
    pass

# Export map
EXPORT_DIR = BASE_PATH / "exports"
try:
    EXPORT_DIR.mkdir(exist_ok=True, parents=True)
except:
    pass

# De specifieke configuratiebestanden (Excel)
CONFIG_FILE_CERT = CONFIG_DIR / "Medewerker_Certificaat_Config.xlsx"
CONFIG_FILE_COMP = CONFIG_DIR / "Medewerker_Competentie_Config.xlsx"
TODO_FILE = CONFIG_DIR / "Todo_Planner.xlsx"
TRAINING_CATALOG_FILE = CONFIG_DIR / "training_catalog_cleaned_for_app.xlsx"
CONFIG_FILE_MATRIX = CONFIG_DIR / "matrix_config.json" # Fallback

# Input bestanden (Referentie naar jouw mappenstructuur)
INPUT_FILES = {
    "staff": BASE_PATH / "ReadyForFlow-Personeel" / "STAFF_CompMan.xlsx",
    "certificates": BASE_PATH / "ReadyForFlow-Certificates" / "Certificates_Overview_ready.xlsx",
    "cert_results": BASE_PATH / "ReadyForFlow-CertResults" / "Certification_Results_overview.xlsx",
    "training_req": BASE_PATH / "ReadyForFlow-Training" / "Training_Req_Xaurum_ready.xlsx",
    "competences": BASE_PATH / "ReadyForFlow-Competences" / "Competences_Overview_ready.xlsx",
}

# Standaardnamen voor eventuele lokale imports
EXCEL_FILE_RESULTS = "Resultaten.xlsx"
EXCEL_FILE_PLANNING = "Planning.xlsx"

# ═══════════════════════════════════════════════════════════
# 4. KLEUREN & UI INSTELLINGEN
# ═══════════════════════════════════════════════════════════
STATUS_COLORS = {
    "ok": "#c8e6c9",           # Groen
    "warning": "#fff9c4",      # Geel
    "critical": "#ffcdd2",     # Rood
    "neutral": "#f5f5f5",      # Grijs
    "header": "#e0e0e0",       # Header
    "highlight": "#e3f2fd"     # Selectie
}

# ═══════════════════════════════════════════════════════════
# 5. VERTALINGEN
# ═══════════════════════════════════════════════════════════
# Vertalingen worden nu geladen uit SQL tabel [TM_NaamMapping].
# De oude hardcoded lijst is verwijderd om verwarring te voorkomen.

# # ===============================================================
# # Training Management System - Configuratie
# # ===============================================================

# import os
# from pathlib import Path

# # ═══════════════════════════════════════════════════════════
# # 1. SQL SERVER CONFIGURATIE
# # ═══════════════════════════════════════════════════════════
# SQL_CONNECTION_STRING = (
    # "mssql+pyodbc:///?odbc_connect="
    # "DRIVER={ODBC Driver 17 for SQL Server};"
    # "SERVER=ShrdSqlDevVM01;"
    # "DATABASE=Operations_support_portal;"
    # "Trusted_Connection=yes;"
# )

# # ═══════════════════════════════════════════════════════════
# # 2. PADEN EN MAPPEN
# # ═══════════════════════════════════════════════════════════
# # Bepaal de basis map (waar dit bestand staat)
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# # Config map (voor eventuele lokale json files)
# CONFIG_DIR = os.path.join(BASE_DIR, "config")
# if not os.path.exists(CONFIG_DIR):
    # os.makedirs(CONFIG_DIR)

# # Excel Export/Import mappen
# EXPORT_DIR = os.path.join(BASE_DIR, "exports")
# if not os.path.exists(EXPORT_DIR):
    # os.makedirs(EXPORT_DIR)

# # ═══════════════════════════════════════════════════════════
# # 3. BESTANDSDEFINITIES (DIT ONTBRAK!)
# # ═══════════════════════════════════════════════════════════
# # Deze definities zijn nodig zodat de UI niet crasht.
# CONFIG_FILE_CERT = os.path.join(CONFIG_DIR, "certificates.json")
# CONFIG_FILE_COMP = os.path.join(CONFIG_DIR, "competences.json")
# CONFIG_FILE_MATRIX = os.path.join(CONFIG_DIR, "matrix_config.json")

# # Standaardnamen voor Excel imports (fallback)
# EXCEL_FILE_RESULTS = "Resultaten.xlsx"
# EXCEL_FILE_PLANNING = "Planning.xlsx"

# # ═══════════════════════════════════════════════════════════
# # 4. KLEUREN & UI INSTELLINGEN
# # ═══════════════════════════════════════════════════════════
# STATUS_COLORS = {
    # "ok": "#c8e6c9",           # Groen
    # "warning": "#fff9c4",      # Geel
    # "critical": "#ffcdd2",     # Rood
    # "neutral": "#f5f5f5",      # Grijs
    # "header": "#e0e0e0",       # Header
    # "highlight": "#e3f2fd"     # Selectie
# }

# # ═══════════════════════════════════════════════════════════
# # 5. SYSTEEM INFO
# # ═══════════════════════════════════════════════════════════
# # USERNAME = os.getenv("USERNAME") or os.getenv("USER") or "UnknownUser"

# # ═══════════════════════════════════════════════════════════
# # 4. VERTALINGEN
# # ═══════════════════════════════════════════════════════════
# # LET OP: De hardcoded CERTIFICATE_MAPPING is verwijderd.
# # Alle vertalingen (Frans -> Nederlands) worden nu geladen uit 
# # de SQL Database tabel: [TM_NaamMapping].
# #
# # Zie: DataStore.load_translations() en DataStore._load_and_translate_excel()

# # # ===============================================================
# # # Training Management System v10 - PyQt6 (FIXED VERSION)
# # # Dashboard + Medewerkerbeheer + Planner/To-do (automatisch + zwevend)
# # # ===============================================================

# # import os
# # import math
# # import webbrowser
# # import re

# # from pathlib import Path
# # from datetime import datetime
# # from typing import Dict, List, Optional, Tuple, Any
# # from PyQt6.QtGui import QDesktopServices, QColor
# # from PyQt6.QtCore import QUrl
# # from sqlalchemy import create_engine, text

# # import pandas as pd

# # # --- SQL DATABASE CONFIGURATIE ---
# # # Dit is de ontbrekende variabele:
# # SQL_CONNECTION_STRING = (
    # # "mssql+pyodbc:///?odbc_connect="
    # # "DRIVER={ODBC Driver 17 for SQL Server};"
    # # "SERVER=ShrdSqlDevVM01;"
    # # "DATABASE=Operations_support_portal;"
    # # "Trusted_Connection=yes;"
# # )

# # # in trainingtest.py (bovenaan bij imports)


# # from PyQt6.QtWidgets import (
    # # QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    # # QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox,
    # # QScrollArea, QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
    # # QDialog, QDialogButtonBox, QToolButton, QButtonGroup,
    # # QStackedWidget, QFrame, QDateEdit, QTextEdit, QInputDialog,
    # # QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSizePolicy,
    # # )

# # from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF, QDate, QUrl
# # from PyQt6.QtGui import (
    # # QIcon, QPainter, QPixmap, QColor,
    # # QPen, QPainterPath, QRadialGradient,
    # # QDesktopServices, QBrush, QLinearGradient, QFontMetrics, 
# # )
# # from dataclasses import dataclass

# # ===============================================================
# # PADEN / SETTINGS
# # ===============================================================

# from xaurum.theme import APP_STYLE, load_logo_icon

# @dataclass
# class StatusToggleInfo:
    # key: str
    # label: str
    # nodig: bool
    # widget: object = None


# # ===============================================================
# # PADEN / SETTINGS
# # ===============================================================

# USERNAME = os.getenv("USERNAME") or os.getenv("USER") or "CP1234"

# POSSIBLE_BASE_PATHS = [
    # Path(f"C:/Users/{USERNAME}/EQUANS/Competentie Management - Documenten"),
    # Path(f"C:/Users/{USERNAME}/OneDrive - EQUANS/Competentie Management - Documenten"),
    # Path(f"C:/Users/{USERNAME}/OneDrive/EQUANS/Competentie Management - Documenten"),
# ]
# BASE_PATH = next((p for p in POSSIBLE_BASE_PATHS if p.exists()), Path("."))


# # ══════════════════════════════════════════════════════════════
# # INPUT FILES - Aangepast aan jouw mappenstructuur
# # ══════════════════════════════════════════════════════════════
# INPUT_FILES = {
    # # Bestanden in submappen (ReadyForFlow-...)
    # "staff": BASE_PATH / "ReadyForFlow-Personeel" / "STAFF_CompMan.xlsx",
    # "certificates": BASE_PATH / "ReadyForFlow-Certificates" / "Certificates_Overview_ready.xlsx",
    # "cert_results": BASE_PATH / "ReadyForFlow-CertResults" / "Certification_Results_overview.xlsx",
    # "training_req": BASE_PATH / "ReadyForFlow-Training" / "Training_Req_Xaurum_ready.xlsx",
    # "competences": BASE_PATH / "ReadyForFlow-Competences" / "Competences_Overview_ready.xlsx",
    
    # # Master-bestanden in hoofdmap
    # "master_cert": BASE_PATH / "Master_Certificaten.xlsx",
    # "master_comp": BASE_PATH / "Master_Competenties.xlsx",
# }

# # Config-map
# CONFIG_DIR = BASE_PATH / "config"
# CONFIG_DIR.mkdir(exist_ok=True, parents=True)

# CONFIG_FILE_CERT = CONFIG_DIR / "Medewerker_Certificaat_Config.xlsx"
# CONFIG_FILE_COMP = CONFIG_DIR / "Medewerker_Competentie_Config.xlsx"
# TODO_FILE = CONFIG_DIR / "Todo_Planner.xlsx"
# TRAINING_CATALOG_FILE = CONFIG_DIR / "training_catalog_cleaned_for_app.xlsx"

# # # ═══════════════════════════════════════════════════════════════════════════════
# # # CERTIFICAATNAAM STANDAARDISATIE MAPPING
# # # Converteert Franse/afwijkende namen naar standaard Nederlands
# # # ═══════════════════════════════════════════════════════════════════════════════
# # CERTNAME_STANDAARD_MAPPING = {
    # # # EA-E-293 - BA5 Laagspanning
    # # "EA-E-293 - BA5 Basse Tension": "EA-E-293 - BA5 Laagspanning",
    
    # # # EA-E-295 - BA5 Schakelen Hoogspanning
    # # "EA-E-295 - BA5 Schakelen HS": "EA-E-295 - BA5 Schakelen Hoogspanning",
    
    # # # EA-E-297 - BA5 Schakelen LS
    # # "EA-E-297 - BA5 Manoeuvres BT": "EA-E-297 - BA5 Schakelen LS",
    
    # # # EA-S-012 - Hulpverlener
    # # "EA-S-012 - Secouriste - Refresh": "EA-S-012 - Hulpverlener - Refresh",
    # # "EA-S-012 - Secouriste - Basis": "EA-S-012 - Hulpverlener - Basis",
    # # "EA-S-012 - Secouriste":  "EA-S-012 - Hulpverlener",
    
    # # # EA-S-051 - Asbest
    # # "EA-S-051 - Amiante, poussière de silice et fibres céramiques réfractaires": "EA-S-051 - Asbest Informatie Basis",
    # # "EA-S-051 - Asbest, kwartsstof en vuurvaste keramische vezels": "EA-S-051 - Asbest Informatie Basis",
    
    # # # IS-005 - Zelfrijdende hoogwerker
    # # "IS-005 - Elévateur à nacelle automoteur - Refresh": "IS-005 - Zelfrijdende hoogwerker - Refresh",
    # # "IS-005 - Elévateur à nacelle automoteur - Training": "IS-005 - Zelfrijdende hoogwerker - Training",
    # # "IS-005 - Elévateur à nacelle automoteur":  "IS-005 - Zelfrijdende hoogwerker",
    
    # # # IS-001 - Vorkheftruck
    # # "IS-001 - Chariot à Fourche Avancé - Refresh": "IS-001 - Vorkheftruck - Refresh",
    # # "IS-001 - Chariot à Fourche Avancé":  "IS-001 - Vorkheftruck",
# # }


# # def get_standaard_certname(certname: str) -> str:
    # # """
    # # Converteert Franse/afwijkende certificaatnamen naar standaard Nederlands.
    
    # # Args:
        # # certname: De originele certificaatnaam
        
    # # Returns:
        # # De gestandaardiseerde Nederlandse naam, of de originele naam als geen mapping bestaat
    # # """
    # # if not certname or pd.isna(certname):
        # # return certname
    # # return CERTNAME_STANDAARD_MAPPING.get(str(certname).strip(), certname)

