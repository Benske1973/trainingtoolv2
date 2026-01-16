# ===============================================================
# BESTAND: xaurum/ui/tabs/dashboard.py
# ===============================================================

import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from xaurum.core.datastore import DataStore
from xaurum.ui.widgets import GaugeWidget

class StatCard(QWidget):
    """
    Een moderne, zakelijke tegel voor statistieken in Equans-stijl.
    """
    def __init__(self, title: str, value: str, icon_text: str, color_hex: str):
        super().__init__()
        self.setMinimumHeight(110)
        self.setStyleSheet(f"""
            QWidget#CardContainer {{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e2e8f0;
            }}
            QLabel#IconLabel {{
                background-color: {color_hex}20; /* 20% opacity van de kleur */
                color: {color_hex};
                border-radius: 24px; /* Maakt het rond */
                font-size: 20px;
                font-weight: bold;
            }}
        """)

        # Container layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # De eigenlijke kaart (voor styling)
        self.container = QWidget()
        self.container.setObjectName("CardContainer")
        
        # Subtiele schaduw toevoegen voor diepte
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15)) # Heel lichte schaduw
        self.container.setGraphicsEffect(shadow)

        inner_layout = QHBoxLayout(self.container)
        inner_layout.setContentsMargins(20, 20, 20, 20)
        inner_layout.setSpacing(15)

        # 1. Het Icoon (Links)
        self.lbl_icon = QLabel(icon_text)
        self.lbl_icon.setObjectName("IconLabel")
        self.lbl_icon.setFixedSize(48, 48)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(self.lbl_icon)

        # 2. Tekst en Waarde (Rechts)
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("""
            font-family: 'Segoe UI'; 
            font-size: 13px; 
            color: #64748b; 
            font-weight: 600;
        """)
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("""
            font-family: 'Segoe UI'; 
            font-size: 26px; 
            color: #002439; 
            font-weight: bold;
        """)

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_value)
        
        inner_layout.addWidget(text_container)
        inner_layout.addStretch() # Duw alles naar links

        layout.addWidget(self.container)

    def update_value(self, value: str):
        self.lbl_value.setText(value)


class DashboardTab(QWidget):
    """
    Dashboard tab met gauges en moderne stat-cards.
    """
    def __init__(self, data: DataStore):
        super().__init__()
        self.data = data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # ══════════════════════════════════════════════════════════════
        # TITEL & HEADER
        # ══════════════════════════════════════════════════════════════
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)

        title = QLabel("Training Management Dashboard")
        title.setStyleSheet("""
            font-family: 'Segoe UI';
            font-size: 26px;
            font-weight: bold;
            color: #00263D;
        """)
        header_layout.addWidget(title)

        self.lbl_filter = QLabel("Laden...")
        self.lbl_filter.setStyleSheet("""
            font-family: 'Segoe UI';
            font-size: 14px;
            color: #64748b;
        """)
        header_layout.addWidget(self.lbl_filter)
        
        layout.addLayout(header_layout)

    
        # ══════════════════════════════════════════════════════════════
        # GAUGES SECTIE
        # ══════════════════════════════════════════════════════════════
        gauge_container = QWidget()
        gauge_container.setStyleSheet("background: transparent;")
        gauge_layout = QHBoxLayout(gauge_container)
        gauge_layout.setContentsMargins(0, 30, 0, 30) # Iets meer marge boven/onder
        gauge_layout.setSpacing(50) # Meer ruimte tussen de grotere gauges
        # AANGEPAST: Centreren in plaats van links uitlijnen
        gauge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Gauge 1: Actief (Groen)
        self.gauge_active = GaugeWidget("Actief", 0, "#10b981")
        gauge_layout.addWidget(self.gauge_active)

        # Gauge 2: Binnen 6 maanden (Oranje)
        self.gauge_expiring = GaugeWidget("Verloopt (6 mnd)", 0, "#f59e0b")
        gauge_layout.addWidget(self.gauge_expiring)

        # Gauge 3: Verlopen (Rood)
        self.gauge_expired = GaugeWidget("Verlopen", 0, "#ef4444")
        gauge_layout.addWidget(self.gauge_expired)
        
        # AANGEPAST: Deze stretch is verwijderd om centreren mogelijk te maken
        # gauge_layout.addStretch()

        layout.addWidget(gauge_container)
        # ══════════════════════════════════════════════════════════════
        # STATS TEGELS (DE NIEUWE EQUANS STIJL)
        # ══════════════════════════════════════════════════════════════
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # 1. Medewerkers (Blauw)
        # Icon suggestie: 👥 (Unicode) of FontAwesome als je dat hebt
        self.card_employees = StatCard("MEDEWERKERS", "0", "👥", "#005EB8")
        cards_layout.addWidget(self.card_employees)

        # 2. Certificaten (Groen)
        self.card_certificates = StatCard("CERTIFICATEN", "0", "📜", "#10b981")
        cards_layout.addWidget(self.card_certificates)

        # 3. Open Taken (Rood)
        self.card_tasks = StatCard("OPEN TAKEN", "0", "📋", "#ef4444")
        cards_layout.addWidget(self.card_tasks)

        # 4. Competenties (Paars)
        self.card_competences = StatCard("COMPETENTIES", "0", "🎯", "#8b5cf6")
        cards_layout.addWidget(self.card_competences)

        layout.addLayout(cards_layout)

        # ══════════════════════════════════════════════════════════════
        # STATISTIEKEN BALK (Onderaan)
        # ══════════════════════════════════════════════════════════════
        self.lbl_stats = QLabel()
        self.lbl_stats.setStyleSheet("""
            font-family: 'Segoe UI';
            font-size: 13px;
            color: #475569;
            padding: 15px;
            background: #f1f5f9;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
        """)
        self.lbl_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_stats)

        layout.addStretch(1)

    def refresh(self):
        """
        Ververst het dashboard met actuele data.
        """
        # 1. Filter tekst updaten
        cc = self.data.active_costcenter
        if cc:
            self.lbl_filter.setText(f"Filter actief: <b>{cc}</b>")
        else:
            self.lbl_filter.setText("Overzicht voor <b>alle afdelingen</b>")

        # 2. Certificaten data ophalen
        certs = self.data.df.get("certificates", pd.DataFrame())
        
        # Filteren op costcenter
        if cc and not certs.empty and "CostCenter" in certs.columns:
            certs = certs[certs["CostCenter"].astype(str) == str(cc)]

        total = len(certs)
        
        if total == 0:
            self.gauge_active.set_value(0)
            self.gauge_expiring.set_value(0)
            self.gauge_expired.set_value(0)
            self.lbl_stats.setText("Geen data beschikbaar voor de huidige selectie.")
            
            # Reset kaarten
            self.card_certificates.update_value("0")
        else:
            # Tellen
            status_col = certs["Status"].astype(str).str.strip().str.lower()
            active_count = len(status_col[status_col == "actief"])
            expiring_count = len(status_col[status_col.str.contains("binnen", na=False)])
            expired_count = len(status_col[status_col == "verlopen"])

            # Gauges
            self.gauge_active.set_value((active_count / total) * 100)
            self.gauge_expiring.set_value((expiring_count / total) * 100)
            self.gauge_expired.set_value((expired_count / total) * 100)

            # Footer tekst
            self.lbl_stats.setText(
                f"Status Verdeling:  Actief: <b>{active_count}</b>  •  "
                f"Verloopt binnenkort: <b>{expiring_count}</b>  •  "
                f"Verlopen: <b>{expired_count}</b>"
            )
            
            # Kaart update
            self.card_certificates.update_value(str(total))

        # 3. Overige kaarten updaten
        
        # Medewerkers
        staff_df = self.data.df.get("staff", pd.DataFrame())
        staff_count = len(staff_df) if not staff_df.empty else 0
        self.card_employees.update_value(str(staff_count))

        # Open Taken
        todo_df = self.data.df.get("todo", pd.DataFrame())
        if not todo_df.empty and "Status" in todo_df.columns:
            open_tasks = len(todo_df[todo_df["Status"].astype(str).str.strip() == "Open"])
        else:
            open_tasks = 0
        self.card_tasks.update_value(str(open_tasks))

        # Competenties
        comp_df = self.data.df.get("competences", pd.DataFrame())
        comp_count = len(comp_df) if not comp_df.empty else 0
        self.card_competences.update_value(str(comp_count))
