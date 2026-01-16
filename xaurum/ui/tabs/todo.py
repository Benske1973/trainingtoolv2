
import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# PyQt6 Imports
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QLineEdit, QScrollArea, QMessageBox, QGroupBox, QFrame,
    QAbstractItemView, QCheckBox, QApplication
)
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QColor, QDesktopServices, QBrush, QFont

# Xaurum project specifieke imports
from xaurum.core.datastore import DataStore
from xaurum.ui.widgets import ToggleSwitch, TodoRowWidget 
from xaurum.ui.dialogs import (
    IngeschrevenWizard, SelfRegisteredDialog, ReplacementCandidatesDialog
)

# 1. De dataclass moet ALTIJD direct boven een class staan
@dataclass
class StatusToggleInfo:
    key: str
    label: str
    nodig: bool
    widget: Any = None

class TodoTab(QWidget):
    def __init__(self, data_store: DataStore, open_employee_callback=None):
        super().__init__()
        self.data = data_store
        self.open_employee_callback = open_employee_callback
        self._task_widgets: List[TodoRowWidget] = [] 

        self.status_toggles: List[StatusToggleInfo] = [
            StatusToggleInfo("Open", "Open", True),
            StatusToggleInfo("Ingeschreven", "Ingeschreven", True),
            StatusToggleInfo("Afgewerkt", "Afgewerkt", True),
            StatusToggleInfo("On Hold", "On Hold", False),
            StatusToggleInfo("Afwezig (ziekte)", "Afwezig (ziekte)", False),
            StatusToggleInfo("In Wachtrij", "In Wachtrij", False),
            StatusToggleInfo("Geweigerd", "Geweigerd", False),
        ]
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("🗓️ Planner / To-do-lijst")
        title.setStyleSheet("font-family: 'Segoe UI'; font-size: 22px; font-weight: bold; color: #00263D;")
        layout.addWidget(title)

        subtitle = QLabel("Beheer opleidingen. Standaard: Open/Ingeschreven binnen 6 maanden.")
        subtitle.setStyleSheet("font-family: 'Segoe UI'; color: #64748b; font-size: 12px;")
        layout.addWidget(subtitle)

        self.lbl_stats = QLabel("Laden...")
        self.lbl_stats.setStyleSheet("font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; color: #00263D;")
        layout.addWidget(self.lbl_stats)

        # --- SLIMME FILTERS (Clean & Focus) ---
        self.status_filter_layout = QHBoxLayout()
        self.status_filter_layout.setSpacing(15)

        lbl_filter = QLabel("Extra Filters:")
        lbl_filter.setStyleSheet("font-family: 'Segoe UI'; font-size: 11px; font-weight: bold; color: #333;")
        self.status_filter_layout.addWidget(lbl_filter)

        # 1. TOON VERLOPEN (Rood)
        exp_cont = QWidget(); exp_lay = QVBoxLayout(exp_cont); exp_lay.setContentsMargins(0,0,0,0); exp_lay.setSpacing(2)
        self.toggle_show_expired = ToggleSwitch(checked=False)
        #self.toggle_show_expired.toggled.connect(self.on_status_filter_changed)
        self.toggle_show_expired.toggled.connect(self.refresh)
        exp_lay.addWidget(self.toggle_show_expired, alignment=Qt.AlignmentFlag.AlignHCenter)
        exp_lay.addWidget(QLabel("Toon Verlopen", styleSheet="font-size:10px; color:red; font-weight:bold;"), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.status_filter_layout.addWidget(exp_cont)

        # 2. WACHT OP XAURUM (Blauw)
        sync_cont = QWidget(); sync_lay = QVBoxLayout(sync_cont); sync_lay.setContentsMargins(0,0,0,0); sync_lay.setSpacing(2)
        self.toggle_pending_xaurum = ToggleSwitch(checked=False)
        #self.toggle_pending_xaurum.toggled.connect(self.on_status_filter_changed)
        self.toggle_pending_xaurum.toggled.connect(self.refresh)
        sync_lay.addWidget(self.toggle_pending_xaurum, alignment=Qt.AlignmentFlag.AlignHCenter)
        sync_lay.addWidget(QLabel("Wacht op Xaurum", styleSheet="font-size:10px; color:#005596; font-weight:bold;"), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.status_filter_layout.addWidget(sync_cont)

        # 3. LAATSTE 3 MAANDEN (Groen)
        recent_cont = QWidget(); rec_lay = QVBoxLayout(recent_cont); rec_lay.setContentsMargins(0,0,0,0); rec_lay.setSpacing(2)
        self.toggle_show_recent = ToggleSwitch(checked=False)
        #self.toggle_show_recent.toggled.connect(self.on_status_filter_changed)
        self.toggle_show_recent.toggled.connect(self.refresh)
        rec_lay.addWidget(self.toggle_show_recent, alignment=Qt.AlignmentFlag.AlignHCenter)
        rec_lay.addWidget(QLabel("Laatste 3 mnd", styleSheet="font-size:10px; color:green; font-weight:bold;"), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.status_filter_layout.addWidget(recent_cont)

        self.status_filter_layout.addStretch()
        layout.addLayout(self.status_filter_layout)

        # --- WIDGET AREA ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #cbd5e1; border-radius: 4px; background: #f8fafc; }")
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(5, 5, 5, 5); self.task_layout.setSpacing(2); self.task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.task_container)
        layout.addWidget(self.scroll_area, stretch=1)
        
        # --- KNOPPEN BALK ---
        btn_white = "background-color: white; color: #333; border: 1px solid #cbd5e1; padding: 6px 12px; font-size: 12px; border-radius: 4px;"
        btn_blue = "background-color: #002439; color: white; border: none; padding: 6px 12px; font-size: 12px; font-weight: bold; border-radius: 4px;"
        btn_xaurum_style = "background-color: #005596; color: white; border: none; padding: 6px 12px; font-size: 12px; font-weight: bold; border-radius: 4px;"
        
        btn_row = QHBoxLayout()

        self.btn_xaurum = QPushButton("🔗 Zoek in Xaurum")
        self.btn_xaurum.setStyleSheet(btn_xaurum_style)
        self.btn_xaurum.clicked.connect(self.on_open_xaurum)

        self.btn_mark_inschreven = QPushButton("Inschrijven (Wizard)"); self.btn_mark_inschreven.setStyleSheet(btn_blue)
        self.btn_mark_inschreven.clicked.connect(self.on_open_wizard)
        self.btn_mark_self = QPushButton("Zelf ingeschreven"); self.btn_mark_self.setStyleSheet(btn_white)
        self.btn_mark_self.clicked.connect(self.on_mark_self_registered)
        self.btn_cancel = QPushButton("🚫 Afmelden / Annuleren"); self.btn_cancel.setStyleSheet(btn_white)
        self.btn_cancel.clicked.connect(self.on_cancel_or_cannot_attend)
        self.btn_replace = QPushButton("Zoek vervanger"); self.btn_replace.setStyleSheet(btn_white)
        self.btn_replace.clicked.connect(self.on_find_replacements)
        # self.btn_full_cancel = QPushButton("Annulatie"); self.btn_full_cancel.setStyleSheet(btn_white)
        # self.btn_full_cancel.clicked.connect(self.on_full_cancel)
        # Voeg de nieuwe Mail Academy knop toe
        self.btn_mail_academy = QPushButton("📧 Mail Academy")
        self.btn_mail_academy.setStyleSheet(btn_white) # Of btn_blue als je hem wilt laten opvallen
        self.btn_mail_academy.clicked.connect(self.on_trigger_academy_mail)
        
        self.btn_link = QPushButton("Link Opleiding"); self.btn_link.setStyleSheet(btn_white)
        self.btn_link.clicked.connect(self.on_open_training_for_selected)
        self.btn_goto_emp = QPushButton("Naar Medewerker"); self.btn_goto_emp.setStyleSheet(btn_white)
        self.btn_goto_emp.clicked.connect(self.on_open_employee)
        
        self.btn_del = QPushButton("🗑️"); self.btn_del.setFixedSize(32, 28); self.btn_del.setStyleSheet("background: #fee2e2; color: #dc2626; border-radius:4px;")
        self.btn_del.clicked.connect(self.on_delete_task)
        
        # for b in [self.btn_xaurum, self.btn_mark_inschreven, self.btn_mark_self, self.btn_cancel, self.btn_replace, self.btn_full_cancel, self.btn_link, self.btn_goto_emp]:
            # btn_row.addWidget(b)
        
        for b in [self.btn_xaurum, self.btn_mark_inschreven, self.btn_mark_self, self.btn_cancel, self.btn_replace, self.btn_mail_academy, self.btn_link, self.btn_goto_emp]:
            btn_row.addWidget(b)
        
        btn_row.addStretch(); btn_row.addWidget(self.btn_del)
        layout.addLayout(btn_row)

        self.info_label = QLabel("Legende: ⛔=Herkansing • 🔴=Open • 🟡=Ingeschreven • 🟢=Afgewerkt • 📊=Competentie")
        self.info_label.setStyleSheet("color: #64748b; font-size: 11px; margin-bottom: 5px;")
        layout.addWidget(self.info_label)

        # --- DETAILS ---
        detail_group = QGroupBox("Details geselecteerde taak")
        detail_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #cbd5e1; border-radius: 4px; margin-top: 10px; padding: 10px; }")
        d_layout = QVBoxLayout(detail_group)
        r1 = QHBoxLayout()
        self.lbl_sel_emp = QLabel("Medewerker: -"); r1.addWidget(self.lbl_sel_emp)
        self.lbl_sel_cert = QLabel("Opleiding: -"); r1.addWidget(self.lbl_sel_cert)
        d_layout.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Status:"))
        self.cmb_status = QComboBox(); self.cmb_status.addItems(["Open", "Ingeschreven", "Afgewerkt", "On Hold", "Afwezig (ziekte)", "In Wachtrij", "Geweigerd"])
        r2.addWidget(self.cmb_status)
        r2.addWidget(QLabel("Detail:")); self.txt_detail = QLineEdit(); r2.addWidget(self.txt_detail)
        self.btn_save_status = QPushButton("Status opslaan"); self.btn_save_status.setStyleSheet(btn_blue)
        self.btn_save_status.clicked.connect(self.on_save_status); r2.addWidget(self.btn_save_status)
        d_layout.addLayout(r2)
        layout.addWidget(detail_group)
    
    # def refresh(self):
        # """
        # Verbeterde Refresh: Herstelt 'Niet geslaagd' en koppelt Excel-data 
        # voor de 'Wacht op Xaurum' en 'Historiek' filters.
        # """
        # if not hasattr(self, 'data') or self.data is None: return
        
        # # 1. Herladen uit SQL
        # if self.data.USE_SQL_FOR_TODO and self.data.sql_training_manager:
            # try:
                # fresh_todo = self.data.sql_training_manager.get_todo_planner()
                # if not fresh_todo.empty:
                    # self.data.df["todo"] = fresh_todo
            # except Exception as e: print(f"Error reload SQL: {e}")

        # # 2. Basis data
        # self.data.apply_overrule_with_zweef()
        # todo = self.data.df.get("todo", pd.DataFrame()).copy()
        # if todo.empty: 
            # self.populate_widgets(todo)
            # return

        # # 3. Filter op CostCenter
        # if self.data.active_costcenter and "CostCenter" in todo.columns:
            # todo = todo[todo["CostCenter"].astype(str) == str(self.data.active_costcenter)]

        # # 4. Excel data ophalen voor de 'Wacht op Xaurum' check
        # # We kijken in de 'certificates' (Excel) om te zien of we daar nieuwere info hebben
        # certs_excel = self.data.df.get("certificates", pd.DataFrame())
        # excel_lookup = {}
        # if not certs_excel.empty:
            # for _, r in certs_excel.iterrows():
                # key = (str(r.get("staffGID")).strip(), str(r.get("CertName_norm")).strip())
                # excel_lookup[key] = r.get("StartDatum") or r.get("IssuedDate")

        # today = pd.Timestamp.now().normalize()
        # horizon_6m = today + pd.DateOffset(months=6)
        # historie_3m = today - pd.DateOffset(months=3)

        # def should_show(row):
            # status = str(row.get("Status", "")).lower()
            # detail = str(row.get("Status_Detail", "")).lower()
            # gid = str(row.get("staffGID", "")).strip()
            # norm = str(row.get("CertName_norm", "")).strip()
            
            # # --- A. ALTIJD PRIORITEIT: Niet-geslaagden & Ingeschreven ---
            # # Deze negeren alle datum-filters
            # if any(x in detail for x in ["niet geslaagd", "failed", "herkansing"]):
                # return True
            
            # if status == "ingeschreven":
                # return True

            # # --- B. DATUM BEREKENING ---
            # exp = pd.to_datetime(row.get("ExpiryDate"), errors='coerce')
            # days_until = row.get("DaysUntilExpiry")
            # try:
                # days_until = int(float(days_until)) if pd.notna(days_until) else 999
            # except:
                # days_until = 999

            # # --- C. STANDAARD (Open binnen 6 maanden) ---
            # if status == "open" and 0 <= days_until <= 180:
                # return True
            
            # # --- D. TOGGLE: VERLOPEN (Rood) ---
            # if self.toggle_show_expired.isChecked() and status == "open":
                # if days_until < 0:
                    # return True

            # # --- E. TOGGLE: WACHT OP XAURUM (Blauw) ---
            # if self.toggle_pending_xaurum.isChecked():
                # # We checken of de GID+Opleiding combinatie voorkomt in onze Excel-lijst
                # # terwijl de status in de planner nog op 'Open' of 'Ingeschreven' staat.
                # if (gid, norm) in excel_lookup and status != "afgewerkt":
                    # return True

            # # --- F. TOGGLE: LAATSTE 3 MAANDEN (Groen) ---
            # if self.toggle_show_recent.isChecked() and status == "afgewerkt":
                # # Omdat 'BehaaldOp' niet in je SQL tabel zit, gebruiken we 'LastUpdatedAt' 
                # # als indicatie van wanneer de taak is afgerond.
                # finish_date = pd.to_datetime(row.get("LastUpdatedAt"), errors='coerce')
                # if pd.notna(finish_date) and finish_date >= historie_3m:
                    # return True
            
            # return False

        # # 5. Filter toepassen en sorteren
        # filtered_todo = todo[todo.apply(should_show, axis=1)].copy()
        
        # def sort_priority(r):
            # st = str(r.get("Status", "")).lower()
            # det = str(r.get("Status_Detail", "")).lower()
            # if "niet geslaagd" in det: return 0
            # if r.get("DaysUntilExpiry", 0) and float(r.get("DaysUntilExpiry")) < 0: return 1
            # if st == "open": return 2
            # if st == "ingeschreven": return 3
            # return 4

        # filtered_todo['prio'] = filtered_todo.apply(sort_priority, axis=1)
        # filtered_todo = filtered_todo.sort_values(['prio', 'MedewerkerNaam'])
        
        # self.lbl_stats.setText(f"Taken getoond: {len(filtered_todo)}")
        # self.populate_widgets(filtered_todo)
    
    def refresh(self):
        """
        Volledige Refresh: Sorteert gepasseerde opleidingen naar onderen
        en geeft ze een lagere prioriteit voor de weergave.
        """
        if not hasattr(self, 'data') or self.data is None: return
        
        # 1. Herladen uit SQL
        if self.data.USE_SQL_FOR_TODO and self.data.sql_training_manager:
            try:
                fresh_todo = self.data.sql_training_manager.get_todo_planner()
                if not fresh_todo.empty:
                    self.data.df["todo"] = fresh_todo
            except Exception as e: print(f"Error reload SQL: {e}")

        # 2. Basis data
        self.data.apply_overrule_with_zweef()
        todo = self.data.df.get("todo", pd.DataFrame()).copy()
        if todo.empty: 
            self.populate_widgets(todo)
            return

        # 3. Filter op CostCenter
        if self.data.active_costcenter and "CostCenter" in todo.columns:
            todo = todo[todo["CostCenter"].astype(str) == str(self.data.active_costcenter)]

        # 4. Excel data & Tijd instellingen
        certs_excel = self.data.df.get("certificates", pd.DataFrame())
        excel_lookup = {}
        if not certs_excel.empty:
            for _, r in certs_excel.iterrows():
                key = (str(r.get("staffGID")).strip(), str(r.get("CertName_norm")).strip())
                excel_lookup[key] = r.get("StartDatum") or r.get("IssuedDate")

        today = pd.Timestamp.now().normalize()
        historie_3m = today - pd.DateOffset(months=3)

        # 5. Filter Logica
        def should_show(row):
            status = str(row.get("Status", "")).lower()
            detail = str(row.get("Status_Detail", "")).lower()
            gid = str(row.get("staffGID", "")).strip()
            norm = str(row.get("CertName_norm", "")).strip()
            
            # Altijd tonen: Niet-geslaagden & Ingeschreven (ook die in het verleden)
            if any(x in detail for x in ["niet geslaagd", "failed", "herkansing"]):
                return True
            if status == "ingeschreven":
                return True

            # Datum berekening voor Open taken
            days_until = row.get("DaysUntilExpiry")
            try:
                days_until = int(float(days_until)) if pd.notna(days_until) else 999
            except:
                days_until = 999

            # Filters voor Open taken
            if status == "open" and 0 <= days_until <= 180:
                return True
            if self.toggle_show_expired.isChecked() and status == "open" and days_until < 0:
                return True
            if self.toggle_pending_xaurum.isChecked() and (gid, norm) in excel_lookup and status != "afgewerkt":
                return True
            if self.toggle_show_recent.isChecked() and status == "afgewerkt":
                finish_date = pd.to_datetime(row.get("LastUpdatedAt"), errors='coerce')
                if pd.notna(finish_date) and finish_date >= historie_3m:
                    return True
            
            return False

        # Filter toepassen
        filtered_todo = todo[todo.apply(should_show, axis=1)].copy()
        
        # --- 6. NIEUWE SLIMME SORTERING ---
        def sort_priority(r):
            st = str(r.get("Status", "")).lower()
            det = str(r.get("Status_Detail", "")).lower()
            ing_date = r.get("Ingeschreven_Datum")
            
            # Check of de datum gepasseerd is
            is_past = pd.notna(ing_date) and pd.to_datetime(ing_date).date() < today.date()

            if "niet geslaagd" in det: return 0      # 1. Herkansingen (Top prio)
            
            # 2. Verlopen certificaten (Open taken die rood moeten zijn)
            if r.get("DaysUntilExpiry", 0) and float(r.get("DaysUntilExpiry")) < 0 and st == "open": 
                return 1
            
            if st == "open": return 2               # 3. Normale open taken
            
            # 4. Ingeschreven in de TOEKOMST (moet oranje blijven bovenin)
            if st == "ingeschreven" and not is_past: return 3
            
            # 5. Ingeschreven MAAR DATUM GEWEEST (Grijs onderaan de lijst)
            if st == "ingeschreven" and is_past: return 10 
            
            return 20 # De rest

        filtered_todo['prio'] = filtered_todo.apply(sort_priority, axis=1)
        
        # Sorteer op Prioriteit, dan op Datum (zodat oudste 'gepasseerde' taken onderaan staan) 
        # en dan op Naam
        filtered_todo = filtered_todo.sort_values(
            by=['prio', 'Ingeschreven_Datum', 'MedewerkerNaam'], 
            ascending=[True, True, True]
        )
        
        self.lbl_stats.setText(f"Taken getoond: {len(filtered_todo)}")
        self.populate_widgets(filtered_todo)
    
    def populate_widgets(self, df: pd.DataFrame):
        """Maakt de visuele lijst van taken aan."""
        while self.task_layout.count():
            item = self.task_layout.takeAt(0)
            if item.widget(): 
                item.widget().deleteLater()
        
        self._task_widgets = []
        
        if df.empty:
            lbl = QLabel("Geen taken gevonden voor de huidige filters.")
            lbl.setStyleSheet("color: #64748b; font-style: italic; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_layout.addWidget(lbl)
            return

        # Gebruik reset_index zodat 'index' de originele positie in de brondata bevat
        df_display = df.reset_index(drop=False)
        for _, row in df_display.iterrows():
            w = TodoRowWidget(row)
            w.df_index = row['index'] 
            w.mousePressEvent = lambda event, widget=w: self._on_widget_clicked(widget, event)
            self.task_layout.addWidget(w)
            self._task_widgets.append(w)
            
        self.task_layout.addStretch()

    def _on_widget_clicked(self, clicked_widget: TodoRowWidget, event):
        """Handelt het selecteren van een taak af."""
        if event.button() != Qt.MouseButton.LeftButton: return
        for w in self._task_widgets:
            w.setProperty("selected", False)
            w.style().polish(w)
        clicked_widget.setProperty("selected", True)
        clicked_widget.style().polish(clicked_widget)
        self.on_task_selected(selected_widget=clicked_widget)

    def _get_row(self):
        """Haalt de geselecteerde rij veilig op uit de hoofd-dataframe."""
        for w in self._task_widgets:
            if w.property("selected"): 
                idx = w.df_index
                if idx in self.data.df["todo"].index:
                    return self.data.df["todo"].loc[idx]
        return None

    def on_task_selected(self, selected_widget=None):
        """Vult het detailpaneel onderaan de lijst."""
        row = self._get_row()
        if row is None: return
        self.lbl_sel_emp.setText(f"Medewerker: {row.get('MedewerkerNaam', '-')}")
        self.lbl_sel_cert.setText(f"Opleiding: {row.get('CertName', '-')}")
        idx = self.cmb_status.findText(str(row.get("Status", "Open")))
        if idx >= 0: self.cmb_status.setCurrentIndex(idx)
        self.txt_detail.setText(str(row.get("Status_Detail", "")))
    
    def on_trigger_academy_mail(self):
        """Wordt aangeroepen wanneer op de 'Mail Academy' knop geklikt wordt."""
        row = self._get_row()
        if row is None:
            QMessageBox.information(self, "Selectie", "Selecteer eerst een medewerker in de lijst.")
            return
            
        # We vragen voor de zekerheid even of ze echt een mail willen sturen
        confirm = QMessageBox.question(self, "Bevestig", 
                                     f"Wil je een annulatie-mail voor {row['MedewerkerNaam']} klaarzetten voor de Academy?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.send_cancellation_mail(row)
    
    def on_save_status(self):
        """Slaat wijzigingen in status/detail op naar SQL/Excel."""
        row = self._get_row()
        if row is None: return
        
        idx = row.name # Gebruik de unieke index van de dataframe
        self.data.df["todo"].at[idx, "Status"] = self.cmb_status.currentText()
        self.data.df["todo"].at[idx, "Status_Detail"] = self.txt_detail.text()
        self.data.df["todo"].at[idx, "LastUpdatedAt"] = pd.Timestamp.now()
        
        self.data.save_todo()
        self.refresh() 

    def on_delete_task(self):
        """Verwijdert een taak na bevestiging."""
        row = self._get_row()
        if row is None: return
        
        ans = QMessageBox.question(self, "Verwijderen", f"Taak voor {row['MedewerkerNaam']} definitief verwijderen?")
        if ans == QMessageBox.StandardButton.Yes:
            self.data.df["todo"] = self.data.df["todo"].drop(row.name)
            self.data.save_todo()
            self.refresh()

    def on_open_wizard(self):
        """Opent de inschrijvingswizard."""
        row = self._get_row()
        if row is not None:
            engine = self.data.engine if hasattr(self.data, 'engine') else None
            w = IngeschrevenWizard(row, engine, self)
            if w.exec():
                self.refresh()

    def on_mark_self_registered(self):
        """Markeert een medewerker als zelf ingeschreven."""
        row = self._get_row()
        if row is not None:
            d = SelfRegisteredDialog(str(row.get("MedewerkerNaam")), str(row.get("CertName")), self)
            if d.exec():
                idx = row.name
                self.data.df["todo"].at[idx, "Status"] = "Ingeschreven"
                dt = d.get_date()
                loc = d.get_location()
                if dt: self.data.df["todo"].at[idx, "Ingeschreven_Datum"] = pd.Timestamp(dt)
                if loc: self.data.df["todo"].at[idx, "Ingeschreven_Locatie"] = loc
                self.data.save_todo()
                self.refresh()

    def on_find_replacements(self):
        """Zoekt naar vervangers voor een opleiding."""
        row = self._get_row()
        if row is not None:
            try:
                cands = self.data.find_replacement_candidates(row)
                ReplacementCandidatesDialog(cands, self).exec()
            except Exception as e: 
                QMessageBox.warning(self, "Fout", str(e))

    # def on_cannot_attend(self):
        # """Zet een ingeschreven status terug naar Open."""
        # row = self._get_row()
        # if row is None: return
        # if QMessageBox.question(self, "Bevestig", "Inschrijving annuleren?") == QMessageBox.StandardButton.Yes:
            # idx = row.name
            # self.data.df["todo"].at[idx, "Status"] = "Open"
            # self.data.df["todo"].at[idx, "Ingeschreven_Datum"] = pd.NaT
            # self.data.save_todo()
            # self.refresh()
    # def on_cancel_or_cannot_attend(self):
        # """
        # Gecombineerde 'Kan niet gaan' knop.
        # Hergebruikt bestaande Xaurum-zoek en Link-logica.
        # """
        # row = self._get_row()
        # if row is None: return
        
        # naam = row.get("MedewerkerNaam", "deze medewerker")
        # cert = row.get("CertName", "opleiding")

        # # Dialoogvenster opbouwen
        # msg = QMessageBox(self)
        # msg.setWindowTitle("Beheer Afmelding")
        # msg.setText(f"Afmelding verwerken voor: {naam}\nOpleiding: {cert}")
        # msg.setInformativeText("Kies een actie om direct in Xaurum te werken of de status aan te passen.")
        # btn_mail = msg.addButton("📧 Mail Academy (Annulatie)", QMessageBox.ButtonRole.ActionRole)
        
        # # Knoppen toevoegen die bestaande functies triggeren
        # btn_goto_xaurum = msg.addButton("🌐 Open Xaurum (Annuleren)", QMessageBox.ButtonRole.ActionRole)
        # btn_reschedule = msg.addButton("📅 Zoek Nieuwe Datum", QMessageBox.ButtonRole.ActionRole)
        # btn_find_swap = msg.addButton("👥 Zoek Vervanger", QMessageBox.ButtonRole.ActionRole)
        # btn_reset_only = msg.addButton("🔄 Alleen op 'Open' zetten", QMessageBox.ButtonRole.ActionRole)
        
        # msg.addButton("Sluiten", QMessageBox.ButtonRole.RejectRole)

        # msg.exec()
        # clicked = msg.clickedButton()
        # if msg.clickedButton() == btn_mail:
            # self.send_cancellation_mail(row)
        
        # # --- UITVOERING OP BASIS VAN KEUZE ---

        # if clicked == btn_goto_xaurum:
            # # Hergebruik de Selenium-logica om de medewerker te openen
            # self.on_open_xaurum()

        # elif clicked == btn_reschedule:
            # # Hergebruik de 'Link Opleiding' logica om de cursuspagina te openen
            # self.on_open_training_for_selected()

        # elif clicked == btn_find_swap:
            # # Hergebruik de 'Zoek vervanger' logica
            # self.on_find_replacements()

        # elif clicked == btn_reset_only:
            # # De simpele reset-logica
            # if QMessageBox.question(self, "Bevestig", "Status terugzetten naar 'Open'?") == QMessageBox.StandardButton.Yes:
                # idx = row.name
                # self.data.df["todo"].at[idx, "Status"] = "Open"
                # self.data.df["todo"].at[idx, "Ingeschreven_Datum"] = pd.NaT
                # self.data.df["todo"].at[idx, "Status_Detail"] = "Inschrijving geannuleerd"
                # self.data.save_todo()
                # self.refresh()
    def on_cancel_or_cannot_attend(self):
        """
        Gecorrigeerde 'Afmelden' knop met geforceerde styling en SAP-mail integratie.
        """
        row = self._get_row()
        if row is None:
            QMessageBox.information(self, "Selectie", "Selecteer eerst een taak in de lijst.")
            return
        
        naam = row.get("MedewerkerNaam", "deze medewerker")
        cert = row.get("CertName", "opleiding")

        # Dialoogvenster opbouwen
        msg = QMessageBox(self)
        msg.setWindowTitle("Beheer Afmelding")
        msg.setText(f"<b>Medewerker:</b> {naam}<br><b>Opleiding:</b> {cert}")
        msg.setInformativeText("Kies de gewenste actie. Gebruik 'Naar Open' om de lijst op te schonen.")

        # --- FIX: STYLING VOOR ZICHTBAARHEID ---
        msg.setStyleSheet("""
            QPushButton { 
                min-width: 130px; 
                padding: 8px; 
                color: black; 
                background-color: #f0f0f0; 
                border: 1px solid #ababab; 
                font-family: 'Segoe UI';
            }
            QPushButton:hover { background-color: #e2e8f0; }
        """)

        # Knoppen definiëren
        btn_mail = msg.addButton("📧 Mail Academy", QMessageBox.ButtonRole.ActionRole)
        btn_goto_xaurum = msg.addButton("🌐 Open Xaurum", QMessageBox.ButtonRole.ActionRole)
        btn_find_swap = msg.addButton("👥 Zoek Vervanger", QMessageBox.ButtonRole.ActionRole)
        btn_reset_only = msg.addButton("🔄 Naar 'Open'", QMessageBox.ButtonRole.ActionRole)
        btn_close = msg.addButton("Sluiten", QMessageBox.ButtonRole.RejectRole)

        msg.exec()
        clicked = msg.clickedButton()

        # --- ACTIES UITVOEREN ---

        if clicked == btn_mail:
            # Deze functie hebben we aangepast om SAPNR in het onderwerp te zetten
            self.send_cancellation_mail(row)

        elif clicked == btn_goto_xaurum:
            # Opent medewerker direct in de browser via Selenium
            self.on_open_xaurum()

        elif clicked == btn_find_swap:
            # Gebruik de nieuwe handle_swap_process voor de slimme wissel
            if hasattr(self, 'handle_swap_process'):
                self.handle_swap_process(row)
            else:
                self.on_find_replacements()

        elif clicked == btn_reset_only:
            # Zet de status terug zodat de taak weer planbaar is
            if QMessageBox.question(self, "Bevestig", f"Status voor {naam} terugzetten naar 'Open'?") == QMessageBox.StandardButton.Yes:
                idx = row.name
                self.data.df["todo"].at[idx, "Status"] = "Open"
                self.data.df["todo"].at[idx, "Ingeschreven_Datum"] = pd.NaT
                self.data.df["todo"].at[idx, "Ingeschreven_Locatie"] = ""
                self.data.df["todo"].at[idx, "Status_Detail"] = "Inschrijving geannuleerd (terug naar Open)"
                
                # Opslaan via de wrapper die je al hebt
                self.data.save_todo() 
                self.refresh()
                
    def on_full_cancel(self):
        """Annuleert en deactiveert een taak volledig."""
        row = self._get_row()
        if row is None: return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Taak Annuleren / Deactiveren")
        msg_box.setText(f"Wilt u de taak voor {row['MedewerkerNaam']} annuleren?")
        
        deactivate_cb = QCheckBox("Deactiveer deze training ook in de Config (Nodig = 0)")
        deactivate_cb.setChecked(True)
        msg_box.setCheckBox(deactivate_cb)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            should_deactivate = deactivate_cb.isChecked()
            success = self.data.cancel_and_deactivate_task(row, deactivate_config=should_deactivate)
            if success:
                self.refresh()
            else:
                QMessageBox.critical(self, "Fout", "Kon de taak niet annuleren in SQL.")

    def on_open_training_for_selected(self):
        """Opent de URL van de opleiding."""
        row = self._get_row()
        if row is not None:
            url = self.data.find_training_url_for_cert(str(row.get("CertName")))
            if url: QDesktopServices.openUrl(QUrl(url))

    def on_open_employee(self):
        """Callback naar het medewerkers-tabblad."""
        row = self._get_row()
        if row is not None and self.open_employee_callback:
            self.open_employee_callback(str(row.get("MedewerkerNaam")))

    # def on_open_xaurum(self):
        # """Start Selenium om medewerker in Xaurum op te zoeken."""
        # row = self._get_row()
        # if row is None:
            # QMessageBox.information(self, "Selectie nodig", "Selecteer eerst een medewerker.")
            # return

        # original_text = self.btn_xaurum.text()
        # self.btn_xaurum.setEnabled(False)
        # self.btn_xaurum.setText("⏳ Bezig...")
        # self.btn_xaurum.repaint()

        # clean_name = str(row.get("MedewerkerNaam", "")).replace(",", "").strip()
        # QApplication.clipboard().setText(clean_name)

        # try:
            # from smart_auth_bootstrap import _default_profile_dir
            # from selenium import webdriver
            # from selenium.webdriver.edge.options import Options as EdgeOptions
            # from selenium.webdriver.common.by import By
            # from selenium.webdriver.support.ui import WebDriverWait
            # from selenium.webdriver.support import expected_conditions as EC

            # options = EdgeOptions()
            # options.add_experimental_option("detach", True)
            # options.add_argument(f"user-data-dir={_default_profile_dir()}")
            # options.add_argument("--remote-debugging-port=9222")
            # options.add_argument("--disable-blink-features=AutomationControlled")
            
            # driver = webdriver.Edge(options=options)
            # driver.get("https://equans.xaurum.be/nl/dispatcher/team")
            
            # wait = WebDriverWait(driver, 60)
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
            # time.sleep(2) 

            # tabel_rijen = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            # gevonden = False

            # for rij in tabel_rijen:
                # try:
                    # cellen = rij.find_elements(By.TAG_NAME, "td")
                    # if len(cellen) > 0:
                        # naam_tekst = cellen[0].text.strip()
                        # if clean_name.lower() in naam_tekst.lower() or naam_tekst.lower() in clean_name.lower():
                            # laatste_cel = cellen[-1]
                            # links = laatste_cel.find_elements(By.TAG_NAME, "a")
                            # for link in links:
                                # if "opleidingen" in link.text.strip().lower():
                                    # driver.execute_script("arguments[0].scrollIntoView(true);", link)
                                    # time.sleep(0.5)
                                    # driver.execute_script("arguments[0].click();", link)
                                    # gevonden = True
                                    # break
                    # if gevonden: break
                # except: continue

            # if not gevonden:
                # try:
                    # search_field = driver.find_element(By.CSS_SELECTOR, "input[type='search']")
                    # search_field.clear()
                    # search_field.send_keys(clean_name)
                    # from selenium.webdriver.common.keys import Keys
                    # search_field.send_keys(Keys.ENTER)
                # except: pass

        # except Exception as e:
            # QMessageBox.warning(self, "Browser Fout", f"Fout: {e}")
        # finally:
            # self.btn_xaurum.setEnabled(True)
            # self.btn_xaurum.setText(original_text)
    def on_open_xaurum(self):
        """Selenium met uitgebreide console-logs voor probleemoplossing."""
        row = self._get_row()
        if row is None:
            QMessageBox.information(self, "Selectie nodig", "Selecteer eerst een medewerker.")
            return

        original_text = self.btn_xaurum.text()
        self.btn_xaurum.setEnabled(False)
        self.btn_xaurum.setText("⏳ Debugging...")
        self.btn_xaurum.repaint()

        # Naam opschonen
        raw_name = str(row.get("MedewerkerNaam", ""))
        clean_name = raw_name.replace(",", "").strip()
        print(f"\n[DEBUG] Zoekopdracht gestart voor: '{raw_name}'")
        print(f"[DEBUG] Doelnaam in Selenium: '{clean_name.lower()}'")

        try:
            import time
            from smart_auth_bootstrap import _default_profile_dir
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.keys import Keys

            options = EdgeOptions()
            options.add_experimental_option("detach", True)
            options.add_argument(f"user-data-dir={_default_profile_dir()}")
            options.add_argument("--remote-debugging-port=9222")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            driver = webdriver.Edge(options=options)
            driver.get("https://equans.xaurum.be/nl/dispatcher/team")
            
            print("[DEBUG] Wachten op tabel...")
            wait = WebDriverWait(driver, 60)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
            time.sleep(2) 

            tabel_rijen = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            print(f"[DEBUG] Totaal aantal rijen in tabel: {len(tabel_rijen)}")
            
            gevonden = False

            for i, rij in enumerate(tabel_rijen):
                try:
                    cellen = rij.find_elements(By.TAG_NAME, "td")
                    if not cellen: continue
                    
                    naam_tekst = cellen[0].text.strip().lower()
                    target = clean_name.lower()

                    # DEBUG: Print elke rij die we bekijken
                    if i < 10: # Alleen de eerste 10 om je terminal niet te overspoelen
                        print(f"[DEBUG] Rij {i}: '{naam_tekst}'")

                    if target in naam_tekst or naam_tekst in target:
                        print(f"[DEBUG] ✨ MATCH GEVONDEN op rij {i}: '{naam_tekst}'")
                        laatste_cel = cellen[-1]
                        links = laatste_cel.find_elements(By.TAG_NAME, "a")
                        
                        for link in links:
                            link_tekst = link.text.strip().lower()
                            if "opleidingen" in link_tekst:
                                print(f"[DEBUG] 🚀 Klikken op link: '{link_tekst}'")
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                                time.sleep(0.5)
                                driver.execute_script("arguments[0].click();", link)
                                gevonden = True
                                break
                    if gevonden: break
                except Exception as e:
                    print(f"[DEBUG] Fout in rij {i}: {e}")
                    continue

            if not gevonden:
                print(f"[DEBUG] ❌ Geen match gevonden in tabel. Proberen zoekveld in te vullen...")
                try:
                    search_field = driver.find_element(By.CSS_SELECTOR, "input[type='search']")
                    search_field.clear()
                    search_field.send_keys(clean_name)
                    search_field.send_keys(Keys.ENTER)
                    print(f"[DEBUG] Zoekterm '{clean_name}' naar search field gestuurd.")
                except Exception as e:
                    print(f"[DEBUG] Zoekveld mislukt: {e}")

        except Exception as e:
            print(f"[DEBUG] 🛑 FATALE FOUT: {e}")
            QMessageBox.warning(self, "Browser Fout", f"Fout: {e}")
        finally:
            self.btn_xaurum.setEnabled(True)
            self.btn_xaurum.setText(original_text)
            print("[DEBUG] Selenium proces beëindigd.\n")
    # def send_cancellation_mail(self, row):
        # """Zet een Outlook mail klaar voor de Training Academy."""
        # try:
            # import win32com.client as win32
        # except ImportError:
            # QMessageBox.critical(self, "Fout", "De bibliotheek 'pywin32' is niet geïnstalleerd.")
            # return
        
        # # Gegevens voorbereiden
        # naam = row.get("MedewerkerNaam", "Onbekend")
        # cert = row.get("CertName", "Onbekend")
        # datum = row.get("Ingeschreven_Datum")
        # datum_str = datum.strftime("%d-%m-%Y") if pd.notna(datum) else "n.v.t."
        # locatie = row.get("Ingeschreven_Locatie", "n.v.t.")
        
        # try:
            # outlook = win32.Dispatch('outlook.application')
            # mail = outlook.CreateItem(0)
            
            # # Instellingen van de mail
            # mail.To = "trainingacademybelux.training.belux@equans.com"
            # #mail.Subject = f"ANNULATIE: {cert} - {naam}"
            # mail.Subject = f"ANNULATIE: {cert} - {naam} ({sapnr})"
            
            # # HTML Body voor een professionele look
            # mail.HTMLBody = f"""
            # <html>
                # <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 14px;">
                    # <p>Beste Training Academy,</p>
                    # <p>Hierbij wens ik de volgende inschrijving te <b>annuleren</b>:</p>
                    # <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
                        # <tr><td style="padding: 5px; border-bottom: 1px solid #ddd;"><b>Medewerker:</b></td><td style="padding: 5px; border-bottom: 1px solid #ddd;">{naam}</td></tr>
                        # <tr><td style="padding: 5px; border-bottom: 1px solid #ddd;"><b>Opleiding:</b></td><td style="padding: 5px; border-bottom: 1px solid #ddd;">{cert}</td></tr>
                        # <tr><td style="padding: 5px; border-bottom: 1px solid #ddd;"><b>Datum:</b></td><td style="padding: 5px; border-bottom: 1px solid #ddd;">{datum_str}</td></tr>
                        # <tr><td style="padding: 5px; border-bottom: 1px solid #ddd;"><b>Locatie:</b></td><td style="padding: 5px; border-bottom: 1px solid #ddd;">{locatie}</td></tr>
                    # </table>
                    # <p>Gelieve de nodige stappen te ondernemen in Xaurum.</p>
                    # <p>Met vriendelijke groeten,</p>
                    # <p><i>Verstuurd via Xaurum Planner Tool</i></p>
                # </body>
            # </html>
            # """
            
            # mail.Display() # Toon de mail zodat de gebruiker nog iets kan toevoegen
        # except Exception as e:
            # QMessageBox.warning(self, "Outlook Fout", f"Kon Outlook niet aansturen: {str(e)}")

    def send_cancellation_mail(self, row):
        """Zet een Outlook mail klaar voor de Training Academy inclusief SAPNR."""
        try:
            import win32com.client as win32
        except ImportError:
            QMessageBox.critical(self, "Fout", "De bibliotheek 'pywin32' is niet geïnstalleerd.")
            return
        
        # Gegevens ophalen uit de geselecteerde rij
        naam = row.get("MedewerkerNaam", "Onbekend")
        # Verkrijg SAPNR en schoon de tekst op (verwijder .0 van Excel getallen)
        sapnr = str(row.get("staffSAPNR", "GEEN SAPNR")).replace("nan", "GEEN SAPNR").replace(".0", "")
        
        cert = row.get("CertName", "Onbekend")
        datum = row.get("Ingeschreven_Datum")
        datum_str = datum.strftime("%d-%m-%Y") if pd.notna(datum) else "n.v.t."
        locatie = row.get("Ingeschreven_Locatie", "n.v.t.")
        
        try:
            outlook = win32.Dispatch('outlook.application')
            mail = outlook.CreateItem(0)
            
            # Instellingen van de mail
            mail.To = "trainingacademybelux.training.belux@equans.com"
            
            # Onderwerp met SAPNR tussen haakjes
            mail.Subject = f"ANNULATIE: {cert} - {naam} ({sapnr})"
            
            # HTML Body voor een professionele tabel in de mail
            mail.HTMLBody = f"""
            <html>
                <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 14px;">
                    <p>Beste Training Academy,</p>
                    <p>Gelieve de volgende inschrijving te <b>annuleren</b>:</p>
                    <table style="border-collapse: collapse; width: 100%; max-width: 550px; border: 1px solid #ddd;">
                        <tr style="background-color: #f8fafc;">
                            <td style="padding: 10px; border: 1px solid #ddd; width: 150px;"><b>Medewerker:</b></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{naam}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><b>SAP Nummer:</b></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{sapnr}</td>
                        </tr>
                        <tr style="background-color: #f8fafc;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><b>Opleiding:</b></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{cert}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><b>Datum:</b></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{datum_str}</td>
                        </tr>
                        <tr style="background-color: #f8fafc;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><b>Locatie:</b></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{locatie}</td>
                        </tr>
                    </table>
                    <p>Bedankt voor de verwerking in Xaurum.</p>
                    <p>Met vriendelijke groeten,</p>
                    <p><i>Verstuurd via Xaurum Planner Tool</i></p>
                </body>
            </html>
            """
            
            mail.Display() # Toon de mail zodat de gebruiker nog iets kan toevoegen
        except Exception as e:
            QMessageBox.warning(self, "Outlook Fout", f"Kon Outlook niet aansturen: {str(e)}")