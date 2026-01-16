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

# ===============================================================
# HELPERS (OVERSCHRIJFDE BLOK)
# ===============================================================
import re
import unicodedata
from typing import Optional

def normalize_sapnr(val) -> str:
    """
    Standaard SAPNR normalisatie: digits-only string ZONDER leading zeros.
    
    Leeg/ongeldig => ''
    
    Voorbeelden:
        - "17072.0" -> "17072"
        - "00123" -> "123"
        - None -> ""
        - "nan" -> ""
    """
    if val is None:
        return ""
    try:
        if pd.isna(val):
            return ""
    except Exception:
        pass

    s = str(val).strip()
    if s == "" or s.lower() in ("nan", "none", "null"):
        return ""

    # Vaak komt het als '17072.0' of als int/float
    try:
        n = int(float(s))
        return "" if n == 0 else str(n)
    except Exception:
        # Als het puur digits is: strip leading zeros
        if s.isdigit():
            return s.lstrip("0") or "0"  # Als alles zeros is, behoud "0"
        return s

def normalize_certname(name: str) -> str:
    """
    Centrale normalisatiefunctie voor certificaatnamen.
    
    🔧 VERSIE V3 - Uitgebreid met: 
    - Verwijdert diakritica (accents)
    - Maakt lowercase
    - Verwijdert alle niet-alfanumerieke tekens
    - Behoudt eventuele EQUANS-prefix-logica
    - Veilige fallback voor None/NaN
    - NIEUW: Taalvariaties (NL/FR) normaliseren
    - NIEUW:  Suffix variaties verwijderen (Refresh/Training/Basis)
    - NIEUW:  Afkortingen normaliseren (HS→Hoogspanning, LS→Laagspanning)
    - NIEUW: Module opleidingen behouden (Werken op hoogte Module 1/2/3)

    Voor backwards compatibility: dit is dé single-source-of-truth. 
    """
    try:
        if name is None:
            return ""
        s = str(name).strip()
        if s == "" or s.lower() == "nan":
            return ""

        # Behoud jouw eerdere EQUANS-prefix-logica
        if s. upper().startswith("EQUANS -"):
            s = s[8:].lstrip()
        elif s.upper().startswith("EQUANS-"):
            s = s[7:].lstrip()

        # Maak lowercase voor vergelijkingen
        s_lower = s.lower()

        # ═══════════════════════════════════════════════════════════════
        # STAP 1: Check of het een Module opleiding is (NIET normaliseren)
        # ═══════════════════════════════════════════════════════════════
        is_module_training = "module" in s_lower

        # ═══════════════════════════════════════════════════════════════
        # STAP 2: Taalvariaties normaliseren naar Nederlands
        # (voordat we accenten verwijderen, zodat we FR kunnen detecteren)
        # ═══════════════════════════════════════════════════════════════
        taal_mapping = [
            # EA-E-293 - BA5 Laagspanning
            ("basse tension", "laagspanning"),
            
            # EA-E-295 - BA5 Schakelen Hoogspanning (afkorting normaliseren)
            ("schakelen hs", "schakelen hoogspanning"),
            ("ba5 schakelen hs", "ba5 schakelen hoogspanning"),
            
            # EA-E-297 - BA5 Schakelen LS
            ("manoeuvres bt", "schakelen ls"),
            ("ba5 manoeuvres bt", "ba5 schakelen ls"),
            
            # EA-S-012 - Hulpverlener
            ("secouriste", "hulpverlener"),
            
            # EA-S-051 - Asbest
            ("amiante, poussière de silice et fibres céramiques réfractaires", "asbest informatie basis"),
            ("amiante poussiere de silice et fibres ceramiques refractaires", "asbest informatie basis"),
            ("asbest, kwartsstof en vuurvaste keramische vezels", "asbest informatie basis"),
            ("asbest kwartsstof en vuurvaste keramische vezels", "asbest informatie basis"),
            
            # IS-005 - Zelfrijdende hoogwerker
            ("élévateur à nacelle automoteur", "zelfrijdende hoogwerker"),
            ("elevateur a nacelle automoteur", "zelfrijdende hoogwerker"),
            ("elevateur nacelle automoteur", "zelfrijdende hoogwerker"),
            
            # IS-001 - Vorkheftruck
            ("chariot à fourche avancé", "vorkheftruck"),
            ("chariot a fourche avance", "vorkheftruck"),
            ("chariot fourche avance", "vorkheftruck"),
        ]
        
        for fr_term, nl_term in taal_mapping: 
            if fr_term in s_lower:
                s_lower = s_lower.replace(fr_term, nl_term)
                s = s_lower  # Update originele string ook

        # ═══════════════════════════════════════════════════════════════
        # STAP 3: Verwijder suffixes (BEHALVE voor Module opleidingen)
        # ⚠️  DISABLED: Training/Refresh/Basis zijn VERSCHILLENDE trainingen!
        # IS-001 - Training vs IS-001 - Refresh zijn aparte master entries
        # ═══════════════════════════════════════════════════════════════
        # if not is_module_training:
        #     suffixes_to_remove = [
        #         " - refresh",
        #         " - training",
        #         " - basis",
        #         " - initial",
        #         " - herhaling",
        #         " - vernieuwing",
        #         " - update",
        #         " - recurrent",
        #         " - recyclage",
        #     ]
        #
        #     for suffix in suffixes_to_remove:
        #         if s_lower.endswith(suffix):
        #             s = s[:-len(suffix)]
        #             s_lower = s. lower()
        #             break

        # ═══════════════════════════════════════════════════════════════
        # STAP 4: Unicode normalisatie - verwijder accenten
        # ═══════════════════════════════════════════════════════════════
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))

        # lowercase
        s = s.lower()

        # Verwijder alles dat geen letter of cijfer is
        s = re.sub(r"[^a-z0-9]", "", s)

        return s
        
    except Exception: 
        try: 
            return re.sub(r"[^a-z0-9]", "", str(name).lower())
        except Exception: 
            return ""

def detect_name_column(df: pd.DataFrame) -> Optional[str]:
    for col in ["Name+Firstname", "FullName", "Full_Name", "Employee_Name", "Naam"]:
        if col in df.columns:
            return col
    return None


def detect_expiry_column(df: pd.DataFrame) -> Optional[str]:
    for col in ["ExpiryDate", "Expiry_Date", "Expiry Date", "Geldig_tot", "Valid_Until"]:
        if col in df.columns:
            return col
    return None


def is_truthy_value(v) -> bool:
    if pd.isna(v):
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    s = str(v).strip().lower()
    return s in {"waar", "true", "yes", "ja", "y", "x", "v", "on", "1"}


def status_from_expiry(expiry_date) -> str:
    if pd.isna(expiry_date):
        return "Onbekend"
    days = (expiry_date - pd.Timestamp(datetime.now().date())).days
    if days < 0:
        return "Verlopen"
    if days <= 180:
        return "Verloopt binnen 6 maanden"
    return "Actief"


def create_department_logo_icon(size: int = 24) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#005EB8"))
    p.setPen(Qt.GlobalColor.white)
    p.drawEllipse(0, 0, size - 1, size - 1)
    font = p.font()
    font.setPointSize(int(size / 2.5))
    font.setBold(True)
    p.setFont(font)
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "CC")
    p.end()
    return QIcon(pix)


def ensure_certname(df: pd.DataFrame) -> pd.DataFrame:
    """
    Veilige versie van ensure_certname:
    - Detecteert alternatieve kolomnamen en hernoemt indien nodig naar 'CertName'
    - Maakt een backup-kolom '__orig_CertName__' (indien aanwezig)
    - Trim/cast CertName naar string, overschrijft geen bestaande leesbare namen
    - Bereken CertName_norm met de module-level normalize_certname
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # 1) Detecteer alternatieve kolomnamen en hernoem naar CertName indien nodig
    if "CertName" not in df.columns:
        for cand in ("Certificate_Name", "Competency", "Competency_Name",
                     "Certificaat", "Opleiding", "Training_Type", "Naam", "Title"):
            if cand in df.columns:
                df = df.rename(columns={cand: "CertName"})
                break

    # 2) Maak backup van originele kolom als die er is (voor het herstellen later)
    if "CertName" in df.columns and "__orig_CertName__" not in df.columns:
        try:
            df["__orig_CertName__"] = df["CertName"].astype(str).fillna("")
        except Exception:
            df["__orig_CertName__"] = df["CertName"].astype(str).apply(lambda x: str(x) if x is not None else "")

    # 3) Zorg dat CertName bestaat en trim
    if "CertName" not in df.columns:
        df["CertName"] = ""
    else:
        df["CertName"] = df["CertName"].astype(str).fillna("").apply(lambda x: "" if str(x).strip().lower() == "nan" else str(x).strip())

    # 4) Bereken CertName_norm zonder bestaande leesbare CertName onnodig te overschrijven
    def _compute_norm_for_row(row):
        # Gebruik CertName wanneer aanwezig
        cur = row.get("CertName", "")
        if cur and str(cur).strip().lower() != "nan":
            return normalize_certname(cur)
        # probeer alternatieven
        for alt in ("CertName_display", "Title", "Naam", "Name", "Opleiding", "Training", "Certificate_Name"):
            if alt in row and row.get(alt, "") and str(row.get(alt, "")).strip().lower() != "nan":
                return normalize_certname(row.get(alt, ""))
        return ""

    try:
        df["CertName_norm"] = df.apply(_compute_norm_for_row, axis=1)
    except Exception:
        # fallback element-wise
        try:
            df["CertName_norm"] = df.get("CertName", "").astype(str).fillna("").apply(normalize_certname)
        except Exception:
            df["CertName_norm"] = ""

    # 5) Indien CertName leeg maar we hebben __orig_CertName__, herstel alleen lege rijen
    try:
        if "__orig_CertName__" in df.columns:
            mask_restore = (df["CertName"].astype(str).str.strip() == "") & (df["__orig_CertName__"].astype(str).str.strip() != "")
            if mask_restore.any():
                df.loc[mask_restore, "CertName"] = df.loc[mask_restore, "__orig_CertName__"].astype(str).str.strip()
            # optioneel: verwijder backup-kolom als je dat wilt
            df.drop(columns=["__orig_CertName__"], inplace=True, errors="ignore")
    except Exception:
        pass

    # 6) Sanity: strings en strip
    try:
        df["CertName"] = df["CertName"].astype(str).fillna("").apply(lambda x: "" if str(x).strip().lower() == "nan" else str(x).strip())
    except Exception:
        pass
    try:
        df["CertName_norm"] = df["CertName_norm"].astype(str).fillna("")
    except Exception:
        pass

    return df


def format_medewerker_naam(full_name: str) -> str:
    """
    Converteert FullName naar MedewerkerNaam formaat.

    Input:  "ALTINDAG, Arton" of "ACHTERNAAM, Voornaam"
    Output: "Altindag Arton" (Achternaam spatie Voornaam, Title Case, GEEN komma)
    """
    if not full_name or not isinstance(full_name, str):
        return ""

    full_name = full_name.strip()

    if not full_name:
        return ""

    # Geval 1: "ACHTERNAAM, Voornaam" formaat (met komma)
    if ',' in full_name:
        parts = full_name.split(',', 1)
        if len(parts) == 2:
            achternaam = parts[0].strip()
            voornaam = parts[1].strip()

            # Converteer naar Title Case
            achternaam = achternaam.title()
            voornaam = voornaam.title()

            # Return ZONDER komma: "Achternaam Voornaam"
            return f"{achternaam} {voornaam}"

    # Geval 2: Al zonder komma - check of eerste deel UPPERCASE is
    parts = full_name.split()
    if len(parts) >= 2:
        if parts[0].isupper():
            achternaam = parts[0].title()
            voornaam = ' '.join(parts[1:]).title()
            return f"{achternaam} {voornaam}"

    # Geval 3: Onbekend formaat → gewoon Title Case toepassen
    return full_name.title()


