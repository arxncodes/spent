import sys
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow, get_light_stylesheet
from db.repository import init_db


def main():
    # Initialize database (create tables + default categories)
    init_db()

    app = QApplication(sys.argv)

    # Default theme: light neumorphic
    app.setStyleSheet(get_light_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
