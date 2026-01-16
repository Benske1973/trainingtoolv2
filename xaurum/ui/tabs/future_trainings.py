
# ===============================================================
# Training Management System v14 - Interactive Discrepancy Tracker
# ===============================================================

import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QMessageBox, QDialog, QComboBox, QDialogButtonBox, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QBrush, QFont

from xaurum.core.datastore import DataStore

class MappingDialog(QDialog):
    """Popup om een onbekende naam te koppelen aan een Master certificaat."""
    def __init__(self, bad_name, master_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Koppel Onbekende Naam")
        self.setFixedSize(500, 250)
        self.result_name = None

        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(f"❌ Onbekende naam uit Xaurum:\n<b>{bad_name}</b>"))
        layout.addWidget(QLabel("Selecteer de correcte Nederlandse naam uit Master:"))
        
        self.combo = QComboBox()
        self.combo.setEditable(True) # Zodat je kunt typen/zoeken
        self.combo.addItems(sorted(master_list))
        layout.addWidget(self.combo)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept_selection)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def accept_selection(self):
        self.result_name = self.combo.currentText()
        self.accept()

class DiscrepancyTrackerTab(QWidget):
    def __init__(self, data_store: DataStore):
        super().__init__()
        self.data = data_store
        self.init_ui()
        QTimer.singleShot(500, self.refresh)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QFrame()
        header.setStyleSheet(".QFrame {background: white; border-radius: 8px; border: 1px solid #ddd;}")
        hl = QHBoxLayout(header)
        
        titles = QVBoxLayout()
        t = QLabel("🕵️ Discrepanties & Oplossingen")
        t.setStyleSheet("font-size: 18px; font-weight: bold;")
        sub = QLabel("Los configuratiefouten en onbekende namen direct op.")
        sub.setStyleSheet("color: gray;")
        titles.addWidget(t); titles.addWidget(sub)
        
        ref_btn = QPushButton("🔄 Vernieuwen")
        ref_btn.clicked.connect(self.refresh)
        ref_btn.setStyleSheet("background: #2563eb; color: white; font-weight: bold; padding: 8px;")
        
        hl.addLayout(titles)
        hl.addStretch()
        hl.addWidget(ref_btn)
        layout.addWidget(header)

        # Status
        self.stats = QLabel("...")
        layout.addWidget(self.stats)

        # Tabel
        self.table = QTableWidget()
        self.table.setColumnCount(7) # Extra kolom voor knop
        self.table.setHorizontalHeaderLabels(["Type", "GID", "Naam", "Certificaat (Bron)", "Datum", "Advies", "ACTIE"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        
        # Breedtes
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 300)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 200)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)

    def refresh(self):
        self.table.setRowCount(0)
        self.stats.setText("⏳ Analyseren...")
        QTimer.singleShot(100, self._run_analysis)

    def _run_analysis(self):
        # 1. Data ophalen
        req = self.data.df.get("training_req", pd.DataFrame())
        cfg = self.data.df.get("config_cert", pd.DataFrame())
        if cfg.empty: cfg = self.data.df.get("config", pd.DataFrame())
        staff = self.data.df.get("staff", pd.DataFrame())
        mapping = self.data.df.get("mapping_cert", pd.DataFrame())
        master = self.data.df.get("master_cert", pd.DataFrame())

        if req.empty:
            self.stats.setText("✅ Geen inschrijvingen.")
            return

        # 2. Maps bouwen
        # A. Staff (AANGEPASTE VERSIE VOOR NAAM FIX)
        current_cc = getattr(self.data, "selected_costcenter", "")
        valid_staff = {}
        
        if not staff.empty:
            cc_rows = staff
            
            # Kolomnamen zoeken voor filtering en data extractie
            cc_col = next((c for c in ["staffCOSTCENTER315", "CostCenter", "staffCOSTCENTER"] if c in staff.columns), "staffCOSTCENTER315")
            id_col = next((c for c in ["staffGID", "GID"] if c in staff.columns), "staffGID")
            name_col = next((c for c in ["MedewerkerNaam", "FullName", "Naam"] if c in staff.columns), None)

            # Filter op CostCenter indien geselecteerd
            if current_cc and cc_col in staff.columns:
                cc_rows = staff[staff[cc_col].astype(str).str.strip() == current_cc]
            
            for _, r in cc_rows.iterrows():
                sid = str(r.get(id_col, "")).strip()
                name = sid # Fallback naar ID

                # LOGICA NAAM BEPALEN
                if name_col:
                    # Optie A: Kant-en-klare kolom (oudere bestanden)
                    val = str(r.get(name_col, "")).strip()
                    if val and val.lower() != "nan":
                        name = val
                elif "staffFIRSTNAME" in staff.columns and "staffLASTNAME" in staff.columns:
                    # Optie B: Jouw nieuwe STAFF.xlsx (Voornaam + Achternaam samenvoegen)
                    fname = str(r.get('staffFIRSTNAME', '')).strip()
                    lname = str(r.get('staffLASTNAME', '')).strip()
                    if fname.lower() == "nan": fname = ""
                    if lname.lower() == "nan": lname = ""
                    name = f"{lname} {fname}".strip()
                
                if sid: 
                    valid_staff[sid] = name

        # B. Config
        config_map = {}
        if not cfg.empty:
            for _, r in cfg.iterrows():
                sid = str(r['staffGID']).strip()
                if sid in valid_staff:
                    norm = self.data.normalize_certname(str(r['CertName']))
                    nodig = str(r['Nodig']).lower() in ['1', 'true', 'ja']
                    config_map[(sid, norm)] = nodig

        # C. Master & Mapping
        master_list = []
        if not master.empty:
            master_list = sorted(master['CertName'].dropna().unique().tolist())
        
        known_norms = {self.data.normalize_certname(m) for m in master_list}
        trans_map = {}
        
        if not mapping.empty:
            # Kolomnamen zoeken
            src = next((c for c in ["OrigineleNaam", "Frans"] if c in mapping.columns), mapping.columns[0])
            dst = next((c for c in ["VertaaldeNaam", "Nederlands"] if c in mapping.columns), mapping.columns[1])
            for _, r in mapping.iterrows():
                o, d = str(r[src]).strip(), str(r[dst]).strip()
                if o and d:
                    no, nd = self.data.normalize_certname(o), self.data.normalize_certname(d)
                    known_norms.add(no)
                    trans_map[no] = (d, nd) # Bewaar Target Naam + Target Norm

        # 3. Checken
        discrepancies = []
        req_id = next((c for c in ["staffGID", "staffSAPNR"] if c in req.columns), "staffGID")
        req_cert = next((c for c in ["CertName", "Opleiding"] if c in req.columns), "CertName")
        req_date = "ScheduledDate"
        
        today = pd.Timestamp.today().normalize()

        for _, row in req.iterrows():
            sid = str(row.get(req_id, "")).strip()
            raw_cert = str(row.get(req_cert, "")).strip()
            dt = pd.to_datetime(row.get(req_date, pd.NaT))
            
            if pd.notna(dt) and dt < (today - pd.Timedelta(days=7)): continue
            if sid not in valid_staff: continue

            name = valid_staff[sid]
            norm_raw = self.data.normalize_certname(raw_cert)
            
            # CHECK 1: Onbekend?
            if norm_raw not in known_norms:
                discrepancies.append({
                    "type": "🔴 Onbekende Naam", "gid": sid, "name": name, "raw": raw_cert, "date": dt,
                    "msg": "Koppel aan Master", "action": "MAP", "args": (raw_cert, master_list)
                })
                continue

            # Vertaal voor config check
            target_name = raw_cert
            target_norm = norm_raw
            if norm_raw in trans_map:
                target_name, target_norm = trans_map[norm_raw]
            
            # CHECK 2: Mist Config?
            if (sid, target_norm) not in config_map:
                discrepancies.append({
                    "type": "🟠 Config Ontbreekt", "gid": sid, "name": name, "raw": raw_cert, "date": dt,
                    "msg": "Maak aan in Config", "action": "CREATE", "args": (sid, name, target_name, target_norm)
                })
                continue

            # CHECK 3: Staat uit?
            if not config_map[(sid, target_norm)]:
                discrepancies.append({
                    "type": "🟡 Config staat UIT", "gid": sid, "name": name, "raw": raw_cert, "date": dt,
                    "msg": "Zet op 'Nodig'", "action": "ENABLE", "args": (sid, target_norm)
                })

        # 4. Renderen
        self.table.setRowCount(len(discrepancies))
        for i, d in enumerate(discrepancies):
            # Type en Kleur
            color = "#333"
            if "🔴" in d["type"]: color = "#dc2626"
            elif "🟠" in d["type"]: color = "#d97706"
            elif "🟡" in d["type"]: color = "#b45309"
            
            item_t = QTableWidgetItem(d["type"]); item_t.setForeground(QBrush(QColor(color))); item_t.setFont(self._f(True))
            self.table.setItem(i, 0, item_t)
            self.table.setItem(i, 1, QTableWidgetItem(d["gid"]))
            self.table.setItem(i, 2, QTableWidgetItem(d["name"]))
            self.table.setItem(i, 3, QTableWidgetItem(d["raw"]))
            self.table.setItem(i, 4, QTableWidgetItem(d["date"].strftime("%d-%m-%Y") if pd.notna(d["date"]) else ""))
            self.table.setItem(i, 5, QTableWidgetItem(d["msg"]))
            
            # KNOP
            btn = QPushButton(d["action"] + " 🛠️")
            if d["action"] == "MAP": btn.setText("Koppelen 🔗"); btn.setStyleSheet("background: #dc2626; color: white;")
            if d["action"] == "CREATE": btn.setText("Aanmaken ➕"); btn.setStyleSheet("background: #d97706; color: white;")
            if d["action"] == "ENABLE": btn.setText("Activeren ✅"); btn.setStyleSheet("background: #b45309; color: white;")
            
            # Connect met lambda om data mee te geven
            btn.clicked.connect(lambda checked, act=d["action"], args=d["args"]: self.handle_action(act, args))
            self.table.setCellWidget(i, 6, btn)

        self.table.resizeColumnsToContents()
        self.stats.setText(f"Gevonden: {len(discrepancies)} aandachtspunten.")
    
    # def handle_action(self, action, args):
        # """
        # Voert de actie uit (Koppelen, Aanmaken, Activeren) met dialoogvensters DIE KNOPPEN HEBBEN.
        # """
        # # Zorg voor de imports (zet deze eventueel bovenaan je bestand als ze er nog niet staan)
        # from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox, QMessageBox, QInputDialog

        # if action == "MAP":
            # raw_cert, master_list = args
            
            # # 1. Maak het venster
            # dialog = QDialog(self)
            # dialog.setWindowTitle(f"Koppelen: {raw_cert}")
            # dialog.setMinimumWidth(400)
            
            # layout = QVBoxLayout(dialog)
            
            # # 2. Inhoud
            # layout.addWidget(QLabel("<b>Originele naam uit Training Req:</b>"))
            # layout.addWidget(QLabel(f"<i>{raw_cert}</i>"))
            # layout.addSpacing(10)
            # layout.addWidget(QLabel("Kies de juiste Master Opleiding:"))
            
            # combo = QComboBox()
            # combo.setEditable(True) # Zodat je kunt typen/zoeken
            # combo.addItems(sorted(master_list))
            # layout.addWidget(combo)
            
            # # 3. 🛑 DE MISSENDE KNOPPEN TOEVOEGEN
            # buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            # buttons.accepted.connect(dialog.accept)
            # buttons.rejected.connect(dialog.reject)
            # layout.addWidget(buttons)
            
            # # 4. Toon venster en verwerk resultaat
            # if dialog.exec():
                # chosen = combo.currentText()
                # if chosen:
                    # # Opslaan in Mapping tabel/file
                    # print(f"🔗 Koppelen: {raw_cert} -> {chosen}")
                    # # Hier roepen we de interne functie aan om op te slaan
                    # # (Pas dit aan naar hoe jij data opslaat, bv via self.data.add_mapping)
                    # self.data.add_cert_mapping(raw_cert, chosen, "Manual Fix UI") 
                    # self.refresh() # Herlaad scherm

        # elif action == "CREATE":
            # sid, name, cert, cnorm = args
            
            # # 1. Maak het venster
            # dialog = QDialog(self)
            # dialog.setWindowTitle(f"Configuratie Aanmaken")
            # dialog.setMinimumWidth(400)
            # layout = QVBoxLayout(dialog)
            
            # layout.addWidget(QLabel(f"<b>Medewerker:</b> {name}"))
            # layout.addWidget(QLabel(f"<b>Opleiding:</b> {cert}"))
            # layout.addSpacing(10)
            # layout.addWidget(QLabel("Wil je deze opleiding op 'Nodig' zetten voor deze persoon?"))
            
            # # 2. 🛑 DE KNOPPEN
            # buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.Cancel)
            # buttons.accepted.connect(dialog.accept)
            # buttons.rejected.connect(dialog.reject)
            # layout.addWidget(buttons)
            
            # if dialog.exec():
                # print(f"➕ Config aanmaken voor {name} - {cert}")
                # # Opslaan logica
                # # Voorbeeld: self.data.add_config(sid, cert, nodig=True)
                # # Als je geen directe functie hebt, kun je het via SQL manager doen of DataFrame manipulatie
                # # Hieronder een 'best effort' gok van hoe jouw save functie heet:
                # if hasattr(self.data, "add_medewerker_config"):
                     # self.data.add_medewerker_config(sid, cert, nodig=True)
                # else:
                    # QMessageBox.warning(self, "Let op", "Functie add_medewerker_config niet gevonden in DataStore.")
                
                # self.refresh()

        # elif action == "ENABLE":
            # sid, target_norm = args
            # # Dit is simpel genoeg voor een standaard Ja/Nee box (die heeft altijd knoppen)
            # reply = QMessageBox.question(self, "Activeren", 
                                       # "Weet je zeker dat je deze opleiding op 'Nodig' wilt zetten?",
                                       # QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            # if reply == QMessageBox.StandardButton.Yes:
                # print(f"✅ Activeren: {sid} - {target_norm}")
                # # Update logica
                # if hasattr(self.data, "update_config_nodig"):
                    # self.data.update_config_nodig(sid, target_norm, True)
                # self.refresh()
    
    def handle_action(self, action, args):
        """
        Verwerkt acties voor discrepanties met keuzemenu voor Nieuw/Koppelen.
        """
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                                     QDialogButtonBox, QRadioButton, QButtonGroup, 
                                     QLineEdit, QGroupBox, QMessageBox)

        if action == "MAP":
            # args bevat: (raw_cert_naam, lijst_met_master_certificaten)
            raw_cert, master_list = args
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Oplossen: {raw_cert}")
            dialog.setMinimumWidth(550)
            layout = QVBoxLayout(dialog)
            
            # --- INFO BLOK ---
            layout.addWidget(QLabel(f"<b>Gevonden in import:</b> <span style='color:red'>{raw_cert}</span>"))
            layout.addWidget(QLabel("Deze naam is onbekend. Wat wil je doen?"))
            layout.addSpacing(10)

            # --- KEUZE 1: KOPPELEN (Mapping) ---
            gb_map = QGroupBox("Optie 1: Het is een bestaande opleiding (Koppelen)")
            lay_map = QVBoxLayout(gb_map)
            rb_map = QRadioButton("Koppel aan bestaande Master Opleiding")
            rb_map.setChecked(True) # Default
            combo_master = QComboBox()
            combo_master.setEditable(True)
            combo_master.addItems(sorted(master_list))
            lay_map.addWidget(rb_map)
            lay_map.addWidget(combo_master)
            layout.addWidget(gb_map)

            # --- KEUZE 2: NIEUW CERTIFICAAT ---
            gb_new_cert = QGroupBox("Optie 2: Het is een nieuwe Opleiding")
            lay_new_cert = QVBoxLayout(gb_new_cert)
            rb_new_cert = QRadioButton("Maak aan als nieuw Certificaat")
            clean_name = raw_cert.strip() 
            txt_new_cert = QLineEdit(clean_name)
            lay_new_cert.addWidget(rb_new_cert)
            lay_new_cert.addWidget(txt_new_cert)
            layout.addWidget(gb_new_cert)

            # --- KEUZE 3: NIEUWE COMPETENTIE ---
            gb_new_comp = QGroupBox("Optie 3: Het is een Competentie/Vaardigheid")
            lay_new_comp = QVBoxLayout(gb_new_comp)
            rb_new_comp = QRadioButton("Maak aan als nieuwe Competentie")
            txt_new_comp = QLineEdit(clean_name)
            lay_new_comp.addWidget(rb_new_comp)
            lay_new_comp.addWidget(txt_new_comp)
            layout.addWidget(gb_new_comp)

            # Grouping voor logica
            bg = QButtonGroup(dialog)
            bg.addButton(rb_map)
            bg.addButton(rb_new_cert)
            bg.addButton(rb_new_comp)

            # --- KNOPPEN ---
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            # UITVOEREN
            if dialog.exec():
                if rb_map.isChecked():
                    # SCENARIO 1: Koppelen
                    target = combo_master.currentText()
                    if target:
                        self.data.add_cert_mapping(raw_cert, target, "Manual Map UI")
                        QMessageBox.information(self, "Gelukt", f"Gekoppeld: {raw_cert} -> {target}")

                elif rb_new_cert.isChecked():
                    # SCENARIO 2: Nieuw Certificaat
                    target = txt_new_cert.text().strip()
                    if target:
                        # 1. Maak aan in Master
                        if self.data.sql_training_manager:
                            self.data.sql_training_manager.add_master_certificate(target)
                        # 2. Voeg mapping toe (zodat raw -> netjes werkt)
                        self.data.add_cert_mapping(raw_cert, target, "New Cert UI")
                        QMessageBox.information(self, "Gelukt", f"Nieuw certificaat aangemaakt: {target}")

                elif rb_new_comp.isChecked():
                    # SCENARIO 3: Nieuwe Competentie
                    target = txt_new_comp.text().strip()
                    if target:
                        # 1. Maak aan in Master Comp
                        if self.data.sql_training_manager:
                            self.data.sql_training_manager.add_master_competence(target)
                        # 2. Voeg mapping toe
                        self.data.add_cert_mapping(raw_cert, target, "New Comp UI")
                        QMessageBox.information(self, "Gelukt", f"Nieuwe competentie aangemaakt: {target}")
                
                # Herlaad data
                self.data.load_translations()
                self.refresh()

        elif action == "CREATE":
            sid, name, cert, cnorm = args
            dialog = QDialog(self)
            dialog.setWindowTitle("Configuratie Aanmaken")
            lay = QVBoxLayout(dialog)
            lay.addWidget(QLabel(f"Wil je <b>{cert}</b> toevoegen aan de verplichte opleidingen voor <b>{name}</b>?"))
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.Cancel)
            btns.accepted.connect(dialog.accept)
            btns.rejected.connect(dialog.reject)
            lay.addWidget(btns)
            if dialog.exec():
                self.data.add_medewerker_config(sid, cert, nodig=True)
                self.refresh()

        elif action == "ENABLE":
            sid, target_norm = args
            reply = QMessageBox.question(self, "Activeren", "Zet deze opleiding op 'Nodig'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.data.update_config_nodig(sid, target_norm, True)
                self.refresh()
    
    def _f(self, b=False):
        f = QFont(); f.setBold(b); return f