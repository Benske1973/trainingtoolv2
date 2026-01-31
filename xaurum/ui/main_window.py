# ===============================================================
# BESTAND: xaurum/ui/main_window.py (OPSCHOONDE VERSIE NA SQL-DIRECTE FIX)
# ===============================================================

import os
import math
import webbrowser
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# PyQt Imports
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
    QIcon, QPainter, QPixmap, QColor, QDesktopServices,
    QPen, QPainterPath, QRadialGradient, QBrush, QLinearGradient, QFontMetrics,
)

# Derde partij imports
from sqlalchemy import create_engine, text
import pandas as pd
from dataclasses import dataclass

# Project Imports (vanuit xaurum package)
from xaurum.theme import APP_STYLE, load_logo_icon
from xaurum.config import *
from xaurum.utils import *
from xaurum.core.datastore import DataStore

# Tab Imports
from xaurum.ui.tabs.dashboard import DashboardTab
from xaurum.ui.tabs.employees import EmployeeManagementTab
from xaurum.ui.tabs.todo import TodoTab
from xaurum.ui.tabs.alerts import AlertsTab
from xaurum.ui.tabs.future_trainings import DiscrepancyTrackerTab
from xaurum.ui.tabs.config import ConfigTab
# FIX: Correcte import van het nieuwe tabblad
from xaurum.ui.tabs.StaffSearchTab import StaffSearchTab 

# Logger instellen
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Training Management System v10")
        self.resize(1500, 900)
        
        # Witte achtergrond voor de hele app basis
        self.setStyleSheet("QMainWindow { background-color: #ffffff; }")

        self.data = DataStore()
        self.superuser_enabled: bool = False

        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central)

        # Sidebar (Links)
        self.sidebar = self._build_sidebar()
        main_layout.addWidget(self.sidebar, 0)

        # Rechter container (Header + Content)
        right_container = QWidget()
        right_container.setStyleSheet("background-color: #ffffff;") # Wit canvas
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0) # Marges op 0, header regelt padding
        right_layout.setSpacing(0)
        main_layout.addWidget(right_container, 1)

        # ══════════════════════════════════════════════════════════════
        # HEADER (Bovenbalk)
        # ══════════════════════════════════════════════════════════════
        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(70) 
        # Witte achtergrond met een heel subtiel lijntje onderaan
        self.header_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(30, 0, 30, 0) 
        
        # 1. Titel (Links)
        self.lbl_app_title = QLabel("Training Management System")
        self.lbl_app_title.setStyleSheet("""
            font-family: 'Segoe UI';
            font-size: 20px;
            font-weight: 600;
            color: #002439; /* Equans Donkerblauw */
            border: none;
        """)
        header_layout.addWidget(self.lbl_app_title)
        
        header_layout.addStretch(1)

        # 2. Knop Afdeling Wisselen (Rechts) - AANGEPAST NAAR #00263D
        self.btn_switch_cc = QPushButton("Afdeling wisselen")
        self.btn_switch_cc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_switch_cc.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                color: #00263D; /* AANGEPAST: Equans donkerblauw */
                font-family: 'Segoe UI';
                font-weight: 600;
                padding: 6px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #00263D; /* AANGEPAST: Border ook donkerblauw bij hover */
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        self.btn_switch_cc.clicked.connect(self.on_change_costcenter)
        header_layout.addWidget(self.btn_switch_cc)

        right_layout.addWidget(self.header_widget)

        # ══════════════════════════════════════════════════════════════
        # CONTENT AREA (Stacked Widget)
        # ══════════════════════════════════════════════════════════════
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
        right_layout.addWidget(content_container, 1)

        # Tabs initialiseren
        self.page_dashboard = DashboardTab(self.data)
        self.page_emp = EmployeeManagementTab(self.data)
        self.page_todo = TodoTab(self.data, open_employee_callback=self.open_employee_from_planner)
        self.page_alerts = AlertsTab(self.data)
        self.page_discrepancy = DiscrepancyTrackerTab(self.data)
        self.page_config = ConfigTab(self.data, parent_window=self)
        # FIX: Initialisatie van de nieuwe tab
        self.page_staff_search = StaffSearchTab(self.data)

        self.stack.addWidget(self.page_dashboard)         # index 0
        self.stack.addWidget(self.page_emp)               # index 1
        self.stack.addWidget(self.page_todo)              # index 2
        self.stack.addWidget(self.page_alerts)            # index 3
        self.stack.addWidget(self.page_discrepancy)       # index 4
        self.stack.addWidget(self.page_config)            # index 5
        # FIX: Toevoegen aan de stack
        self.stack.addWidget(self.page_staff_search)      # index 6

        self.init_menu()

        self.statusBar().showMessage("Data laden...")
        QTimer.singleShot(100, self.load_data)

    def _build_sidebar(self) -> QWidget:
        """
        Bouwt de sidebar.
        """
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 20, 12, 20) 
        layout.setSpacing(10)
        w.setFixedWidth(240) 
        
        # Donkere achtergrond instellen
        w.setStyleSheet("QWidget { background-color: #002439; color: #ffffff; }")

        # 1. LOGO
        current_dir = os.path.dirname(os.path.abspath(__file__))
        xaurum_root = os.path.dirname(current_dir) 
        logo_path = os.path.join(xaurum_root, 'assets', 'logo.png')

        lbl_logo = QLabel()
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_logo.setPixmap(scaled_pixmap)
        else:
            lbl_logo.setText("BELUX\nCompetentie\nManagement")
            lbl_logo.setStyleSheet("font-size:16px;font-weight:bold;color:#ffffff;")

        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        lbl_logo.setContentsMargins(10, 0, 0, 20) 
        layout.addWidget(lbl_logo)

        # 2. NAVIGATIE
        lbl_nav = QLabel("MENU")
        lbl_nav.setStyleSheet("font-size:10px; font-weight:bold; color:#64748b; margin-left: 10px; margin-bottom: 5px; border:none;")
        layout.addWidget(lbl_nav)

        self.btn_nav_group = QButtonGroup(self)
        self.btn_nav_group.setExclusive(True)

        self.btn_nav_dashboard = QPushButton("  Dashboard")
        self._style_nav_button(self.btn_nav_dashboard)
        self.btn_nav_dashboard.setChecked(True)
        self.btn_nav_dashboard.clicked.connect(lambda: self.show_page(0))
        self.btn_nav_group.addButton(self.btn_nav_dashboard)
        layout.addWidget(self.btn_nav_dashboard)

        self.btn_nav_emp = QPushButton("  Medewerkerbeheer")
        self._style_nav_button(self.btn_nav_emp)
        self.btn_nav_emp.clicked.connect(lambda: self.show_page(1))
        self.btn_nav_group.addButton(self.btn_nav_emp)
        layout.addWidget(self.btn_nav_emp)

        self.btn_nav_todo = QPushButton("  Planner / To-do")
        self._style_nav_button(self.btn_nav_todo)
        self.btn_nav_todo.clicked.connect(lambda: self.show_page(2))
        self.btn_nav_group.addButton(self.btn_nav_todo)
        layout.addWidget(self.btn_nav_todo)

        self.btn_nav_alerts = QPushButton("  Alerts (3 weken)")
        self._style_nav_button(self.btn_nav_alerts)
        self.btn_nav_alerts.clicked.connect(lambda: self.show_page(3))
        self.btn_nav_group.addButton(self.btn_nav_alerts)
        layout.addWidget(self.btn_nav_alerts)

        # self.btn_nav_future_trainings = QPushButton("  Toekomstige trainingen")
        # self._style_nav_button(self.btn_nav_future_trainings)
        # self.btn_nav_future_trainings.clicked.connect(lambda: self.show_page(4))
        # self.btn_nav_group.addButton(self.btn_nav_future_trainings)
        # layout.addWidget(self.btn_nav_future_trainings)
        # --- AANGEPAST: DISCREPANTIES TRACKER ---
        self.btn_nav_discrepancy = QPushButton("  Discrepanties Tracker")
        self._style_nav_button(self.btn_nav_discrepancy)
        # We koppelen hem aan pagina index 4
        self.btn_nav_discrepancy.clicked.connect(lambda: self.show_page(4))
        self.btn_nav_group.addButton(self.btn_nav_discrepancy)
        layout.addWidget(self.btn_nav_discrepancy)
        # ----------------------------------------
        self.btn_nav_config = QPushButton("  Config (superuser)")
        self._style_nav_button(self.btn_nav_config)
        self.btn_nav_config.clicked.connect(lambda: self.show_page(5))
        self.btn_nav_group.addButton(self.btn_nav_config)
        self.btn_nav_config.setVisible(False)
        layout.addWidget(self.btn_nav_config)
        
        # FIX: Navigatieknop voor Medewerker Zoeken
        self.btn_staff_search = QPushButton("  Medewerker Zoeken")
        self.btn_staff_search.setObjectName("StaffSearch")
        
        self._style_nav_button(self.btn_staff_search)
        self.btn_nav_group.addButton(self.btn_staff_search)
        
        self.btn_staff_search.clicked.connect(lambda: self.show_page(6)) 
        
        layout.addWidget(self.btn_staff_search)
        
        # 3. RUIMTE
        layout.addStretch(1)

        # 4. REFRESH SECTIE 
        
        # Informatie tekst (Datum)
        self.lbl_last_update = QLabel("Laatst bijgewerkt:\n-")
        self.lbl_last_update.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.lbl_last_update.setStyleSheet("font-size:10px; color:#94a3b8; margin-left: 5px; margin-bottom: 5px; border:none;")
        layout.addWidget(self.lbl_last_update)

        # De Knop (AANGEPAST: Groen #70bd95 en RECHTHOEKIG)
        self.btn_refresh_data = QPushButton("DATA VERVERSEN")
        self.btn_refresh_data.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_data.setFixedHeight(36)
        self.btn_refresh_data.setStyleSheet("""
            QPushButton {
                background-color: #70bd95; /* Belux Groen */
                color: white;
                font-weight: bold;
                font-size: 11px;
                border: none;
                border-radius: 0px; /* GEEN afronding */
                text-align: center;
            }
            QPushButton:hover {
                background-color: #5da683; /* Iets donkerder bij hover */
            }
            QPushButton:pressed {
                background-color: #4b8a6a;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)
        self.btn_refresh_data.clicked.connect(self.on_refresh_xaurum_data)
        layout.addWidget(self.btn_refresh_data)

        return w

    def _style_nav_button(self, btn: QPushButton):
        """
        Stijlt een navigatieknop in de sidebar.
        """
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(40) 
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 10px;
                border-radius: 0px; /* GEEN afronding */
                border: none;
                background: transparent;
                color: #cbd5e1;
                font-size: 13px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: #ffffff;
            }
            QPushButton:checked {
                background: #70bd95; /* Belux Groen */
                color: white;
                font-weight: 600;
            }
        """)

    def init_menu(self):
        menubar = self.menuBar()
        # Menu stijlen om bij wit te passen
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #ffffff;
                color: #333;
            }
            QMenuBar::item:selected {
                background-color: #f1f5f9;
            }
        """)
        
        beheer_menu = menubar.addMenu("Beheer")

        act_change_cc = beheer_menu.addAction("Costcenter wijzigen...")
        act_change_cc.triggered.connect(self.on_change_costcenter)

        beheer_menu.addSeparator()

        act_refresh = beheer_menu.addAction("🔄 Xaurum data verversen")
        act_refresh.triggered.connect(self.on_refresh_xaurum_data)

        beheer_menu.addSeparator()

        act_superuser = beheer_menu.addAction("Superuser (config) activeren/uitschakelen...")
        act_superuser.triggered.connect(self.on_toggle_superuser)

    def on_toggle_superuser(self):
        if self.superuser_enabled:
            reply = QMessageBox.question(
                self,
                "Superuser uitschakelen",
                "Superuser is momenteel actief.\n"
                "Wil je superuser uitschakelen en de Config-tab verbergen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.superuser_enabled = False
                self.btn_nav_config.setVisible(False)
                self.statusBar().showMessage("Superuser uitgeschakeld", 5000)
            return

        pin, ok = QInputDialog.getText(
            self,
            "Superuser activeren",
            "Geef de superuser-pincode in:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return

        if pin.strip() == "456852":
            self.superuser_enabled = True
            self.btn_nav_config.setVisible(True)
            self.statusBar().showMessage("Superuser geactiveerd – Config-tab zichtbaar", 8000)
        else:
            QMessageBox.warning(
                self,
                "Onjuiste pincode",
                "De ingegeven pincode is niet correct."
            )

    # def show_page(self, index: int):
        # if index == 5 and not self.superuser_enabled:
            # QMessageBox.warning(
                # self,
                # "Superuser vereist",
                # "De Config-tab is alleen toegankelijk voor een superuser.\n"
                # "Activeer superuser via het menu 'Beheer'."
            # )
            # index = 0

        # self.stack.setCurrentIndex(index)

        # # Pagina-specifieke acties en knop-highlighting
        # if index == 0:
            # self.lbl_app_title.setText("Training Management System") 
            # self.btn_nav_dashboard.setChecked(True)
            # self.page_dashboard.refresh()

        # elif index == 1:
            # self.btn_nav_emp.setChecked(True)

        # elif index == 2:
            # self.btn_nav_todo.setChecked(True)
            # self.page_todo.refresh()

        # elif index == 3:
            # self.btn_nav_alerts.setChecked(True)
            # self.page_alerts.refresh()

        # # elif index == 4:
            # # self.btn_nav_future_trainings.setChecked(True)
            # # if hasattr(self, "page_future_trainings") and hasattr(self.page_future_trainings, "refresh"):
                # # self.page_future_trainings.refresh()
        
        
        
        # elif index == 5:
            # self.btn_nav_config.setChecked(True)
            # if hasattr(self, "page_config") and hasattr(self.page_config, "refresh"):
                # self.page_config.refresh()
    
        # # FIX: Nieuwe tabblad logica
        # elif index == 6: 
            # if hasattr(self, "btn_staff_search"):
                # self.btn_staff_search.setChecked(True)
            # # Roep refresh aan. De tab beheert nu zelf de laadlogica.
            # if hasattr(self, "page_staff_search") and hasattr(self.page_staff_search, "refresh"):
                # self.page_staff_search.refresh()
    def show_page(self, index: int):
        # Config tab (index 5) beveiliging
        if index == 5 and not self.superuser_enabled:
            QMessageBox.warning(
                self,
                "Superuser vereist",
                "De Config-tab is alleen toegankelijk voor een superuser.\n"
                "Activeer superuser via het menu 'Beheer'."
            )
            index = 0

        self.stack.setCurrentIndex(index)

        # Reset alle knoppen (visueel)
        # (Niet strikt nodig omdat QButtonGroup setExclusive(True) heeft, maar veiligheidshalve)
        
        # Pagina-specifieke acties en knop-highlighting
        if index == 0:
            self.lbl_app_title.setText("Training Management System") 
            self.btn_nav_dashboard.setChecked(True)
            self.page_dashboard.refresh()

        elif index == 1:
            self.btn_nav_emp.setChecked(True)

        elif index == 2:
            self.btn_nav_todo.setChecked(True)
            self.page_todo.refresh()

        elif index == 3:
            self.btn_nav_alerts.setChecked(True)
            self.page_alerts.refresh()

        elif index == 4:
            # --- FIX: GEBRUIK DE NIEUWE NAMEN ---
            if hasattr(self, "btn_nav_discrepancy"):
                self.btn_nav_discrepancy.setChecked(True)
            
            if hasattr(self, "page_discrepancy") and hasattr(self.page_discrepancy, "refresh"):
                self.page_discrepancy.refresh()
            # ------------------------------------

        elif index == 5:
            self.btn_nav_config.setChecked(True)
            if hasattr(self, "page_config") and hasattr(self.page_config, "refresh"):
                self.page_config.refresh()
    
        elif index == 6: 
            if hasattr(self, "btn_staff_search"):
                self.btn_staff_search.setChecked(True)
            if hasattr(self, "page_staff_search") and hasattr(self.page_staff_search, "refresh"):
                self.page_staff_search.refresh()
    
    def load_data(self):
        # STAP 1: Staff data laden (essentieel voor CostCenter selectie)
        self.statusBar().showMessage("Staff laden voor costcenter selectie...")
        QApplication.processEvents()
        
        print("\n" + "="*60)
        print("🚀 APP OPSTARTEN - STAP 1: Staff laden")
        print("="*60)
        
        ok = self.data.load_staff_only()
        
        if not ok:
            QMessageBox.critical(
                self, 
                "Fout bij laden staff",
                "Kan staff data niet laden.\n\n" + 
                "\n".join(self.data.errors) if self.data.errors else "Onbekende fout."
            )
            self.statusBar().showMessage("Fout bij laden staff")
            return
        
        staff_count = len(self.data.df.get("staff", pd.DataFrame()))
        print(f"    ✅ {staff_count} medewerkers geladen voor costcenter selectie")
        
        # STAP 2: Costcenter selectie
        print("\n" + "="*60)
        print("🚀 APP OPSTARTEN - STAP 2: Costcenter selectie")
        print("="*60)
        
        self.statusBar().showMessage("Selecteer costcenter...")
        QApplication.processEvents()
        
        self.choose_costcenter()
        
        selected_costcenter = getattr(self.data, 'active_costcenter', None)
        
        if selected_costcenter:
            print(f"    ✅ Geselecteerd costcenter: {selected_costcenter}")
        else:
            print("    ℹ️ Geen specifiek costcenter geselecteerd - alle data laden")
        
        # STAP 3: Volledige Data Load
        print("\n" + "="*60)
        print("🚀 APP OPSTARTEN - STAP 3: Data laden")
        print("="*60)
        
        cc_display = selected_costcenter or "alle afdelingen"
        self.statusBar().showMessage(f"Data laden voor {cc_display}...")
        QApplication.processEvents()
        
        ok = self.data.load_all(costcenter_filter=selected_costcenter)

        if not ok:
            QMessageBox.critical(
                self,
                "Fout bij laden data",
                "Kan data niet laden.\n\n" +
                "\n".join(self.data.errors) if self.data.errors else "Onbekende fout."
            )
            self.statusBar().showMessage("Fout bij laden data")
            return

        # 🔧 DATA CLEANUP: Herbereken alle CertName_norm waarden (V4 normalize)
        try:
            print("\n" + "="*60)
            print("🔧 DATA CLEANUP: Renormaliseren certificaatnamen")
            print("="*60)
            self.data.renormalize_all_certnames()

            # 📝 Standaardiseer certificaatnamen naar Nederlandse vorm in config
            self.data.standardize_config_certnames()

            # 🧹 Verwijder duplicaten NA renormalisatie en standaardisatie
            self.data.remove_duplicate_tasks()
            self.data.remove_duplicate_configs()  # Ook config en certificates cleanen

            # ⚠️ SQL SAVE UITGESCHAKELD TIJDENS STARTUP (te traag)
            # De data wordt alleen in-memory gecleaned, niet naar SQL geschreven
            # Dit voorkomt dat ALLE records bij elke startup ge-UPDATE worden
            print("   ℹ️ Data cleanup in-memory voltooid (SQL save uitgeschakeld)")
        except Exception as e:
            print(f"⚠️ Fout bij renormaliseren: {e}")
            import traceback
            traceback.print_exc()

        # 🆕 Sync functies uitvoeren (inclusief certificate scan)
        try:
            self.data.sync_todo_with_config()
            self.data.create_tasks_for_expiring_certificates()
            self.data.merge_todo_with_config()
            self.data.sync_competence_tasks()
            self.data.update_status_from_tasktype_and_xaurum()
            self.data.apply_overrule_with_zweef()

            # 💾 Verrijk todo met staff info (CostCenter, MedewerkerNaam)
            self.data.enrich_todo_with_staff_info()

            # 🔧 CONDITIONELE SQL SAVE: Alleen als cost centers ontbreken
            # Check of er taken zijn zonder CostCenter
            todo = self.data.df.get("todo", pd.DataFrame())
            if not todo.empty and "CostCenter" in todo.columns:
                missing_cc = todo["CostCenter"].isna().sum()
                if missing_cc > 0:
                    print(f"   ⚠️ {missing_cc} taken zonder CostCenter - opslaan naar SQL...")
                    self.data.save_todo()
                    print("   ✅ Todo opgeslagen met cost center info")
                else:
                    print("   ℹ️ Todo sync voltooid (alle cost centers aanwezig, geen save nodig)")
            else:
                print("   ℹ️ Todo sync voltooid (geen CostCenter kolom)")
        except Exception as e:
            print(f"⚠️ Fout bij sync functies: {e}")
            import traceback
            traceback.print_exc()

        # STAP 4: UI Verversen
        print("\n" + "="*60)
        print("🚀 APP OPSTARTEN - STAP 4: UI verversen")
        print("="*60)
        
        self.statusBar().showMessage("UI verversen...")
        QApplication.processEvents()
        
        # Gebruik één robuuste lus om ALLE pagina's te verversen
        pages_to_refresh = [
            getattr(self, "page_emp", None),
            getattr(self, "page_dashboard", None),
            getattr(self, "page_todo", None),
            getattr(self, "page_alerts", None),
            getattr(self, "page_future_trainings", None),
            getattr(self, "page_config", None),
            getattr(self, "page_staff_search", None), 
        ]

        for page in pages_to_refresh:
            try:
                if page is not None and hasattr(page, "refresh"):
                    page.refresh()
            except Exception as e:
                page_name = type(page).__name__ if page else "Onbekende Pagina"
                print(f"    ⚠️ Pagina refresh fout op {page_name}: {e}")

        now = datetime.now().strftime("%d-%m-%Y %H:%M")
        self.lbl_last_update.setText(f"Laatst bijgewerkt:\n{now}")
        
        if self.data.errors:
            error_count = len(self.data.errors)
            QMessageBox.warning(
                self,
                f"{error_count} Waarschuwing(en)",
                "Er zijn waarschuwingen tijdens het laden:\n\n" +
                "\n".join(self.data.errors[:10]) +
                (f"\n\n...en {error_count - 10} meer" if error_count > 10 else "")
            )
        
        todo_count = len(self.data.df.get("todo", pd.DataFrame()))
        staff_count = len(self.data.df.get("staff", pd.DataFrame()))
        
        status_msg = f"✅ Geladen: {staff_count} medewerkers, {todo_count} taken"
        if selected_costcenter:
            status_msg += f" (costcenter: {selected_costcenter})"
        
        self.statusBar().showMessage(status_msg, 10000)
        
        print("\n" + "="*60)
        print("🎉 APP OPSTARTEN VOLTOOID")
        print("="*60 + "\n")

    # def choose_costcenter(self):
        # """
        # Toont een dialoog om een costcenter te kiezen.
        # V43-FIX: Gebruikt de expliciete kolom 'staffCOSTCENTER315' zoals gevonden in de DB.
        # """
        # options = []
        # # De exacte kolomnaam in SQL Server
        # sql_col_name = "staffCOSTCENTER315"

        # try:
            # if self.data and self.data.sql_staff_manager and self.data.sql_staff_manager.engine:
                # from sqlalchemy import text
                # import pandas as pd
                
                # print(f"   🔍 SQL Lookup: Ophalen unieke waarden uit {sql_col_name}...")
                
                # # Query op de specifieke kolom
                # query = text(f"""
                    # SELECT DISTINCT {sql_col_name} 
                    # FROM dbo.tblSTAFF 
                    # WHERE {sql_col_name} IS NOT NULL AND {sql_col_name} <> ''
                    # ORDER BY {sql_col_name}
                # """)
                
                # with self.data.sql_staff_manager.engine.connect() as conn:
                    # df_cc = pd.read_sql(query, conn)
                    
                    # if not df_cc.empty:
                        # # De kolomnaam in het resultaat is ook staffCOSTCENTER315
                        # vals = df_cc[sql_col_name].astype(str).str.strip().unique()
                        # options = sorted([v for v in vals if v.lower() != 'nan'])
                        # print(f"   🏢 SQL: {len(options)} afdelingen gevonden.")
            
        # except Exception as e:
            # print(f"   ⚠️ Kon CostCenters niet uit SQL halen: {e}")

        # # Fallback: Check geheugen als SQL faalde
        # if not options:
            # try:
                # if "staff" in self.data.df:
                    # staff_df = self.data.df["staff"]
                    # # Check of de hernoemde kolom 'CostCenter' bestaat, of de originele
                    # target = "CostCenter" if "CostCenter" in staff_df.columns else sql_col_name
                    
                    # if target in staff_df.columns:
                        # vals = staff_df[target].astype(str).unique()
                        # options = sorted([v for v in vals if v.lower() != 'nan'])
            # except: pass

        # if not options:
            # QMessageBox.warning(self, "Geen data", f"Kon geen afdelingen vinden in kolom '{sql_col_name}'.")
            # return

        # # Huidige selectie vinden
        # current = getattr(self.data, 'active_costcenter', "")
        # current_index = 0
        # if current and str(current) in options:
            # current_index = options.index(str(current))
            
        # # Toon dialoog
        # item, ok = QInputDialog.getItem(
            # self, 
            # "Afdeling Selecteren", 
            # "Kies een CostCenter (WBS):", 
            # options, 
            # current_index, 
            # False 
        # )

        # if ok and item:
            # self.data.active_costcenter = item
            # print(f"   ✅ Nieuwe keuze ingesteld: {item}")
    def choose_costcenter(self):
        """
        Toont een dialoog om een costcenter te kiezen (Code + Duidelijke Naam).
        V45-FIX: Gebruikt 'staffORGUNIT' als omschrijving omdat dit de duidelijkste afdelingsnaam is.
        Technisch filteren we nog steeds op 'staffCOSTCENTER315'.
        """
        options_display = [] # Wat de gebruiker ziet: "Code - OrgUnit"
        options_map = {}     # Vertaalt keuze terug naar "Code"
        
        # De kolomnamen in SQL
        col_code = "staffCOSTCENTER315" # De technische sleutel
        col_name = "staffORGUNIT"       # De leesbare naam (bv. "Pool BC Buildings Nivelles")

        try:
            if self.data and self.data.sql_staff_manager and self.data.sql_staff_manager.engine:
                from sqlalchemy import text
                import pandas as pd
                
                print(f"   🔍 SQL Lookup: Ophalen codes ({col_code}) en namen ({col_name})...")
                
                # Haal unieke combinaties op
                query = text(f"""
                    SELECT DISTINCT {col_code}, {col_name}
                    FROM dbo.tblSTAFF 
                    WHERE {col_code} IS NOT NULL AND {col_code} <> ''
                    ORDER BY {col_code}
                """)
                
                with self.data.sql_staff_manager.engine.connect() as conn:
                    df = pd.read_sql(query, conn)
                    
                    if not df.empty:
                        for _, row in df.iterrows():
                            code = str(row[col_code]).strip()
                            # Haal de OrgUnit op als naam
                            name = str(row[col_name]).strip() if row[col_name] else ""
                            
                            # Maak de weergave tekst
                            if name and name.lower() != "nan" and name != "None":
                                display_text = f"{code} - {name}"
                            else:
                                display_text = code
                                
                            options_display.append(display_text)
                            options_map[display_text] = code
                            
                        print(f"   🏢 SQL: {len(options_display)} afdelingen geladen.")
            
        except Exception as e:
            print(f"   ⚠️ Kon CostCenters niet uit SQL halen: {e}")

        # Fallback (Geheugen) als SQL faalt
        if not options_display:
            try:
                if "staff" in self.data.df:
                    staff_df = self.data.df["staff"]
                    # We gebruiken hier de interne naam 'CostCenter' (want die is al hernoemd in load_all)
                    if "CostCenter" in staff_df.columns:
                        unique_codes = sorted(staff_df["CostCenter"].astype(str).unique())
                        for code in unique_codes:
                            name = ""
                            # Probeer staffORGUNIT te vinden in geheugen (als die kolom bestaat)
                            # Let op: load_all haalt select * op, dus staffORGUNIT zou erin moeten zitten.
                            if col_name in staff_df.columns:
                                match = staff_df[staff_df["CostCenter"] == code]
                                if not match.empty:
                                    val = match.iloc[0][col_name]
                                    if val and str(val).lower() != 'nan':
                                        name = str(val)
                            
                            display_text = f"{code} - {name}" if name else code
                            options_display.append(display_text)
                            options_map[display_text] = code
            except: pass

        if not options_display:
            QMessageBox.warning(self, "Geen data", "Kon geen afdelingen vinden.")
            return

        # Zoek huidige selectie
        current_code = getattr(self.data, 'active_costcenter', "")
        current_index = 0
        
        for idx, text_opt in enumerate(options_display):
            if options_map[text_opt] == str(current_code):
                current_index = idx
                break
            
        # Toon dialoog
        item, ok = QInputDialog.getItem(
            self, 
            "Afdeling Selecteren", 
            "Kies een afdeling:", 
            options_display, 
            current_index, 
            False 
        )

        if ok and item:
            # We slaan alleen de code op (bijv. 10O4B2)
            real_code = options_map.get(item, item)
            self.data.active_costcenter = real_code
            print(f"   ✅ Nieuwe keuze: {real_code} ({item})")
    
    # def choose_costcenter(self):
        # """
        # Toont een dialoog om een costcenter te kiezen.
        # V41-FIX: 
        # 1. Verwijdert 'WHERE Active=1' omdat die kolom mogelijk niet bestaat in tblSTAFF.
        # 2. Voegt extra checks toe bij de fallback om KeyError te voorkomen.
        # """
        # options = []
        # try:
            # # Probeer direct uit SQL (Bypasst geheugen-filter)
            # if self.data and self.data.sql_staff_manager and self.data.sql_staff_manager.engine:
                # from sqlalchemy import text
                # import pandas as pd
                
                # print("   🔍 SQL Lookup: Alle CostCenters ophalen...")
                # # VEILIGE QUERY: Geen aannames over 'Active' kolom
                # query = text("""
                    # SELECT DISTINCT CostCenter 
                    # FROM dbo.tblSTAFF 
                    # WHERE CostCenter IS NOT NULL AND CostCenter <> ''
                    # ORDER BY CostCenter
                # """)
                
                # with self.data.sql_staff_manager.engine.connect() as conn:
                    # df_cc = pd.read_sql(query, conn)
                    # # Maak er een nette lijst van
                    # if not df_cc.empty and "CostCenter" in df_cc.columns:
                        # options = sorted(df_cc["CostCenter"].astype(str).str.strip().unique())
                        # print(f"   🏢 Gevonden in SQL: {len(options)} afdelingen.")
            
        # except Exception as e:
            # print(f"   ⚠️ Kon CostCenters niet uit SQL halen: {e}")
            
        # # Fallback: gebruik geheugen als SQL faalde of leeg was
        # if not options:
            # try:
                # if "staff" in self.data.df:
                    # staff_df = self.data.df["staff"]
                    # if not staff_df.empty and "CostCenter" in staff_df.columns:
                        # options = sorted(staff_df["CostCenter"].astype(str).unique())
                        # print(f"   🏢 Fallback: {len(options)} afdelingen uit geheugen.")
            # except Exception as mem_err:
                # print(f"   ❌ Fallback mislukt: {mem_err}")

        # # Als er ECHT niks is gevonden
        # if not options:
            # # Noodoplossing: Voeg desnoods handmatig wat toe of toon lege lijst
            # print("   ❌ Geen costcenters gevonden in SQL of Geheugen.")
            # # Je zou hier kunnen kiezen om de app niet te laten crashen:
            # # options = ["Onbekend"] 
            # # Maar een waarschuwing is beter:
            # QMessageBox.warning(self, "Geen data", 
                # "Kon geen afdelingen vinden.\nCheck database connectie of kolomnamen.")
            # return

        # # Huidige selectie vinden
        # current = getattr(self.data, 'active_costcenter', "")
        # current_index = 0
        # if current and str(current) in options:
            # current_index = options.index(str(current))
            
        # # Toon dialoog
        # item, ok = QInputDialog.getItem(
            # self, 
            # "Afdeling Selecteren", 
            # "Kies een CostCenter:", 
            # options, 
            # current_index, 
            # False 
        # )

        # if ok and item:
            # self.data.active_costcenter = item
            # print(f"   ✅ Nieuwe keuze ingesteld: {item}")
    # # =========================================================================
    # # FIX VOOR HET KIEZEN VAN AFDELINGEN (SQL LOOKUP)
    # # =========================================================================

    # def choose_costcenter(self):
        # """
        # Toont een dialoog om een costcenter te kiezen.
        # V40-FIX: Haalt de lijst rechtstreeks uit SQL (dbo.tblSTAFF) zodat we 
        # ALLE afdelingen zien, ook als het geheugen gefilterd is op één afdeling.
        # """
        # options = []
        # try:
            # # Probeer de lijst direct uit SQL te halen (Bypasst de geheugen-filter)
            # if self.data and self.data.sql_staff_manager and self.data.sql_staff_manager.engine:
                # from sqlalchemy import text
                # import pandas as pd
                
                # print("   🔍 SQL Lookup: Alle CostCenters ophalen...")
                # query = text("""
                    # SELECT DISTINCT CostCenter 
                    # FROM dbo.tblSTAFF 
                    # WHERE Active = 1 AND CostCenter IS NOT NULL AND CostCenter <> ''
                    # ORDER BY CostCenter
                # """)
                
                # with self.data.sql_staff_manager.engine.connect() as conn:
                    # df_cc = pd.read_sql(query, conn)
                    # # Maak er een nette lijst van strings van
                    # options = sorted(df_cc["CostCenter"].astype(str).str.strip().unique())
                    # print(f"   🏢 Gevonden in SQL: {len(options)} afdelingen.")
            
        # except Exception as e:
            # print(f"   ⚠️ Kon CostCenters niet uit SQL halen: {e}")
            # # Fallback: gebruik wat we in het geheugen hebben
            # if "staff" in self.data.df:
                # options = sorted(self.data.df["staff"]["CostCenter"].astype(str).unique())

        # if not options:
            # QMessageBox.warning(self, "Geen data", "Geen costcenters gevonden in de database.")
            # return

        # # Huidige selectie vinden voor de dropdown
        # current = getattr(self.data, 'active_costcenter', "")
        # current_index = 0
        # if current and str(current) in options:
            # current_index = options.index(str(current))
            
        # # Toon de dialoog
        # item, ok = QInputDialog.getItem(
            # self, 
            # "Afdeling Wisselen", 
            # "Kies een CostCenter:", 
            # options, 
            # current_index, 
            # False # Niet bewerkbaar (alleen selecteren)
        # )

        # if ok and item:
            # # Update de pointer in DataStore
            # self.data.active_costcenter = item
            # print(f"   ✅ Nieuwe keuze ingesteld: {item}")
    # def choose_costcenter(self):
        # staff = self.data.df.get("staff", pd.DataFrame())
        
        # if staff.empty:
            # self.data.active_costcenter = None
            # return
        
        # cc_col = None
        # for col in ["staffCOSTCENTER315", "staffCOSTCENTER", "CostCenter", "Costcenter", "Afdeling"]:
            # if col in staff.columns:
                # cc_col = col
                # break
        
        # if not cc_col:
            # self.data.active_costcenter = None
            # return
        
        # org_col = None
        # for col in ["staffORGUNIT", "OrgUnit", "Pool", "Afdeling_Naam", "Department"]:
            # if col in staff.columns:
                # org_col = col
                # break
        
        # options_dict = {}
        # tmp = staff.copy()
        # tmp[cc_col] = tmp[cc_col].astype(str).str.strip()
        
        # if org_col:
            # tmp[org_col] = tmp[org_col].astype(str).str.strip()
        
        # for cc in sorted(tmp[cc_col].dropna().unique().tolist()):
            # if not cc or cc.lower() == 'nan':
                # continue
            
            # if org_col:
                # units = tmp[tmp[cc_col] == cc][org_col].dropna().unique().tolist()
                # units = [u for u in units if u and u.lower() != 'nan']
                # if units:
                    # display_text = f"{cc} – {units[0]}"
                # else:
                    # display_text = cc
            # else:
                # display_text = cc
            
            # options_dict[display_text] = cc
        
        # if not options_dict:
            # self.data.active_costcenter = None
            # return
        
        # sorted_options = ["-- Alle afdelingen --"] + sorted(options_dict.keys())
        
        # choice, ok = QInputDialog.getItem(
            # self,
            # "Selecteer Costcenter",
            # "Kies een costcenter om mee te werken:\n\n"
            # "(Formaat: Costcenter – Afdelingsnaam)",
            # sorted_options,
            # 0,
            # False
        # )
        
        # if ok and choice:
            # if choice == "-- Alle afdelingen --":
                # self.data.active_costcenter = None
            # else:
                # selected_cc = options_dict.get(choice, choice.split(" – ")[0])
                # self.data.active_costcenter = selected_cc
        # else:
            # self.data.active_costcenter = None

    # def on_change_costcenter(self):
        # ok = self.data.load_all()
        # if not ok:
            # QMessageBox.critical(self, "Fout bij herladen data",
                                 # "\n".join(self.data.errors) or "Onbekende fout.")
            # return
        
        # self.choose_costcenter()
        # self.data.apply_costcenter_filter(self.data.active_costcenter)

        # self.data.sync_todo_with_config()
        # self.data.create_tasks_for_expiring_certificates()  # 🆕 Scan certificates op vervaldata
        # self.data.merge_todo_with_config()
        # self.data.sync_competence_tasks()
        # self.data.update_status_from_tasktype_and_xaurum()
        # self.data.apply_overrule_with_zweef()

        # # 💾 Verrijk todo met staff info (CostCenter, MedewerkerNaam) en sla op naar SQL
        # self.data.enrich_todo_with_staff_info()
        # self.data.save_todo()

        # # Update alle tabs bij Costcenter wijziging
        # self.page_emp.refresh()
        # self.page_dashboard.refresh()
        # self.page_todo.refresh()
        # self.page_alerts.refresh()
        
        # if hasattr(self, "page_future_trainings"):
             # self.page_future_trainings.refresh()
        
        # if hasattr(self, "page_staff_search"):
             # self.page_staff_search.refresh()

        # now = datetime.now().strftime("%d-%m-%Y %H:%M")
        # self.lbl_last_update.setText(f"Laatst bijgewerkt:\n{now}")
        
        # self.statusBar().showMessage("Costcenter gewijzigd", 5000)
    # def on_change_costcenter(self):
        # """
        # FIXED: Eerst kiezen, DAN laden met filter.
        # Voorkomt dat 'load_all()' per ongeluk alle data ophaalt omdat er nog geen filter is.
        # """
        # # 1. EERST KIEZEN (De oogkleppen opzetten)
        # self.choose_costcenter()
        # selected_cc = getattr(self.data, 'active_costcenter', None)

        # # Als de gebruiker op Cancel drukt of 'Alle afdelingen' kiest (None), 
        # # is dat ook een keuze. We gaan door.

        # # 2. DAN PAS LADEN (Met de filter direct actief!)
        # # Hierdoor voert DataStore Stap 10 direct de juiste SQL query uit (WHERE CostCenter = ...)
        # self.statusBar().showMessage(f"Data laden voor {selected_cc or 'alle afdelingen'}...")
        # QApplication.processEvents()

        # ok = self.data.load_all(costcenter_filter=selected_cc)
        
        # if not ok:
            # QMessageBox.critical(self, "Fout bij herladen data",
                                 # "\n".join(self.data.errors) or "Onbekende fout.")
            # return
        
        # # 3. Extra zekerheid (Memory filter)
        # self.data.apply_costcenter_filter(self.data.active_costcenter)

        # # 4. Syncen & Opslaan (Nu veilig omdat we alleen de juiste data hebben)
        # self.data.sync_todo_with_config()
        # self.data.create_tasks_for_expiring_certificates()
        # self.data.merge_todo_with_config()
        # self.data.sync_competence_tasks()
        # self.data.update_status_from_tasktype_and_xaurum()
        # self.data.apply_overrule_with_zweef()

        # # 💾 Verrijk todo en sla op
        # self.data.enrich_todo_with_staff_info()
        # self.data.save_todo()

        # # 5. UI Verversen
        # self.page_emp.refresh()
        # self.page_dashboard.refresh()
        # self.page_todo.refresh()
        # self.page_alerts.refresh()
        # self.page_discrepancy.refresh() # Zorg dat deze ook ververst
        
        # if hasattr(self, "page_staff_search"):
             # self.page_staff_search.refresh()

        # now = datetime.now().strftime("%d-%m-%Y %H:%M")
        # self.lbl_last_update.setText(f"Laatst bijgewerkt:\n{now}")
        
        # self.statusBar().showMessage(f"Costcenter gewijzigd naar {selected_cc}", 5000)
    def on_change_costcenter(self):
        """
        FIXED WORKFLOW:
        1. Gebruiker kiest uit de VOLLEDIGE SQL lijst (via choose_costcenter V40).
        2. DataStore laadt data SPECIFIEK voor die keuze (via load_all V38).
        3. UI ververst.
        """
        # 1. EERST KIEZEN (De gebruiker moet kunnen kiezen uit alles)
        self.choose_costcenter()
        
        # Haal de keuze op die zojuist is gezet
        selected_cc = getattr(self.data, 'active_costcenter', None)

        # Als er geannuleerd is of niets gekozen, stoppen we (of herladen we huidig)
        # We gaan door om de view te verversen/bevestigen.

        # 2. DAN PAS LADEN (Met de filter direct actief!)
        self.statusBar().showMessage(f"Data laden voor {selected_cc}...")
        QApplication.processEvents()

        # Dit roept DataStore Stap 10 aan, die nu de query "WHERE CostCenter = '...'" doet
        ok = self.data.load_all(costcenter_filter=selected_cc)
        
        if not ok:
            QMessageBox.critical(self, "Fout", "Kon data niet laden voor deze afdeling.")
            return
        
        # 3. Extra zekerheid (Memory filter)
        self.data.apply_costcenter_filter(self.data.active_costcenter)

        # 4. Syncen & Opslaan (Nu veilig omdat we alleen de juiste data hebben)
        self.data.sync_todo_with_config()
        self.data.create_tasks_for_expiring_certificates()
        self.data.merge_todo_with_config()
        self.data.sync_competence_tasks()
        self.data.update_status_from_tasktype_and_xaurum()
        
        # 💾 Verrijk todo en sla op (Schoont oude data van DEZE afdeling op in SQL)
        self.data.enrich_todo_with_staff_info()
        self.data.save_todo()

        # 5. UI Verversen
        self.page_emp.refresh()
        self.page_dashboard.refresh()
        self.page_todo.refresh()
        self.page_alerts.refresh()
        if hasattr(self, "page_discrepancy"): self.page_discrepancy.refresh()
        if hasattr(self, "page_staff_search"): self.page_staff_search.refresh()

        # Update labels
        now = datetime.now().strftime("%d-%m-%Y %H:%M")
        if hasattr(self, "lbl_last_update"):
            self.lbl_last_update.setText(f"Laatst bijgewerkt:\n{now}")
        
        self.statusBar().showMessage(f"Succesvol gewisseld naar {selected_cc}", 5000)
    
    
    def on_refresh_xaurum_data(self):
        reply = QMessageBox.question(
            self,
            "Data verversen",
            "Wil je alle Xaurum-data opnieuw laden?\n\n"
            "Dit herlaadt de volgende bestanden:\n"
            "• Certificates_Overview_ready.xlsx\n"
            "• Certification_Results_overview.xlsx\n"
            "• Training_Req_Xaurum_ready.xlsx\n"
            "• Competences_Overview_ready.xlsx\n\n"
            "Niet-opgeslagen wijzigingen in Medewerkerbeheer gaan verloren.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.btn_refresh_data.setEnabled(False)
            self.btn_refresh_data.setText("LADEN...")
            self.statusBar().showMessage("Xaurum data verversen...")
            QApplication.processEvents()
        except Exception:
            pass

        try:
            try:
                self._show_file_status()
            except Exception:
                pass

            current_cc = getattr(self.data, "active_costcenter", None)

            ok = False
            try:
                ok = self.data.load_all(costcenter_filter=current_cc)
            except TypeError:
                ok = self.data.load_all()
            except Exception as e:
                logger.exception("Fout bij load_all met filter: %s", e)
                ok = False

            if not ok:
                try:
                    QMessageBox.warning(
                        self,
                        "Waarschuwing bij laden",
                        "Data is geladen, maar met waarschuwingen:\n\n" +
                        "\n".join(getattr(self.data, "errors", [])[:10])
                    )
                except Exception:
                    pass

            try:
                self.data.apply_costcenter_filter(current_cc)
            except Exception:
                pass

            for fn in (
                "sync_todo_with_config",
                "create_tasks_for_expiring_certificates",  # 🆕 Scan certificates op vervaldata
                "merge_todo_with_config",
                "sync_competence_tasks",
                "update_status_from_tasktype_and_xaurum",
                "apply_overrule_with_zweef",
                "close_finished_tasks",
            ):
                try:
                    if hasattr(self.data, fn):
                        getattr(self.data, fn)()
                except Exception:
                    logger.exception("Post-load functie %s faalde", fn)

            # 💾 Verrijk todo met staff info (CostCenter, MedewerkerNaam) en sla op naar SQL
            try:
                self.data.enrich_todo_with_staff_info()
                self.data.save_todo()
            except Exception:
                logger.exception("enrich/save_todo faalde")

            # Eén enkele veilige lus voor alle tabbladen
            for page in (getattr(self, "page_emp", None),
                          getattr(self, "page_dashboard", None),
                          getattr(self, "page_todo", None),
                          getattr(self, "page_alerts", None),
                          getattr(self, "page_future_trainings", None),
                          getattr(self, "page_config", None),
                          getattr(self, "page_staff_search", None)):
                try:
                    if page is not None and hasattr(page, "refresh"):
                        page.refresh()
                except Exception:
                    pass

            try:
                now = datetime.now().strftime("%d-%m-%Y %H:%M")
                if hasattr(self, "lbl_last_update"):
                    self.lbl_last_update.setText(f"Laatst bijgewerkt:\n{now}")
            except Exception:
                pass

            try:
                self.statusBar().showMessage("✅ Xaurum data succesvol ververst!", 5000)
                self._show_refresh_summary()
            except Exception:
                pass

        except Exception as e:
            logger.exception("Onverwachte fout in refresh flow")
            try:
                QMessageBox.critical(
                    self,
                    "Fout bij verversen",
                    f"Er is een fout opgetreden bij het verversen van de data:\n\n{e}"
                )
                self.statusBar().showMessage("❌ Fout bij verversen data", 5000)
            except Exception:
                pass

        finally:
            try:
                self.btn_refresh_data.setEnabled(True)
                self.btn_refresh_data.setText("DATA VERVERSEN")
            except Exception:
                pass
    
    def _show_file_status(self):
        print("\n" + "=" * 60)
        print("📊 XAURUM BESTANDSSTATUS")
        print("=" * 60)
        
        files_to_check = {
            "Certificates": INPUT_FILES.get("certificates"),
            "Cert Results": INPUT_FILES.get("cert_results"),
            "Training Req": INPUT_FILES.get("training_req"),
            "Competences": INPUT_FILES.get("competences"),
        }
        
        for name, path in files_to_check.items():
            if path and path.exists():
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                age = datetime.now() - mtime
                if age.days > 0:
                    age_str = f"{age.days}d {age.seconds//3600}u"
                else:
                    age_str = f"{age.seconds//3600}u {(age.seconds%3600)//60}m"
                print(f"    ✅ {name:20} | {mtime.strftime('%d-%m-%Y %H:%M')} | ({age_str} oud)")
            else:
                print(f"    ❌ {name:20} | NIET GEVONDEN")
        
        print("=" * 60 + "\n")

    def _show_refresh_summary(self):
        staff_df = self.data.df.get("staff", pd.DataFrame())
        cert_df = self.data.df.get("certificates", pd.DataFrame())
        todo_df = self.data.df.get("todo", pd.DataFrame())
        comp_df = self.data.df.get("competences", pd.DataFrame())
        training_req_df = self.data.df.get("training_req", pd.DataFrame())
        
        staff_count = len(staff_df) if not staff_df.empty else 0
        cert_count = len(cert_df) if not cert_df.empty else 0
        todo_count = len(todo_df) if not todo_df.empty else 0
        comp_count = len(comp_df) if not comp_df.empty else 0
        training_count = len(training_req_df) if not training_req_df.empty else 0
        
        filter_text = self.data.active_costcenter or "Alle afdelingen"
        
        QMessageBox.information(
            self,
            "Data ververst",
            f"✅ Xaurum data succesvol ververst!\n\n"
            f"📊 Samenvatting:\n"
            f"• {staff_count} actieve medewerkers\n"
            f"• {cert_count} certificaten\n"
            f"• {todo_count} taken in planner\n"
            f"• {comp_count} competenties\n"
            f"• {training_count} ingeschreven opleidingen\n\n"
            f"🏢 Filter: {filter_text}"
        )

    def open_employee_from_planner(self, emp_name: str):
        self.show_page(1)
        self.page_emp.select_employee_by_name(emp_name)