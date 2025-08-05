from theme import Theme
from config_utils import get_theme_mode
from main_window import MainWindow
from PySide6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)

    theme = Theme(get_theme_mode())

    window = MainWindow(theme)
    window.show()

    sys.exit(app.exec())