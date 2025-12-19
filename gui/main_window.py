from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QStackedWidget,
    QSizePolicy,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QSpinBox,
    QDoubleSpinBox,
    QProgressBar,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QIcon
import os
import base64
import sys

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from typing import Optional, Dict
from .transaction_form import TransactionForm
from .transaction_list import TransactionListPage
from .reports import ReportsPage
from .settings import SettingsPage

from db.repository import (
    add_transaction,
    list_transactions,
    get_totals,
    filter_transactions,
    get_categories,
    get_expense_by_category_summary,
    get_budgets_with_status,
    create_budget,
    update_budget,
    delete_budget,
    any_budget_overspent,   # <--- add this
    create_recurring_rule,
    get_setting,
    set_setting,
)


# ==========================================================
# LIGHT THEME
# ==========================================================
def get_light_stylesheet() -> str:
    return """
    * {
        font-family: 'Segoe UI', sans-serif;
        font-size: 10pt;
    }

    QMainWindow, QWidget#MainBackground {
        background-color: #f3f4fb;
    }

    QLabel {
        color: #1f2933;
        background: transparent;
    }

    /* Sidebar */
    QFrame#Sidebar {
        background-color: #f6f7ff;
        border-radius: 24px;
        border: 1px solid #d7d9ec;
    }

    QPushButton#NavButton {
        background-color: transparent;
        border-radius: 15px;
        border: 1px solid transparent;
        padding: 9px 14px;
        color: #374151;
        font-weight: 500;
        text-align: left;
    }
    QPushButton#NavButton:hover {
        background-color: #e5e8ff;
        border-color: #c3c8f5;
    }
    QPushButton#NavButton:checked {
        background-color: #4f46e5;
        border-color: #4338ca;
        color: #ffffff;
    }

    /* Cards */
    QFrame#Card {
        background-color: #ffffff;
        border-radius: 22px;
        border: 1px solid #dde2f0;
    }

    /* General Buttons */
    QPushButton {
        background-color: #ffffff;
        border-radius: 14px;
        border: 1px solid #d1d5e5;
        padding: 8px 14px;
        color: #111827;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #eef2ff;
        border-color: #9aa5ff;
    }

    /* Primary Button */
    QPushButton#PrimaryButton {
        background-color: #4f46e5;
        border-radius: 16px;
        border: 1px solid #4338ca;
        color: #ffffff;
        padding: 8px 18px;
        font-weight: 600;
    }

    /* Input fields */
    QLineEdit, QComboBox, QTextEdit, QDateEdit {
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #d1d5e5;
        padding: 6px 10px;
        color: #111827;
    }

    /* Table */
    QTableWidget {
        background-color: #ffffff;
        border-radius: 18px;
        border: 1px solid #dde2f0;
        gridline-color: #e5e7f5;
        color: #111827;
    }
    QHeaderView::section {
        background-color: #f3f4ff;
        padding: 6px;
        font-weight: 600;
        color: #374151;
        border-bottom: 1px solid #dde2f0;
    }

    /* Scrollbar */
    QScrollBar:vertical {
        background: transparent;
        width: 10px;
    }
    QScrollBar::handle:vertical {
        background: #c7d2fe;
        border-radius: 6px;
        min-height: 30px;
    }

    QStatusBar {
        background-color: #f6f7ff;
        border-top: 1px solid #dde2f0;
        color: #4b5563;
    }
    QDoubleSpinBox::up-button,
    QDoubleSpinBox::down-button,
    QSpinBox::up-button,
    QSpinBox::down-button {
        width: 0px;
        height: 0px;
        border: none;
        padding: 0;
    }
    QDoubleSpinBox::drop-down,
    QSpinBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: right;
        width: 18px;
        border: none;
    }
    """


# ==========================================================
# DARK THEME
# ==========================================================
def get_dark_stylesheet() -> str:
    return """
    * {
        font-family: 'Segoe UI', sans-serif;
        font-size: 10pt;
    }

    QMainWindow, QWidget#MainBackground {
        background-color: #0f172a;
    }

    QLabel {
        color: #e2e8f0;
        background: transparent;
    }

    /* Sidebar */
    QFrame#Sidebar {
        background-color: #1e293b;
        border-radius: 24px;
        border: 1px solid #1a2433;
    }

    QPushButton#NavButton {
        background-color: transparent;
        border-radius: 15px;
        border: 1px solid transparent;
        padding: 9px 14px;
        color: #cbd5e1;
        text-align: left;
    }
    QPushButton#NavButton:hover {
        background-color: #293548;
        border-color: #3b4a66;
    }
    QPushButton#NavButton:checked {
        background-color: #4f46e5;
        border-color: #4338ca;
        color: white;
    }

    /* Cards */
    QFrame#Card {
        background-color: #1a2433;
        border-radius: 22px;
        border: 1px solid #273347;
    }

    /* General buttons */
    QPushButton {
        background-color: #1e293b;
        border-radius: 14px;
        border: 1px solid #273347;
        padding: 8px 14px;
        color: #e2e8f0;
    }
    QPushButton:hover {
        background-color: #273347;
    }

    /* Primary Button */
    QPushButton#PrimaryButton {
        background-color: #4f46e5;
        border-radius: 16px;
        border: 1px solid #4338ca;
        color: white;
        padding: 8px 18px;
        font-weight: 600;
    }

    /* Inputs */
    QLineEdit, QComboBox, QTextEdit, QDateEdit {
        background-color: #1e293b;
        border-radius: 12px;
        border: 1px solid #273347;
        padding: 6px 10px;
        color: #e2e8f0;
    }

    /* Table */
    QTableWidget {
        background-color: #1e293b;
        border-radius: 16px;
        border: 1px solid #273347;
        color: #e2e8f0;
        gridline-color: #2c394c;
    }
    QHeaderView::section {
        background-color: #273347;
        color: #e2e8f0;
        font-weight: 600;
        padding: 6px;
        border-bottom: 1px solid #36455d;
    }

    QTableWidget::item:selected {
        background-color: #4f46e5;
        color: white;
    }

    QStatusBar {
        background-color: #1e293b;
        border-top: 1px solid #273347;
        color: #94a3b8;
    }
    """


# ==========================================================
# MAIN WINDOW
# ==========================================================
class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # --- Title card ---
        title_card = QFrame()
        title_card.setObjectName("Card")
        title_layout = QVBoxLayout(title_card)
        title_layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 14pt; font-weight: 600;")
        subtitle = QLabel("Quick overview of your money in Spent.")
        subtitle.setStyleSheet("color: #6b7280;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        main_layout.addWidget(title_card)

        # --- Stats row ---
        stats_card = QFrame()
        stats_card.setObjectName("Card")
        stats_layout = QHBoxLayout(stats_card)
        stats_layout.setContentsMargins(16, 16, 16, 16)
        stats_layout.setSpacing(24)

        self.income_value = QLabel("₹0.00")
        self.expense_value = QLabel("₹0.00")
        self.balance_value = QLabel("₹0.00")

        for lbl in (self.income_value, self.expense_value, self.balance_value):
            lbl.setStyleSheet("font-size: 13pt; font-weight: 600;")

        income_box = QVBoxLayout()
        income_box.addWidget(QLabel("Total Income"))
        income_box.addWidget(self.income_value)

        expense_box = QVBoxLayout()
        expense_box.addWidget(QLabel("Total Expense"))
        expense_box.addWidget(self.expense_value)

        balance_box = QVBoxLayout()
        balance_box.addWidget(QLabel("Current Balance"))
        balance_box.addWidget(self.balance_value)

        stats_layout.addLayout(income_box)
        stats_layout.addLayout(expense_box)
        stats_layout.addLayout(balance_box)
        stats_layout.addStretch()
        main_layout.addWidget(stats_card)

        # --- Middle row: left = small pie, right = recent transactions ---
        middle_row = QHBoxLayout()
        middle_row.setSpacing(8)

        # Pie card
        pie_card = QFrame()
        pie_card.setObjectName("Card")
        pie_layout = QVBoxLayout(pie_card)
        pie_layout.setContentsMargins(12, 12, 12, 12)
        pie_title = QLabel("Top Expense Categories")
        pie_title.setStyleSheet("font-weight: 600;")
        pie_layout.addWidget(pie_title)

        self.pie_fig = Figure(figsize=(3, 3))
        self.pie_canvas = FigureCanvas(self.pie_fig)
        self.pie_ax = self.pie_fig.add_subplot(111)
        pie_layout.addWidget(self.pie_canvas)

        # Recent transactions card
        recent_card = QFrame()
        recent_card.setObjectName("Card")
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(12, 12, 12, 12)
        recent_title = QLabel("Recent Transactions")
        recent_title.setStyleSheet("font-weight: 600;")
        recent_layout.addWidget(recent_title)

        self.recent_table = QTableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(
            ["Date", "Amount", "Type", "Category"]
        )
        self.recent_table.horizontalHeader().setStretchLastSection(True)
        recent_layout.addWidget(self.recent_table)

        middle_row.addWidget(pie_card, 1)
        middle_row.addWidget(recent_card, 1)

        main_layout.addLayout(middle_row)

    # ===== public update methods =====

    def update_totals(self, income: float, expense: float, balance: float):
        self.income_value.setText(f"₹{income:,.2f}")
        self.expense_value.setText(f"₹{expense:,.2f}")
        self.balance_value.setText(f"₹{balance:,.2f}")

    def update_recent(self, rows):
        self.recent_table.setRowCount(0)
        for tx in rows[:5]:
            r = self.recent_table.rowCount()
            self.recent_table.insertRow(r)
            vals = [
                tx.get("date", ""),
                f"{tx.get('amount', 0):.2f}",
                tx.get("type", ""),
                tx.get("category", ""),
            ]
            for c, v in enumerate(vals):
                self.recent_table.setItem(r, c, QTableWidgetItem(str(v)))

    def update_category_pie(self, totals_dict):
        self.pie_ax.clear()

        if not totals_dict:
            self.pie_ax.text(
                0.5,
                0.5,
                "No expense data yet",
                ha="center",
                va="center",
                fontsize=10,
                color="#6b7280",
            )
            self.pie_ax.axis("off")
            self.pie_canvas.draw_idle()
            return

        labels = list(totals_dict.keys())
        values = list(totals_dict.values())

        # keep at most 5 slices, group rest as "Other"
        if len(labels) > 5:
            combined = sorted(
                zip(labels, values), key=lambda x: x[1], reverse=True
            )
            top = combined[:4]
            rest = combined[4:]
            labels = [name for name, _ in top] + ["Other"]
            values = [val for _, val in top] + [sum(v for _, v in rest)]

        colors = ["#7c3aed", "#a855f7", "#ec4899", "#6366f1", "#22c55e"]
        wedges, texts, autotexts = self.pie_ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            radius=0.90,
            colors=colors[: len(labels)],
            textprops={"fontsize": 8},
            pctdistance=0.7,
            labeldistance=1.05,
        )
        for t in texts:
            t.set_fontsize(8)
        for at in autotexts:
            at.set_fontsize(8)

        self.pie_ax.axis("equal")
        self.pie_fig.tight_layout(pad=1.0)
        self.pie_canvas.draw_idle()


class CategoriesPage(QWidget):
    categories_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        title = QLabel("Categories")
        title.setStyleSheet("font-weight: 600;")
        card_layout.addWidget(title)

        form_row = QHBoxLayout()
        form_row.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Category name")

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Expense", "Income"])

        self.add_btn = QPushButton("➕ Add")
        self.add_btn.setObjectName("PrimaryButton")
        self.update_btn = QPushButton("✏️ Update")
        self.delete_btn = QPushButton("🗑 Delete")

        self.add_btn.clicked.connect(self.add_category)
        self.update_btn.clicked.connect(self.update_category)
        self.delete_btn.clicked.connect(self.delete_category)

        form_row.addWidget(QLabel("Name:"))
        form_row.addWidget(self.name_edit)
        form_row.addWidget(QLabel("Type:"))
        form_row.addWidget(self.type_combo)
        form_row.addWidget(self.add_btn)
        form_row.addWidget(self.update_btn)
        form_row.addWidget(self.delete_btn)

        card_layout.addLayout(form_row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Type"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnHidden(0, True)  # hide ID column
        self.table.itemSelectionChanged.connect(self.load_selected_into_form)

        card_layout.addWidget(self.table)
        main_layout.addWidget(card)

        self.refresh_table()

    # --- DB hooks ---

    def refresh_table(self):
        from db.repository import get_categories  # local import to avoid circular at top

        rows = get_categories()
        self.table.setRowCount(0)

        for c in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(c["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(c["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(c["type"]))

    def _current_category_id(self) -> int | None:
        r = self.table.currentRow()
        if r < 0:
            return None
        item = self.table.item(r, 0)
        if not item:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def load_selected_into_form(self):
        r = self.table.currentRow()
        if r < 0:
            return
        name_item = self.table.item(r, 1)
        type_item = self.table.item(r, 2)
        if name_item:
            self.name_edit.setText(name_item.text())
        if type_item:
            t = type_item.text()
            idx = 0 if t == "expense" else 1
            self.type_combo.setCurrentIndex(idx)

    def add_category(self):
        from db.repository import create_category

        name = self.name_edit.text().strip()
        type_str = self.type_combo.currentText().lower()
        if not name:
            return

        created = create_category(name, type_str)
        if created:
            self.refresh_table()
            self.categories_changed.emit()

    def update_category(self):
        from db.repository import update_category

        cat_id = self._current_category_id()
        if cat_id is None:
            return

        name = self.name_edit.text().strip()
        type_str = self.type_combo.currentText().lower()
        if not name:
            return

        updated = update_category(cat_id, name, type_str)
        if updated:
            self.refresh_table()
            self.categories_changed.emit()

    def delete_category(self):
        from db.repository import delete_category

        cat_id = self._current_category_id()
        if cat_id is None:
            return

        deleted = delete_category(cat_id)
        if deleted:
            self.refresh_table()
            self.categories_changed.emit()



class BudgetsPage(QWidget):
    budgets_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.has_overspend = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        title = QLabel("Budgets")
        title.setStyleSheet("font-size: 13pt; font-weight: 600;")
        header_row.addWidget(title)
        header_row.addStretch()

        self.add_btn = QPushButton("➕ Add Budget")
        self.add_btn.setObjectName("PrimaryButton")
        self.add_btn.clicked.connect(self.open_add_dialog)
        header_row.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        header_row.addWidget(self.edit_btn)

        self.del_btn = QPushButton("🗑 Delete")
        self.del_btn.clicked.connect(self.delete_selected_budget)
        header_row.addWidget(self.del_btn)

        card_layout.addLayout(header_row)

        # Table: ID hidden + 6 visible columns
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Category", "Budget (₹)", "Spent", "Remaining", "Cycle day", "Progress"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnHidden(0, True)

        card_layout.addWidget(self.table)
        main_layout.addWidget(card)

    # ---- internal helpers ----

    def _selected_row_index(self) -> int:
        return self.table.currentRow()

    def _selected_budget_id(self) -> Optional[int]:
        r = self._selected_row_index()
        if r < 0:
            return None
        item = self.table.item(r, 0)
        if not item:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    # ---- public API called by MainWindow ----

    def refresh_data(self):
        """Reload budgets and spending status from DB and update table."""
        rows = get_budgets_with_status()
        self.has_overspend = any(b["overspent"] for b in rows)

        self.table.setRowCount(0)

        for b in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)

            # ID (hidden)
            self.table.setItem(r, 0, QTableWidgetItem(str(b["id"])))

            self.table.setItem(r, 1, QTableWidgetItem(b["category_name"]))
            self.table.setItem(r, 2, QTableWidgetItem(f"{b['amount']:.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{b['spent']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{b['remaining']:.2f}"))
            self.table.setItem(r, 5, QTableWidgetItem(str(b["cycle_day"])))

            # Progress capsule
            progress = QProgressBar()
            progress.setRange(0, 100)

            percent = b["percent"]
            overspent = b["overspent"]

            if overspent:
                progress.setValue(100)
                progress.setFormat(f"{percent:.0f}% (Over)")
                chunk_color = "#ef4444"
            else:
                clamped = max(0, min(int(round(percent)), 100))
                progress.setValue(clamped)
                progress.setFormat(f"{percent:.0f}%")
                chunk_color = "#7c3aed"  # neon purple

            progress.setTextVisible(True)
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border-radius: 8px;
                    background-color: rgba(148, 163, 184, 0.28);
                    text-align: center;
                    min-height: 14px;
                }}
                QProgressBar::chunk {{
                    border-radius: 8px;
                    background-color: {chunk_color};
                }}
            """)

            self.table.setCellWidget(r, 6, progress)

    # ---- dialogs ----

    def open_add_dialog(self):
        self._open_budget_dialog(existing=None)

    def open_edit_dialog(self):
        bid = self._selected_budget_id()
        if bid is None:
            return

        # Read row info
        r = self._selected_row_index()
        name_item = self.table.item(r, 1)
        amount_item = self.table.item(r, 2)
        cycle_item = self.table.item(r, 5)

        if not (name_item and amount_item and cycle_item):
            return

        existing = {
            "id": bid,
            "category_name": name_item.text(),
            "amount": float(amount_item.text()),
            "cycle_day": int(cycle_item.text()),
        }
        self._open_budget_dialog(existing=existing)

    def _open_budget_dialog(self, existing: Optional[Dict] = None):
        dlg = QDialog(self)
        dlg.setModal(True)
        dlg.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dlg.setAttribute(Qt.WA_TranslucentBackground)

        # Outer layout removes big border
        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        # Popup card container
        card = QFrame()
        card.setObjectName("popupCard")
        card.setMinimumWidth(420)
        card.setStyleSheet("""
            QFrame#popupCard {
                border-radius: 20px;
                background-color: rgba(30, 30, 45, 0.88);
            }
            QLabel {
                font-size: 11pt;
                color: #d8d9e0;
            }
            QComboBox, QDoubleSpinBox, QSpinBox {
                border-radius: 12px;
                padding: 8px;
                font-size: 11pt;
            }
            QPushButton {
                border-radius: 14px;
                padding: 8px 18px;
                font-weight: 600;
            }
            QPushButton#saveBtn {
                background-color: #7c3aed;
                color: white;
            }
            QPushButton#saveBtn:hover {
                background-color: #8b5cf6;
            }
            QPushButton#cancelBtn {
                background-color: rgba(255,255,255,0.10);
                border: 1px solid rgba(255,255,255,0.25);
                color: #e5e7eb;
            }
            QPushButton#cancelBtn:hover {
                background-color: rgba(255,255,255,0.18);
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 24)
        card_layout.setSpacing(16)

        title = QLabel("Add Budget" if existing is None else "Edit Budget")
        title.setStyleSheet("font-size: 16pt; font-weight: 600; margin-bottom: 6px;")
        card_layout.addWidget(title)

        # CATEGORY
        card_layout.addWidget(QLabel("Category:"))
        cat_combo = QComboBox()
        for c in get_categories("expense"):
            cat_combo.addItem(c["name"], c["id"])
        card_layout.addWidget(cat_combo)

        # AMOUNT
        card_layout.addWidget(QLabel("Monthly Budget (₹):"))
        amount = QDoubleSpinBox()
        amount.setDecimals(2)
        amount.setRange(0, 10_000_000)
        amount.setSingleStep(500.0)
        card_layout.addWidget(amount)

        # CYCLE DAY
        card_layout.addWidget(QLabel("Cycle Day (1–28):"))
        cycle = QSpinBox()
        cycle.setRange(1, 28)
        card_layout.addWidget(cycle)

        # Prefill on edit
        if existing:
            amount.setValue(existing["amount"])
            cycle.setValue(existing["cycle_day"])
            idx = cat_combo.findText(existing["category_name"])
            if idx >= 0:
                cat_combo.setCurrentIndex(idx)

        # BUTTON BAR
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("saveBtn")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        card_layout.addLayout(btn_row)

        outer.addWidget(card)

        cancel_btn.clicked.connect(dlg.reject)
        save_btn.clicked.connect(dlg.accept)

        dlg.resize(450, 380)

        # Fade-in animation
        dlg.setWindowOpacity(0.0)
        anim = QPropertyAnimation(dlg, b"windowOpacity")
        anim.setDuration(160)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

        if dlg.exec() != QDialog.Accepted:
            return

        category_id = cat_combo.currentData()
        amt = amount.value()
        cyc = cycle.value()

        if existing:
            update_budget(existing["id"], category_id, amt, cyc)
        else:
            create_budget(category_id, amt, cyc)

        self.refresh_data()
        self.budgets_changed.emit()


    def delete_selected_budget(self):
        bid = self._selected_budget_id()
        if bid is None:
            return

        reply = QMessageBox.question(
            self,
            "Delete Budget",
            "Are you sure you want to delete this budget?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        deleted = delete_budget(bid)
        if deleted:
            self.refresh_data()
            self.budgets_changed.emit()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spent — Personal Expense Tracker")
        self.resize(1100, 700)
        # load persisted theme
        theme = get_setting("theme", "light") or "light"
        self.current_theme = theme

        central = QWidget()
        central.setObjectName("MainBackground")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 8)
        main_layout.setSpacing(10)

        # Header / Summary bar
        header_card = QFrame()
        header_card.setObjectName("Card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(24)

        # optional logo + app title (if `assets/logo.png` or `logo.png` exists)
        try:
            logo_lbl = QLabel()
            # When running as a PyInstaller one-file bundle the bundled files
            # are extracted into `sys._MEIPASS`. Prefer that path first, then
            # fall back to the working directory assets folder.
            base_path = getattr(sys, "_MEIPASS", os.getcwd())
            logo_path = os.path.join(base_path, "assets", "logo.png")

            # If no bundled logo, try a `logo.png` in the working directory,
            # otherwise create a small placeholder in the working `assets/`.
            if not os.path.exists(logo_path):
                root_logo = os.path.join(os.getcwd(), "logo.png")
                if os.path.exists(root_logo):
                    logo_path = root_logo
                else:
                    try:
                        # Create placeholder in the project assets (not _MEIPASS)
                        placeholder_dir = os.path.join(os.getcwd(), "assets")
                        os.makedirs(placeholder_dir, exist_ok=True)
                        placeholder_path = os.path.join(placeholder_dir, "logo.png")
                        placeholder_b64 = (
                            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
                        )
                        if not os.path.exists(placeholder_path):
                            with open(placeholder_path, "wb") as f:
                                f.write(base64.b64decode(placeholder_b64))
                        logo_path = placeholder_path
                    except Exception:
                        pass

            if os.path.exists(logo_path):
                pix = QPixmap(logo_path).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_lbl.setPixmap(pix)
                logo_lbl.setFixedSize(36, 36)
                header_layout.addWidget(logo_lbl)
                title_lbl = QLabel("Spent")
                title_lbl.setStyleSheet("font-size:13pt; font-weight:700; margin-left:6px;")
                header_layout.addWidget(title_lbl)
                try:
                    self.setWindowIcon(QIcon(logo_path))
                except Exception:
                    pass
            else:
                title_lbl = QLabel("Spent")
                title_lbl.setStyleSheet("font-size:13pt; font-weight:700;")
                header_layout.addWidget(title_lbl)
        except Exception:
            pass

        self.label_income = QLabel("Income: ₹0.00")
        self.label_expense = QLabel("Expense: ₹0.00")
        self.label_balance = QLabel("Balance: ₹0.00")

        header_layout.addWidget(self.label_income)
        header_layout.addWidget(self.label_expense)
        header_layout.addWidget(self.label_balance)
        header_layout.addStretch()

        self.theme_button = QPushButton("🌙 Dark")
        self.theme_button.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_button)

        main_layout.addWidget(header_card)

        # Sidebar + pages
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(10)

        # Buttons
        self.btn_dashboard = QPushButton("🏠 Dashboard")
        self.btn_transactions = QPushButton("📒 Transactions")
        self.btn_categories = QPushButton("📂 Categories")
        self.btn_budgets = QPushButton("💰 Budgets")
        self.btn_reports = QPushButton("📊 Reports")
        self.btn_settings = QPushButton("⚙️ Settings")

        self.nav_buttons = [
            self.btn_dashboard,
            self.btn_transactions,
            self.btn_categories,
            self.btn_budgets,
            self.btn_reports,
            self.btn_settings,
        ]

        for b in self.nav_buttons:
            b.setObjectName("NavButton")
            b.setCheckable(True)
            sidebar_layout.addWidget(b)
        sidebar_layout.addStretch()
        content_layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        main_layout.addLayout(content_layout)

        # Pages
        self.dashboard_page = DashboardPage()
        self.transactions_page = self._build_transactions_page()
        self.categories_page = CategoriesPage()
        self.budgets_page = BudgetsPage()
        self.reports_page = ReportsPage()
        self.settings_page = SettingsPage()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.transactions_page)
        self.stack.addWidget(self.categories_page)
        self.stack.addWidget(self.budgets_page)
        self.stack.addWidget(self.reports_page)
        self.stack.addWidget(self.settings_page)
        # when categories change from Category page -> refresh dropdowns
        self.categories_page.categories_changed.connect(self.on_categories_changed)

        # initial category load
        self.on_categories_changed()
        # Nav logic
        self.btn_dashboard.clicked.connect(lambda: self._switch_page(0, self.btn_dashboard))
        self.btn_transactions.clicked.connect(lambda: self._switch_page(1, self.btn_transactions))
        self.btn_categories.clicked.connect(lambda: self._switch_page(2, self.btn_categories))
        self.btn_budgets.clicked.connect(lambda: self._switch_page(3, self.btn_budgets))
        self.btn_reports.clicked.connect(lambda: self._switch_page(4, self.btn_reports))
        self.btn_settings.clicked.connect(lambda: self._switch_page(5, self.btn_settings))

        self.statusBar().showMessage("Ready — Spent")

        # Start on Transactions page
        self._switch_page(1, self.btn_transactions)
        self.refresh_transactions()
        self.refresh_totals()
        self.reports_page.refresh_data()
        # apply theme from settings
        try:
            if self.current_theme == "dark":
                QApplication.instance().setStyleSheet(get_dark_stylesheet())
                self.theme_button.setText("☀️ Light")
            else:
                QApplication.instance().setStyleSheet(get_light_stylesheet())
                self.theme_button.setText("🌙 Dark")
        except Exception:
            pass
        # when categories change -> refresh dropdowns
        self.categories_page.categories_changed.connect(self.on_categories_changed)

        # when budgets change -> refresh alerts / indicators
        self.budgets_page.budgets_changed.connect(self.refresh_budgets_ui)

        # load categories + budgets initially
        self.on_categories_changed()
        self.refresh_budgets_ui()
    def _build_transactions_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        title = QLabel("Transactions")
        card_layout.addWidget(title)

        self.transaction_form = TransactionForm()
        self.transaction_list = TransactionListPage()

        self.transaction_form.transaction_submitted.connect(self.handle_transaction_submitted)
        self.transaction_list.filters_changed.connect(self.apply_filters)

        card_layout.addWidget(self.transaction_form)
        card_layout.addWidget(self.transaction_list)
        layout.addWidget(card)
        return container

    # ---------- DB-related helpers ----------

    def handle_transaction_submitted(self, data: dict):
        # If user asked to repeat this transaction, create a recurring rule
        repeat = data.get("repeat")
        if repeat and repeat != "None":
            mapping = {
                "Every week": ("weekly", 1),
                "Every month": ("monthly", 1),
                "Every year": ("yearly", 1),
            }
            every, interval = mapping.get(repeat, ("monthly", 1))
            rule = {
                "type": data.get("type"),
                "amount": data.get("amount"),
                "category": data.get("category"),
                "payment_method": data.get("payment_method"),
                "tags": data.get("tags"),
                "note": data.get("note"),
                "every": every,
                "interval": interval,
                "next_date": data.get("date"),
            }
            try:
                create_recurring_rule(rule)
            except Exception:
                pass

        # Always add the immediate transaction
        add_transaction(data)
        self.refresh_transactions()
        self.refresh_totals()
        self.reports_page.refresh_data()
        self.refresh_budgets_ui()

    def refresh_transactions(self):
        rows = list_transactions()
        self.transaction_list.set_transactions(rows)

        # dashboard: recent transactions + top categories
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.update_recent(rows)
            cat_totals = get_expense_by_category_summary()
            self.dashboard_page.update_category_pie(cat_totals)

    def refresh_totals(self):
        inc, exp, bal = get_totals()
        self.label_income.setText(f"Income: ₹{inc:,.2f}")
        self.label_expense.setText(f"Expense: ₹{exp:,.2f}")
        self.label_balance.setText(f"Balance: ₹{bal:,.2f}")

        # also update dashboard cards
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.update_totals(inc, exp, bal)

    # ---------- UI helpers ----------

    def _switch_page(self, index, button):
        for b in self.nav_buttons:
            b.setChecked(False)
        button.setChecked(True)
        self.stack.setCurrentIndex(index)

    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
            QApplication.instance().setStyleSheet(get_dark_stylesheet())
            self.theme_button.setText("☀️ Light")
        else:
            self.current_theme = "light"
            QApplication.instance().setStyleSheet(get_light_stylesheet())
            self.theme_button.setText("🌙 Dark")

        # persist theme choice
        try:
            set_setting("theme", self.current_theme)
        except Exception:
            pass
    def apply_filters(self, f: dict):
        rows = filter_transactions(
            date_from=f["date_from"],
            date_to=f["date_to"],
            category=f["category"],
            type_=f["type"],
        )
        self.transaction_list.set_transactions(rows)
        self.refresh_totals()
    def on_categories_changed(self):
        """Reload categories from DB and push them into form + filters."""
        self.categories_data = get_categories()
        self._apply_categories_to_children()

    def _apply_categories_to_children(self):
        if hasattr(self, "transaction_form"):
            self.transaction_form.set_category_options(self.categories_data)
        if hasattr(self, "transaction_list"):
            self.transaction_list.set_category_options(self.categories_data)
    def refresh_budgets_ui(self):
        """Refresh budgets table + update overspend indicator."""
        self.budgets_page.refresh_data()
        overspent = getattr(self.budgets_page, "has_overspend", False)
        self._update_budget_alert_indicator(overspent)


    def _update_budget_alert_indicator(self, overspent: bool):
        if overspent:
            self.btn_budgets.setText("💰 Budgets ⚠")
            # don't spam, just set a helpful status
            self.statusBar().showMessage("Budget alert: some categories are overspent this cycle.")
        else:
            self.btn_budgets.setText("💰 Budgets")
            self.statusBar().showMessage("Ready — Spent")
__all__ = ["MainWindow", "get_light_stylesheet", "get_dark_stylesheet"]
