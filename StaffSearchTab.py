# ===============================================================
# BESTAND: xaurum/ui/tabs/StaffSearchTab.py (FINAL FIX: STATUS FILTER + PARAMETERS)
# ===============================================================

import pandas as pd
from typing import Dict, List, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, 
    QMessageBox, QApplication 
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QBrush, QFont

# Derde partij imports
from sqlalchemy import create_engine, text # <-- 'text' is cruciaal voor parameters

# Project Imports (Assumeren dat dit nu correct wordt geïmporteerd)
from xaurum.config import SQL_CONNECTION_STRING 


class StaffSearchTab(QWidget):
    """
    Tabblad om medewerkers op te zoeken op naam, GID of SAPNR.
    Voert de zoekquery direct uit op de SQL-server bij elke zoekactie.
    """
    def __init__(self, data_store):
        super().__init__()
        self.data = data_store
        
        self.search_timer = QTimer(self)
        self.search_timer.setInterval(400)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.init_ui()
        
        self.lbl_status.setText("Voer een naam, GID of SAP-nummer in om te zoeken op de server.")

        # Verbinding initialiseren
        try:
            self.sql_engine = create_engine(SQL_CONNECTION_STRING)
        except Exception as e:
            self.sql_engine = None
            self.lbl_status.setText(f"❌ Fout: Kan SQL-engine niet initialiseren. Controleer SQL_CONNECTION_STRING. ({e})")


    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # --- 1. Header en Zoekveld ---
        title = QLabel("👥 Medewerkers Zoeken (Live SQL)")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e293b;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Zoek **actieve** medewerkers op naam, GID of SAP-nummer. De resultaten worden direct opgehaald van de SQL-server."
        )
        subtitle.setStyleSheet("font-size: 13px; color: #64748b;")
        layout.addWidget(subtitle)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Zoeken op Naam, GID of SAPNR...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.search_timer.start) 
        layout.addWidget(self.search_input)
        
        self.lbl_status = QLabel("Voer een naam, GID of SAP-nummer in om te zoeken op de server.")
        self.lbl_status.setStyleSheet("font-style: italic; color: #64748b; margin-top: 5px;")
        layout.addWidget(self.lbl_status)

        # --- 2. Tabel ---
        self.table = QTableWidget()
        columns = ["Naam", "Staff GID", "SAPNR", "Costcenter", "Telefoonnummer", "Manager"] 
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #f8fafc;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: bold;
                color: #475569;
            }
        """)
        
        layout.addWidget(self.table)
        
    def refresh(self):
        """
        Voert een initiële (lege) zoekopdracht uit bij het openen van de tab.
        """
        if self.sql_engine:
            self.perform_search(initial_load=True)
        else:
            self.lbl_status.setText("❌ Fout: SQL-verbinding niet beschikbaar.")


    def perform_search(self, initial_load=False):
        """Voert de zoekopdracht direct uit op de SQL-server."""
        if not self.sql_engine:
            self.lbl_status.setText("❌ Fout: SQL-verbinding niet beschikbaar.")
            self.table.setRowCount(0)
            return

        search_term = self.search_input.text().strip()
        
        if not search_term and not initial_load:
            self.table.setRowCount(0)
            self.lbl_status.setText("Voer een naam, GID of SAP-nummer in om te zoeken op de server.")
            return

        self.lbl_status.setText("Bezig met zoeken op server...")
        QApplication.processEvents() 

        try:
            like_term = f"%{search_term.replace(' ', '%')}%"

            # 1. De query met de WHERE clausule (voor zoeken)
            # FIX 1: dbo.tblSTAFF (op basis van uw file explorer)
            # FIX 2: staffSTATUSID = 1 toegevoegd
            # FIX 3: :term plekhouder voor zoeken
            sql_search_query = """
                SELECT TOP 1000 
                    staffLASTNAME + ' ' + staffFIRSTNAME AS "Naam", 
                    staffGID AS "Staff GID", 
                    staffSAPNR AS "SAPNR", 
                    staffCOSTCENTER315 AS "Costcenter", 
                    staffPHONEPRO AS "Telefoonnummer", 
                    staffORGUNIT AS "Manager"
                FROM 
                    dbo.tblSTAFF
                WHERE 
                    staffSTAFFSTATUSID = 1 AND 
                    (staffLASTNAME LIKE :term OR 
                    staffFIRSTNAME LIKE :term OR 
                    staffGID LIKE :term OR 
                    staffSAPNR LIKE :term)
                ORDER BY 
                    staffLASTNAME
            """
            
            # 2. De query ZONDER de WHERE clausule (voor initial_load)
            # FIX 1: dbo.tblSTAFF
            # FIX 2: staffSTATUSID = 1 toegevoegd
            sql_initial_query = """
                SELECT TOP 1000 
                    staffLASTNAME + ' ' + staffFIRSTNAME AS "Naam", 
                    staffGID AS "Staff GID", 
                    staffSAPNR AS "SAPNR", 
                    staffCOSTCENTER315 AS "Costcenter", 
                    staffPHONEPRO AS "Telefoonnummer", 
                    staffORGUNIT AS "Manager"
                FROM dbo.tblSTAFF
                WHERE staffSTAFFSTATUSID = 1
                ORDER BY staffLASTNAME
            """

            if initial_load:
                # Gebruik de query ZONDER parameters
                results_df = pd.read_sql(sql_initial_query, self.sql_engine)
            else:
                # Gebruik de query MET parameters. text() zorgt dat plekhouders werken.
                results_df = pd.read_sql(
                    text(sql_search_query),  # <<< FIX: text() zorgt dat plekhouders werken
                    self.sql_engine, 
                    params={'term': like_term}
                )

            self.populate_table(results_df)
            self.lbl_status.setText(f"✅ {len(results_df)} actieve medewerker(s) gevonden.")

        except Exception as e:
            # Vang de fout en toon deze aan de gebruiker
            self.lbl_status.setText(f"❌ Fout bij server-query. ({e})")
            print(f"SQL Fout: {e}")
            self.table.setRowCount(0)

        
    def populate_table(self, results_df: pd.DataFrame):
        """Vult de QTableWidget met de zoekresultaten."""
        self.table.setRowCount(0)
        if results_df.empty:
            return

        self.table.setRowCount(len(results_df))
        
        # Kolomnamen komen overeen met de aliassen in de SQL-query
        cols_to_show = ["Naam", "Staff GID", "SAPNR", "Costcenter", "Telefoonnummer", "Manager"]
        
        for row_idx, (index, row) in enumerate(results_df.iterrows()):
            for col_idx, header in enumerate(cols_to_show):
                
                value = str(row.get(header, "") or "").strip()
                
                if value.lower() in ('nan', 'null', ''):
                    value = ""
                
                item = QTableWidgetItem(value)
                
                if header in ["Costcenter", "Manager"]:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                    item.setForeground(QBrush(QColor("#005EB8")))
                
                self.table.setItem(row_idx, col_idx, item)
                
        self.table.resizeColumnsToContents()
# # ===============================================================
# # BESTAND: xaurum/ui/tabs/StaffSearchTab.py (FINAL FIX: DIRECTE SQL + KOLOMMEN)
# # ===============================================================

# import pandas as pd
# from typing import Dict, List, Any
# from PyQt6.QtWidgets import (
    # QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    # QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, 
    # QMessageBox, QApplication 
# )
# from PyQt6.QtCore import Qt, QTimer
# from PyQt6.QtGui import QColor, QBrush, QFont

# # Derde partij imports
# from sqlalchemy import create_engine, text

# # Project Imports (Assumeren dat dit nu correct wordt geïmporteerd)
# from xaurum.config import SQL_CONNECTION_STRING 


# class StaffSearchTab(QWidget):
    # """
    # Tabblad om medewerkers op te zoeken op naam, GID of SAPNR.
    # Voert de zoekquery direct uit op de SQL-server bij elke zoekactie.
    # """
    # def __init__(self, data_store):
        # super().__init__()
        # self.data = data_store
        
        # self.search_timer = QTimer(self)
        # self.search_timer.setInterval(400)
        # self.search_timer.setSingleShot(True)
        # self.search_timer.timeout.connect(self.perform_search)
        
        # self.init_ui()
        
        # self.lbl_status.setText("Voer een naam, GID of SAP-nummer in om te zoeken op de server.")

        # # Verbinding initialiseren
        # try:
            # self.sql_engine = create_engine(SQL_CONNECTION_STRING)
        # except Exception as e:
            # self.sql_engine = None
            # self.lbl_status.setText(f"❌ Fout: Kan SQL-engine niet initialiseren. Controleer SQL_CONNECTION_STRING. ({e})")


    # def init_ui(self):
        # layout = QVBoxLayout(self)
        # layout.setContentsMargins(24, 24, 24, 24)
        # layout.setSpacing(16)

        # # --- 1. Header en Zoekveld ---
        # title = QLabel("👥 Medewerkers Zoeken (Live SQL)")
        # title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e293b;")
        # layout.addWidget(title)

        # subtitle = QLabel(
            # "Zoek medewerkers op naam, GID of SAP-nummer. De resultaten worden direct opgehaald van de SQL-server."
        # )
        # subtitle.setStyleSheet("font-size: 13px; color: #64748b;")
        # layout.addWidget(subtitle)

        # self.search_input = QLineEdit()
        # self.search_input.setPlaceholderText("Zoeken op Naam, GID of SAPNR...")
        # self.search_input.setStyleSheet("""
            # QLineEdit {
                # padding: 8px;
                # border: 1px solid #cbd5e1;
                # border-radius: 4px;
                # font-size: 14px;
            # }
        # """)
        # self.search_input.textChanged.connect(self.search_timer.start) 
        # layout.addWidget(self.search_input)
        
        # self.lbl_status = QLabel("Voer een naam, GID of SAP-nummer in om te zoeken op de server.")
        # self.lbl_status.setStyleSheet("font-style: italic; color: #64748b; margin-top: 5px;")
        # layout.addWidget(self.lbl_status)

        # # --- 2. Tabel ---
        # self.table = QTableWidget()
        # columns = ["Naam", "Staff GID", "SAPNR", "Costcenter", "Telefoonnummer", "Manager"] 
        # self.table.setColumnCount(len(columns))
        # self.table.setHorizontalHeaderLabels(columns)
        
        # self.table.setShowGrid(False)
        # self.table.setAlternatingRowColors(True)
        # self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        # self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # self.table.verticalHeader().setVisible(False)
        
        # header = self.table.horizontalHeader()
        # header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # header.setStretchLastSection(True)
        # header.setStyleSheet("""
            # QHeaderView::section {
                # background-color: #f8fafc;
                # padding: 8px;
                # border: none;
                # border-bottom: 2px solid #e2e8f0;
                # font-weight: bold;
                # color: #475569;
            # }
        # """)
        
        # layout.addWidget(self.table)
        
    # def refresh(self):
        # """
        # Voert een initiële (lege) zoekopdracht uit bij het openen van de tab.
        # """
        # if self.sql_engine:
            # self.perform_search(initial_load=True)
        # else:
            # self.lbl_status.setText("❌ Fout: SQL-verbinding niet beschikbaar.")


    # # def perform_search(self, initial_load=False):
        # # """Voert de zoekopdracht direct uit op de SQL-server."""
        # # if not self.sql_engine:
            # # self.lbl_status.setText("❌ Fout: SQL-verbinding niet beschikbaar.")
            # # self.table.setRowCount(0)
            # # return

        # # search_term = self.search_input.text().strip()
        
        # # if not search_term and not initial_load:
            # # self.table.setRowCount(0)
            # # self.lbl_status.setText("Voer een naam, GID of SAP-nummer in om te zoeken op de server.")
            # # return

        # # self.lbl_status.setText("Bezig met zoeken op server...")
        # # QApplication.processEvents() 

        # # try:
            # # like_term = f"%{search_term.replace(' ', '%')}%"

            # # # GEKORRIGEERDE SQL QUERY
            # # # Tabelnaam: dbo.TM_XaurumStaff (gebruik dit als de correcte naam)
            # # # Kolomselectie is aangepast aan de door u aangeleverde structuur
            # # sql_query = """
                # # SELECT TOP 1000 
                    # # staffLASTNAME + ' ' + staffFIRSTNAME AS "Naam", 
                    # # staffGID AS "Staff GID", 
                    # # staffSAPNR AS "SAPNR", 
                    # # staffCOSTCENTER315 AS "Costcenter", 
                    # # staffPHONEPRO AS "Telefoonnummer", 
                    # # staffORGUNIT AS "Manager" -- Gebruik staffORGUNIT als placeholder
                # # FROM 
                    # # dbo.tblSTAFF 
                # # WHERE 
                    # # staffLASTNAME LIKE :term OR 
                    # # staffFIRSTNAME LIKE :term OR 
                    # # staffGID LIKE :term OR 
                    # # staffSAPNR LIKE :term
                # # ORDER BY 
                    # # staffLASTNAME
            # # """
            
            # # if initial_load:
                # # # Toon de top 1000 van alle medewerkers bij het openen
                # # sql_query = """
                    # # SELECT TOP 1000 
                        # # staffLASTNAME + ' ' + staffFIRSTNAME AS "Naam", 
                        # # staffGID AS "Staff GID", 
                        # # staffSAPNR AS "SAPNR", 
                        # # staffCOSTCENTER315 AS "Costcenter", 
                        # # staffPHONEPRO AS "Telefoonnummer", 
                        # # staffORGUNIT AS "Manager"
                    # # FROM dbo.tblSTAFF 
                    # # ORDER BY staffLASTNAME
                # # """
                # # results_df = pd.read_sql(sql_query, self.sql_engine)
            # # else:
                # # # Voer de zoekquery uit met de LIKE parameter
                # # results_df = pd.read_sql(
                    # # sql_query, 
                    # # self.sql_engine, 
                    # # params={'term': like_term}
                # # )

            # # self.populate_table(results_df)
            # # self.lbl_status.setText(f"✅ {len(results_df)} medewerker(s) gevonden.")

        # # except Exception as e:
            # # # Vang de fout en toon deze aan de gebruiker
            # # self.lbl_status.setText(f"❌ Fout bij server-query. Controleer tabelnaam/kolommen. ({e})")
            # # print(f"SQL Fout: {e}")
            # # self.table.setRowCount(0)
    # # ===============================================================
# # AANPASSING IN xaurum/ui/tabs/StaffSearchTab.py (perform_search)
# # ===============================================================

    # # def perform_search(self, initial_load=False):
        # # # ... (bestaande checks)

        # # self.lbl_status.setText("Bezig met zoeken op server...")
        # # QApplication.processEvents() 

        # # try:
            # # like_term = f"%{search_term.replace(' ', '%')}%"

            # # # 1. De query met de WHERE clausule (voor zoeken)
            # # sql_search_query = """
                # # SELECT TOP 1000 
                    # # staffLASTNAME + ' ' + staffFIRSTNAME AS "Naam", 
                    # # staffGID AS "Staff GID", 
                    # # staffSAPNR AS "SAPNR", 
                    # # staffCOSTCENTER315 AS "Costcenter", 
                    # # staffPHONEPRO AS "Telefoonnummer", 
                    # # staffORGUNIT AS "Manager"
                # # FROM 
                    # # dbo.tblSTAFF
                # # WHERE 
                    # # staffLASTNAME LIKE :term OR 
                    # # staffFIRSTNAME LIKE :term OR 
                    # # staffGID LIKE :term OR 
                    # # staffSAPNR LIKE :term
                # # ORDER BY 
                    # # staffLASTNAME
            # # """
            
            # # # 2. De query ZONDER de WHERE clausule (voor initial_load)
            # # sql_initial_query = """
                # # SELECT TOP 1000 
                    # # staffLASTNAME + ' ' + staffFIRSTNAME AS "Naam", 
                    # # staffGID AS "Staff GID", 
                    # # staffSAPNR AS "SAPNR", 
                    # # staffCOSTCENTER315 AS "Costcenter", 
                    # # staffPHONEPRO AS "Telefoonnummer", 
                    # # staffORGUNIT AS "Manager"
                # # FROM dbo.tblSTAFF
                # # ORDER BY staffLASTNAME
            # # """

            # # if initial_load:
                # # # Gebruik de query ZONDER parameters (Stap 2)
                # # results_df = pd.read_sql(sql_initial_query, self.sql_engine)
            # # else:
                # # # Gebruik de query MET parameters. We moeten de query wrappen in text().
                # # results_df = pd.read_sql(
                    # # text(sql_search_query),  # <<< FIX: text() zorgt dat plekhouders werken
                    # # self.sql_engine, 
                    # # params={'term': like_term}
                # # )

            # # self.populate_table(results_df)
            # # self.lbl_status.setText(f"✅ {len(results_df)} medewerker(s) gevonden.")

        # # except Exception as e:
            # # # Vang de fout en toon deze aan de gebruiker
            # # self.lbl_status.setText(f"❌ Fout bij server-query. Controleer tabelnaam/kolommen. ({e})")
            # # print(f"SQL Fout: {e}")
            # # self.table.setRowCount(0)
    # # ===============================================================
# # AANPASSING IN xaurum/ui/tabs/StaffSearchTab.py (perform_search)
# # ===============================================================

    # def perform_search(self, initial_load=False):
        # # ... (bestaande checks voor engine en search_term)

        # self.lbl_status.setText("Bezig met zoeken op server...")
        # QApplication.processEvents() 

        # try:
            # search_term = self.search_input.text().strip() # Zorg dat search_term hier gedefinieerd is
            # like_term = f"%{search_term.replace(' ', '%')}%"

            # # 1. De query met de WHERE clausule (voor zoeken)
            # sql_search_query = """
                # SELECT TOP 1000 
                    # staffLASTNAME + ' ' + staffFIRSTNAME AS "Naam", 
                    # staffGID AS "Staff GID", 
                    # staffSAPNR AS "SAPNR", 
                    # staffCOSTCENTER315 AS "Costcenter", 
                    # staffPHONEPRO AS "Telefoonnummer", 
                    # staffORGUNIT AS "Manager"
                # FROM 
                    # dbo.tblSTAFF 
                # WHERE 
                    # staffLASTNAME LIKE :term OR 
                    # staffFIRSTNAME LIKE :term OR 
                    # staffGID LIKE :term OR 
                    # staffSAPNR LIKE :term
                # ORDER BY 
                    # staffLASTNAME
            # """
            
            # # 2. De query ZONDER de WHERE clausule (voor initial_load)
            # sql_initial_query = """
                # SELECT TOP 1000 
                    # staffLASTNAME + ' ' + staffFIRSTNAME AS "Naam", 
                    # staffGID AS "Staff GID", 
                    # staffSAPNR AS "SAPNR", 
                    # staffCOSTCENTER315 AS "Costcenter", 
                    # staffPHONEPRO AS "Telefoonnummer", 
                    # staffORGUNIT AS "Manager"
                # FROM dbo.tblSTAFF
                # ORDER BY staffLASTNAME
            # """

            # if initial_load:
                # # Gebruik de query ZONDER parameters
                # results_df = pd.read_sql(sql_initial_query, self.sql_engine)
            # else:
                # # Gebruik de query MET parameters. We moeten de query wrappen in text().
                # results_df = pd.read_sql(
                    # text(sql_search_query),  # <<< DE FIX: WRAAI DE QUERY IN text()
                    # self.sql_engine, 
                    # params={'term': like_term}
                # )

            # self.populate_table(results_df)
            # self.lbl_status.setText(f"✅ {len(results_df)} medewerker(s) gevonden.")

        # except NameError as e:
             # # Vang NameError op als search_term niet gedefinieerd zou zijn (wat niet zou mogen)
             # self.lbl_status.setText(f"❌ Fout bij server-query. ({e})")
             # print(f"NameError: {e}")
             # self.table.setRowCount(0)
        # except Exception as e:
            # # Vang de pyodbc.ProgrammingError op
            # self.lbl_status.setText(f"❌ Fout bij server-query. (pyodbc.ProgrammingError) ({e})")
            # print(f"SQL Fout: {e}")
            # self.table.setRowCount(0)    
    
    # def populate_table(self, results_df: pd.DataFrame):
        # """Vult de QTableWidget met de zoekresultaten."""
        # self.table.setRowCount(0)
        # if results_df.empty:
            # return

        # self.table.setRowCount(len(results_df))
        
        # # Kolomnamen komen overeen met de aliassen in de SQL-query
        # cols_to_show = ["Naam", "Staff GID", "SAPNR", "Costcenter", "Telefoonnummer", "Manager"]
        
        # for row_idx, (index, row) in enumerate(results_df.iterrows()):
            # for col_idx, header in enumerate(cols_to_show):
                
                # value = str(row.get(header, "") or "").strip()
                
                # if value.lower() in ('nan', 'null', ''):
                    # value = ""
                
                # item = QTableWidgetItem(value)
                
                # if header in ["Costcenter", "Manager"]:
                    # font = QFont()
                    # font.setBold(True)
                    # item.setFont(font)
                    # item.setForeground(QBrush(QColor("#005EB8")))
                
                # self.table.setItem(row_idx, col_idx, item)
                
        # self.table.resizeColumnsToContents()