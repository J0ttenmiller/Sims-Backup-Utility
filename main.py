from theme import Theme
from config_utils import get_theme_mode, get_update_available
from main_window import MainWindow
from updater import sync_stored_version_on_startup, check_updates
from version import __version__

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import sys


if __name__ == "__main__":
    app = QApplication(sys.argv)

    sync_stored_version_on_startup(__version__)

    theme = Theme(get_theme_mode())
    window = MainWindow(theme)

    def finished(latest_version=None, installed_version=None, update_available=None):
        if get_update_available():
            window.show_settings_red_dot()
        else:
            window.hide_settings_red_dot()

    check_updates(parent=window, callback=finished, silent=True)

    if "--minimized" in sys.argv:
        QTimer.singleShot(100, window.hide)
    else:
        window.show()

    sys.exit(app.exec())