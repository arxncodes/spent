from typing import List, Dict
import numpy as np
from matplotlib.patches import ConnectionPatch
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from db.repository import (
    get_expense_by_category_summary,
    get_monthly_income_expense_summary,
    get_balance_timeseries,
)


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Title card
        title_card = QFrame()
        title_card.setObjectName("Card")
        title_layout = QVBoxLayout(title_card)
        title_layout.setContentsMargins(16, 12, 16, 12)
        title = QLabel("Reports & Insights")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size: 14pt; font-weight: 600;")
        subtitle = QLabel("Visualize your spending, income, and balance over time.")
        subtitle.setAlignment(Qt.AlignLeft)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addWidget(title_card)

        # Charts container
        charts_row = QHBoxLayout()
        charts_row.setSpacing(8)

        # Left column: Pie + Balance line stacked
        left_col = QVBoxLayout()
        left_col.setSpacing(8)

        self.pie_card, self.pie_canvas, self.pie_ax = self._create_chart_card("Expense by Category")
        left_col.addWidget(self.pie_card)

        self.balance_card, self.balance_canvas, self.balance_ax = self._create_chart_card("Balance Over Time")
        left_col.addWidget(self.balance_card)

        # Right column: Monthly bar
        self.bar_card, self.bar_canvas, self.bar_ax = self._create_chart_card("Monthly Income vs Expense", stretch=True)

        charts_row.addLayout(left_col)
        charts_row.addWidget(self.bar_card)

        layout.addLayout(charts_row)

    def _create_chart_card(self, title: str, stretch: bool = False):
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(6)

        label = QLabel(title)
        label.setAlignment(Qt.AlignLeft)
        label.setStyleSheet("font-weight: 600;")
        card_layout.addWidget(label)

        fig = Figure(figsize=(4, 3))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        card_layout.addWidget(canvas)

        if stretch:
            card.setMinimumWidth(420)

        return card, canvas, ax

    # ------------ PUBLIC API ------------

    def refresh_data(self):
        """Call this whenever transactions change."""
        self._draw_expense_pie()
        self._draw_monthly_bar()
        self._draw_balance_line()

    # ------------ INDIVIDUAL CHART DRAWS ------------

    def _draw_expense_pie(self):
        self.pie_ax.clear()
        self.pie_ax.set_title("Expense by Category", fontsize=10, pad=6)

        data = get_expense_by_category_summary()
        if not data:
            self.pie_ax.text(
                0.5, 0.5, "No expense data",
                ha="center", va="center",
                fontsize=11, color="#6b7280",
            )
            self.pie_canvas.draw_idle()
            return

        labels = list(data.keys())
        values = list(data.values())

        colors = ["#7c3aed", "#a855f7", "#ec4899", "#6366f1", "#22c55e", "#f97316", "#0ea5e9"]
        while len(colors) < len(labels):
            colors += colors

        # Text inside pie, no connector lines
        wedges, texts, autotexts = self.pie_ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            radius=0.90,
            colors=colors[: len(labels)],
            textprops={"fontsize": 8},
            pctdistance=0.70,     # % stays inside
            labeldistance=1.02,   # category stays near border but inside graph
        )

        # Improve readability
        for t in texts:
            t.set_fontsize(8)
        for at in autotexts:
            at.set_fontsize(8)

        self.pie_ax.axis("equal")
        self.pie_canvas.figure.tight_layout(pad=1.4)
        self.pie_canvas.draw_idle()





    def _draw_monthly_bar(self):
        self.bar_ax.clear()
        self.bar_ax.set_title("Monthly Income vs Expense", fontsize=10, pad=10)

        rows = get_monthly_income_expense_summary()
        if not rows:
            self.bar_ax.text(
                0.5, 0.5, "No monthly data",
                ha="center", va="center",
                fontsize=11, color="#6b7280"
            )
            self.bar_canvas.draw_idle()
            return

        months = [r["month"] for r in rows]
        income = [r["income"] for r in rows]
        expense = [r["expense"] for r in rows]

        x = range(len(months))
        width = 0.35

        self.bar_ax.bar(
            [i - width / 2 for i in x], income, width,
            label="Income", color="#4f46e5"
        )
        self.bar_ax.bar(
            [i + width / 2 for i in x], expense, width,
            label="Expense", color="#ec4899"
        )

        self.bar_ax.set_xticks(list(x))
        self.bar_ax.set_xticklabels(months, rotation=35, ha="right", fontsize=8)
        self.bar_ax.set_ylabel("Amount (₹)", fontsize=8)
        self.bar_ax.legend(fontsize=8, loc="upper right")
        self.bar_ax.grid(axis="y", linestyle="--", alpha=0.3)

        self.bar_canvas.figure.tight_layout(pad=1)
        self.bar_canvas.draw_idle()


    def _draw_balance_line(self):
        self.balance_ax.clear()
        self.balance_ax.set_title("Balance Over Time", fontsize=10, pad=10)

        points = get_balance_timeseries()
        if not points:
            self.balance_ax.text(
                0.5, 0.5, "No data yet",
                ha="center", va="center",
                fontsize=11, color="#6b7280"
            )
            self.balance_canvas.draw_idle()
            return

        dates = [p["date"] for p in points]
        balances = [p["balance"] for p in points]
        x = range(len(dates))

        self.balance_ax.plot(
            x, balances,
            marker="o", linewidth=2,
            markersize=5, color="#a855f7"
        )

        if len(dates) > 8:
            step = max(1, len(dates) // 8)
            labels = [dates[i] if i % step == 0 else "" for i in range(len(dates))]
        else:
            labels = dates

        self.balance_ax.set_xticks(list(x))
        self.balance_ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        self.balance_ax.set_ylabel("Balance (₹)", fontsize=8)
        self.balance_ax.grid(axis="y", linestyle="--", alpha=0.3)

        self.balance_canvas.figure.tight_layout(pad=1)
        self.balance_canvas.draw_idle()
