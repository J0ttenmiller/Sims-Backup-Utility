from theme import Theme
from config_utils import get_theme_mode
from main_window import MainWindow
from PySide6.QtWidgets import QApplication
import sys

from version import __version__
from updater import sync_stored_version_on_startup, silent_update_check

if __name__ == "__main__":
    sync_stored_version_on_startup(__version__)
    
    silent_update_check()

    app = QApplication(sys.argv)

    theme = Theme(get_theme_mode())

    window = MainWindow(theme)
    window.show()

    sys.exit(app.exec())