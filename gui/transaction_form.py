from typing import List, Dict

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QPushButton,
    QLabel,
    QDateEdit,
)
from PySide6.QtCore import Signal, QDate


class TransactionForm(QWidget):
    transaction_submitted = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._categories: List[Dict] = []

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()

        # ---- widgets ----
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("Amount")

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Expense", "Income"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)

        self.category_combo = QComboBox()

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Cash", "Card", "UPI", "Bank Transfer"])

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Tags (comma separated)")

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Note")

        # ✅ REPEAT COMBO (proper place)
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems([
            "None",
            "Every week",
            "Every month",
            "Every year",
        ])

        self.add_button = QPushButton("➕ Add")
        self.add_button.setObjectName("PrimaryButton")
        self.add_button.clicked.connect(self.on_submit)

        # ---- layout ----
        row1.addWidget(QLabel("Date:"))
        row1.addWidget(self.date_edit)
        row1.addWidget(QLabel("Amount:"))
        row1.addWidget(self.amount_edit)
        row1.addWidget(QLabel("Type:"))
        row1.addWidget(self.type_combo)
        row1.addWidget(QLabel("Category:"))
        row1.addWidget(self.category_combo)

        row2.addWidget(QLabel("Payment:"))
        row2.addWidget(self.payment_combo)
        row2.addWidget(QLabel("Repeat:"))
        row2.addWidget(self.repeat_combo)
        row2.addWidget(QLabel("Tags:"))
        row2.addWidget(self.tags_edit)
        row2.addWidget(self.add_button)

        main_layout.addLayout(row1)
        main_layout.addLayout(row2)
        main_layout.addWidget(QLabel("Note:"))
        main_layout.addWidget(self.note_edit)

    # ----- categories from DB -----

    def set_category_options(self, categories: List[Dict]):
        self._categories = categories or []
        self._populate_category_combo()

    def _on_type_changed(self, _text: str):
        self._populate_category_combo()

    def _populate_category_combo(self):
        current_type = self.type_combo.currentText().lower()
        prev = self.category_combo.currentText()

        names = [c["name"] for c in self._categories if c["type"] == current_type]
        if not names:
            names = ["General"] if current_type == "expense" else ["Other"]

        self.category_combo.clear()
        self.category_combo.addItems(names)

        if prev in names:
            self.category_combo.setCurrentText(prev)

    # ----- submit -----

    def on_submit(self):
        amount_text = self.amount_edit.text().strip()
        if not amount_text:
            return

        try:
            amount = float(amount_text)
        except ValueError:
            return

        type_str = self.type_combo.currentText().lower()

        data = {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "amount": amount,
            "type": type_str,
            "category": self.category_combo.currentText(),
            "payment_method": self.payment_combo.currentText(),
            "tags": self.tags_edit.text().strip(),
            "note": self.note_edit.toPlainText().strip(),
            "repeat": self.repeat_combo.currentText(),  # ✅ used later by recurring engine
        }

        self.transaction_submitted.emit(data)

        # reset fields
        self.amount_edit.clear()
        self.tags_edit.clear()
        self.note_edit.clear()
        self.repeat_combo.setCurrentIndex(0)
