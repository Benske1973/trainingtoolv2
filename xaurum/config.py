# ===============================================================
# Training Management System - Configuratie (Constants & Paths)
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
# 2. PADEN EN MAPPEN (SharePoint Logica)
# ═══════════════════════════════════════════════════════════

# Huidige gebruiker ophalen (nodig voor het pad)
USERNAME = os.getenv("USERNAME") or os.getenv("USER") or "CP1234"

# Lijst met mogelijke locaties van de SharePoint map
POSSIBLE_BASE_PATHS = [
    Path(f"C:/Users/{USERNAME}/EQUANS/Competentie Management - Documenten"),
    Path(f"C:/Users/{USERNAME}/OneDrive - EQUANS/Competentie Management - Documenten"),
    Path(f"C:/Users/{USERNAME}/OneDrive/EQUANS/Competentie Management - Documenten"),
    # Fallback naar de map van het script zelf als niets gevonden wordt
    Path(os.path.dirname(os.path.abspath(__file__))).parent
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
CONFIG_FILE_MATRIX = CONFIG_DIR / "matrix_config.json"  # Fallback

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
