from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
    QComboBox,
    QMessageBox,
    QLineEdit,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QTextEdit,
)
from PySide6.QtCore import Qt

from db.repository import (
    export_transactions_csv,
    export_transactions_json,
    import_transactions_csv,
    import_transactions_json,
    backup_db,
    restore_db,
    set_setting,
    get_setting,
)
from db.repository import create_recurring_rule, list_recurring_rules, delete_recurring_rule, wipe_all_data


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        title = QLabel("Settings")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-weight: 600; font-size: 12pt;")
        layout.addWidget(title)

        # Currency selection
        row = QHBoxLayout()
        row.addWidget(QLabel("Currency:"))
        self.currency = QComboBox()
        self.currency.addItems(["₹ (INR)", "$ (USD)", "€ (EUR)", "£ (GBP)"])
        current = get_setting("currency", "₹ (INR)")
        if current:
            idx = self.currency.findText(current)
            if idx >= 0:
                self.currency.setCurrentIndex(idx)
        row.addWidget(self.currency)
        save_cur = QPushButton("Save")
        save_cur.clicked.connect(self.save_currency)
        row.addWidget(save_cur)
        layout.addLayout(row)

        # Start of week / month
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Start of Week:"))
        self.week_start = QComboBox()
        self.week_start.addItems(["Sunday", "Monday"])
        ws = get_setting("week_start", "Monday")
        idx = self.week_start.findText(ws)
        if idx >= 0:
            self.week_start.setCurrentIndex(idx)
        row2.addWidget(self.week_start)

        row2.addWidget(QLabel("Start of Month (day):"))
        self.month_start = QComboBox()
        self.month_start.addItems([str(i) for i in range(1, 29)])
        ms = get_setting("month_start", "1")
        idx = self.month_start.findText(ms)
        if idx >= 0:
            self.month_start.setCurrentIndex(idx)
        row2.addWidget(self.month_start)

        save_cycle = QPushButton("Save")
        save_cycle.clicked.connect(self.save_cycle_settings)
        row2.addWidget(save_cycle)
        layout.addLayout(row2)

        # Export / Import
        ex_row = QHBoxLayout()
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_json_btn = QPushButton("Export JSON")
        self.import_csv_btn = QPushButton("Import CSV")
        self.import_json_btn = QPushButton("Import JSON")

        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_json_btn.clicked.connect(self.export_json)
        self.import_csv_btn.clicked.connect(self.import_csv)
        self.import_json_btn.clicked.connect(self.import_json)

        ex_row.addWidget(self.export_csv_btn)
        ex_row.addWidget(self.export_json_btn)
        ex_row.addWidget(self.import_csv_btn)
        ex_row.addWidget(self.import_json_btn)
        layout.addLayout(ex_row)

        # Backup / Restore DB
        br_row = QHBoxLayout()
        self.backup_btn = QPushButton("Backup DB")
        self.restore_btn = QPushButton("Restore DB")
        self.backup_btn.clicked.connect(self.backup_db)
        self.restore_btn.clicked.connect(self.restore_db)
        br_row.addWidget(self.backup_btn)
        br_row.addWidget(self.restore_btn)
        layout.addLayout(br_row)

        # Wipe Data button
        wipe_row = QHBoxLayout()
        self.wipe_btn = QPushButton("🗑 Wipe Data")
        self.wipe_btn.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold;")
        self.wipe_btn.clicked.connect(self.wipe_data)
        wipe_row.addWidget(self.wipe_btn)
        wipe_row.addStretch()
        layout.addLayout(wipe_row)

        layout.addStretch()

        # Recurring rules management
        title2 = QLabel("Recurring Rules")
        title2.setAlignment(Qt.AlignLeft)
        title2.setStyleSheet("font-weight: 600; font-size: 12pt; margin-top:12px;")
        layout.addWidget(title2)

        rr_row = QHBoxLayout()
        self.rr_list = QComboBox()
        self.rr_refresh_btn = QPushButton("Refresh")
        self.rr_add_btn = QPushButton("Add Rule")
        self.rr_del_btn = QPushButton("Delete Rule")
        rr_row.addWidget(self.rr_list)
        rr_row.addWidget(self.rr_refresh_btn)
        rr_row.addWidget(self.rr_add_btn)
        rr_row.addWidget(self.rr_del_btn)
        layout.addLayout(rr_row)

        self.rr_refresh_btn.clicked.connect(self.load_recurring_rules)
        self.rr_add_btn.clicked.connect(self.add_recurring_rule)
        self.rr_del_btn.clicked.connect(self.delete_recurring_rule)

        self.load_recurring_rules()

    def save_currency(self):
        cur = self.currency.currentText()
        set_setting("currency", cur)
        QMessageBox.information(self, "Saved", "Currency saved.")

    def save_cycle_settings(self):
        set_setting("week_start", self.week_start.currentText())
        set_setting("month_start", self.month_start.currentText())
        QMessageBox.information(self, "Saved", "Cycle settings saved.")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "transactions.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            export_transactions_csv(path)
            QMessageBox.information(self, "Exported", f"Exported to {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Export failed: {e}")

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "transactions.json", "JSON Files (*.json)")
        if not path:
            return
        try:
            export_transactions_json(path)
            QMessageBox.information(self, "Exported", f"Exported to {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Export failed: {e}")

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            count = import_transactions_csv(path)
            QMessageBox.information(self, "Imported", f"Imported {count} rows from CSV.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Import failed: {e}")

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            count = import_transactions_json(path)
            QMessageBox.information(self, "Imported", f"Imported {count} rows from JSON.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Import failed: {e}")

    def backup_db(self):
        path, _ = QFileDialog.getSaveFileName(self, "Backup DB", "spent_backup.db", "DB Files (*.db);;All Files (*)")
        if not path:
            return
        ok = backup_db(path)
        if ok:
            QMessageBox.information(self, "Backup", f"Backup created at {path}")
        else:
            QMessageBox.warning(self, "Error", "Backup failed.")

    def restore_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore DB", "", "DB Files (*.db);;All Files (*)")
        if not path:
            return
        ok = restore_db(path)
        if ok:
            QMessageBox.information(self, "Restore", "Database restored. Restart app to apply changes.")
        else:
            QMessageBox.warning(self, "Error", "Restore failed.")

    def wipe_data(self):
        reply = QMessageBox.question(
            self,
            "Wipe All Data",
            "Delete all transactions, budgets, and recurring rules? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        ok = wipe_all_data()
        if ok:
            QMessageBox.information(self, "Data Wiped", "All data has been deleted.")
        else:
            QMessageBox.warning(self, "Error", "Failed to wipe data.")

    # ---- Recurring rules handlers ----
    def load_recurring_rules(self):
        self.rr_list.clear()
        rows = list_recurring_rules()
        for r in rows:
            label = f"{r['id']}: {r['type']} {r['amount']} on {r['next_date']} ({r['every']})"
            self.rr_list.addItem(label, r['id'])

    def add_recurring_rule(self):
        # simple dialog to create a monthly/weekly/yearly rule
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Recurring Rule")
        form = QFormLayout(dlg)

        type_combo = QComboBox()
        type_combo.addItems(["Expense", "Income"])
        amt = QLineEdit()
        category = QLineEdit()
        every = QComboBox()
        every.addItems(["monthly", "weekly", "yearly"])        
        next_date = QLineEdit()
        next_date.setPlaceholderText("YYYY-MM-DD")

        form.addRow("Type:", type_combo)
        form.addRow("Amount:", amt)
        form.addRow("Category:", category)
        form.addRow("Every:", every)
        form.addRow("Next date:", next_date)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        form.addRow(buttons)

        def on_save():
            try:
                data = {
                    "type": type_combo.currentText().lower(),
                    "amount": float(amt.text()),
                    "category": category.text().strip(),
                    "every": every.currentText(),
                    "interval": 1,
                    "next_date": next_date.text().strip() or None,
                }
                create_recurring_rule(data)
                dlg.accept()
                self.load_recurring_rules()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Invalid input: {e}")

        buttons.accepted.connect(on_save)
        buttons.rejected.connect(dlg.reject)
        dlg.exec()

    def delete_recurring_rule(self):
        idx = self.rr_list.currentIndex()
        if idx < 0:
            return
        rid = self.rr_list.currentData()
        if not rid:
            return
        ok = QMessageBox.question(self, "Delete Rule", "Delete selected recurring rule?", QMessageBox.Yes | QMessageBox.No)
        if ok != QMessageBox.Yes:
            return
        delete_recurring_rule(rid)
        self.load_recurring_rules()
