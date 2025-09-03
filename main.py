from theme import Theme
from config_utils import get_theme_mode, get_update_available
from main_window import MainWindow
from updater import sync_stored_version_on_startup, silent_update_check
from version import __version__

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer
import sys


if __name__ == "__main__":
    app = QApplication(sys.argv)

    sync_stored_version_on_startup(__version__)

    theme = Theme(get_theme_mode())
    window = MainWindow(theme)

    def finished():
        if get_update_available():
            window.show_settings_red_dot()
        else:
            window.hide_settings_red_dot()

    silent_update_check(finished_callback=finished)

    minimized = "--minimized" in sys.argv
    if minimized:
        QTimer.singleShot(100, window.hide)
    else:
        window.show()

    sys.exit(app.exec())