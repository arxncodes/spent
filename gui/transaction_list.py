from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QComboBox,
    QDateEdit,
    QPushButton,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QLineEdit,
    QTextEdit,
    QMessageBox,
)
from PySide6.QtCore import QDate, Signal

from db.repository import update_transaction, delete_transaction


class TransactionListPage(QWidget):
    filters_changed = Signal(dict)  # emit filters upward

    def __init__(self, parent=None):
        super().__init__(parent)

        self._categories: List[Dict] = []

        main_layout = QVBoxLayout(self)

        # === FILTER BAR ===
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())

        self.category_filter = QComboBox()
        self.category_filter.addItem("All")  # dynamic categories later

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Expense", "Income"])

        self.apply_btn = QPushButton("🔍 Apply")
        self.apply_btn.setObjectName("PrimaryButton")
        self.reset_btn = QPushButton("♻ Reset")

        self.apply_btn.clicked.connect(self.apply_filters)
        self.reset_btn.clicked.connect(self.reset_filters)

        # Edit / Delete buttons
        self.edit_btn = QPushButton("✏️ Edit")
        self.delete_btn = QPushButton("🗑 Delete")
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        self.delete_btn.clicked.connect(self.delete_selected)

        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(self.apply_btn)
        filter_layout.addWidget(self.reset_btn)
        filter_layout.addWidget(self.edit_btn)
        filter_layout.addWidget(self.delete_btn)

        # === TABLE ===
        # include hidden ID column at index 0
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Date", "Amount", "Type", "Category", "Payment", "Tags", "Note"]
        )
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(True)

        main_layout.addLayout(filter_layout)
        main_layout.addWidget(self.table)

    # ----- categories from DB -----

    def set_category_options(self, categories: List[Dict]):
        """Fill category filter combo."""
        self._categories = categories or []
        prev = self.category_filter.currentText()

        names = sorted({c["name"] for c in self._categories})

        self.category_filter.clear()
        self.category_filter.addItem("All")
        for n in names:
            self.category_filter.addItem(n)

        if prev in ["All"] + names:
            self.category_filter.setCurrentText(prev)

    # ----- filters -----

    def apply_filters(self):
        payload = {
            "date_from": self.date_from.date().toString("yyyy-MM-dd"),
            "date_to": self.date_to.date().toString("yyyy-MM-dd"),
            "category": self.category_filter.currentText(),
            "type": self.type_filter.currentText(),
        }
        self.filters_changed.emit(payload)

    def reset_filters(self):
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.category_filter.setCurrentIndex(0)
        self.type_filter.setCurrentIndex(0)
        self.apply_filters()

    # ----- table -----

    def set_transactions(self, rows: List[Dict]):
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)

            # store id in hidden column
            self.table.setItem(r, 0, QTableWidgetItem(str(row.get("id", ""))))

            vals = [
                row["date"],
                f"{row['amount']:.2f}",
                row["type"],
                row["category"],
                row["payment_method"],
                row["tags"],
                row["note"],
            ]
            for c, v in enumerate(vals, start=1):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))

    def _selected_row_tx_id(self) -> Optional[int]:
        r = self.table.currentRow()
        if r < 0:
            return None
        item = self.table.item(r, 0)
        if not item:
            return None
        try:
            return int(item.text())
        except Exception:
            return None

    def open_edit_dialog(self):
        tx_id = self._selected_row_tx_id()
        if tx_id is None:
            return

        # gather current values from row
        r = self.table.currentRow()
        date = self.table.item(r, 1).text()
        amount = self.table.item(r, 2).text()
        type_ = self.table.item(r, 3).text()
        category = self.table.item(r, 4).text()
        payment = self.table.item(r, 5).text()
        tags = self.table.item(r, 6).text()
        note = self.table.item(r, 7).text()

        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Transaction")
        form = QFormLayout(dlg)

        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.fromString(date, "yyyy-MM-dd"))

        amt_edit = QLineEdit()
        amt_edit.setText(amount)

        type_combo = QComboBox()
        type_combo.addItems(["Expense", "Income"])
        type_combo.setCurrentText(type_.capitalize())

        cat_edit = QLineEdit()
        cat_edit.setText(category)

        pay_edit = QLineEdit()
        pay_edit.setText(payment)

        tags_edit = QLineEdit()
        tags_edit.setText(tags)

        note_edit = QTextEdit()
        note_edit.setPlainText(note)

        form.addRow("Date:", date_edit)
        form.addRow("Amount:", amt_edit)
        form.addRow("Type:", type_combo)
        form.addRow("Category:", cat_edit)
        form.addRow("Payment:", pay_edit)
        form.addRow("Tags:", tags_edit)
        form.addRow("Note:", note_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        form.addRow(buttons)

        def on_accept():
            try:
                data = {
                    "date": date_edit.date().toString("yyyy-MM-dd"),
                    "amount": float(amt_edit.text()),
                    "type": type_combo.currentText().lower(),
                    "category": cat_edit.text().strip(),
                    "payment_method": pay_edit.text().strip(),
                    "tags": tags_edit.text().strip(),
                    "note": note_edit.toPlainText().strip(),
                }
                ok = update_transaction(tx_id, data)
                if ok:
                    dlg.accept()
                    # refresh parent list via filters
                    self.apply_filters()
                else:
                    QMessageBox.warning(self, "Error", "Failed to update transaction.")
            except Exception:
                QMessageBox.warning(self, "Error", "Invalid input.")

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dlg.reject)

        dlg.exec()

    def delete_selected(self):
        tx_id = self._selected_row_tx_id()
        if tx_id is None:
            return

        reply = QMessageBox.question(self, "Delete Transaction", "Delete selected transaction?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        ok = delete_transaction(tx_id)
        if ok:
            self.apply_filters()
        else:
            QMessageBox.warning(self, "Error", "Failed to delete transaction.")
